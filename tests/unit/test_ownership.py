from __future__ import annotations

import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "check_ownership", Path(__file__).resolve().parents[2] / "scripts" / "check_ownership.py"
)
check_ownership = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_ownership)


def test_globs():
    allowed = check_ownership.is_allowed
    assert allowed("backend/app/engine/state.py", ["backend/app/engine/**"])
    assert allowed("backend/app/engine/sub/x.py", ["backend/app/engine/**"])
    assert not allowed("backend/app/contracts.py", ["backend/app/engine/**"])
    assert allowed("eval/reports/engine_traj.json", ["eval/reports/engine_*"])
    assert not allowed("eval/reports/ml_f1.json", ["eval/reports/engine_*"])
    assert allowed("Dockerfile", ["Dockerfile"])
