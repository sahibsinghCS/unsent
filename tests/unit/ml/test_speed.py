"""The /finish speed-ups must not change any output."""

import numpy as np

from backend.app import content
from backend.app.embed import embed
from backend.app.ml.critic import Critic
from backend.app.ml.model import EMBEDDINGS, EmbeddingCache, stacked_proba
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


def test_embedding_cache_gives_the_same_vectors_and_evicts():
    cache = EmbeddingCache(max_items=3)
    assert np.allclose(cache.embed(TEXTS), embed(TEXTS), atol=1e-6)
    assert np.allclose(cache.embed(TEXTS[:2]), embed(TEXTS[:2]), atol=1e-6)  # after eviction too
    assert len(cache._items) <= 3


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
    EMBEDDINGS.clear()
    plain = _report(monkeypatch, SkillDetector(trained_dir, prewarm=False))
    fast = SkillDetector(trained_dir, prewarm=True)
    for node in build(CONVO)[1]:  # what the pipeline does during the chat
        if node.role == "user":
            fast.predict(node.bubbles[0], [])
    assert _same(_report(monkeypatch, fast), plain)
    EMBEDDINGS.clear()
    assert _same(_report(monkeypatch, fast), plain)  # memoized explanations, cold embedding cache


def test_memoized_explanations_are_copies(trained_dir):
    detector = SkillDetector(trained_dir, prewarm=True)
    text = "are you thinking about killing yourself?"
    first = detector.explain(text, [])
    for h in first:
        h.text = "changed"
    assert detector.explain(text, []) == detector.explain_now(text, [])
