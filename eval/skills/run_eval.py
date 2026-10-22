"""Skill-detector evaluation on held-out data -> eval/reports/ml_skills.json + PNGs in eval/skills/.

    uv run python eval/skills/run_eval.py [--data-dir data/skills] [--models-dir models]

Uses the trained artifact as-is (no retraining). Set FR_EMBED to the embedder it was trained with.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.config import DATA_DIR, EVAL_REPORTS_DIR, MODELS_DIR  # noqa: E402
from backend.app.ml.evaluate import run  # noqa: E402
from backend.app.ml.skill_detector import SkillDetector  # noqa: E402
from backend.app.ml.train import ARTIFACT, META  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate the skill detector on held-out data")
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR / "skills")
    parser.add_argument("--models-dir", type=Path, default=MODELS_DIR)
    parser.add_argument("--report", type=Path, default=EVAL_REPORTS_DIR / "ml_skills.json")
    parser.add_argument("--figures", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args(argv)
    if not (args.models_dir / ARTIFACT).exists():
        print(f"ml eval: no artifact in {args.models_dir}; run `make train` first (skipped)")
        return 0
    if not args.data_dir.exists():
        print(f"ml eval: no data in {args.data_dir} (skipped)")
        return 0
    meta = json.loads((args.models_dir / META).read_text(encoding="utf-8"))
    notes = f"trained {meta['trained_at']} with {meta['embedder']}, data {meta['data_hash'][:12]}"
    model = SkillDetector(args.models_dir).model
    results = run(model, args.data_dir, args.report, args.figures, notes)
    for split, result in results.items():
        line = ", ".join(f"{k} {v['macro_f1']:.3f}" for k, v in result["scores"].items())
        print(
            f"{split} (n={result['n']}): macro-F1 {line}; ECE {result['ece_before']} -> {result['ece_after']}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
