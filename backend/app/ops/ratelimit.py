"""In-memory token-bucket rate limits, one set of buckets per client.

A bucket holds up to `limit` tokens and refills at `limit / period` tokens per second. Each request
takes one token; an empty bucket means "too many requests" and tells the client how long to wait.
Everything lives in memory, which is fine because the app runs exactly one worker process.
"""

from __future__ import annotations

import math
import os
import re
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass

from backend.app.config import env_flag, env_int, is_prod

MINUTE = 60.0
DAY = 86_400.0


@dataclass(frozen=True)
class Limit:
    """`limit` requests per `period` seconds."""

    name: str
    limit: int
    period: float

    @property
    def rate(self) -> float:
        return self.limit / self.period


@dataclass(frozen=True)
class Rule:
    """Which requests a group of limits applies to."""

    group: str
    method: str
    pattern: re.Pattern[str]
    limits: tuple[Limit, ...]


def default_rules() -> list[Rule]:
    """Limits from the environment (per client). First matching rule wins; /api/health is exempt."""

    def per_min(group: str, env: str, default: int) -> Limit:
        return Limit(f"{group}/min", env_int(env, default), MINUTE)

    session = r"/api/sessions/[^/]+"
    return [
        Rule("session_create", "POST", re.compile(r"/api/sessions/?"),
             (per_min("session_create", "FR_RL_SESSIONS_PER_MIN", 10),)),
        Rule("message", "POST", re.compile(session + r"/messages/?"),
             (per_min("message", "FR_RL_MESSAGES_PER_MIN", 30),
              Limit("message/day", env_int("FR_RL_MESSAGES_PER_DAY", 300), DAY))),
        Rule("whatif", "POST", re.compile(session + r"/whatif/?"),
             (per_min("whatif", "FR_RL_WHATIF_PER_MIN", 6),)),
        Rule("guardian", "POST", re.compile(r"/api/guardian/check/?"),
             (per_min("guardian", "FR_RL_GUARDIAN_PER_MIN", 30),)),
        Rule("api", "*", re.compile(r"/api/.*"), (per_min("api", "FR_RL_API_PER_MIN", 240),)),
    ]  # fmt: skip


EXEMPT_PATHS = frozenset({"/api/health", "/api/health/"})


def rate_limit_enabled() -> bool:
    """On by default in prod (FR_ENV=prod); FR_RATE_LIMIT=0/1 overrides."""
    return env_flag("FR_RATE_LIMIT", default=is_prod())


class RateLimiter:
    """Thread-safe token buckets keyed by (client, limit name)."""

    def __init__(
        self,
        rules: list[Rule] | None = None,
        clock: Callable[[], float] = time.monotonic,
        max_idle: float = 2 * DAY,
    ) -> None:
        self.rules = rules if rules is not None else default_rules()
        self._clock = clock
        self._max_idle = max_idle
        self._buckets: dict[tuple[str, str], tuple[float, float]] = {}  # -> (tokens, updated)
        self._lock = threading.Lock()
        self._last_cleanup = clock()

    def rule_for(self, method: str, path: str) -> Rule | None:
        if path in EXEMPT_PATHS:
            return None
        for rule in self.rules:
            if rule.method in ("*", method) and rule.pattern.fullmatch(path):
                return rule
        return None

    def check(self, client: str, method: str, path: str) -> float | None:
        """Take a token for this request. Returns None if allowed, else seconds until retry."""
        rule = self.rule_for(method, path)
        if rule is None:
            return None
        now = self._clock()
        with self._lock:
            if now - self._last_cleanup > MINUTE:
                self._cleanup(now)
            levels = [self._level(client, limit, now) for limit in rule.limits]
            waits = [
                (1.0 - tokens) / limit.rate
                for limit, tokens in zip(rule.limits, levels, strict=True)
                if tokens < 1.0
            ]
            if waits:  # refused: keep the refilled levels but take nothing
                for limit, tokens in zip(rule.limits, levels, strict=True):
                    self._buckets[(client, limit.name)] = (tokens, now)
                return max(waits)
            for limit, tokens in zip(rule.limits, levels, strict=True):
                self._buckets[(client, limit.name)] = (tokens - 1.0, now)
        return None

    def _level(self, client: str, limit: Limit, now: float) -> float:
        tokens, updated = self._buckets.get((client, limit.name), (float(limit.limit), now))
        return min(float(limit.limit), tokens + (now - updated) * limit.rate)

    def _cleanup(self, now: float) -> None:
        """Forget buckets that have been idle long enough to be full again (or past max_idle)."""
        periods = {limit.name: limit.period for rule in self.rules for limit in rule.limits}
        stale = [
            key
            for key, (_, updated) in self._buckets.items()
            if now - updated > min(self._max_idle, periods.get(key[1], DAY))
        ]
        for key in stale:
            del self._buckets[key]
        self._last_cleanup = now

    def __len__(self) -> int:
        with self._lock:
            return len(self._buckets)


def retry_after_header(seconds: float) -> str:
    """Whole seconds, at least 1 (HTTP Retry-After takes an integer)."""
    return str(max(1, math.ceil(seconds)))


def trust_proxy() -> bool:
    return os.getenv("FR_TRUST_PROXY", "0").strip().lower() in {"1", "true", "yes", "on"}


def proxy_hops() -> int:
    """How many trusted proxies append to X-Forwarded-For (FR_PROXY_HOPS, default 1)."""
    try:
        return max(1, int(os.getenv("FR_PROXY_HOPS", "1")))
    except ValueError:
        return 1
