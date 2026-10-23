"""Token buckets: limits per client and per endpoint group, refill, daily cap, cleanup."""

from __future__ import annotations

import re

from backend.app.ops.ratelimit import DAY, MINUTE, Limit, RateLimiter, Rule, default_rules


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def test_defaults_match_the_spec(monkeypatch):
    for name in ("SESSIONS", "MESSAGES", "WHATIF", "GUARDIAN"):
        monkeypatch.delenv(f"FR_RL_{name}_PER_MIN", raising=False)
    rules = {r.group: r for r in default_rules()}
    assert [lim.limit for lim in rules["session_create"].limits] == [10]
    assert [(lim.limit, lim.period) for lim in rules["message"].limits] == [
        (30, MINUTE),
        (300, DAY),
    ]
    assert rules["whatif"].limits[0].limit == 6
    assert rules["guardian"].limits[0].limit == 30


def test_limits_are_env_configurable(monkeypatch):
    monkeypatch.setenv("FR_RL_SESSIONS_PER_MIN", "3")
    rules = {r.group: r for r in default_rules()}
    assert rules["session_create"].limits[0].limit == 3


def test_routes_map_to_groups_and_health_is_exempt():
    limiter = RateLimiter(clock=Clock())
    group = lambda m, p: r.group if (r := limiter.rule_for(m, p)) else None  # noqa: E731
    assert group("POST", "/api/sessions") == "session_create"
    assert group("POST", "/api/sessions/s_abc/messages") == "message"
    assert group("POST", "/api/sessions/s_abc/whatif") == "whatif"
    assert group("POST", "/api/guardian/check") == "guardian"
    assert group("GET", "/api/sessions/s_abc") == "api"
    assert group("GET", "/api/health") is None
    assert group("GET", "/assets/index.js") is None


def test_bucket_refuses_then_refills():
    clock = Clock()
    limiter = RateLimiter(clock=clock)
    for _ in range(10):
        assert limiter.check("1.2.3.4", "POST", "/api/sessions") is None
    wait = limiter.check("1.2.3.4", "POST", "/api/sessions")
    assert wait is not None and 0 < wait <= 6.01  # one token every 6 s
    assert limiter.check("5.6.7.8", "POST", "/api/sessions") is None  # other clients unaffected
    clock.now += wait
    assert limiter.check("1.2.3.4", "POST", "/api/sessions") is None


def test_groups_have_separate_buckets():
    limiter = RateLimiter(clock=Clock())
    for _ in range(6):
        assert limiter.check("c", "POST", "/api/sessions/s_1/whatif") is None
    assert limiter.check("c", "POST", "/api/sessions/s_1/whatif") is not None
    assert limiter.check("c", "POST", "/api/sessions/s_1/messages") is None


def test_daily_cap_applies_even_when_per_minute_allows():
    clock = Clock()
    rules = [
        Rule("m", "POST", re.compile(r"/m"), (Limit("m/min", 30, MINUTE), Limit("m/day", 40, DAY)))
    ]
    limiter = RateLimiter(rules=rules, clock=clock)
    sent = 0
    for _ in range(10):  # 10 minutes of trying 30 per minute
        for _ in range(30):
            if limiter.check("c", "POST", "/m") is None:
                sent += 1
        clock.now += MINUTE
    assert sent == 40  # the daily bucket refills only ~0.3 tokens in 10 minutes
    assert limiter.check("c", "POST", "/m") is not None


def test_refused_request_takes_no_token():
    clock = Clock()
    limiter = RateLimiter(clock=clock)
    for _ in range(6):
        limiter.check("c", "POST", "/api/sessions/s/whatif")
    for _ in range(50):  # hammering while blocked doesn't push the wait further out
        limiter.check("c", "POST", "/api/sessions/s/whatif")
    clock.now += 10.0
    assert limiter.check("c", "POST", "/api/sessions/s/whatif") is None


def test_idle_buckets_are_cleaned_up():
    clock = Clock()
    limiter = RateLimiter(clock=clock)
    for i in range(50):
        limiter.check(f"client{i}", "POST", "/api/sessions")
    assert len(limiter) == 50
    clock.now += 2 * MINUTE
    limiter.check("new", "POST", "/api/sessions")
    assert len(limiter) == 1
