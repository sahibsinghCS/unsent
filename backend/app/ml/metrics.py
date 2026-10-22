"""Shared scoring helpers for training and evaluation (per-label precision/recall/F1)."""

from __future__ import annotations

import numpy as np
from sklearn.metrics import precision_recall_fscore_support

from backend.app.ml.model import LABELS

THRESHOLD = 0.5


def per_label_scores(y: np.ndarray, probs: np.ndarray, threshold: float = THRESHOLD) -> dict:
    """{label: {precision, recall, f1, support}} plus 'macro_f1' over labels that occur in y."""
    pred = (probs >= threshold).astype(int)
    out: dict = {}
    f1s = []
    for j, label in enumerate(LABELS):
        p, r, f, _ = precision_recall_fscore_support(
            y[:, j], pred[:, j], average="binary", zero_division=0
        )
        support = int(y[:, j].sum())
        out[label.value] = {
            "precision": round(float(p), 4),
            "recall": round(float(r), 4),
            "f1": round(float(f), 4),
            "support": support,
        }
        if support > 0:
            f1s.append(float(f))
    out["macro_f1"] = round(float(np.mean(f1s)), 4) if f1s else 0.0
    return out
