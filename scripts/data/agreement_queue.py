"""Compare the authored (intended) labels with the independent blind labels.

Writes eval/reports/data_agreement.json (per-label agreement and Cohen's kappa, reported separately for
composed and free-form replies) and data/skills/queue.jsonl = every disagreement + a random audit of
agreed rows (100 composed + 20 free-form), for the human labeler.
"""

from __future__ import annotations

import json
import random
from datetime import UTC, datetime

from adjudicate_rules import adjudicate
from common import DATA, LABELS, ROOT, read_jsonl, write_jsonl

SK = DATA / "skills"


def kappa(a: list[bool], b: list[bool]) -> float:
    n = len(a)
    po = sum(x == y for x, y in zip(a, b, strict=True)) / n
    pa, pb = sum(a) / n, sum(b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def run(audit: dict[str, int] | None = None, seed: int = 42) -> dict:
    audit = audit or {"composed": 100, "freeform": 20, "freeform_train": 10}
    ctx = {
        c["context_id"]: c
        for c in read_jsonl(SK / "contexts.jsonl") + read_jsonl(SK / "contexts_extra.jsonl")
    }
    replies = {r["id"]: r for r in read_jsonl(SK / "replies.jsonl")}
    for name in ("replies_freeform", "replies_train_extra"):
        for r in read_jsonl(SK / f"{name}.jsonl"):
            replies[r["id"]] = r
    blind = {r["id"]: r for r in read_jsonl(SK / "blind_labels.jsonl")}
    ids = [i for i in replies if i in blind]
    now = datetime.now(UTC).astimezone().isoformat(timespec="seconds")

    def src(i: str) -> str:
        return replies[i].get("source", "composed")

    def same(i: str) -> bool:
        return all(
            bool(replies[i]["intended"][lab]) == bool(blind[i]["labels"].get(lab, False))
            for lab in LABELS
        )

    records, summary = [], {}
    for subset in ("all", "composed", "freeform", "freeform_train"):
        sub = [i for i in ids if subset == "all" or src(i) == subset]
        if not sub:
            continue
        per_label = {}
        for lab in LABELS:
            a = [bool(replies[i]["intended"][lab]) for i in sub]
            b = [bool(blind[i]["labels"].get(lab, False)) for i in sub]
            agree = sum(x == y for x, y in zip(a, b, strict=True)) / len(sub)
            k = kappa(a, b)
            per_label[lab] = {
                "agreement": round(agree, 4),
                "kappa": round(k, 4),
                "n_positive_authored": sum(a),
            }
            for metric, val, note in (
                (f"agreement_{lab}", agree, f"authored vs blind labeler; kappa={k:.3f}"),
                (f"kappa_{lab}", k, "Cohen's kappa, authored vs blind labeler"),
            ):
                records.append(
                    {
                        "lane": "data",
                        "metric": metric,
                        "value": round(val, 4),
                        "n": len(sub),
                        "split": subset,
                        "notes": note,
                        "created": now,
                    }
                )
        exact = sum(same(i) for i in sub) / len(sub)
        mean_k = sum(v["kappa"] for v in per_label.values()) / len(LABELS)
        records.append(
            {
                "lane": "data",
                "metric": "exact_match_rate",
                "value": round(exact, 4),
                "n": len(sub),
                "split": subset,
                "notes": "all 10 labels identical",
                "created": now,
            }
        )
        records.append(
            {
                "lane": "data",
                "metric": "mean_kappa",
                "value": round(mean_k, 4),
                "n": len(sub),
                "split": subset,
                "notes": "mean over 10 labels",
                "created": now,
            }
        )
        summary[subset] = {
            "rows": len(sub),
            "exact_match": round(exact, 4),
            "mean_kappa": round(mean_k, 4),
            "per_label": per_label,
        }
    (ROOT / "eval" / "reports").mkdir(parents=True, exist_ok=True)
    (ROOT / "eval" / "reports" / "data_agreement.json").write_text(
        json.dumps(records, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    def row(i: str, kind: str) -> dict:
        r, c = replies[i], ctx[replies[i]["context_id"]]
        o = {lab: bool(r["intended"][lab]) for lab in LABELS}
        b = {lab: bool(blind[i]["labels"].get(lab, False)) for lab in LABELS}
        return {
            "id": i,
            "kind": kind,
            "source": src(i),
            "context_id": r["context_id"],
            "scenario_id": c["scenario_id"],
            "level": c["level"],
            "context": c["friend_messages"],
            "text": r["text"],
            "lang": r["lang"],
            "intended": o,
            "blind": b,
            "disagree": [lab for lab in LABELS if o[lab] != b[lab]],
        }

    all_dis = [row(i, "disagreement") for i in ids if not same(i)]
    adjudicated = adjudicate(all_dis)
    write_jsonl(SK / "adjudicated_labels.jsonl", adjudicated)
    done = {x["id"] for x in adjudicated}
    dis = [r for r in all_dis if r["id"] not in done]  # only judgment calls stay for the human
    rng = random.Random(seed)
    audit_rows = []
    for s, n in audit.items():
        pool = sorted(i for i in ids if src(i) == s and same(i))
        audit_rows += [row(i, "audit") for i in rng.sample(pool, min(n, len(pool)))]
    queue = dis + audit_rows
    rng.shuffle(queue)
    write_jsonl(SK / "queue.jsonl", queue)
    return {
        "queue_rows": len(queue),
        "disagreements": len(dis),
        "audit": len(audit_rows),
        **summary,
    }


if __name__ == "__main__":
    out = run()
    for k, v in out.items():
        if isinstance(v, dict):
            v = {kk: vv for kk, vv in v.items() if kk != "per_label"}
        print(k, v)
