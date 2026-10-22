"""Import the counselor's filled-in CSV (downloaded from Google Sheets) and compare it with our final labels.

Usage: python scripts/data/import_counselor.py path/to/sheet.csv
Writes data/skills/counselor_labels.jsonl and eval/reports/data_counselor_agreement.json.
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from common import DATA, LABELS, ROOT, read_jsonl, write_jsonl


def truthy(v: str) -> bool:
    return str(v).strip().upper() in {"TRUE", "YES", "1", "X", "✓", "✔"}


def parse(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    header_at = next(i for i, r in enumerate(rows) if r and r[0].strip().lower() == "id")
    header = [h.strip() for h in rows[header_at]]
    out = []
    for r in rows[header_at + 1 :]:
        if not r or not r[0].strip():
            continue
        d = dict(zip(header, r, strict=False))
        out.append(
            {
                "id": d["id"].strip(),
                "labels": {lab: truthy(d.get(lab, "")) for lab in LABELS},
                "unsure": truthy(d.get("unsure", "")),
                "label_source": "counselor",
            }
        )
    return out


def compare(counselor: list[dict], final: list[dict]) -> list[dict]:
    fin = {r["id"]: r["labels"] for r in final}
    now = datetime.now(UTC).astimezone().isoformat(timespec="seconds")
    rows = [c for c in counselor if c["id"] in fin and not c["unsure"]]
    recs = []
    for lab in LABELS:
        agree = sum(bool(c["labels"][lab]) == bool(fin[c["id"]][lab]) for c in rows) / max(
            1, len(rows)
        )
        recs.append(
            {
                "lane": "data",
                "metric": f"counselor_agreement_{lab}",
                "value": round(agree, 4),
                "n": len(rows),
                "split": "test",
                "notes": "counselor vs final labels (30-row sample)",
                "created": now,
            }
        )
    exact = sum(
        all(bool(c["labels"][lab]) == bool(fin[c["id"]][lab]) for lab in LABELS) for c in rows
    ) / max(1, len(rows))
    recs.append(
        {
            "lane": "data",
            "metric": "counselor_exact_match",
            "value": round(exact, 4),
            "n": len(rows),
            "split": "test",
            "notes": "all 10 labels identical",
            "created": now,
        }
    )
    return recs


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    counselor = parse(Path(sys.argv[1]))
    write_jsonl(DATA / "skills" / "counselor_labels.jsonl", counselor)
    recs = compare(counselor, read_jsonl(DATA / "skills" / "final.jsonl"))
    (ROOT / "eval" / "reports").mkdir(parents=True, exist_ok=True)
    (ROOT / "eval" / "reports" / "data_counselor_agreement.json").write_text(
        json.dumps(recs, indent=1) + "\n", encoding="utf-8"
    )
    print(f"imported {len(counselor)} rows; exact-match {recs[-1]['value']:.0%}")


if __name__ == "__main__":
    main()
