"""Train the skill detector (ML lane).

    make train                                   # data/skills, real embeddings
    uv run python -m backend.app.ml.train --data-dir DIR --out-dir models

Model A and Model B are fitted on train, the stackers on val, and test is only scored (never fitted).
Writes skill_detector.joblib + skill_detector.meta.json (data hash, counts, date, metrics, embedder).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import random
from pathlib import Path

import joblib
import numpy as np

from backend.app.config import DATA_DIR, MODELS_DIR
from backend.app.embed import get_embedder
from backend.app.ml.data import SPLITS, data_hash, load_splits, to_xy
from backend.app.ml.metrics import per_label_scores
from backend.app.ml.model import SkillModel
from backend.app.ml.uncertainty import tune_band, uncertainty_stats

ARTIFACT = "skill_detector.joblib"
META = "skill_detector.meta.json"
MAX_ARTIFACT_MB = 25


def train(data_dir: Path, out_dir: Path, seed: int = 0) -> dict:
    """Train, save the artifact + meta file into out_dir, and return the meta dict."""
    random.seed(seed)
    np.random.seed(seed)
    splits = load_splits(data_dir)
    if not splits["train"] or not splits["val"]:
        raise ValueError("train and val splits must both be non-empty")
    model = SkillModel(embedder=get_embedder().name, seed=seed)
    model.fit_base(*to_xy(splits["train"]))
    val_texts, val_contexts, val_y = to_xy(splits["val"])
    model.fit_stackers(val_texts, val_contexts, val_y)
    val = model.components(val_texts, val_contexts)
    model.uncertain_band = tune_band(val.pa, val.pb, val.p, val_y)

    metrics = {}
    for name in ("val", "test"):
        if splits[name]:
            texts, contexts, y = to_xy(splits[name])
            metrics[name] = per_label_scores(y, model.components(texts, contexts).p)

    out_dir.mkdir(parents=True, exist_ok=True)
    artifact = out_dir / ARTIFACT
    joblib.dump(model, artifact, compress=3)
    size_mb = artifact.stat().st_size / 1e6
    if size_mb > MAX_ARTIFACT_MB:
        raise RuntimeError(f"artifact is {size_mb:.1f} MB (> {MAX_ARTIFACT_MB} MB)")
    meta = {
        "embedder": model.embedder,
        "data_dir": str(data_dir),
        "data_hash": data_hash(data_dir),
        "counts": {name: len(splits[name]) for name in SPLITS},
        "seed": seed,
        "trained_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "artifact_mb": round(size_mb, 2),
        "stacker_fallback_labels": [k for k, s in model.stackers.items() if s.fallback],
        "uncertain_band": list(model.uncertain_band),
        "uncertain_val": uncertainty_stats(val.pa, val.pb, val.p, val_y, model.uncertain_band),
        "metrics": metrics,
    }
    (out_dir / META).write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return meta


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR / "skills")
    parser.add_argument("--out-dir", type=Path, default=MODELS_DIR)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args(argv)
    meta = train(args.data_dir, args.out_dir, args.seed)
    summary = {k: v["macro_f1"] for k, v in meta["metrics"].items()}
    print(f"trained with {meta['embedder']} on {meta['counts']} -> macro-F1 {summary}")
    print(f"saved {args.out_dir / ARTIFACT} ({meta['artifact_mb']} MB)")


if __name__ == "__main__":
    main()
