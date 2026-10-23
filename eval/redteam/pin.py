"""Freeze today's passing safety cases as permanent regression tests (tests/safety/pinned/).

Always uses the hash embedder (what `make check` runs). Pins:
  attacks_pass.json  attack-bank ids whose single-message Guardian action matches expected_action today
  fuzz_cases.json    a seeded sample of fuzzed critical messages (all Guardian splits) handled right today
Cases that fail today are NOT pinned: they are listed in eval/redteam/results/ and wt-notes/redteam.md
(Requests) for the safety lane. Run: uv run python -m eval.redteam.pin
"""

from __future__ import annotations

import json
import random

from eval.redteam import common

FUZZ_SAMPLE = 400


def main() -> None:
    common.configure("hash")
    from backend.app.safety.guardian import Guardian
    from eval.redteam import attacks, fuzz

    guardian = Guardian()
    passing = [r["id"] for r in attacks.classify(guardian, common.attacks()) if r["match"]]
    results = [r for r in fuzz.fuzz(guardian, fuzz.rows_for("all")) if r["correct"]]
    rng = random.Random(common.SEED)
    sample = sorted(
        rng.sample(results, k=min(FUZZ_SAMPLE, len(results))),
        key=lambda r: (r["id"], r["perturbation"], r["text"]),
    )
    cases = [{k: r[k] for k in ("id", "category", "perturbation", "text")} for r in sample]
    common.PINNED.mkdir(parents=True, exist_ok=True)
    for name, payload in (("attacks_pass.json", passing), ("fuzz_cases.json", cases)):
        path = common.PINNED / name
        path.write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{path.relative_to(common.ROOT)}: {len(payload)} cases")


if __name__ == "__main__":
    main()
