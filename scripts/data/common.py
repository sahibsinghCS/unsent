"""Shared paths and tiny IO helpers for the data lane scripts."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
SCENARIO_DIR = DATA / "scenarios"
SCENARIOS = ["after-the-breakup", "failing-chem", "giving-stuff-away", "group-chat", "new-school"]
LABELS = [
    "checked_in",
    "validated",
    "asked_directly",
    "encouraged_help",
    "referred_adult",
    "referred_988",
    "follow_up",
    "dismissed",
    "advice_dump",
    "promised_secrecy",
]

# Same list the repo's contract tests use, plus a few extras for the data lane.
METHOD_WORDS = re.compile(
    r"\b(pills?|overdose|gun|rope|noose|hang(?:ing)? myself|jump(?:ing)? off|bridge|razor|"
    r"cut(?:ting)? myself|bleach|poison|train tracks|knife|rifle|stab|slit|"
    r"pastillas?|soga|veneno|puente)\b",
    re.IGNORECASE,
)


def read_jsonl(path: Path) -> list[dict]:
    if not Path(path).exists():
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def load_scenario(sid: str) -> dict:
    path = SCENARIO_DIR / f"{sid}.json"
    if (
        not path.exists()
    ):  # user-made-friend template lives on the integrator branch; tests keep a copy
        path = ROOT / "tests" / "unit" / "data" / "fixtures" / f"{sid}.json"
    return json.loads(path.read_text(encoding="utf-8"))
