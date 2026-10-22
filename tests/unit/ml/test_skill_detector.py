import json

import numpy as np
import pytest

from backend.app.contracts import SkillLabel
from backend.app.ml import skill_detector
from backend.app.ml.model import Components
from backend.app.ml.skill_detector import EmbedderMismatchError, SkillDetector, artifact_ready
from backend.app.ml.train import ARTIFACT, META


def test_predict_returns_all_labels_as_probabilities(detector):
    probs = detector.predict("hey are you ok? you seemed off", ["whatever"])
    assert set(probs) == set(SkillLabel)
    assert all(0.0 <= p <= 1.0 for p in probs.values())


def test_learns_the_obvious_cases(detector):
    ctx = ["i dont want to be here anymore"]
    assert (
        detector.predict("are you thinking about killing yourself?", ctx)[SkillLabel.ASKED_DIRECTLY]
        >= 0.5
    )
    assert detector.predict("you can call or text 988 anytime", ctx)[SkillLabel.REFERRED_988] >= 0.5


def test_predict_is_deterministic(detector):
    a = detector.predict("i'll text you tonight", [])
    b = detector.predict("i'll text you tonight", [])
    assert a == b


def test_artifact_ready_checks_the_embedder(trained_dir, tmp_path, monkeypatch):
    assert artifact_ready(trained_dir)
    assert not artifact_ready(tmp_path)
    monkeypatch.setenv("FR_EMBED", "fastembed")
    assert not artifact_ready(trained_dir)


def test_refuses_to_load_a_mismatched_artifact(trained_dir, tmp_path):
    import joblib

    model = joblib.load(trained_dir / ARTIFACT)
    model.embedder = "some-other-embedder"
    joblib.dump(model, tmp_path / ARTIFACT)
    meta = json.loads((trained_dir / META).read_text())
    (tmp_path / META).write_text(json.dumps({**meta, "embedder": "some-other-embedder"}))
    with pytest.raises(EmbedderMismatchError):
        SkillDetector(tmp_path).predict("hi", [])


def test_uncertain_flags_model_disagreement(detector, monkeypatch):
    pa = np.zeros((1, 10))
    pb = np.zeros((1, 10))
    pa[0, 2], pb[0, 2] = 0.9, 0.2  # asked_directly: the two models disagree by 0.7
    pa[0, 1], pb[0, 1] = 0.6, 0.3  # validated: gap 0.3, not uncertain
    monkeypatch.setattr(
        detector, "components", lambda texts, context: Components(pa=pa, pb=pb, p=pa)
    )
    assert detector.uncertain("x", []) == [SkillLabel.ASKED_DIRECTLY]


def test_explain_gives_valid_offsets(detector):
    text = "lol ur fine dont be dramatic"
    for h in detector.explain(text, ["i feel like everyone hates me"]):
        assert text[h.start : h.end] == h.text and h.delta >= 0.1


def test_not_implemented_without_a_matching_artifact():
    # Repo artifacts are trained with fastembed; under FR_EMBED=hash the stub must stay in charge.
    assert skill_detector.IMPLEMENTED == artifact_ready()
