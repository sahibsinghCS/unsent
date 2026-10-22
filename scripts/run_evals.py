"""Run every lane evaluation that exists (eval/*/run_eval.py). Results land in eval/reports/. Run: make eval"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    scripts = sorted((ROOT / "eval").glob("*/run_eval.py"))
    if not scripts:
        print("eval: no lane evaluations yet")
    failed = 0
    for script in scripts:
        print(f"== {script.relative_to(ROOT)}")
        failed += subprocess.run([sys.executable, str(script)], cwd=ROOT).returncode != 0
    sys.exit(1 if failed else 0)
