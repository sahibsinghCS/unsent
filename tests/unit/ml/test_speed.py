"""The /finish speed-ups must not change any output."""

import numpy as np

from backend.app import content
from backend.app import session as session_module
from backend.app.embed import reset_embedder
from backend.app.ml import skill_detector
from backend.app.ml.critic import Critic
from backend.app.ml.model import stacked_proba
from backend.app.ml.skill_detector import SkillDetector
from tests.unit.ml.test_critic import CONVO, EXEMPLARS, FakeEngine, FakeGuardian, build

TEXTS = [
    "hey are you ok? you seemed really off",
    "that sounds really hard. i'm glad you told me",
    "lol you'll be fine",
    "can we talk to the counselor tomorrow? i'll go with you",
]


def test_stacked_proba_matches_each_logistic_regression(detector):
    model = detector.model
    x = model.vectorizer.transform(TEXTS)
    fast = stacked_proba(model.model_b, model.labels, x)
    slow = np.column_stack([model.model_b[label].predict_proba(x)[:, 1] for label in model.labels])
    assert np.allclose(fast, slow, atol=1e-9)


def _report(monkeypatch, detector):
    monkeypatch.setattr(content, "load_exemplars", lambda scenario_id, locale="en": EXEMPLARS)
    session, path = build(CONVO)
    critic = Critic(detector=detector, guardian=FakeGuardian(), engine=FakeEngine())
    return critic.score_conversation(session, path).model_dump()


def _same(a, b):
    """Reports equal, with probabilities compared to 1e-9."""
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(_same(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(_same(x, y) for x, y in zip(a, b, strict=True))
    if isinstance(a, float):
        return abs(a - b) < 1e-9
    return a == b


def test_fixed_conversation_report_is_identical_with_all_speedups(monkeypatch, trained_dir):
    reset_embedder()
    plain = _report(monkeypatch, SkillDetector(trained_dir, prewarm=False))
    fast = SkillDetector(trained_dir, prewarm=True)
    for node in build(CONVO)[1]:  # what the pipeline does during the chat
        if node.role == "user":
            fast.predict(node.bubbles[0], [])
    assert _same(_report(monkeypatch, fast), plain)
    reset_embedder()
    assert _same(_report(monkeypatch, fast), plain)  # memoized explanations, cold embedding cache


def test_memoized_explanations_are_copies(trained_dir):
    detector = SkillDetector(trained_dir, prewarm=True)
    text = "are you thinking about killing yourself?"
    first = detector.explain(text, [])
    for h in first:
        h.text = "changed"
    assert detector.explain(text, []) == detector.explain_now(text, [])


def test_explanations_expire_with_the_session_ttl(trained_dir, monkeypatch):
    detector = SkillDetector(trained_dir, prewarm=True)
    detector.predict("are you thinking about killing yourself?", [])
    detector.explain("that sounds really hard", [])
    assert len(detector._explanations) == 2
    assert detector.purge_expired() == 0  # still fresh (60-minute TTL)
    monkeypatch.setenv("FR_SESSION_TTL_MIN", "0")
    assert detector.purge_expired() == 2 and not detector._explanations


def test_explanation_purge_is_registered_with_the_session_sweeper(trained_dir, monkeypatch):
    assert skill_detector.purge_expired in session_module._sweepers
    detector = SkillDetector(trained_dir, prewarm=True)
    monkeypatch.setattr(skill_detector, "_service", detector)
    detector.explain("i'll text you tonight", [])
    monkeypatch.setenv("FR_SESSION_TTL_MIN", "0")
    session_module.sweep_derived_caches(force=True)
    assert not detector._explanations


def test_an_expired_explanation_is_recomputed_identically(trained_dir, monkeypatch):
    detector = SkillDetector(trained_dir, prewarm=True)
    text = "hey are you ok? you seemed really off"
    first = detector.explain(text, [])
    monkeypatch.setenv("FR_SESSION_TTL_MIN", "0")
    detector.purge_expired()
    monkeypatch.delenv("FR_SESSION_TTL_MIN")
    assert detector.explain(text, []) == first
