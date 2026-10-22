"""Assemble data/lines/<scenario>.en.jsonl from the authored modules in scripts/data/lines_src/."""

from __future__ import annotations

import importlib

from common import DATA, write_jsonl

MODULES = {
    "maya": "mya",
    "maya_es": "mya",
    "jordan": "jor",
    "sam": "sam",
    "eli": "eli",
    "priya": "pri",
}

TONE = {
    "opening": "casual",
    "success": "relieved",
    "neutral": "continuing",
    "checked_in": "warming",
    "validated": "softening",
    "asked_directly": {
        0: "surprised, deflecting",
        1: "surprised, deflecting",
        2: "hesitant, partial truth",
        3: "honest, no details",
        4: "relieved, honest",
    },
    "encouraged_help": {
        0: "polite brush-off",
        1: "unsure",
        2: "doubtful",
        3: "scared but listening",
        4: "agreeing",
    },
    "referred": {0: "resistant", 1: "resistant", 2: "resistant", 3: "hesitant", 4: "open"},
    "follow_up": "grateful",
    "dismissed": "hurt, closing off",
    "advice_dump": "unheard",
    "promised_secrecy": "uneasy relief",
    "secrecy_broken": "betrayed",
    "off_topic": "confused",
    "fail": "shutting down",
}


def tone(reaction: str, level: int) -> str:
    t = TONE[reaction]
    return t[level] if isinstance(t, dict) else t


def build(name: str) -> list[dict]:
    mod = importlib.import_module(f"lines_src.{name}")
    locale = getattr(mod, "LOCALE", "en")
    counters: dict[tuple[int, str], int] = {}
    rows = []
    for level, reaction, cue, bubbles, fact_ids in mod.ROWS:
        n = counters[(level, reaction)] = counters.get((level, reaction), 0) + 1
        rows.append(
            {
                "id": f"{MODULES[name]}-{locale}-L{level}-{reaction}-{n:02d}",
                "scenario_id": mod.SID,
                "locale": locale,
                "level": level,
                "reaction": reaction,
                "bubbles": bubbles,
                "fact_ids": fact_ids,
                "cue": cue,
                "tone": tone(reaction, level),
                "review_status": "draft",
            }
        )
    return rows


if __name__ == "__main__":
    import sys

    for name in MODULES:
        try:
            rows = build(name)
        except ModuleNotFoundError:
            print("skip", name)
            continue
        mod = importlib.import_module(f"lines_src.{name}")
        sid = mod.SID
        write_jsonl(
            DATA / "lines" / f"{sid}.{mod.LOCALE if hasattr(mod, 'LOCALE') else 'en'}.jsonl", rows
        )
        print(sid, len(rows))
    sys.exit(0)
