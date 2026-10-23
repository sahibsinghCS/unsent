"""Seeded 70/15/15 split of data/skills/final.jsonl, grouped by context_id, stratified by scenario.

Composed replies: every reply of a context lands in the same split (no leakage of the friend context).
Train-only free-form rows (source "freeform_train", own x-* contexts) always go to train. Free-form replies: the freeform replies of composed-val contexts go to val; those of composed-test contexts
plus a seeded half of the composed-train contexts become test_freeform.jsonl (never trained on); the rest go
to train. data/skills/survey_real.jsonl (real anonymous replies) always goes to test.
"""

from __future__ import annotations

import random
from collections import Counter

from common import DATA, LABELS, SCENARIOS, read_jsonl, write_jsonl

SK = DATA / "skills"
# contexts per scenario (15 each) -> (train, val, test); alternates so totals are close to 70/15/15
COUNTS = [(10, 2, 3), (11, 2, 2)]


def split_contexts(rows: list[dict], seed: int = 42) -> dict[str, str]:
    """Assign each context to train/val/test using the composed rows' contexts (all contexts appear there)."""
    rng = random.Random(seed)
    by_sc: dict[str, list[str]] = {}
    for r in rows:
        by_sc.setdefault(r["scenario_id"], [])
        if r["context_id"] not in by_sc[r["scenario_id"]]:
            by_sc[r["scenario_id"]].append(r["context_id"])
    assign: dict[str, str] = {}
    for i, sid in enumerate(sorted(by_sc)):
        ctxs = sorted(by_sc[sid])
        rng.shuffle(ctxs)
        n = len(ctxs)
        tr, va, _ = COUNTS[i % 2]
        tr, va = round(n * tr / 15), max(1, round(n * va / 15))
        for j, c in enumerate(ctxs):
            assign[c] = "train" if j < tr else "val" if j < tr + va else "test"
    return assign


def main() -> None:
    rows = read_jsonl(SK / "final.jsonl")
    train_only = [r for r in rows if r.get("source") == "freeform_train"]
    composed = [r for r in rows if r.get("source", "composed") == "composed"]
    freeform = [r for r in rows if r.get("source") == "freeform"]
    assign = split_contexts(composed)
    rng = random.Random(42)
    train_ctx = sorted(c for c, s in assign.items() if s == "train")
    rng.shuffle(train_ctx)
    ff_test_ctx = set(train_ctx[: len(train_ctx) // 2]) | {
        c for c, s in assign.items() if s == "test"
    }
    out: dict[str, list[dict]] = {"train": [], "val": [], "test": [], "test_freeform": []}
    for r in composed:
        out[assign[r["context_id"]]].append(r)
    for r in freeform:
        if r.get("split_hint") == "test_freeform" or r["context_id"] in ff_test_ctx:
            out["test_freeform"].append(r)
        else:
            out[assign[r["context_id"]]].append(r)
    out["train"] += train_only  # TRAIN-ONLY rows (own contexts); never val/test
    out["test"] += read_jsonl(SK / "survey_real.jsonl")
    for name, rs in out.items():
        write_jsonl(SK / "splits" / f"{name}.jsonl", rs)
        pos = Counter(k for r in rs for k in LABELS if r["labels"].get(k))
        print(name, len(rs), dict(pos))
    assert set(SCENARIOS) >= {r["scenario_id"] for r in rows}


if __name__ == "__main__":
    main()
