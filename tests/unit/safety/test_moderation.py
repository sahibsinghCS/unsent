"""Optional OpenAI moderation signal: supporting evidence only; the local speaker rules win."""

from __future__ import annotations

import pytest

from backend.app import llm
from backend.app.safety.guardian import Guardian


@pytest.fixture
def fake_moderation():
    scores: dict[str, float] = {}
    llm.register_fake("moderation", lambda messages, schema: dict(scores))
    yield scores
    llm.clear_fakes()


def test_offline_behaves_identically():
    llm.clear_fakes()  # no fake registered -> LLMUnavailable, like no key or no network
    on, off = Guardian(use_moderation=True), Guardian(use_moderation=False)
    for text in ["i want to kill myself", "are you thinking about suicide?", "kys", "you ok?"]:
        a, b = on.check_user(text, []), off.check_user(text, [])
        assert (a.level, a.action, a.categories, a.sources) == (
            b.level,
            b.action,
            b.categories,
            b.sources,
        )


def test_moderation_cannot_overrule_asking_the_friend(fake_moderation):
    fake_moderation.update({"self-harm": 0.97, "self-harm/intent": 0.91})
    result = Guardian(use_moderation=True).check_user(
        "are you thinking about killing yourself?", []
    )
    assert (result.level, result.action) == ("none", "continue")
    assert "moderation" not in result.sources
    assert any("overruled by speaker rules" in e for e in result.evidence)


def test_moderation_supports_a_local_crisis(fake_moderation):
    fake_moderation.update({"self-harm/intent": 0.95})
    result = Guardian(use_moderation=True).check_user("i want to kill myself", [])
    assert result.level == "crisis"
    assert "moderation" in result.sources and "lexicon" in result.sources


def test_moderation_alone_only_raises_to_concern(fake_moderation):
    fake_moderation.update({"self-harm/intent": 0.93})
    result = Guardian(use_moderation=True).check_user("the plan for saturday is set", [])
    assert (result.level, result.action) == ("concern", "show_resources")
    assert result.sources == ["moderation"]


def test_moderation_never_blocks_or_pauses_alone(fake_moderation):
    fake_moderation.update({"harassment": 0.99, "violence": 0.99, "self-harm": 0.6})
    result = Guardian(use_moderation=True).check_user("the plan for saturday is set", [])
    assert result.action == "continue"


def test_moderation_low_scores_change_nothing(fake_moderation):
    fake_moderation.update({"self-harm": 0.01})
    result = Guardian(use_moderation=True).check_user("you ok?", [])
    assert (result.action, result.evidence) == ("continue", [])
