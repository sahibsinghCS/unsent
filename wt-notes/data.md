# wt-notes: data lane

## Done
- Skills: 75 contexts, 825 replies (17% Spanish/Spanglish), blind labels (independent Sonnet pass), agreement report, review queue (123 rows), agreed `final.jsonl` (802) and seeded 70/15/15 splits grouped by context.
- Guardian: 698 messages (8 categories) + stratified splits.
- Line bank: 5 × 201 English lines (full level × reaction coverage, fact-gated). Exemplars: 5 × 40. Red-team: 250 attacks.
- Tools: `tools/labeler/index.html` (+ headless test `test_labeler.mjs`), `merge_labels.py`, `split.py`, `agreement_queue.py`, `export_counselor.py`, `import_counselor.py`, `validate.py`; tests in `tests/unit/data/`.
- Docs: `docs/DATASET.md`, `docs/how/data.md`, `docs/CHATGPT_TESTSET_PROMPT.md`.

## In progress
- Nothing. Stretch done: Spanish line bank `data/lines/after-the-breakup.es.jsonl` (201 lines, all cells).

## Decisions
- Disagreements are dropped from `final.jsonl` until Sahib labels them (human > agreed); `--provisional` keeps intended labels for early training.
- Duplicate-line rule is per (level, reaction) cell, since Eli's very short lines ("ok", "thx") legitimately repeat across cells.
- `lang` is `en`, `es` or `mix` (Spanglish). Exemplar labels c/v/f are authored; asked/referred/encouraged are derived from the text so they cannot drift.
- Red-team `expected_action` vocabulary is documented at the top of `scripts/data/author_redteam.py`.

## Requests
- None blocking. Optional: integrator may want `eval/reports/data_*.json` linked in the README metrics table.

## Known issues
- Agreement is very high (mean κ 0.991) because replies are authored from clear phrases; real-world difficulty is higher (see DATASET.md limitations).
- Spanish is not yet native-reviewed. All lines are `review_status: draft`.
- Sahib must label `data/skills/queue.jsonl` (123 rows) then run `merge_labels.py && split.py`; counselor sheet at `data/skills/counselor_sheet.csv`.

## Numbers
- Exact label match 802/825 (97.2%); per-label κ 0.96–1.00; mean κ 0.991 (`eval/reports/data_agreement.json`).
