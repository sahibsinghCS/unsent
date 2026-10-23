# wt-notes: data lane

## Done
- Skills: 75 contexts, 825 replies (17% Spanish/Spanglish), blind labels (independent Sonnet pass), agreement report, review queue (123 rows), agreed `final.jsonl` (802) and seeded 70/15/15 splits grouped by context.
- Guardian: 698 messages (8 categories) + stratified splits.
- Line bank: 5 × 201 English lines (full level × reaction coverage, fact-gated). Exemplars: 5 × 40. Red-team: 250 attacks.
- Tools: `tools/labeler/index.html` (+ headless test `test_labeler.mjs`), `merge_labels.py`, `split.py`, `agreement_queue.py`, `export_counselor.py`, `import_counselor.py`, `validate.py`; tests in `tests/unit/data/`.
- Docs: `docs/DATASET.md`, `docs/how/data.md`, `docs/CHATGPT_TESTSET_PROMPT.md`.

## In progress
- Nothing. Stretch done: Spanish line bank `data/lines/after-the-breakup.es.jsonl` (201 lines, all cells).

## Update (integrator request: free-form + leakage)
- Added `replies_freeform.jsonl` (443 hand-written replies incl. asked_directly/follow_up hard negatives), fixed composed joins and Guardian doubled words, re-ran ONE blind pass (1,299 rows). Agreement: composed 85.9% exact / mean kappa 0.949; free-form 77.9% / 0.887.
- New splits incl. `test_freeform.jsonl` (197, incl. 26 test-only referred_988/near-miss rows; 0.0% 5-gram leakage vs train; composed test 21.0%). `eval/reports/data_leakage.json`. No normalized text in more than one split.
- Did NOT merge origin/claude/amazing-carson-31tzo3 (AGENTS rule: never merge; integrator said skip).
- queue.jsonl now 247 rows (127 disagreements + 120 audit); final.jsonl 1,172 rows until Sahib labels them.

## Update 3 (rule adjudication)
- `adjudicate_rules.py` settles disagreements using only the explicit LABEL_GUIDE rules (referral alone = referred_* only; "i'll go with you" is part of the referral; named adult / 988 / explicit ask). 94 of 221 adjudicated (`adjudicated_labels.jsonl`, source `adjudicated_rule`); 127 judgment calls + 120 audit remain in `queue.jsonl` (247 rows) for Sahib. Priority: human > adjudicated_rule > agreed.
- final.jsonl 1,172; splits 666/152/133/221; ids only added, none moved; test_freeform leakage 0.0%.

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
- Sahib must label `data/skills/queue.jsonl` (247 rows) then run `merge_labels.py && split.py`; counselor sheet at `data/skills/counselor_sheet.csv`.

## Numbers
- Blind agreement: composed 85.9% exact (mean κ 0.949), free-form 74.9% (κ 0.879) (`eval/reports/data_agreement.json`).
