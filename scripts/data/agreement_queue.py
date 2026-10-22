"""Compare the authored (intended) labels with the independent blind labels.

Writes eval/reports/data_agreement.json (per-label agreement and Cohen's kappa) and
data/skills/queue.jsonl = every disagreement + 100 random agreed rows (audit), for the human labeler.
"""

from __future__ import annotations

import json
import random
from datetime import datetime, timezone

from common import DATA, LABELS, ROOT, read_jsonl, write_jsonl

SK = DATA / "skills"


def kappa(a: list[bool], b: list[bool]) -> float:
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def run(audit_n: int = 100, seed: int = 42) -> dict:
    ctx = {c["context_id"]: c for c in read_jsonl(SK / "contexts.jsonl")}
    replies = {r["id"]: r for r in read_jsonl(SK / "replies.jsonl")}
    blind = {r["id"]: r for r in read_jsonl(SK / "blind_labels.jsonl")}
    ids = [i for i in replies if i in blind]
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    records, per_label = [], {}
    for lab in LABELS:
        a = [bool(replies[i]["intended"][lab]) for i in ids]
        b = [bool(blind[i]["labels"].get(lab, False)) for i in ids]
        agree = sum(x == y for x, y in zip(a, b)) / len(ids)
        k = kappa(a, b)
        per_label[lab] = {
            "agreement": round(agree, 4),
            "kappa": round(k, 4),
            "n_positive_authored": sum(a),
            "n_positive_blind": sum(b),
        }
        records.append(
            {
                "lane": "data",
                "metric": f"agreement_{lab}",
                "value": round(agree, 4),
                "n": len(ids),
                "split": "all",
                "notes": f"authored vs blind labeler; kappa={k:.3f}",
                "created": now,
            }
        )
        records.append(
            {
                "lane": "data",
                "metric": f"kappa_{lab}",
                "value": round(k, 4),
                "n": len(ids),
                "split": "all",
                "notes": "Cohen's kappa, authored vs blind labeler",
                "created": now,
            }
        )
    exact = [
        i
        for i in ids
        if all(
            bool(replies[i]["intended"][l]) == bool(blind[i]["labels"].get(l, False))
            for l in LABELS
        )
    ]
    mean_k = sum(v["kappa"] for v in per_label.values()) / len(LABELS)
    records.append(
        {
            "lane": "data",
            "metric": "exact_match_rate",
            "value": round(len(exact) / len(ids), 4),
            "n": len(ids),
            "split": "all",
            "notes": "all 10 labels identical",
            "created": now,
        }
    )
    records.append(
        {
            "lane": "data",
            "metric": "mean_kappa",
            "value": round(mean_k, 4),
            "n": len(ids),
            "split": "all",
            "notes": "mean over 10 labels",
            "created": now,
        }
    )
    (ROOT / "eval" / "reports").mkdir(parents=True, exist_ok=True)
    (ROOT / "eval" / "reports" / "data_agreement.json").write_text(
        json.dumps(records, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    def row(i: str, kind: str) -> dict:
        r, c = replies[i], ctx[replies[i]["context_id"]]
        o = {l: bool(r["intended"][l]) for l in LABELS}
        b = {l: bool(blind[i]["labels"].get(l, False)) for l in LABELS}
        return {
            "id": i,
            "kind": kind,
            "context_id": r["context_id"],
            "scenario_id": c["scenario_id"],
            "level": c["level"],
            "context": c["friend_messages"],
            "text": r["text"],
            "lang": r["lang"],
            "intended": o,
            "blind": b,
            "disagree": [l for l in LABELS if o[l] != b[l]],
        }

    exact_set = set(exact)
    dis = [row(i, "disagreement") for i in ids if i not in exact_set]
    rng = random.Random(seed)
    audit = [row(i, "audit") for i in rng.sample(sorted(exact_set), min(audit_n, len(exact_set)))]
    queue = dis + audit
    rng.shuffle(queue)
    write_jsonl(SK / "queue.jsonl", queue)
    return {
        "rows": len(ids),
        "exact_match": len(exact),
        "disagreements": len(dis),
        "audit": len(audit),
        "mean_kappa": round(mean_k, 4),
        "per_label": per_label,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=1))
