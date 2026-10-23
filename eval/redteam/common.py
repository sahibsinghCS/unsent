"""Shared helpers for the red-team harness: environment, data loaders and the report writer.

Nothing here calls the network. The harness picks the embedder before any backend import touches it,
so `configure()` must run first (the entry points do this).
"""

from __future__ import annotations

import hashlib
import json
import os
import random
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
REPORTS = ROOT / "eval" / "reports"
PINNED = ROOT / "tests" / "safety" / "pinned"
DETAILS = ROOT / "eval" / "redteam" / "results"
LANE = "redteam"
SEED = 20261025
CREATED = datetime.now(UTC).isoformat(timespec="seconds")

# Categories in data/guardian/messages.jsonl that must be flagged / must pass through.
CRITICAL_POSITIVE = ("self_risk", "harm_to_other", "method_seeking", "prompt_injection")
CRITICAL_NEGATIVE = ("asking_friend", "tricky_negative")

# What each attack-bank expected_action means for Guardian.check_user's `action`.
# stay_in_persona / continue_low_trust: the Guardian lets the message through; the ENGINE handles it.
ACCEPT = {
    "crisis_pause": {"pause_roleplay"},
    "block_message": {"block_message"},
    "continue": {"continue"},
    "continue_low_trust": {"continue"},
    "stay_in_persona": {"continue"},
}


def configure(embed: str = "auto", live: bool = False) -> str:
    """Deterministic settings for a harness run (offline unless `live`). Returns the embedder used:
    'auto' means the production embedder (fastembed) when installed, else the test-only hash one."""
    if not live:
        os.environ["FR_LLM"] = "0"
        os.environ["FR_GUARDIAN_MODERATION"] = "0"
    if embed == "auto":
        embed = "fastembed" if _fastembed_ready() else "hash"
    os.environ["FR_EMBED"] = embed
    random.seed(SEED)
    return embed


def _fastembed_ready() -> bool:
    try:
        import fastembed  # noqa: F401
    except ImportError:
        return False
    return True


def read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]


def attack_half(attack_id: str) -> str:
    """'dev' or 'holdout' for an attack-bank id (fixed rule shared with the safety lane): dev when the
    first hex digit of sha256(id) is 0-7. The safety lane may tune the Guardian on dev only."""
    return "dev" if hashlib.sha256(attack_id.encode()).hexdigest()[0] in "01234567" else "holdout"


def attacks() -> list[dict]:
    """The reviewed attack bank (data lane): {id, strategy, text, expected_action}."""
    return read_jsonl(DATA / "redteam" / "attacks.jsonl")


def guardian_rows(split: str | None = None) -> list[dict]:
    """Guardian examples; `split` = train | val | test, or None for all of them."""
    if split is None:
        return read_jsonl(DATA / "guardian" / "messages.jsonl")
    return read_jsonl(DATA / "guardian" / "splits" / f"{split}.jsonl")


def record(metric: str, value: float, n: int, split: str, notes: str = "") -> dict:
    """One eval/README.md record."""
    return {
        "lane": LANE,
        "metric": metric,
        "value": round(float(value), 4) if isinstance(value, float) else value,
        "n": int(n),
        "split": split,
        "notes": notes,
        "created": CREATED,
    }


def rate(hits: int, n: int) -> float:
    return round(hits / n, 4) if n else 0.0


def write_report(name: str, records: Iterable[dict], embed: str, extra: dict | None = None) -> Path:
    """Write eval/reports/redteam_<name>.json. Records from runs with OTHER embedders are kept, so the
    hash (CI) and fastembed (production) runs can live side by side; `extra` goes to a sibling
    eval/redteam/results/<name>.<embed>.json (failure lists, confusion tables), outside eval/reports/ so
    /api/metrics only ever sees metric records."""
    path = REPORTS / f"redteam_{name}.json"
    tag = f"embed={embed}"
    kept = []
    if path.exists():
        try:
            kept = [
                r for r in json.loads(path.read_text(encoding="utf-8")) if tag not in r["notes"]
            ]
        except (json.JSONDecodeError, KeyError, TypeError):
            kept = []
    # The embedder goes into the split too, so (lane, metric, split) names exactly one record.
    rows = [
        {**r, "split": f"{r['split']} [{embed}]", "notes": f"{r['notes']}; {tag}".strip("; ")}
        for r in records
    ]
    path.write_text(json.dumps(kept + rows, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    if extra is not None:
        details = DETAILS / f"{name}.{embed}.json"
        details.parent.mkdir(parents=True, exist_ok=True)
        details.write_text(json.dumps(extra, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return path
