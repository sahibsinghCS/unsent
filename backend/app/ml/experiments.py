"""Clause-pooling experiment (ML lane): does scoring each sentence help multi-skill messages?

Decision rule, fixed before looking at results: adopt pooling only if the out-of-fold macro-F1 on val
improves AND calibration (ECE) gets no more than 0.01 worse. Out-of-fold = the stacker is refitted on 4/5
of val and scored on the other 1/5 (5 folds, seeded), so the comparison isn't flattered by fitting and
scoring on the same rows. Test sets are reported for information only; they never decide anything.
"""

from __future__ import annotations

import copy

import numpy as np
from sklearn.model_selection import KFold

from backend.app.ml.calibrate import Stacker, expected_calibration_error
from backend.app.ml.data import to_xy
from backend.app.ml.metrics import per_label_scores
from backend.app.ml.model import LABELS, SkillModel
from backend.app.ml.rules import gate_asked_directly

MAX_ECE_INCREASE = 0.01
ASKED = [label.value for label in LABELS].index("asked_directly")


def _gate(p: np.ndarray, texts: list[str]) -> np.ndarray:
    p = p.copy()
    p[:, ASKED] = gate_asked_directly(texts, list(p[:, ASKED]))
    return p


def out_of_fold(pa: np.ndarray, pb: np.ndarray, y: np.ndarray, folds: int, seed: int) -> np.ndarray:
    """Stacked probabilities where each val row is scored by a stacker that never saw it."""
    p = np.zeros_like(pa)
    for fit_idx, score_idx in KFold(folds, shuffle=True, random_state=seed).split(pa):
        for j in range(pa.shape[1]):
            stacker = Stacker(seed).fit(pa[fit_idx, j], pb[fit_idx, j], y[fit_idx, j])
            p[score_idx, j] = stacker.predict(pa[score_idx, j], pb[score_idx, j])
    return p


def _summary(y: np.ndarray, p: np.ndarray) -> dict:
    return {
        "macro_f1": per_label_scores(y, p)["macro_f1"],
        "ece": round(expected_calibration_error(p, y), 4),
        "brier": round(float(np.mean((p - y) ** 2)), 4),
        "validated_f1": per_label_scores(y, p)["validated"]["f1"],
    }


def compare_pooling(
    model: SkillModel, val: list[dict], info_sets: dict[str, list[dict]], folds=5, seed=0
) -> dict:
    """{'whole': {...}, 'pooled': {...}, 'adopt': bool} with val OOF and info-only test numbers."""
    texts, contexts, y = to_xy(val)
    folds = min(folds, len(val))
    out: dict = {}
    for name, pooling in (("whole", False), ("pooled", True)):
        variant = copy.deepcopy(model)
        variant.pooling = pooling
        pa, pb = variant.scored_proba(texts, contexts)
        result = {"val_oof": _summary(y, _gate(out_of_fold(pa, pb, y, folds, seed), texts))}
        variant.fit_stackers(texts, contexts, y)
        for set_name, rows in info_sets.items():
            set_texts, set_contexts, set_y = to_xy(rows)
            result[set_name] = _summary(set_y, variant.components(set_texts, set_contexts).p)
        out[name] = result
    whole, pooled = out["whole"]["val_oof"], out["pooled"]["val_oof"]
    out["adopt"] = bool(
        pooled["macro_f1"] > whole["macro_f1"] and pooled["ece"] <= whole["ece"] + MAX_ECE_INCREASE
    )
    out["rule"] = (
        "adopt iff val out-of-fold macro-F1 improves and ECE rises by at most "
        f"{MAX_ECE_INCREASE}; {folds}-fold, seed {seed}"
    )
    return out
