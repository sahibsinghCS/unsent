"""When to say "uncertain" (ML lane).

A label is flagged only if Model A and Model B land on opposite sides of 0.5 AND the final calibrated
probability sits in a middle band. The band is chosen on the validation set (never on a test set):
the widest band whose flagged decisions are clearly more error-prone than unflagged ones while keeping
the flag rate low, so the flag stays rare and meaningful.
"""

from __future__ import annotations

import numpy as np

DEFAULT_BAND = (0.25, 0.75)
CANDIDATE_BANDS = ((0.35, 0.65), (0.3, 0.7), (0.25, 0.75), (0.2, 0.8), (0.15, 0.85))
MAX_FLAG_RATE = 0.15  # at most this share of messages may carry any uncertain flag (on val)


def uncertain_mask(pa: np.ndarray, pb: np.ndarray, p: np.ndarray, band=DEFAULT_BAND) -> np.ndarray:
    """Boolean (rows × labels): models disagree about yes/no and the final probability is mid-band."""
    low, high = band
    disagree = (np.asarray(pa) >= 0.5) != (np.asarray(pb) >= 0.5)
    p = np.asarray(p)
    return disagree & (p >= low) & (p <= high)


def uncertainty_stats(pa, pb, p, y, band=DEFAULT_BAND) -> dict:
    """Flag rate per message and error rate of flagged vs unflagged label decisions (threshold 0.5)."""
    mask = uncertain_mask(pa, pb, p, band)
    wrong = (np.asarray(p) >= 0.5) != (np.asarray(y) == 1)
    flagged, unflagged = wrong[mask], wrong[~mask]
    return {
        "band": list(band),
        "messages": int(mask.shape[0]),
        "flag_rate_per_message": round(float(mask.any(axis=1).mean()), 4) if mask.size else 0.0,
        "flagged_decisions": int(mask.sum()),
        "flagged_error_rate": round(float(flagged.mean()), 4) if flagged.size else None,
        "unflagged_error_rate": round(float(unflagged.mean()), 4) if unflagged.size else None,
    }


def tune_band(pa, pb, p, y) -> tuple[float, float]:
    """Pick the band on validation data: biggest error-rate gap, flag rate ≤ MAX_FLAG_RATE."""
    best, best_gap = DEFAULT_BAND, -1.0
    for band in CANDIDATE_BANDS:
        stats = uncertainty_stats(pa, pb, p, y, band)
        if stats["flagged_error_rate"] is None or stats["flag_rate_per_message"] > MAX_FLAG_RATE:
            continue
        gap = stats["flagged_error_rate"] - (stats["unflagged_error_rate"] or 0.0)
        if gap > best_gap + 1e-9:
            best, best_gap = band, gap
    return best
