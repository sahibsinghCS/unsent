"""The LLM wrapper never touches the network in tests and always fails safe (LLMUnavailable)."""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from backend.app import llm


class Reply(BaseModel):
    bubbles: list[str]


@pytest.fixture(autouse=True)
def _clean_fakes():
    llm.clear_fakes()
    yield
    llm.clear_fakes()


def test_pytest_runs_in_fake_mode():
    assert llm.fake_mode()


def test_registered_fake_is_used_and_validated():
    llm.register_fake("actor", lambda messages, schema: {"bubbles": ["hey"]})
    reply = llm.chat_json("actor", [{"role": "user", "content": "hi"}], Reply)
    assert reply.bubbles == ["hey"]


def test_missing_fake_raises_unavailable():
    with pytest.raises(llm.LLMUnavailable):
        llm.chat_json("actor", [{"role": "user", "content": "hi"}], Reply)


def test_disabled_or_missing_key_raises_unavailable(monkeypatch):
    monkeypatch.setenv("FR_FAKE_LLM", "0")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(llm.LLMUnavailable):
        llm.chat_json("actor", [{"role": "user", "content": "hi"}], Reply)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("FR_LLM", "0")
    with pytest.raises(llm.LLMUnavailable):
        llm.chat_json("actor", [{"role": "user", "content": "hi"}], Reply)


def test_budget_guard(monkeypatch, tmp_path):
    monkeypatch.setenv("FR_FAKE_LLM", "0")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("LLM_DAILY_BUDGET_USD", "0.01")
    monkeypatch.setattr(llm, "USAGE_LOG", tmp_path / "usage.jsonl")
    llm._spent.clear()
    llm._log_usage({"role": "actor", "prompt": "actor", "est_cost_usd": 0.02})
    with pytest.raises(llm.LLMUnavailable, match="budget"):
        llm.chat_json("actor", [{"role": "user", "content": "hi"}], Reply)
    llm._spent.clear()


def test_cache_key_is_stable_and_input_sensitive():
    a = llm._cache_key({"model": "m", "messages": [{"role": "user", "content": "hi"}]})
    b = llm._cache_key({"model": "m", "messages": [{"role": "user", "content": "hi"}]})
    c = llm._cache_key({"model": "m", "messages": [{"role": "user", "content": "hey"}]})
    assert a == b != c


def test_model_for_role(monkeypatch):
    monkeypatch.setenv("OPENAI_MODEL_JUDGE", "judge-model")
    assert llm.model_for("judge") == "judge-model"
    monkeypatch.delenv("OPENAI_MODEL_ACTOR", raising=False)
    monkeypatch.setenv("OPENAI_MODEL", "base-model")
    assert llm.model_for("actor") == "base-model"


def test_production_cache_is_memory_only_and_expires(monkeypatch, tmp_path):
    monkeypatch.setenv("FR_ENV", "prod")
    monkeypatch.delenv("FR_LLM_CACHE", raising=False)
    monkeypatch.setattr(llm, "CACHE_DIR", tmp_path / "cache")
    assert llm.cache_mode() == "memory"
    llm._cache_put("abc", {"bubbles": ["hi"]})
    assert llm._cache_get("abc") == {"bubbles": ["hi"]}
    assert not (tmp_path / "cache").exists(), "nothing may be written to disk in production"
    monkeypatch.setenv("FR_SESSION_TTL_MIN", "0")
    assert llm._cache_get("abc") is None
    llm._memory_cache.clear()


def test_dev_cache_defaults_to_disk(monkeypatch):
    monkeypatch.setenv("FR_ENV", "dev")
    monkeypatch.delenv("FR_LLM_CACHE", raising=False)
    assert llm.cache_mode() == "disk"
    monkeypatch.setenv("FR_LLM_CACHE", "off")
    assert llm.cache_mode() == "off"


def test_production_usage_log_stays_in_memory(monkeypatch, tmp_path):
    monkeypatch.setenv("FR_ENV", "prod")
    monkeypatch.setattr(llm, "USAGE_LOG", tmp_path / "usage.jsonl")
    llm._spent.clear()
    llm._log_usage({"role": "actor", "prompt": "actor", "est_cost_usd": 0.03})
    llm._log_usage({"role": "actor", "prompt": "actor", "est_cost_usd": 0.02})
    assert not (tmp_path / "usage.jsonl").exists(), "nothing may be written to disk in production"
    assert abs(llm.spent_today_usd() - 0.05) < 1e-9
    llm._spent.clear()


def test_dev_usage_log_adds_to_todays_file_total(monkeypatch, tmp_path):
    monkeypatch.setenv("FR_ENV", "dev")
    log = tmp_path / "usage.jsonl"
    monkeypatch.setattr(llm, "USAGE_LOG", log)
    llm._spent.clear()
    llm._log_usage({"role": "actor", "prompt": "actor", "est_cost_usd": 0.04})
    llm._spent.clear()  # e.g. a restart: the file still holds today's spending
    llm._log_usage({"role": "actor", "prompt": "actor", "est_cost_usd": 0.01})
    assert log.exists() and len(log.read_text().splitlines()) == 2
    assert abs(llm.spent_today_usd() - 0.05) < 1e-9
    llm._spent.clear()
