"""A chat never mixes languages: language check, Spanish LLM voice, Spanish fallbacks, ES patterns."""

from __future__ import annotations

import json
import os

import pytest

from backend.app import llm
from backend.app.content import LINES_DIR, get_scenario
from backend.app.contracts import ActorOutput, Line, State
from backend.app.contracts import Reaction as R
from backend.app.contracts import SkillLabel as L
from backend.app.embed import reset_embedder
from backend.app.engine import actor
from backend.app.engine.language import detect, wrong_language
from backend.app.engine.service import Engine
from backend.app.engine.verifier import fact_leaks, verify

from .conftest import Convo, probs

ES_BANK = LINES_DIR / "after-the-breakup.es.jsonl"
needs_es_bank = pytest.mark.skipif(not ES_BANK.exists(), reason="no Spanish bank yet")


@pytest.fixture(autouse=True)
def _no_fakes():
    llm.clear_fakes()
    yield
    llm.clear_fakes()


class Fake:
    def __init__(self, *replies: dict) -> None:
        self.replies, self.calls = list(replies), []

    def __call__(self, messages, schema):
        self.calls.append(messages)
        return self.replies[min(len(self.calls), len(self.replies)) - 1]


@pytest.mark.parametrize(
    ("bubbles", "expected"),
    [
        (["honestly im just tired", "its whatever"], "en"),
        (["la neta estoy cansada", "no sé jaja"], "es"),
        (["jaja ok", "perdón, es que no he dormido nada"], "es"),
        (["ok"], None),
        (["...", "😭"], None),
        (["lol you'll be fine"], "en"),
    ],
)
def test_detect(bubbles, expected):
    assert detect(bubbles) == expected


def test_wrong_language():
    assert wrong_language(["i just cant sleep lately"], "es") == "en"
    assert wrong_language(["no puedo dormir"], "en") == "es"
    assert wrong_language(["ok"], "es") is None
    assert wrong_language(["i just cant sleep"], "fr") is None  # unchecked locales


def test_no_bank_line_is_flagged_as_the_wrong_language():
    for path in sorted(LINES_DIR.glob("*.jsonl")) if LINES_DIR.exists() else []:
        for row in map(json.loads, path.open(encoding="utf-8")):
            assert not wrong_language(row["bubbles"], row["locale"]), (path.name, row["id"])


@needs_es_bank
def test_english_llm_reply_in_spanish_chat_falls_back_to_spanish_bank():
    fake = Fake({"bubbles": ["honestly not great", "i just cant sleep"], "fact_ids": []})
    llm.register_fake("actor", fake)
    engine = Engine()
    convo = Convo(engine, get_scenario("after-the-breakup"), locale="es")
    friend = convo.say("oye, ¿estás bien? te vi rara", probs(L.CHECKED_IN))
    assert len(fake.calls) == 2  # one retry, told why
    assert "wrong language" in fake.calls[1][0]["content"]
    assert friend.line_id and "-es-" in friend.line_id
    assert detect(friend.bubbles) in ("es", None)


@needs_es_bank
def test_spanish_llm_reply_passes_and_prompt_is_spanish():
    reply = {"bubbles": ["la neta no muy bien", "no he podido dormir jaja"], "fact_ids": ["f1a"]}
    fake = Fake(reply)
    llm.register_fake("actor", fake)
    convo = Convo(Engine(), get_scenario("after-the-breakup"), locale="es")
    friend = convo.say("oye, ¿estás bien? te vi rara", probs(L.CHECKED_IN))
    assert friend.bubbles == reply["bubbles"] and len(fake.calls) == 1
    system = fake.calls[0][0]["content"]
    assert "Write ONLY in Spanish" in system and "jaja" in system
    es_texts = {json.dumps(json.loads(r)["bubbles"], ensure_ascii=False) for r in ES_BANK.open()}
    examples = [ln[2:] for ln in system.splitlines() if ln.startswith('- ["')]
    assert examples and all(ex in es_texts for ex in examples)  # few-shot from the Spanish bank


@needs_es_bank
def test_spanish_chat_never_falls_back_to_english():
    scenario = get_scenario("after-the-breakup")
    bank = actor.load_bank(scenario.id, "es")
    state = State(level=2, turn=3, trust=45)
    ranked = actor.ranked_candidates(scenario, state, [], "x", probs(L.FOLLOW_UP), "es", bank)
    # Every candidate is a Spanish bank line: the English scenario fallbacks are never offered.
    assert ranked and all(c.line is not None and c.line.locale == "es" for c in ranked)
    # Even if every line with the reaction is gone, the last resort is a calm Spanish line.
    calm_only = [ln for ln in bank if ln.reaction == R.NEUTRAL and ln.level == 0]
    ranked = actor.ranked_candidates(scenario, state, [], "x", probs(L.FOLLOW_UP), "es", calm_only)
    assert all(c.line is not None and c.line.locale == "es" for c in ranked)


def test_english_fallback_or_line_rejected_in_spanish_chat(scenario):
    fallback = ActorOutput(bubbles=[scenario.fallback_lines[0][0]], source="fallback")
    assert verify(fallback, scenario, State(), [], locale="en").ok
    assert not verify(fallback, scenario, State(), [], locale="es").ok
    line = Line(id="x", scenario_id=scenario.id, level=0, reaction=R.NEUTRAL, bubbles=["idk lol"])
    output = ActorOutput(bubbles=line.bubbles, line_id="x", source="bank")
    assert any(
        "wrong language" in r
        for r in verify(output, scenario, State(), [line], locale="es").reasons
    )


@pytest.mark.parametrize(
    ("bubbles", "level", "reason"),
    [
        (["como una IA no tengo sentimientos"], 1, "breaks character"),
        (["esto es solo una simulación jaja"], 1, "breaks character"),
        (["deberías hablar con un terapeuta"], 1, "advice"),
        (["llama a la línea de crisis"], 2, "advice"),
        (["a veces quiero morirme"], 2, "suicidal thoughts"),
        (["compré pastillas"], 2, "method word"),
        (["call 988 if you need to"], 2, "advice"),
    ],
)
def test_spanish_and_resource_patterns(scenario, bubbles, level, reason):
    output = ActorOutput(bubbles=bubbles, source="llm")
    result = verify(output, scenario, State(level=level), [])
    assert not result.ok and any(reason in r for r in result.reasons), result.reasons


def test_friend_may_accept_988_at_level_4_and_not_really_is_not_a_persona_break(scenario):
    ok = ActorOutput(bubbles=["ok", "we can text 988 together"], source="llm")
    assert verify(ok, scenario, State(level=4, status="ended_success"), [], locale="en").ok
    hungry = ActorOutput(bubbles=["im not really hungry"], source="llm")
    assert verify(hungry, scenario, State(level=1), []).ok


def test_bank_line_disclosing_too_early_is_caught_at_runtime(scenario):
    line = Line(id="early", scenario_id=scenario.id, level=2, reaction=R.ASKED_DIRECTLY,
                bubbles=["sometimes i think about not being here"])  # fmt: skip
    output = ActorOutput(bubbles=line.bubbles, line_id="early", source="bank")
    assert not verify(output, scenario, State(level=2), [line]).ok
    assert verify(output, scenario, State(level=3), [line]).ok


@pytest.mark.slow
def test_fact_leak_detected_across_languages(monkeypatch):
    """The real multilingual model links a Spanish reply to an English fact (needs the model)."""
    monkeypatch.setenv("FR_EMBED", "fastembed")
    reset_embedder()
    try:
        from backend.app.embed import embed_one

        embed_one("hola")
    except Exception as exc:  # no model download possible (offline CI)
        pytest.skip(f"fastembed model unavailable: {exc}")
    scenario = get_scenario("after-the-breakup")
    assert fact_leaks(["siento que solo soy una carga para mis amigos"], scenario, 1)  # f2b
    assert fact_leaks(["siento que nada va a mejorar nunca"], scenario, 1)  # f2a
    assert not fact_leaks(["solo estoy cansada, no he dormido"], scenario, 1)  # f0a/f1a: unlocked
    assert not fact_leaks(["todos en la escuela ya saben, qué vergüenza"], scenario, 1)  # f1b
    os.environ["FR_EMBED"] = "hash"
    reset_embedder()
