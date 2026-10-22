"""Agreement with counselor labels: Cohen's kappa + bootstrap CI (ML lane).

    uv run python -m backend.app.ml.kappa \
        --ours data/skills/final.jsonl --counselor data/skills/counselor_labels.jsonl

Both files are JSON lines with {"id", "labels": {label: bool}} (the counselor file comes from the data
lane's import_counselor.py). Rows are matched by id. With --model, our side is the trained detector's
prediction (p ≥ 0.5) on the counselor rows' text instead of our human labels.

Kappa answers: "how much more do we agree than two people flipping coins with the same habits?"
1 = perfect, 0 = chance level, below 0 = worse than chance.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

import numpy as np

from backend.app.config import DATA_DIR, EVAL_REPORTS_DIR
from backend.app.content import read_jsonl
from backend.app.ml.model import LABELS

BOOTSTRAP = 1000


def cohen_kappa(a: np.ndarray, b: np.ndarray) -> float:
    """Cohen's kappa for two 0/1 raters. If chance agreement is 1 (both constant), 1.0 if identical."""
    a = np.asarray(a, dtype=int).ravel()
    b = np.asarray(b, dtype=int).ravel()
    if a.size == 0:
        return float("nan")
    observed = float(np.mean(a == b))
    pa, pb = a.mean(), b.mean()
    expected = float(pa * pb + (1 - pa) * (1 - pb))
    if expected >= 1.0:
        return 1.0 if observed == 1.0 else 0.0
    return (observed - expected) / (1 - expected)


def bootstrap_ci(
    a: np.ndarray, b: np.ndarray, n_boot: int = BOOTSTRAP, seed: int = 0
) -> tuple[float, float]:
    """95% percentile CI of kappa, resampling rows (a/b may be 1-D or rows × labels)."""
    rng = np.random.default_rng(seed)
    n = len(a)
    values = [cohen_kappa(a[idx], b[idx]) for idx in (rng.integers(0, n, n) for _ in range(n_boot))]
    low, high = np.percentile(values, [2.5, 97.5])
    return float(low), float(high)


def label_matrix(rows: list[dict]) -> np.ndarray:
    return np.array(
        [
            [int(bool(r.get("labels", {}).get(label.value, False))) for label in LABELS]
            for r in rows
        ],
        dtype=int,
    ).reshape(len(rows), len(LABELS))


def agreement(ours: list[dict], counselor: list[dict], seed: int = 0) -> dict:
    """{label: {kappa, ci95, n}} plus 'overall' (all row×label decisions pooled)."""
    by_id = {str(r["id"]): r for r in ours}
    pairs = [(by_id[str(c["id"])], c) for c in counselor if str(c["id"]) in by_id]
    if not pairs:
        raise ValueError("no overlapping ids between the two label files")
    a = label_matrix([p[0] for p in pairs])
    b = label_matrix([p[1] for p in pairs])
    out: dict = {}
    for j, label in enumerate(LABELS):
        low, high = bootstrap_ci(a[:, j], b[:, j], seed=seed)
        out[label.value] = {
            "kappa": round(cohen_kappa(a[:, j], b[:, j]), 4),
            "ci95": [round(low, 4), round(high, 4)],
            "n": len(pairs),
        }
    low, high = bootstrap_ci(a, b, seed=seed)
    out["overall"] = {
        "kappa": round(cohen_kappa(a, b), 4),
        "ci95": [round(low, 4), round(high, 4)],
        "n": len(pairs),
    }
    return out


def model_rows(counselor: list[dict]) -> list[dict]:
    """Detector predictions (p ≥ 0.5) on the counselor rows, in the same {id, labels} format."""
    from backend.app.ml.skill_detector import get_service

    detector = get_service()
    rows = []
    for row in counselor:
        probs = detector.predict(row["text"], row.get("context") or [])
        rows.append({"id": row["id"], "labels": {k.value: v >= 0.5 for k, v in probs.items()}})
    return rows


def to_records(result: dict, source: str) -> list[dict]:
    created = dt.datetime.now(dt.UTC).isoformat(timespec="seconds")
    return [
        {
            "lane": "ml",
            "metric": f"counselor_kappa_{name}",
            "value": stats["kappa"],
            "n": stats["n"],
            "split": "counselor",
            "notes": f"{source} vs counselor; 95% bootstrap CI {stats['ci95']} ({BOOTSTRAP} resamples)",
            "ci95": stats["ci95"],
            "created": created,
        }
        for name, stats in result.items()
    ]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Cohen's kappa vs counselor labels")
    parser.add_argument("--ours", type=Path, default=DATA_DIR / "skills" / "final.jsonl")
    parser.add_argument(
        "--counselor", type=Path, default=DATA_DIR / "skills" / "counselor_labels.jsonl"
    )
    parser.add_argument("--model", action="store_true", help="use detector predictions as 'ours'")
    parser.add_argument("--out", type=Path, default=EVAL_REPORTS_DIR / "ml_counselor.json")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args(argv)
    counselor = read_jsonl(args.counselor)
    ours = model_rows(counselor) if args.model else read_jsonl(args.ours)
    source = "detector" if args.model else "our labels"
    result = agreement(ours, counselor, seed=args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(to_records(result, source), indent=2) + "\n", encoding="utf-8")
    overall = result["overall"]
    print(f"overall kappa {overall['kappa']} CI {overall['ci95']} n={overall['n']} -> {args.out}")


if __name__ == "__main__":
    main()
