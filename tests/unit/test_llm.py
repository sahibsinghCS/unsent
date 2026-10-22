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
