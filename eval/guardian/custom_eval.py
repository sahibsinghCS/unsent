"""Custom friends (SAFETY lane) -> eval/reports/safety_custom.json

screen_profile on profile fields, plus check_friend on sample texts, using the red-team lane's
custom-friend seeds (dev-half attacks, Spanish Guardian rows, hand-written seeds) and every seeded
perturbation, and its benign profiles for false refusals.
Run: uv run python eval/guardian/custom_eval.py
"""

from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("FR_LLM", "0")

from backend.app.config import EVAL_REPORTS_DIR  # noqa: E402
from backend.app.embed import get_embedder  # noqa: E402
from backend.app.safety.guardian import Guardian, screen_profile  # noqa: E402
from eval.redteam import custom  # noqa: E402

# Persona curiosity ("are you a real person?") is answered in character, not refused.
CURIOSITY = {"persona_breaker"}


def blocked(g: Guardian, field: str, text: str) -> bool:
    out = screen_profile(text).action == "block_message"
    return out or (field == "sample" and g.check_friend(text).level != "none")


def main() -> None:
    g = Guardian(use_moderation=False)
    stats: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for seed in custom.seeds():
        for _, text in custom.variants(seed):
            for field in ("personality", "situation", "sample"):
                k = stats[seed["kind"]]
                k[0] += blocked(g, field, text)
                k[1] += 1
    attack = [v for k, v in stats.items() if k not in CURIOSITY]
    hit, n = sum(v[0] for v in attack), sum(v[1] for v in attack)
    refused, fields = 0, 0
    for p in custom.benign_profiles():
        for f in ("name", "personality", "situation"):
            fields += 1
            refused += screen_profile(p.get(f, "")).action == "block_message"
        for t in p.get("sample_texts", []):
            fields += 1
            refused += blocked(g, "sample", t)
    created = datetime.now(UTC).isoformat(timespec="seconds")
    note = f"embedder={get_embedder().name}; screen_profile is lexicon-only"

    def rec(metric: str, value: float, count: int, notes: str) -> dict:
        return {
            "lane": "safety",
            "metric": metric,
            "value": round(value, 4),
            "n": count,
            "split": "custom_friend_seeds",
            "notes": f"{notes}; {note}",
            "created": created,
        }

    records = [
        rec(
            "custom.attack_fields_blocked",
            hit / n,
            n,
            "all seeds x perturbations x 3 fields, excl. persona curiosity",
        ),
        rec("custom.benign_fields_refused", refused / fields, fields, "red-team benign profiles"),
    ]
    for kind, (b, c) in sorted(stats.items()):
        records.append(
            rec(
                f"custom.blocked.{kind}",
                b / c,
                c,
                "curiosity: answered in persona" if kind in CURIOSITY else "",
            )
        )
    out = EVAL_REPORTS_DIR / "safety_custom.json"
    out.write_text(json.dumps(records, indent=1) + "\n")
    for r in records:
        print(f"{r['metric']:<40} {r['value']:>7}  n={r['n']}")


if __name__ == "__main__":
    main()
