"""Leakage report: what share of each eval set's replies is made ONLY of word 5-grams that also occur in train.

Rows shorter than 5 words count as one gram (the whole text). Writes eval/reports/data_leakage.json.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime

from common import DATA, ROOT, read_jsonl

SPLITS = DATA / "skills" / "splits"


def grams(text: str, n: int = 5) -> set[str]:
    w = re.findall(r"[\w']+", text.lower())
    if len(w) <= n:
        return {" ".join(w)}
    return {" ".join(w[i : i + n]) for i in range(len(w) - n + 1)}


def share_all_in_train(rows: list[dict], train_grams: set[str]) -> float:
    if not rows:
        return 0.0
    return sum(grams(r["text"]) <= train_grams for r in rows) / len(rows)


def main() -> None:
    train = read_jsonl(SPLITS / "train.jsonl")
    tg: set[str] = set()
    for r in train:
        tg |= grams(r["text"])
    now = datetime.now(UTC).astimezone().isoformat(timespec="seconds")
    recs = []
    for name in ("val", "test", "test_freeform"):
        rows = read_jsonl(SPLITS / f"{name}.jsonl")
        s = share_all_in_train(rows, tg)
        recs.append(
            {
                "lane": "data",
                "metric": "share_all_5grams_in_train",
                "value": round(s, 4),
                "n": len(rows),
                "split": name,
                "notes": "share of rows whose every word 5-gram also occurs in train (lower is better)",
                "created": now,
            }
        )
        print(f"{name}: n={len(rows)} share={s:.1%}")
    (ROOT / "eval" / "reports" / "data_leakage.json").write_text(
        json.dumps(recs, indent=1) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
