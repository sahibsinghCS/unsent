"""Export 30 held-out test rows as a CSV for a school counselor to label in Google Sheets.

Columns: id | friend said | helper reply | 10 checkbox columns | unsure | notes. Row 1 = instructions, row 2 = header.
In Google Sheets: File > Import (CSV), then select the checkbox columns and Insert > Checkbox.
The CSV never contains our labels (independent verification).
"""

from __future__ import annotations

import csv
import random

from common import DATA, LABELS, ROOT, read_jsonl

INSTRUCTIONS = (
    "Thank you! Each row is a text a teen sends to a friend who is struggling. Read the friend's message, then the helper's reply, "
    "and tick every box that describes what the helper's reply DOES (leave a box empty if it does not). Judge the words, not the intent. "
    "checked_in = asks how they are / notices something is off. validated = acknowledges feelings without judging. "
    "asked_directly = explicitly names suicide / killing themselves / ending their life in a question ('are you ok?' does NOT count). "
    "encouraged_help = encourages getting support / 'you don't have to do this alone'. referred_adult = suggests a specific trusted adult (counselor, parent, teacher). "
    "referred_988 = mentions 988 or a crisis line. follow_up = commits to stay/check in again. dismissed = minimizes, jokes, or changes the subject. "
    "advice_dump = jumps to 'just do X' fixes. promised_secrecy = agrees to keep it secret. Tick 'unsure' if you cannot decide. Spanish rows are included."
)


def pick(rows: list[dict], n: int = 30, seed: int = 42) -> list[dict]:
    """Greedy pick so every label appears at least 2 times, then fill randomly."""
    rng = random.Random(seed)
    rows = rows[:]
    rng.shuffle(rows)
    chosen: list[dict] = []
    need = {lab: 2 for lab in LABELS}
    for lab in LABELS:
        for r in rows:
            if need[lab] <= 0:
                break
            if r["labels"].get(lab) and r not in chosen and len(chosen) < n:
                chosen.append(r)
                for k in LABELS:
                    if r["labels"].get(k):
                        need[k] -= 1
    for r in rows:
        if len(chosen) >= n:
            break
        if r not in chosen:
            chosen.append(r)
    chosen.sort(key=lambda r: r["id"])
    return chosen


def main() -> None:
    test = [
        r
        for r in read_jsonl(DATA / "skills" / "splits" / "test.jsonl")
        if r.get("label_source") != "survey"
    ]
    chosen = pick(test)
    out = DATA / "skills" / "counselor_sheet.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([INSTRUCTIONS])
        w.writerow(["id", "friend_said", "helper_reply", *LABELS, "unsure", "notes"])
        for r in chosen:
            w.writerow(
                [
                    r["id"],
                    " / ".join(r["context"]),
                    r["text"],
                    *["FALSE"] * len(LABELS),
                    "FALSE",
                    "",
                ]
            )
    print(f"wrote {out.relative_to(ROOT)} ({len(chosen)} rows)")


if __name__ == "__main__":
    main()
