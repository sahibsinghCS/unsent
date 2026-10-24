"""The LLM wrapper never touches the network in tests and always fails safe (LLMUnavailable)."""

from __future__ import annotations

import threading

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


class _FakeCompletions:
    """Stands in for client.chat.completions: replays scripted results and records each request."""

    def __init__(self, results):
        self.results = list(results)
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        result = self.results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


def _response(content: str, finish: str = "stop", tokens_out: int = 20):
    from types import SimpleNamespace as NS

    return NS(
        choices=[NS(message=NS(content=content), finish_reason=finish)],
        usage=NS(prompt_tokens=100, completion_tokens=tokens_out),
    )


def _bad_request(text: str):
    import httpx
    import openai

    request = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    return openai.BadRequestError(text, response=httpx.Response(400, request=request), body=None)


@pytest.fixture
def real_call(monkeypatch, tmp_path):
    """Pretend a real call is allowed, with a scripted fake client and a throwaway usage log."""
    from types import SimpleNamespace as NS

    monkeypatch.setenv("FR_FAKE_LLM", "0")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("FR_LLM_CACHE", "off")
    monkeypatch.setattr(llm, "USAGE_LOG", tmp_path / "usage.jsonl")
    llm._spent.clear()

    def install(results):
        fake = _FakeCompletions(results)
        monkeypatch.setattr(llm, "_openai_client", lambda: NS(chat=NS(completions=fake)))
        return fake

    yield install
    llm._spent.clear()


def test_reasoning_models_are_asked_for_minimal_reasoning(real_call):
    fake = real_call([_response('{"bubbles": ["hey"]}')])
    assert llm.chat_json("actor", [{"role": "user", "content": "hi"}], Reply).bubbles == ["hey"]
    assert fake.calls[0]["reasoning_effort"] == "minimal"


def test_models_without_reasoning_effort_get_the_request_without_it(real_call):
    fake = real_call(
        [
            _bad_request("Unrecognized request argument: reasoning_effort"),
            _response('{"bubbles": ["ok"]}'),
        ]
    )
    assert llm.chat_json("actor", [{"role": "user", "content": "hi"}], Reply).bubbles == ["ok"]
    assert "reasoning_effort" in fake.calls[0] and "reasoning_effort" not in fake.calls[1]


def test_empty_reply_cut_off_by_length_is_retried_with_more_room(real_call):
    fake = real_call(
        [_response("", finish="length", tokens_out=400), _response('{"bubbles": ["yo"]}')]
    )
    assert llm.chat_json(
        "actor", [{"role": "user", "content": "hi"}], Reply, max_tokens=400
    ).bubbles == ["yo"]
    assert [c["max_completion_tokens"] for c in fake.calls] == [400, 1200]
    assert len(llm.USAGE_LOG.read_text().splitlines()) == 2, "both calls count toward the budget"


def test_reasoning_effort_can_be_turned_off(real_call, monkeypatch):
    monkeypatch.setenv("OPENAI_REASONING_EFFORT", "off")
    fake = real_call([_response('{"bubbles": ["hi"]}')])
    llm.chat_json("actor", [{"role": "user", "content": "hi"}], Reply)
    assert "reasoning_effort" not in fake.calls[0]


def test_memory_cache_survives_concurrent_writes_and_purges(monkeypatch):
    """Requests run on a thread pool: writes and sweeps at the same time must never raise."""
    monkeypatch.setenv("FR_LLM_CACHE", "memory")
    monkeypatch.setenv("FR_SESSION_TTL_MIN", "0")  # every entry is already stale: max churn
    errors: list[BaseException] = []

    def hammer(worker: int) -> None:
        try:
            for i in range(300):
                llm._cache_put(f"{worker}-{i}", {"bubbles": ["x"]})
                llm._cache_get(f"{worker}-{i - 1}")
                llm.purge_expired()
        except BaseException as exc:  # noqa: BLE001 - any error is the failure we're testing for
            errors.append(exc)

    threads = [threading.Thread(target=hammer, args=(w,)) for w in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(30)
    llm._memory_cache.clear()
    assert errors == []
