"""Reading the labeled practice replies (data/skills, written by the data lane) for training and eval."""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np

from backend.app.content import read_jsonl
from backend.app.ml.model import LABELS

SPLITS = ("train", "val", "test")
# Extra held-out test sets the data lane may add (evaluated separately, never trained on).
EXTRA_TEST_SETS = {
    "test_freeform": "test_freeform.jsonl",
    "survey_real": "survey_real.jsonl",
    "cross_model": "test_cross_model.jsonl",
}


def _bucket(row_id: str) -> str:
    """Deterministic 70/15/15 split by a hash of the row id (used only when no splits/ exist)."""
    value = int(hashlib.sha256(row_id.encode()).hexdigest(), 16) % 100
    return "train" if value < 70 else "val" if value < 85 else "test"


def load_splits(data_dir: Path) -> dict[str, list[dict]]:
    """train/val/test rows: from data_dir/splits/ if present, else a hash split of final.jsonl."""
    split_dir = data_dir / "splits"
    if all((split_dir / f"{name}.jsonl").exists() for name in SPLITS):
        return {name: read_jsonl(split_dir / f"{name}.jsonl") for name in SPLITS}
    final = data_dir / "final.jsonl"
    if not final.exists():
        raise FileNotFoundError(f"no splits/ or final.jsonl in {data_dir}")
    out: dict[str, list[dict]] = {name: [] for name in SPLITS}
    for row in read_jsonl(final):
        out[_bucket(str(row["id"]))].append(row)
    return out


def load_extra_test_sets(data_dir: Path) -> dict[str, list[dict]]:
    """Optional extra test sets found in data_dir or data_dir/splits (name -> rows)."""
    found: dict[str, list[dict]] = {}
    for name, filename in EXTRA_TEST_SETS.items():
        for folder in (data_dir / "splits", data_dir):
            if (folder / filename).exists():
                rows = [r for r in read_jsonl(folder / filename) if "labels" in r]
                if rows:
                    found[name] = rows
                break
    return found


def data_hash(data_dir: Path) -> str:
    """sha256 over the files the model is trained and evaluated on (provenance in the meta file)."""
    digest = hashlib.sha256()
    for name in [f"splits/{s}.jsonl" for s in SPLITS] + ["final.jsonl"]:
        path = data_dir / name
        if path.exists():
            digest.update(name.encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


def last_friend_message(row: dict) -> str:
    context = row.get("context") or []
    return context[-1] if context else ""


def to_xy(rows: list[dict]) -> tuple[list[str], list[str], np.ndarray]:
    """texts, last friend messages, and a (n × 10) 0/1 label matrix (missing labels count as 0)."""
    texts = [row["text"] for row in rows]
    contexts = [last_friend_message(row) for row in rows]
    y = np.array(
        [
            [int(bool(row.get("labels", {}).get(label.value, False))) for label in LABELS]
            for row in rows
        ],
        dtype=int,
    ).reshape(len(rows), len(LABELS))
    return texts, contexts, y
