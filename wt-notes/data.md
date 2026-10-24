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
- queue.jsonl now 259 rows (129 disagreements + 130 audit); final.jsonl 1,410 rows until Sahib labels them.

## Update 3 (rule adjudication)
- `adjudicate_rules.py` settles disagreements using only the explicit LABEL_GUIDE rules (referral alone = referred_* only; "i'll go with you" is part of the referral; named adult / 988 / explicit ask). 94 of 221 adjudicated (`adjudicated_labels.jsonl`, source `adjudicated_rule`); 127 judgment calls + 120 audit remain in `queue.jsonl` (259 rows) for Sahib. Priority: human > adjudicated_rule > agreed.
- final.jsonl 1,172; splits 666/152/133/221; ids only added, none moved; test_freeform leakage 0.0%.

## Update 4 (train-only round, from ML error analysis)
- Added 160 TRAIN-ONLY rows (`replies_train_extra.jsonl`, contexts `x-*` in `contexts_extra.jsonl`): follow_up hard negatives and genuine follow-ups, ~50 Spanish, agreement replies, minimizing vs genuine normalizing. Blind-labeled with the updated guide (98.8% exact match, kappa 0.992). 40 Spanish exemplars for Maya in `data/exemplars/after-the-breakup.es.jsonl`.
- final.jsonl 1,330; splits 824/152/133/221 (158 new rows in train only, all other ids unchanged); test_freeform leakage 0.0%; queue 259 rows (129 disagreements + 130 audit).

## Update 5 (engine bank evaluation)
- Rewrote 3 level-2 asked_directly lines (mya-en/mya-es/jor-en -03) as hesitant partial truths without disclosure, and made 16 duplicate line texts distinct (15 Eli, 1 Priya) via `scripts/data/lines_src/patches.py` (same ids and cells). `validate.py` now enforces scenario-wide unique line text and the engine's level<3 disclosure backstop. The integrator's bank validator (`python -m backend.app.engine.verifier --all`, run in a temporary worktree of origin/claude/amazing-carson-31tzo3 with my data/lines copied in) reports OK for all 5 scenarios and the es bank.

## Update 6 (final train-only batch)
- +80 TRAIN-ONLY rows (t0161-t0240, contexts `y-*`): ~50 Spanish/Spanglish encouragement/follow-up/referral/validation and ~30 English indirect encouragement (with ultimatum hard negatives). Blind agreement on the 240 train-only rows: 97.9% exact, kappa 0.989. `adjudicate_rules.py` also treats "could really help / take weight off" as general encouragement (R-ENC-GEN).
- final.jsonl 1,410; splits 904/152/133/221 (only additions to train; val/test/test_freeform ids identical); test_freeform leakage 0.0%; queue 259 (129 + 130 audit).

## Update 7 ("Add your own friend": neutral bank)
- Wrote `data/lines/_custom.en.jsonl` and `_custom.es.jsonl` (201 lines each, ids `cus-en-L2-validated-01`, scenario_id `_custom`, fact ids c0a..c4b) and `data/exemplars/_custom.en.jsonl` / `_custom.es.jsonl` (40 each). Sources: `scripts/data/lines_src/custom.py`, `custom_es.py`, `author_exemplars.py`. Situation-neutral and gender-neutral (no names, no third-party pronouns, no breakup/grades/chat details); L3 is indirect with no clinical words; no hotlines/advice from the friend.
- Checked with the integrator's `validate_bank` and `services.guardian().check_friend` (all bubbles level none), via `tests/unit/data/test_custom_bank.py` (the engine part skips on a branch without `validate_bank`; I ran it in a temporary worktree of origin/claude/amazing-carson-31tzo3: 5 passed). The template is copied to `tests/unit/data/fixtures/_custom.json` (my lane) because data/scenarios is not mine and I did not merge.
- Exemplar label derivation now also recognises singular "parent" and Spanish "familiar/adulto" (two Maya exemplar files changed slightly).

## Decisions
- Disagreements are dropped from `final.jsonl` until Sahib labels them (human > agreed); `--provisional` keeps intended labels for early training.
- Duplicate-line rule is per (level, reaction) cell, since Eli's very short lines ("ok", "thx") legitimately repeat across cells.
- `lang` is `en`, `es` or `mix` (Spanglish). Exemplar labels c/v/f are authored; asked/referred/encouraged are derived from the text so they cannot drift.
- Red-team `expected_action` vocabulary is documented at the top of `scripts/data/author_redteam.py`.

## Requests
- **Integrator:** `tests/unit/test_contracts.py::test_line_bank_and_exemplar_files_validate` asserts every `data/lines/*.jsonl` scenario_id is in `load_scenarios()`, which skips `_custom` (underscore files). With the new `_custom` banks it fails until that test skips or whitelists `_custom` (one line; not my file).
- None blocking. Optional: integrator may want `eval/reports/data_*.json` linked in the README metrics table.

## Known issues
- Agreement is very high (mean κ 0.991) because replies are authored from clear phrases; real-world difficulty is higher (see DATASET.md limitations).
- Spanish is not yet native-reviewed. All lines are `review_status: draft`.
- Sahib must label `data/skills/queue.jsonl` (259 rows) then run `merge_labels.py && split.py`; counselor sheet at `data/skills/counselor_sheet.csv`.

## Numbers
- Blind agreement: composed 85.9% exact (mean κ 0.949), free-form 74.9% (κ 0.879) (`eval/reports/data_agreement.json`).
