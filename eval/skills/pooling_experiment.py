"""Clause-pooling experiment -> eval/reports/ml_pooling.json (decision made on val only).

FR_EMBED=fastembed uv run python eval/skills/pooling_experiment.py
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.config import DATA_DIR, EVAL_REPORTS_DIR, MODELS_DIR  # noqa: E402
from backend.app.ml.data import load_extra_test_sets, load_splits  # noqa: E402
from backend.app.ml.experiments import compare_pooling  # noqa: E402
from backend.app.ml.skill_detector import SkillDetector  # noqa: E402


def to_records(result: dict, sizes: dict[str, int]) -> list[dict]:
    created = dt.datetime.now(dt.UTC).isoformat(timespec="seconds")
    records = []
    for variant in ("whole", "pooled"):
        for split, stats in result[variant].items():
            for metric, value in stats.items():
                records.append(
                    {
                        "lane": "ml",
                        "metric": f"pooling_{variant}_{metric}",
                        "value": value,
                        "n": sizes[split],
                        "split": split,
                        "notes": f"clause-pooling experiment; adopt={result['adopt']}; {result['rule']}"
                        + ("" if split == "val_oof" else "; info only, not used to decide"),
                        "created": created,
                    }
                )
    return records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR / "skills")
    parser.add_argument("--models-dir", type=Path, default=MODELS_DIR)
    parser.add_argument("--report", type=Path, default=EVAL_REPORTS_DIR / "ml_pooling.json")
    args = parser.parse_args(argv)
    splits = load_splits(args.data_dir)
    info = {"test": splits["test"], **load_extra_test_sets(args.data_dir)}
    model = SkillDetector(args.models_dir).model
    result = compare_pooling(model, splits["val"], info)
    sizes = {"val_oof": len(splits["val"]), **{k: len(v) for k, v in info.items()}}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(to_records(result, sizes), indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
