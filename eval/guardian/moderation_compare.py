"""Local Guardian vs OpenAI moderation vs combined (SAFETY lane) -> eval/reports/safety_moderation.json

  uv run python eval/guardian/moderation_compare.py

Subsets of the TEST split (plus the holdout): slang/leet/algospeak, Spanish, and asking_friend.
"Flagged" means any non-continue action. Moderation alone counts as flagged when its top
self-harm or harassment/violence score is >= 0.5. Runs only when OPENAI_API_KEY is set (the
moderation endpoint is free); otherwise it records "not run (no key)".
"""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.app.config import DATA_DIR, EVAL_REPORTS_DIR  # noqa: E402
from backend.app.safety import moderation  # noqa: E402
from backend.app.safety.dataset import load_rows, split_rows  # noqa: E402
from backend.app.safety.guardian import Guardian  # noqa: E402

OUT = EVAL_REPORTS_DIR / "safety_moderation.json"
CREATED = datetime.now(UTC).isoformat(timespec="seconds")
SAFE = {"asking_friend", "tricky_negative", "neutral"}


def subsets(rows: list[dict]) -> dict[str, list[dict]]:
    return {
        "slang": [r for r in rows if r.get("style") in {"slang", "leet", "algospeak", "emoji"}],
        "spanish": [r for r in rows if r.get("lang") in {"es", "mix"}],
        "asking_friend": [r for r in rows if r["category"] == "asking_friend"],
    }


def moderation_flags(scores: dict[str, float] | None) -> bool:
    if not scores:
        return False
    keys = moderation.SELF_HARM_KEYS + moderation.HARM_KEYS
    return max(scores.get(k, 0.0) for k in keys) >= moderation.SUPPORT


def correct(row: dict, flagged: bool) -> bool:
    return flagged != (row["category"] in SAFE)


def main() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        record = {
            "lane": "safety",
            "metric": "moderation_compare",
            "value": None,
            "n": 0,
            "split": "test",
            "notes": "not run (no key): set OPENAI_API_KEY and rerun this script",
            "created": CREATED,
        }
        OUT.write_text(json.dumps([record], indent=1) + "\n")
        print("not run (no key)")
        return

    rows = split_rows(load_rows())["test"]
    hold = DATA_DIR / "guardian_extra" / "holdout.jsonl"
    if hold.exists():
        rows += [json.loads(x) for x in hold.read_text(encoding="utf-8").splitlines() if x]
    local = Guardian(use_moderation=False)
    combined = Guardian(use_moderation=True)
    records = []
    for name, sub in subsets(rows).items():
        if not sub:
            continue
        acc = {"local": 0, "moderation": 0, "combined": 0}
        for row in sub:
            scores = moderation.fetch(row["text"])
            acc["local"] += correct(row, local.check_user(row["text"], []).action != "continue")
            acc["moderation"] += correct(row, moderation_flags(scores))
            acc["combined"] += correct(
                row, combined.check_user(row["text"], []).action != "continue"
            )
        for system, hits in acc.items():
            metric = "flag_rate_on_asking" if name == "asking_friend" else "accuracy"
            value = hits / len(sub)
            if name == "asking_friend":
                value = 1 - value  # share of good questions wrongly flagged
            records.append(
                {
                    "lane": "safety",
                    "metric": f"moderation_compare.{name}.{system}.{metric}",
                    "value": round(value, 4),
                    "n": len(sub),
                    "split": "test+holdout",
                    "notes": "flagged = any non-continue action; moderation threshold 0.5",
                    "created": CREATED,
                }
            )
            print(f"{name:<14} {system:<11} {metric:<20} {value:.3f}  n={len(sub)}")
    OUT.write_text(json.dumps(records, indent=1) + "\n")


if __name__ == "__main__":
    main()
