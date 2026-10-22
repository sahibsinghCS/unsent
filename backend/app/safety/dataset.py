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
    """Rows keep a split their source already assigned; the rest get a stratified 70/15/15."""
    fixed = {k: [r for r in rows if r.get("split") == k] for k in ("train", "val", "test")}
    free = [r for r in rows if r.get("split") not in fixed]
    labels = [r["category"] for r in free]
    train, rest = train_test_split(free, test_size=0.30, stratify=labels, random_state=seed)
    rest_labels = [r["category"] for r in rest]
    val, test = train_test_split(rest, test_size=0.50, stratify=rest_labels, random_state=seed)
    return {
        "train": fixed["train"] + train,
        "val": fixed["val"] + val,
        "test": fixed["test"] + test,
    }
