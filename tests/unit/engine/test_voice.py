"""LLM voice (faked, never the real API): prompt limits, verifier catches, retry, bank fallback."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from backend.app import llm, services
from backend.app.content import get_scenario
from backend.app.contracts import ActorOutput, State
from backend.app.contracts import Reaction as R
from backend.app.contracts import SkillLabel as L
from backend.app.engine import actor
from backend.app.engine.verifier import fact_leaks, verify
from backend.app.engine.voice import path_seed, system_prompt

from .conftest import FIXTURES, Convo, probs


@pytest.fixture(autouse=True)
def _no_fakes():
    llm.clear_fakes()
    yield
    llm.clear_fakes()


class Fake:
    """Returns the given replies in order (last one repeats) and records every prompt."""

    def __init__(self, *replies: dict) -> None:
        self.replies, self.calls = list(replies), []

    def __call__(self, messages, schema):
        self.calls.append(messages)
        return self.replies[min(len(self.calls), len(self.replies)) - 1]


def say(
    text="are you ok? you seem off", labels=(L.CHECKED_IN,), convo=None, engine=None, scenario=None
):
    convo = convo or Convo(engine, scenario)
    return convo, convo.say(text, probs(*labels))


GOOD = {"bubbles": ["honestly not great", "i cant sleep lately"], "fact_ids": ["f1a"]}


def test_good_llm_reply_is_used(engine, scenario):
    fake = Fake(GOOD)
    llm.register_fake("actor", fake)
    convo, friend = say(engine=engine, scenario=scenario)
    assert friend.bubbles == GOOD["bubbles"] and friend.line_id is None
    assert len(fake.calls) == 1 and engine.voice_stats["llm_ok"] == 1


def test_prompt_has_only_unlocked_facts_reaction_examples_and_history(engine, scenario):
    fake = Fake(GOOD)
    llm.register_fake("actor", fake)
    convo, _ = say(engine=engine, scenario=scenario)
    messages = fake.calls[0]
    system = messages[0]["content"]
    level = convo.state.level
    for lvl, spec in scenario.levels.items():
        for fact in spec.facts:
            assert (fact.text in system) == (int(lvl) <= level), fact.id
    assert "Reaction: CHECKED_IN" in system
    assert "## Examples" in system and '["' in system  # bank lines as style examples
    assert messages[-1] == {"role": "user", "content": "are you ok? you seem off"}
    assert messages[1]["role"] == "assistant"  # the friend's opening
    assert "$" not in system  # every placeholder filled


def test_locked_fact_leak_is_caught_then_retry_fixes_it(engine, scenario):
    leak = {"bubbles": ["honestly sometimes i dont want to be alive"], "fact_ids": []}
    fake = Fake(leak, GOOD)
    llm.register_fake("actor", fake)
    _, friend = say(engine=engine, scenario=scenario)
    assert friend.bubbles == GOOD["bubbles"]
    assert len(fake.calls) == 2
    assert "rejected by the safety check" in fake.calls[1][0]["content"]
    assert "suicidal thoughts before level 3" in fake.calls[1][0]["content"]


@pytest.mark.parametrize(
    "bad",
    [
        {"bubbles": ["as an AI language model i cant feel that"]},
        {"bubbles": ["you should call 988 tbh"]},
        {"bubbles": ["you should see a therapist lol"]},
        {"bubbles": ["ok"], "fact_ids": ["f3a"]},  # declares a locked fact
        {"bubbles": ["i took some pills"]},
        {"bubbles": ["a", "b", "c", "d"]},  # schema violation -> treated as unavailable
        {"bubbles": ["x" * 260]},
    ],
)
def test_bad_llm_replies_fall_back_to_bank(engine, scenario, bad):
    llm.register_fake("actor", Fake(bad))
    _, friend = say(engine=engine, scenario=scenario)
    assert friend.line_id and friend.line_id.startswith("atb-")
    assert engine.voice_stats["llm_ok"] == 0


def test_rejected_twice_then_bank(engine, scenario):
    fake = Fake({"bubbles": ["im just a simulation"]})
    llm.register_fake("actor", fake)
    _, friend = say(engine=engine, scenario=scenario)
    assert len(fake.calls) == 2 and engine.voice_stats["llm_rejected"] == 2
    assert friend.line_id is not None


def test_no_fake_means_unavailable_means_bank(engine, scenario):
    _, friend = say(engine=engine, scenario=scenario)
    assert friend.line_id is not None and engine.voice_stats["llm_unavailable"] == 1


def test_fr_llm_off_uses_bank_without_key(engine, scenario, monkeypatch):
    monkeypatch.setenv("FR_FAKE_LLM", "0")
    monkeypatch.setenv("FR_LLM", "0")
    _, friend = say(engine=engine, scenario=scenario)
    assert friend.line_id is not None


def test_silent_turn_never_calls_llm(engine, scenario):
    fake = Fake(GOOD)
    llm.register_fake("actor", fake)
    _, friend = say("lol you'll be fine", (L.DISMISSED,), engine=engine, scenario=scenario)
    assert friend.seen_no_reply and fake.calls == []


def test_llm_output_source_and_verify(scenario, bank):
    ok = ActorOutput(bubbles=["idk just tired"], source="llm")
    assert verify(ok, scenario, State(level=0), bank).ok
    leak = ActorOutput(bubbles=["i feel like a burden to everyone"], source="llm")
    result = verify(leak, scenario, State(level=1), bank)
    assert not result.ok and any("f2b" in r for r in result.reasons)
    assert verify(leak, scenario, State(level=2), bank).ok  # unlocked at level 2


def test_suicidal_disclosure_backstop_only_below_level_3(scenario):
    text = ["sometimes i think about not being here"]
    assert fact_leaks(text, scenario, 2, threshold=2.0)  # lexicon catches it without embeddings
    assert not fact_leaks(text, scenario, 3, threshold=2.0)


def test_leak_detector_on_labeled_set():
    rows = [json.loads(x) for x in (FIXTURES.parents[3] / "eval/engine/leak_set.jsonl").open()]
    tp = fp = fn = 0
    for row in rows:
        caught = bool(fact_leaks([row["text"]], get_scenario(row["scenario_id"]), row["level"]))
        tp += caught and row["leak"]
        fp += caught and not row["leak"]
        fn += (not caught) and row["leak"]
    assert tp / (tp + fn) >= 0.85, (tp, fp, fn)  # recall: leaks are the safety-relevant error
    assert tp / (tp + fp) >= 0.75, (tp, fp, fn)


def test_seed_and_prompt_are_deterministic(scenario):
    convo = Convo(services.engine(), scenario)
    convo.say("hey", probs())
    assert path_seed(convo.path) == path_seed(list(convo.path))
    state = convo.state
    assert system_prompt(scenario, state, R.NEUTRAL, []) == system_prompt(
        scenario, state, R.NEUTRAL, []
    )


def test_api_marks_llm_voice(monkeypatch):
    monkeypatch.setenv(actor.BANK_DIR_ENV, str(FIXTURES))
    monkeypatch.setenv("FR_STUB_ONLY", "guardian,skills,critic,whatif")
    services.reset()
    llm.register_fake(
        "actor", Fake({"bubbles": ["lol im fine", "just tired"], "fact_ids": ["f0a"]})
    )
    from backend.app.main import app

    client = TestClient(app)
    sid = client.post("/api/sessions", json={"scenario_id": "after-the-breakup"}).json()[
        "session_id"
    ]
    body = client.post(f"/api/sessions/{sid}/messages", json={"text": "you ok?"}).json()
    assert body["friend_node"]["voice"] == "llm"
    assert body["friend_node"]["bubbles"] == ["lol im fine", "just tired"]
