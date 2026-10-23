import numpy as np

from backend.app.contracts import SkillLabel
from backend.app.ml.experiments import compare_pooling, out_of_fold
from backend.app.ml.model import sentences


def test_sentences_only_split_multi_sentence_messages():
    assert sentences("are you ok?") == []
    assert sentences("i'm glad you told me. can we talk to the counselor? ok") == [
        "i'm glad you told me.",
        "can we talk to the counselor?",
    ]


def test_pooling_keeps_negatives_on_the_whole_message(detector):
    model = detector.model
    text = "i won't tell anyone. except the counselor, because i care about you"
    whole_pa, whole_pb = model.base_proba([text], [""])
    model_pooling = model.pooling
    try:
        model.pooling = True
        pa, pb = model.scored_proba([text], [""])
    finally:
        model.pooling = model_pooling
    secrecy = list(model.labels).index(SkillLabel.PROMISED_SECRECY.value)
    referred = list(model.labels).index(SkillLabel.REFERRED_ADULT.value)
    # Batched float32 math can differ in the last bits between batch sizes and CPUs, so compare the
    # logic (negatives keep the whole-message score, positives take the max) with a tiny tolerance.
    tol = 1e-5
    assert np.isclose(pa[0, secrecy], whole_pa[0, secrecy], atol=tol)
    assert np.isclose(pb[0, secrecy], whole_pb[0, secrecy], atol=tol)
    assert pa[0, referred] >= whole_pa[0, referred] - tol  # positives can only go up (max)


def test_out_of_fold_never_scores_a_row_with_its_own_stacker():
    rng = np.random.default_rng(0)
    pa, pb = rng.uniform(size=(40, 2)), rng.uniform(size=(40, 2))
    y = (pa > 0.5).astype(int)
    p = out_of_fold(pa, pb, y, folds=5, seed=0)
    assert p.shape == pa.shape and np.all((p >= 0) & (p <= 1))


def test_compare_pooling_reports_both_variants(detector):
    from backend.app.content import read_jsonl
    from tests.unit.ml.conftest import SEED

    rows = read_jsonl(SEED)
    result = compare_pooling(detector.model, rows[:60], {"test": rows[60:]}, folds=3)
    assert set(result) == {"whole", "pooled", "adopt", "rule"}
    assert {"val_oof", "test"} <= set(result["pooled"])
    assert isinstance(result["adopt"], bool)
    assert detector.model.pooling is False  # the experiment never mutates the live model
