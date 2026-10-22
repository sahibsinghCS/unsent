"""Build data/skills/final.jsonl from intended + blind + human labels, and report audit stats.

Priority per reply: human label > agreed (intended == blind on all 10 labels) > dropped.
`--provisional` (before the blind pass exists) keeps every row with its intended labels,
marked label_source "intended", so ML can start training early.
"""

from __future__ import annotations

import argparse
import json

from common import DATA, LABELS, read_jsonl, write_jsonl

SK = DATA / "skills"


def _labels(row: dict) -> dict[str, bool]:
    src = row.get("labels") or row.get("intended") or {}
    return {k: bool(src.get(k, False)) for k in LABELS}


def build(provisional: bool = False) -> tuple[list[dict], dict]:
    ctx = {c["context_id"]: c for c in read_jsonl(SK / "contexts.jsonl")}
    replies = read_jsonl(SK / "replies.jsonl")
    blind = {r["id"]: _labels(r) for r in read_jsonl(SK / "blind_labels.jsonl")}
    human = {r["id"]: _labels(r) for r in read_jsonl(SK / "human_labels.jsonl")}
    queue_ids = {r["id"] for r in read_jsonl(SK / "queue.jsonl")}
    out, stats = [], {"human": 0, "agreed": 0, "intended": 0, "dropped_disagreement": 0}
    audit_n, audit_wrong = 0, {k: 0 for k in LABELS}
    for r in replies:
        intended = _labels(r)
        if r["id"] in human:
            labels, src = human[r["id"]], "human"
            if r["id"] in queue_ids and r["id"] in blind and blind[r["id"]] == intended:
                audit_n += 1
                for k in LABELS:
                    audit_wrong[k] += int(human[r["id"]][k] != intended[k])
        elif provisional and r["id"] not in blind:
            labels, src = intended, "intended"
        elif r["id"] in blind and blind[r["id"]] == intended:
            labels, src = intended, "agreed"
        else:
            stats["dropped_disagreement"] += 1
            continue
        stats[src] += 1
        c = ctx[r["context_id"]]
        out.append(
            {
                "id": r["id"],
                "context_id": r["context_id"],
                "scenario_id": c["scenario_id"],
                "level": c["level"],
                "context": c["friend_messages"],
                "text": r["text"],
                "lang": r["lang"],
                "labels": labels,
                "label_source": src,
            }
        )
    stats["audit_rows_checked"] = audit_n
    stats["audit_label_errors_among_agreed"] = audit_wrong
    return out, stats


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--provisional", action="store_true")
    a = ap.parse_args()
    rows, stats = build(a.provisional)
    write_jsonl(SK / "final.jsonl", rows)
    print(json.dumps({"final_rows": len(rows), **stats}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
