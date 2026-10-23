"""`make eval` entry point for the red-team lane (scripts/run_evals.py runs eval/*/run_eval.py)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from eval.redteam.__main__ import main  # noqa: E402

if __name__ == "__main__":
    sys.argv = [sys.argv[0], "--embed", "auto"]
    sys.exit(main())
