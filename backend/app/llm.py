"""The only place FirstReply talks to an LLM (OpenAI).

What it is used for (and nothing else):
  - the friend's wording (ENGINE lane): the state engine decides WHAT the friend may reveal; the LLM only
    decides HOW to say it, and every reply is verified before it is shown;
  - optional rewrite suggestions (ML lane), always re-scored by our own skill detector;
  - a free extra moderation signal (SAFETY lane);
  - red-team attacker bots (RED-TEAM lane).
It is never used in unit tests (fakes) and never to generate datasets (data is written into files).

Every call is cached (same input -> same output), logged (token counts and estimated cost; never message
text) and capped by a daily budget. Privacy: in production (FR_ENV=prod) the cache and the usage log live
only in memory (cache entries expire with the session TTL, 60 min), so nothing is written to disk. In
development it is a disk cache under .cache/llm/ (gitignored) for repeatable tests and demos. If the key is missing, the budget is spent, or the API
fails, calls raise LLMUnavailable and callers fall back to local behaviour (e.g. the reviewed line bank).
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from collections.abc import Callable
from datetime import date
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from backend.app.config import ROOT, env_flag, is_prod, session_ttl_seconds

T = TypeVar("T", bound=BaseModel)

CACHE_DIR = ROOT / ".cache" / "llm"
USAGE_LOG = ROOT / "eval" / "logs" / "llm_usage.jsonl"
MODERATION_MODEL = "omni-moderation-latest"
DEFAULT_MODEL = "gpt-5-mini"


class LLMUnavailable(RuntimeError):
    """Raised when no LLM answer can be produced; callers must fall back to local behaviour."""


# ---------------------------------------------------------------- configuration


def model_for(role: str) -> str:
    """Model for a role ('actor', 'judge', 'bulk'): OPENAI_MODEL_<ROLE>, else OPENAI_MODEL, else default."""
    return os.getenv(f"OPENAI_MODEL_{role.upper()}") or os.getenv("OPENAI_MODEL", DEFAULT_MODEL)


def enabled() -> bool:
    """FR_LLM=0 turns every LLM feature off (fully offline mode)."""
    return env_flag("FR_LLM", default=True)


def fake_mode() -> bool:
    """Fakes are used when FR_FAKE_LLM=1, and automatically inside pytest unless FR_FAKE_LLM=0."""
    explicit = os.getenv("FR_FAKE_LLM")
    if explicit is not None and explicit.strip() != "":
        return explicit.strip().lower() in {"1", "true", "yes", "on"}
    return "PYTEST_CURRENT_TEST" in os.environ


def daily_budget_usd() -> float:
    return float(os.getenv("LLM_DAILY_BUDGET_USD", "2.0"))


def _prices() -> tuple[float, float]:
    """(input, output) USD per 1M tokens, used only for the budget estimate. Set them to your model's prices."""
    return (
        float(os.getenv("OPENAI_PRICE_INPUT_PER_M", "0.25")),
        float(os.getenv("OPENAI_PRICE_OUTPUT_PER_M", "2.00")),
    )


# ---------------------------------------------------------------- fakes (tests and offline demos)

FakeFn = Callable[[list[dict], type[BaseModel]], BaseModel | dict]
_fakes: dict[str, FakeFn] = {}


def register_fake(prompt_name: str, fn: FakeFn) -> None:
    """Register a deterministic fake answer for a prompt (used in tests and FR_FAKE_LLM=1)."""
    _fakes[prompt_name] = fn


def clear_fakes() -> None:
    _fakes.clear()


# ---------------------------------------------------------------- budget and usage log

_lock = threading.Lock()
_spent: dict[str, float] = {}


def spent_today_usd() -> float:
    today = date.today().isoformat()
    with _lock:
        if today not in _spent:
            total = 0.0
            if not is_prod() and USAGE_LOG.exists():
                for raw in USAGE_LOG.read_text(encoding="utf-8").splitlines():
                    try:
                        row = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    if row.get("day") == today:
                        total += float(row.get("est_cost_usd", 0.0))
            _spent.clear()
            _spent[today] = total
        return _spent[today]


def _log_usage(entry: dict[str, Any]) -> None:
    """Record one call's tokens and estimated cost (never message text). In production it stays in
    memory, so nothing is written to disk; in development it is appended to eval/logs/llm_usage.jsonl."""
    today = date.today().isoformat()
    entry = {"day": today, "ts": time.time(), **entry}
    spent_today_usd()  # load today's running total (and roll over the day) before adding to it
    with _lock:
        _spent[today] = _spent.get(today, 0.0) + float(entry.get("est_cost_usd", 0.0))
        if is_prod():
            return
        USAGE_LOG.parent.mkdir(parents=True, exist_ok=True)
        with USAGE_LOG.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")


def status() -> dict[str, Any]:
    """Shown by /api/health and the Transparency page."""
    return {
        "enabled": enabled(),
        "fake": fake_mode(),
        "has_key": bool(os.getenv("OPENAI_API_KEY")),
        "model_actor": model_for("actor"),
        "spent_today_usd": round(spent_today_usd(), 4),
        "daily_budget_usd": daily_budget_usd(),
    }


# ---------------------------------------------------------------- cache


def _cache_key(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


def cache_mode() -> str:
    """'disk' (dev default: repeatable tests and demos), 'memory' (prod default: nothing written to disk,
    entries expire with the session TTL) or 'off'. Override with FR_LLM_CACHE."""
    mode = os.getenv("FR_LLM_CACHE", "").strip().lower()
    if mode in {"disk", "memory", "off"}:
        return mode
    return "memory" if is_prod() else "disk"


_memory_cache: dict[str, tuple[float, dict]] = {}


def _cache_get(key: str) -> dict | None:
    mode = cache_mode()
    if mode == "off":
        return None
    if mode == "memory":
        item = _memory_cache.get(key)
        if item is None or time.time() - item[0] > session_ttl_seconds():
            _memory_cache.pop(key, None)
            return None
        return item[1]
    path = CACHE_DIR / key[:2] / f"{key}.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
    return None


def purge_expired() -> int:
    """Drop in-memory cache entries older than the session TTL (production cache). Returns the count."""
    cutoff = time.time() - session_ttl_seconds()
    stale = [k for k, (ts, _) in list(_memory_cache.items()) if ts < cutoff]
    for key in stale:
        _memory_cache.pop(key, None)
    return len(stale)


def _cache_put(key: str, value: dict) -> None:
    mode = cache_mode()
    if mode == "off":
        return
    if mode == "memory":
        cutoff = time.time() - session_ttl_seconds()
        for stale in [k for k, (ts, _) in _memory_cache.items() if ts < cutoff]:
            del _memory_cache[stale]
        _memory_cache[key] = (time.time(), value)
        return
    path = CACHE_DIR / key[:2] / f"{key}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------- client

_client_lock = threading.Lock()
_client: Any = None


def _openai_client() -> Any:
    global _client
    with _client_lock:
        if _client is None:
            from openai import OpenAI

            _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"], timeout=20.0, max_retries=1)
        return _client


def _ensure_real_call_allowed() -> None:
    if not enabled():
        raise LLMUnavailable("LLM disabled (FR_LLM=0)")
    if not os.getenv("OPENAI_API_KEY"):
        raise LLMUnavailable("OPENAI_API_KEY is not set")
    if spent_today_usd() >= daily_budget_usd():
        raise LLMUnavailable("daily LLM budget reached")


def chat_json(
    prompt_name: str,
    messages: list[dict[str, str]],
    schema: type[T],
    role: str = "actor",
    temperature: float | None = 0.8,
    max_tokens: int = 400,
    seed: int | None = None,
    use_cache: bool = True,
) -> T:
    """Ask the LLM for a JSON object matching `schema`. Raises LLMUnavailable on any failure."""
    if fake_mode():
        fake = _fakes.get(prompt_name)
        if fake is None:
            raise LLMUnavailable(f"no fake registered for prompt '{prompt_name}'")
        result = fake(messages, schema)
        return result if isinstance(result, schema) else schema.model_validate(result)

    _ensure_real_call_allowed()
    model = model_for(role)
    key = _cache_key(
        {
            "model": model,
            "messages": messages,
            "schema": schema.__name__,
            "temperature": temperature,
            "seed": seed,
        }
    )
    if use_cache:
        cached = _cache_get(key)
        if cached is not None:
            try:
                parsed = schema.model_validate(cached)
                _log_usage({"role": role, "prompt": prompt_name, "model": model, "cached": True})
                return parsed
            except ValidationError:
                pass

    started = time.perf_counter()
    response = _create_completion(model, messages, schema, temperature, max_tokens, seed)
    latency_ms = (time.perf_counter() - started) * 1000
    content = response.choices[0].message.content or ""
    usage = getattr(response, "usage", None)
    tokens_in = getattr(usage, "prompt_tokens", 0) or 0
    tokens_out = getattr(usage, "completion_tokens", 0) or 0
    price_in, price_out = _prices()
    _log_usage(
        {
            "role": role,
            "prompt": prompt_name,
            "model": model,
            "cached": False,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "est_cost_usd": (tokens_in * price_in + tokens_out * price_out) / 1_000_000,
            "latency_ms": round(latency_ms),
        }
    )
    try:
        data = json.loads(content)
        parsed = schema.model_validate(data)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise LLMUnavailable(f"LLM returned invalid JSON for {schema.__name__}") from exc
    if use_cache:
        _cache_put(key, data)
    return parsed


def _create_completion(
    model: str,
    messages: list[dict[str, str]],
    schema: type[BaseModel],
    temperature: float | None,
    max_tokens: int,
    seed: int | None,
) -> Any:
    """Call Chat Completions, dropping parameters a model rejects (some models only allow defaults)."""
    import openai

    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_completion_tokens": max_tokens,
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": schema.__name__, "schema": schema.model_json_schema()},
        },
    }
    if temperature is not None:
        kwargs["temperature"] = temperature
    if seed is not None:
        kwargs["seed"] = seed
    for _ in range(4):
        try:
            return _openai_client().chat.completions.create(**kwargs)
        except openai.BadRequestError as exc:
            text = str(exc).lower()
            if "temperature" in text and "temperature" in kwargs:
                kwargs.pop("temperature")
            elif "seed" in text and "seed" in kwargs:
                kwargs.pop("seed")
            elif "response_format" in text or "json_schema" in text:
                kwargs["response_format"] = {"type": "json_object"}
            else:
                raise LLMUnavailable(f"OpenAI rejected the request: {exc}") from exc
        except openai.APIError as exc:
            raise LLMUnavailable(f"OpenAI error: {exc}") from exc
    raise LLMUnavailable("OpenAI request could not be made compatible with this model")


def moderate(text: str) -> dict[str, float]:
    """OpenAI moderation category scores (free endpoint), e.g. {'self-harm/intent': 0.93, ...}."""
    if fake_mode():
        fake = _fakes.get("moderation")
        if fake is None:
            raise LLMUnavailable("no fake registered for 'moderation'")
        return dict(fake([{"role": "user", "content": text}], BaseModel))  # type: ignore[arg-type]
    _ensure_real_call_allowed()
    key = _cache_key({"moderation": MODERATION_MODEL, "text": text})
    cached = _cache_get(key)
    if cached is not None:
        return cached
    import openai

    try:
        result = _openai_client().moderations.create(model=MODERATION_MODEL, input=text)
    except openai.APIError as exc:
        raise LLMUnavailable(f"moderation error: {exc}") from exc
    scores = result.results[0].category_scores
    data = scores.model_dump(by_alias=True) if hasattr(scores, "model_dump") else dict(scores)
    data = {k: float(v) for k, v in data.items() if v is not None}
    _cache_put(key, data)
    _log_usage(
        {"role": "moderation", "prompt": "moderation", "model": MODERATION_MODEL, "cached": False}
    )
    return data
