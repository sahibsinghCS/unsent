"""Render freeform_src.py (hand-written whole replies) to data/skills/replies_freeform.jsonl."""

from __future__ import annotations

from common import DATA, LABELS, write_jsonl
from freeform_src import HINTED, ordered

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
SPANISH_MARK = "¿¡áéíóúñ"
SPANISH_WORDS = (
    "no te",
    "estás",
    "cómo",
    "gracias",
    "vamos",
    "aquí",
    "tengo",
    "puedo",
    "bueno",
    "mañana",
)


def build() -> list[dict]:
    rows, seen = [], set()
    for ctx_id, text, codes in ordered():
        if True:
            key = " ".join(text.lower().split())
            assert key not in seen, text
            seen.add(key)
            on = {CODE[c] for c in codes.split() if c != "-"}
            es = any(c in text for c in SPANISH_MARK)
            lower = text.lower()
            lang = (
                "es"
                if es and not any(w in lower for w in (" the ", " you ", " i "))
                else "mix"
                if es
                else "en"
            )
            rows.append(
                {
                    "id": f"f{len(rows) + 1:04d}",
                    "context_id": ctx_id,
                    "text": text,
                    "style": "freeform",
                    "lang": lang,
                    "intended": {lab: lab in on for lab in LABELS},
                    "source": "freeform",
                    **({"split_hint": "test_freeform"} if text in HINTED else {}),
                }
            )
    return rows


if __name__ == "__main__":
    from collections import Counter

    rows = build()
    write_jsonl(DATA / "skills" / "replies_freeform.jsonl", rows)
    pos = Counter(k for r in rows for k, v in r["intended"].items() if v)
    print(
        len(rows),
        dict(pos),
        Counter(r["lang"] for r in rows),
        "no-label:",
        sum(not any(r["intended"].values()) for r in rows),
    )
