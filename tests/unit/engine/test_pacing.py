"""Pacing targets (eval/engine/pacing.py) hold for the live config.yaml across all 5 scenarios."""

from __future__ import annotations

import importlib.util
from pathlib import Path

PACING = Path(__file__).resolve().parents[3] / "eval" / "engine" / "pacing.py"


def _pacing():
    spec = importlib.util.spec_from_file_location("pacing", PACING)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_all_pacing_targets_met():
    result = _pacing().evaluate()
    failures = [name for name, ok in result["checks"] if not ok]
    assert not failures, failures
    assert len(result["checks"]) == 5 * 7


def test_excellent_helper_wins_fast_and_slip_recovers():
    runs = _pacing().evaluate()["runs"]
    for run in runs:
        if run["helper"] == "excellent":
            assert run["turns_to_success"] <= (7 if run["persona"] == "open" else 8)
        if run["helper"] == "one_slip":
            assert run["turns_to_success"] <= 10
        if run["helper"] in ("never_asks", "never_refers", "dismissive", "advice_only"):
            assert run["turns_to_success"] is None
