"""Score the CURRENT Guardian on an outside dataset it has never seen (SAFETY lane).

  uv run python eval/guardian/external_check.py /tmp/wtdata/data/guardian/messages.jsonl NAME

Writes eval/reports/safety_external_<NAME>.json. Used once, before training on the data lane's
set, to get an honest "never seen this author's writing" number. Prints every miss for review.
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.app.config import EVAL_REPORTS_DIR  # noqa: E402
from backend.app.embed import get_embedder  # noqa: E402
from backend.app.safety.guardian import Guardian  # noqa: E402
from backend.app.safety.model import CATEGORY_TO_CLASS  # noqa: E402
from backend.app.safety.train_guardian import predicted_class, score  # noqa: E402


def main(path: str, name: str) -> None:
    rows = [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x]
    commit = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=ROOT
    ).stdout.strip()
    created = datetime.now(UTC).isoformat(timespec="seconds")
    note = f"frozen Guardian @ {commit}, never trained on this set; embedder={get_embedder().name}"
    records = []
    for label, g in (
        ("combined", Guardian(use_moderation=False)),
        ("lexicon_only", Guardian(use_classifier=False, use_moderation=False)),
    ):
        preds = [predicted_class(g.check_user(r["text"], [])) for r in rows]
        s = score(rows, preds)
        counts = Counter(r["category"] for r in rows)
        for metric, n in (
            ("asking_friend_fpr", counts["asking_friend"]),
            ("self_risk_recall", counts["self_risk"]),
            ("macro_f1", len(rows)),
        ):
            records.append(
                {
                    "lane": "safety",
                    "metric": f"external_{name}.{label}.{metric}",
                    "value": round(s[{"asking_friend_fpr": "asking_fpr"}.get(metric, metric)], 4),
                    "n": n,
                    "split": f"external:{name}",
                    "notes": note,
                    "created": created,
                }
            )
        print(label, {k: round(v, 4) for k, v in s.items()})
        if label == "combined":
            misses = Counter()
            for r, p in zip(rows, preds, strict=True):
                if p != CATEGORY_TO_CLASS[r["category"]]:
                    misses[(r["category"], p)] += 1
                    print(f"  miss {r['category']:>16} -> {p:<16} {r['text']}")
            print("misses:", dict(misses))
    out = EVAL_REPORTS_DIR / f"safety_external_{name}.json"
    out.write_text(json.dumps(records, indent=1) + "\n")
    print(f"wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "external")
