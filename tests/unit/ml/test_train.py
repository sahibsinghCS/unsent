import json
import shutil

import numpy as np
import pytest

from backend.app.content import read_jsonl
from backend.app.ml.data import load_splits, to_xy
from backend.app.ml.model import LABELS
from backend.app.ml.train import ARTIFACT, MAX_ARTIFACT_MB, META, train
from tests.unit.ml.conftest import SEED


def test_seed_set_is_valid_final_jsonl():
    rows = read_jsonl(SEED)
    assert len(rows) >= 100
    keys = {"id", "context_id", "scenario_id", "level", "context", "text", "lang", "labels"}
    for row in rows:
        assert keys <= set(row)
        assert set(row["labels"]) == {label.value for label in LABELS}
    _, _, y = to_xy(rows)
    assert (y.sum(axis=0) >= 5).all(), "every label needs some positives"


def test_meta_records_provenance(trained_dir):
    meta = json.loads((trained_dir / META).read_text())
    assert meta["embedder"] == "hash-char-ngrams-512"
    assert set(meta["counts"]) == {"train", "val", "test"} and sum(meta["counts"].values()) > 100
    assert len(meta["data_hash"]) == 64 and meta["trained_at"]
    assert 0 <= meta["metrics"]["test"]["macro_f1"] <= 1
    assert (trained_dir / ARTIFACT).stat().st_size < MAX_ARTIFACT_MB * 1e6


def test_training_is_deterministic(seed_data_dir, trained_dir, tmp_path, detector):
    from backend.app.ml.skill_detector import SkillDetector

    train(seed_data_dir, tmp_path, seed=0)
    again = SkillDetector(tmp_path)
    text, ctx = "that sounds so hard, want to talk to the counselor?", ["i failed again"]
    a, b = detector.predict(text, ctx), again.predict(text, ctx)
    assert np.allclose([a[k] for k in LABELS], [b[k] for k in LABELS])


def test_splits_dir_is_preferred_and_test_is_never_fitted(tmp_path):
    rows = read_jsonl(SEED)
    (tmp_path / "splits").mkdir()
    for name, part in (("train", rows[:80]), ("val", rows[80:100]), ("test", rows[100:])):
        with (tmp_path / "splits" / f"{name}.jsonl").open("w") as f:
            f.writelines(json.dumps(r) + "\n" for r in part)
    splits = load_splits(tmp_path)
    assert [len(splits[s]) for s in ("train", "val", "test")] == [80, 20, len(rows) - 100]
    meta = train(tmp_path, tmp_path / "out")
    assert meta["counts"]["test"] == len(rows) - 100


def test_missing_data_is_a_clear_error(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_splits(tmp_path)


def test_copy_of_seed_round_trips(tmp_path):
    shutil.copy(SEED, tmp_path / "final.jsonl")
    splits = load_splits(tmp_path)
    assert sum(len(v) for v in splits.values()) == len(read_jsonl(SEED))
