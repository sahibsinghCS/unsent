"""Guardian training data: load, de-duplicate and split (SAFETY lane).

Sources (read-only):
  - data/guardian/messages.jsonl           written by the DATA lane (when present)
  - data/guardian_extra/messages.jsonl     hand-written hard cases from the SAFETY lane
  - $FR_GUARDIAN_DATA/messages.jsonl       optional extra directory (e.g. a read-only copy of wt/data)
The split is seeded and stratified by category, so the same rows always land in the same split.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from sklearn.model_selection import train_test_split

from backend.app.config import DATA_DIR

CATEGORIES = [
    "self_risk",
    "concern",
    "harm_to_other",
    "method_seeking",
    "prompt_injection",
    "asking_friend",
    "tricky_negative",
    "neutral",
]
SEED = 13


def sources() -> list[Path]:
    paths = [
        DATA_DIR / "guardian" / "messages.jsonl",
        DATA_DIR / "guardian_extra" / "messages.jsonl",
    ]
    extra = os.getenv("FR_GUARDIAN_DATA")
    if extra:
        paths.insert(0, Path(extra) / "messages.jsonl")
    return [p for p in paths if p.exists()]


def load_rows() -> list[dict]:
    """All labeled rows from every source, de-duplicated by lowercase text (first source wins)."""
    rows, seen = [], set()
    for path in sources():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            key = row.get("text", "").strip().lower()
            if not key or key in seen or row.get("category") not in CATEGORIES:
                continue
            seen.add(key)
            row["source_file"] = str(path.relative_to(path.parents[2]))
            rows.append(row)
    return rows


def split_rows(rows: list[dict], seed: int = SEED) -> dict[str, list[dict]]:
    """Stratified 70 / 15 / 15 train / val / test split."""
    labels = [r["category"] for r in rows]
    train, rest = train_test_split(rows, test_size=0.30, stratify=labels, random_state=seed)
    rest_labels = [r["category"] for r in rest]
    val, test = train_test_split(rest, test_size=0.50, stratify=rest_labels, random_state=seed)
    return {"train": train, "val": val, "test": test}
