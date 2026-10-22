"""Stacking + Platt calibration for the two-model ensemble (ML lane).

Model A and Model B each output a probability per label. For every label we fit one small
LogisticRegression on the *validation* set that takes (logit pA, logit pB) and outputs one probability.
A logistic regression on model scores is exactly Platt scaling, so the stacker both combines the two
models and calibrates the result: when it says 0.8, about 80% of such messages really have the label.
"""

from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression

EPS = 1e-4
MIN_CLASS_COUNT = 2  # need at least this many positives AND negatives on val to fit a stacker


def logit(p: np.ndarray) -> np.ndarray:
    """Log-odds of a probability, clipped so 0 and 1 stay finite."""
    p = np.clip(np.asarray(p, dtype=np.float64), EPS, 1 - EPS)
    return np.log(p / (1 - p))


class Stacker:
    """Platt-calibrated stacker for one label: sigmoid(w_a*logit(pA) + w_b*logit(pB) + b).

    If the validation set has too few positives or negatives for this label, it falls back to the
    plain average of the two models (and records that in `fallback`).
    """

    def __init__(self, seed: int = 0) -> None:
        self.seed = seed
        self.model: LogisticRegression | None = None
        self.fallback = False

    def fit(self, pa: np.ndarray, pb: np.ndarray, y: np.ndarray) -> Stacker:
        y = np.asarray(y, dtype=int)
        positives = int(y.sum())
        if positives < MIN_CLASS_COUNT or len(y) - positives < MIN_CLASS_COUNT:
            self.fallback = True
            return self
        self.model = LogisticRegression(C=1.0, random_state=self.seed, max_iter=1000)
        self.model.fit(self._features(pa, pb), y)
        return self

    def predict(self, pa: np.ndarray, pb: np.ndarray) -> np.ndarray:
        if self.model is None:
            return (np.asarray(pa) + np.asarray(pb)) / 2
        return self.model.predict_proba(self._features(pa, pb))[:, 1]

    @staticmethod
    def _features(pa: np.ndarray, pb: np.ndarray) -> np.ndarray:
        return np.column_stack([logit(pa), logit(pb)])


def reliability_curve(
    probs: np.ndarray, y: np.ndarray, bins: int = 10
) -> tuple[list[float], list[float], list[int]]:
    """Mean predicted probability, observed frequency and count for each non-empty bin."""
    probs = np.asarray(probs, dtype=float).ravel()
    y = np.asarray(y, dtype=float).ravel()
    edges = np.linspace(0, 1, bins + 1)
    index = np.clip(np.digitize(probs, edges[1:-1]), 0, bins - 1)
    mean_pred, observed, counts = [], [], []
    for b in range(bins):
        mask = index == b
        if mask.any():
            mean_pred.append(float(probs[mask].mean()))
            observed.append(float(y[mask].mean()))
            counts.append(int(mask.sum()))
    return mean_pred, observed, counts


def expected_calibration_error(probs: np.ndarray, y: np.ndarray, bins: int = 10) -> float:
    """ECE: average gap between predicted probability and observed frequency, weighted by bin size."""
    mean_pred, observed, counts = reliability_curve(probs, y, bins)
    total = sum(counts)
    if total == 0:
        return 0.0
    return float(
        sum(c * abs(p - o) for p, o, c in zip(mean_pred, observed, counts, strict=True)) / total
    )
