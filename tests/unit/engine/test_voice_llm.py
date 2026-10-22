"""Real OpenAI calls (excluded from make check; run `make test-llm` with OPENAI_API_KEY set)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from backend.app.content import get_scenario
from backend.app.contracts import SkillLabel as L
from backend.app.engine.service import Engine

from .conftest import FIXTURES, Convo, probs

pytestmark = [
    pytest.mark.llm,
    pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="needs OPENAI_API_KEY"),
]


def test_three_real_turns(monkeypatch):
    monkeypatch.setenv("FR_FAKE_LLM", "0")
    engine = Engine(bank_dir=Path(FIXTURES))
    convo = Convo(engine, get_scenario("after-the-breakup"))
    turns = [
        ("hey you seemed off at lunch, you ok?", (L.CHECKED_IN,)),
        ("that sounds really hard. i'm glad you told me", (L.VALIDATED,)),
        ("are you thinking about killing yourself?", (L.ASKED_DIRECTLY,)),
    ]
    for text, labels in turns:
        friend = convo.say(text, probs(*labels))
        assert friend.bubbles  # whichever voice answered, it passed the verifier
        print(text, "->", friend.bubbles, engine.voice_stats)
    assert engine.voice_stats["llm_ok"] >= 1, engine.voice_stats
