"""Render train_extra_src.py to data/skills/contexts_extra.jsonl and data/skills/replies_train_extra.jsonl (TRAIN-ONLY)."""

from __future__ import annotations

from common import DATA, LABELS, write_jsonl
from train_extra_src import CTX, ROWS

CODE = {
    "c": "checked_in",
    "v": "validated",
    "a": "asked_directly",
    "e": "encouraged_help",
    "r": "referred_adult",
    "n": "referred_988",
    "f": "follow_up",
    "d": "dismissed",
    "x": "advice_dump",
    "s": "promised_secrecy",
}
ES = "¿¡áéíóúñ"
ES_WORDS = (
    " que ",
    " de ",
    " te ",
    " tú ",
    "aquí",
    "cuenta conmigo",
    "luego",
    "mañana",
    "neta",
    "wey",
    "nomás",
    "jaja",
)


def build() -> tuple[list[dict], list[dict]]:
    ctxs = [
        {"context_id": cid, "scenario_id": sid, "level": lvl, "friend_messages": msgs}
        for cid, (sid, lvl, msgs) in CTX.items()
    ]
    rows, seen = [], set()
    for ctx_id, text, codes in ROWS:
        key = " ".join(text.lower().split())
        assert key not in seen, text
        seen.add(key)
        on = {CODE[c] for c in codes.split() if c != "-"}
        low = " " + text.lower() + " "
        es = any(c in text for c in ES) or any(w in low for w in ES_WORDS)
        english = any(w in low for w in (" the ", " you ", " i ", " it ", " my ", " is ", " to "))
        lang = "mix" if es and english else "es" if es else "en"
        rows.append(
            {
                "id": f"t{len(rows) + 1:04d}",
                "context_id": ctx_id,
                "text": text,
                "style": "freeform",
                "lang": lang,
                "intended": {lab: lab in on for lab in LABELS},
                "source": "freeform_train",
                "split_hint": "train",
            }
        )
    return ctxs, rows


if __name__ == "__main__":
    from collections import Counter

    ctxs, rows = build()
    write_jsonl(DATA / "skills" / "contexts_extra.jsonl", ctxs)
    write_jsonl(DATA / "skills" / "replies_train_extra.jsonl", rows)
    print(
        len(ctxs),
        len(rows),
        Counter(r["lang"] for r in rows),
        dict(Counter(k for r in rows for k, v in r["intended"].items() if v)),
    )
