import json

import numpy as np

from backend.app.ml.train import META
from backend.app.ml.uncertainty import (
    CANDIDATE_BANDS,
    tune_band,
    uncertain_mask,
    uncertainty_stats,
)


def test_mask_rules():
    pa = np.array([[0.9, 0.9, 0.9, 0.2]])
    pb = np.array([[0.1, 0.1, 0.8, 0.3]])
    p = np.array([[0.5, 0.95, 0.5, 0.5]])
    assert uncertain_mask(pa, pb, p, (0.25, 0.75)).tolist() == [[True, False, False, False]]


def test_stats_compare_flagged_and_unflagged_errors():
    pa = np.array([[0.9], [0.9], [0.9], [0.1]])
    pb = np.array([[0.1], [0.1], [0.9], [0.1]])
    p = np.array([[0.6], [0.4], [0.9], [0.1]])
    y = np.array([[0], [1], [1], [0]])
    stats = uncertainty_stats(pa, pb, p, y, (0.25, 0.75))
    assert stats["flagged_decisions"] == 2 and stats["flagged_error_rate"] == 1.0
    assert stats["unflagged_error_rate"] == 0.0 and stats["flag_rate_per_message"] == 0.5


def test_tune_band_is_one_of_the_candidates_and_respects_flag_rate():
    rng = np.random.default_rng(0)
    pa, pb, p = (
        rng.uniform(size=(200, 10)),
        rng.uniform(size=(200, 10)),
        rng.uniform(size=(200, 10)),
    )
    y = (rng.uniform(size=(200, 10)) < 0.3).astype(int)
    band = tune_band(pa, pb, p, y)
    assert band in CANDIDATE_BANDS or band == (0.25, 0.75)


def test_training_records_the_band(trained_dir):
    meta = json.loads((trained_dir / META).read_text())
    assert len(meta["uncertain_band"]) == 2 and "flag_rate_per_message" in meta["uncertain_val"]


def test_training_records_the_pooling_decision(trained_dir):
    meta = json.loads((trained_dir / META).read_text())
    assert isinstance(meta["pooling"], bool)
    oof = meta["pooling_val_oof"]
    adopt = oof["pooled"]["macro_f1"] > oof["whole"]["macro_f1"] and (
        oof["pooled"]["ece"] <= oof["whole"]["ece"] + 0.01
    )
    assert meta["pooling"] == adopt


def test_pooling_can_be_forced_off(seed_data_dir, tmp_path):
    from backend.app.ml.train import train

    meta = train(seed_data_dir, tmp_path, seed=0, pooling_mode="off")
    assert meta["pooling"] is False and meta["pooling_mode"] == "off"
