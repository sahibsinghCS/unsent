"""(a) Single-message attacks: every attack-bank row -> Guardian.check_user, no conversation history.

For each strategy: how often the Guardian's action matches the bank's expected_action, a confusion
table (expected -> actual action) and the full list of misses. Run: uv run python -m eval.redteam.attacks
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict

from eval.redteam import common


def classify(guardian, rows: list[dict]) -> list[dict]:
    """One result row per attack: what the Guardian did and whether it matched the expectation."""
    out = []
    for row in rows:
        result = guardian.check_user(row["text"], [])
        out.append(
            {
                **row,
                "action": result.action,
                "categories": result.categories,
                "match": result.action in common.ACCEPT[row["expected_action"]],
                # A miss that errs on the cautious side (e.g. a persona question blocked) is "safe".
                "unsafe_miss": result.action == "continue"
                and row["expected_action"] in ("crisis_pause", "block_message"),
            }
        )
    return out


def _rates(rows: list[dict], split: str, label: str) -> list[dict]:
    stoppable = [r for r in rows if r["expected_action"] in ("crisis_pause", "block_message")]
    return [
        common.record("attacks.match_rate", common.rate(sum(r["match"] for r in rows), len(rows)),
                      len(rows), split,
                      f"{label}; Guardian action == expected_action, single message, no history"),
        common.record("attacks.unsafe_miss_rate",
                      common.rate(sum(r["unsafe_miss"] for r in stoppable), len(stoppable)),
                      len(stoppable), split,
                      f"{label}; should pause or block but the Guardian let it through"),
    ]  # fmt: skip


def _confusion(rows: list[dict]) -> dict[str, dict[str, dict[str, int]]]:
    tables: dict[str, dict[str, Counter]] = defaultdict(lambda: defaultdict(Counter))
    for r in rows:
        tables[r["strategy"]][r["expected_action"]][r["action"]] += 1
    return {s: {k: dict(v) for k, v in t.items()} for s, t in sorted(tables.items())}


def summarize(results: list[dict], embed: str) -> tuple[list[dict], dict, list[dict]]:
    """Records for the full bank and its dev / holdout halves (common.attack_half), aggregate details
    (counts only, no texts) and the DEV-ONLY failure list. Holdout failures are never written out, so
    the safety lane can fix the Guardian on dev and the holdout number stays an honest test."""
    halves = {
        h: [r for r in results if common.attack_half(r["id"]) == h] for h in ("dev", "holdout")
    }
    records = _rates(results, "attack_bank", "full bank")
    records += _rates(halves["dev"], "attack_bank dev", "dev half (safety lane may tune on it)")
    records += _rates(halves["holdout"], "attack_bank holdout", "holdout half (never tuned on)")
    by_strategy: dict[str, list[dict]] = defaultdict(list)
    for r in results:
        by_strategy[r["strategy"]].append(r)
    for strategy, rows in sorted(by_strategy.items()):
        records.append(
            common.record(
                f"attacks.match_rate.{strategy}",
                common.rate(sum(r["match"] for r in rows), len(rows)),
                len(rows),
                "attack_bank",
                f"full bank; expected: {', '.join(sorted({r['expected_action'] for r in rows}))}",
            )
        )
    dev_failures = [
        {k: r[k] for k in ("id", "strategy", "text", "expected_action", "action", "categories")}
        for r in halves["dev"]
        if not r["match"]
    ]
    details = {
        "embed": embed,
        "split_rule": "dev if sha256(attack id) starts with 0-7, else holdout",
        "confusion_full": _confusion(results),
        "confusion_holdout": _confusion(halves["holdout"]),
        "mismatches": {h: len([r for r in rows if not r["match"]]) for h, rows in halves.items()},
        "dev_failures_file": f"eval/redteam/results/attacks_DEV_ONLY_failures.{embed}.json",
    }
    return records, details, dev_failures


def run(embed: str = "auto") -> dict:
    embed = common.configure(embed)
    from backend.app.safety.guardian import Guardian

    results = classify(Guardian(), common.attacks())
    records, details, dev_failures = summarize(results, embed)
    common.write_report("attacks", records, embed, details)
    path = common.DETAILS / f"attacks_DEV_ONLY_failures.{embed}.json"
    note = (
        "DEV half only. Holdout failures are deliberately not listed (see eval/redteam/attacks.py)."
    )
    payload = {"note": note, "embed": embed, "failures": dev_failures}
    path.write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"records": records, "failures": dev_failures, **details}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--embed", default="auto", choices=["auto", "hash", "fastembed"])
    out = run(parser.parse_args().embed)
    for r in out["records"]:
        print(f"{r['metric']:<40} {r['value']:>7}  n={r['n']}")
    print(f"{len(out['failures'])} dev mismatches -> {out['dev_failures_file']}")


if __name__ == "__main__":
    main()
