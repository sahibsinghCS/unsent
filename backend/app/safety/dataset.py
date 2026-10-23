"""Guardian training data: load, de-duplicate and split (SAFETY lane).

Sources (read-only):
  - data/guardian/messages.jsonl           written by the DATA lane (when present)
  - data/guardian_extra/messages.jsonl     hand-written hard cases from the SAFETY lane
  - $FR_GUARDIAN_DATA/messages.jsonl       optional extra directory (e.g. a read-only copy of wt/data)
Splits are frozen per row (see split_rows), so the same rows always land in the same split.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

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
        preset = _preset_splits(path)
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            key = row.get("text", "").strip().lower()
            if not key or key in seen or row.get("category") not in CATEGORIES:
                continue
            seen.add(key)
            row["source_file"] = f"{path.parent.name}/{path.name}"
            row.setdefault("split", preset.get(row.get("id")))
            rows.append(row)
    return rows


def _preset_splits(messages: Path) -> dict[str, str]:
    """id -> split from a sibling splits/ folder (the data lane's own train/val/test)."""
    out = {}
    for name in ("train", "val", "test"):
        path = messages.parent / "splits" / f"{name}.jsonl"
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    out[json.loads(line)["id"]] = name
    return out


def split_rows(rows: list[dict], seed: int = SEED) -> dict[str, list[dict]]:
    """Rows keep a split their source already assigned (data lane splits, our frozen splits);
    any other row gets a stable 70/15/15 split from a hash of its id, so adding rows never
    reshuffles the rows that were already split."""
    out: dict[str, list[dict]] = {"train": [], "val": [], "test": []}
    for row in rows:
        split = row.get("split")
        if split not in out:
            bucket = int(hashlib.sha256(f"{seed}:{row['id']}".encode()).hexdigest(), 16) % 100
            split = "train" if bucket < 70 else "val" if bucket < 85 else "test"
        out[split].append(row)
    return out
