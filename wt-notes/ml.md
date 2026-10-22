# ml lane notes

## Done
- Seed set: `tests/unit/ml/fixtures/seed.jsonl` (114 hand-written rows, `final.jsonl` format; tests only).
- Model A (fastembed reply ⊕ last-friend-message → LR per label, balanced), Model B (char_wb 2–5 + word
  1–2 TF-IDF → LR per label), per-label Platt stacker on val (`ml/calibrate.py`, `ml/model.py`).
- `ml/train.py` (`make train`, `--data-dir/--out-dir/--seed`): seeded, saves artifact + meta (embedder,
  data hash, counts, date, val/test metrics); checks size < 25 MB; hash-splits `final.jsonl` if no `splits/`.
- `ml/skill_detector.py`: lazy load, refuses mismatched embedder, `predict/predict_many/uncertain/explain`.
  `IMPLEMENTED` = artifact present and trained with the active embedder (True in prod with fastembed;
  False under `FR_EMBED=hash`, so tests/smoke use the keyword stub for the detector).
- `ml/explain.py`: leave-one-word-out occlusion → Highlights (p ≥ 0.5, delta ≥ 0.1, top 3, merged
  neighbours, exact offsets) with greedy-deletion fallback for redundant evidence.
- `ml/critic.py` (`IMPLEMENTED = True`): per-message probs (node.events first), uncertain, highlights,
  rule-based missing skill → verified exemplar rewrite (gain ≥ 0.2 + Guardian), 7-skill summary,
  engine turning point, missed opportunities, template summary.
- `eval/skills/run_eval.py` (+ `ml/evaluate.py`): baseline vs A vs B vs ensemble on test, ECE before/after,
  reliability/confusion/F1 PNGs, extra sets (`survey_real.jsonl`, `test_cross_model.jsonl`) and a
  "test_unseen_text" set (test rows whose text is not in train/val).
- `ml/kappa.py`: Cohen's kappa per label + overall, 1,000-resample seeded bootstrap CI, `--model` option.
- Merged integration branch (contracts 1.2, Sahib approved in this session). Critic fills `rewrite_source`
  ("exemplar" | "llm") and `rewrite_skill` (rubric skill whose labels the gain is measured on; the no-secrecy
  rewrite reports "refer"). LLM fallback (`llm.chat_json("rewrite", role="judge")`, prompt in
  `ml/prompts/rewrite.md`) runs only when no exemplar passes; 2 candidates, same ≥ 0.2 + Guardian check, best
  verified gain wins; `LLMUnavailable`/`FR_LLM=0` → exemplars only. Tests use `llm.register_fake` only.
- Phase B: trained on data lane's provisional splits (origin/wt/data @ 3ed8f17) with fastembed;
  artifact + `eval/reports/ml_skills.json` committed.

## In progress
- Waiting (per integrator, don't retrain yet): new splits with `splits/test_freeform.jsonl`. The eval already reports
  `test_freeform` separately (with the keyword baseline); retrain once when it lands.

## Decisions
- Stacker = LR on (logit pA, logit pB) fitted on val = stacking and Platt calibration in one step; falls
  back to the average when val has < 2 positives or negatives for a label.
- Rubric "listen" is computed per message (validated × (1 − max(dismissed, advice_dump)) in the same
  message), then the best message is taken, so an early slip doesn't erase later listening. no_secrecy =
  1 − peak(promised_secrecy).
- Rewrite triggers (priority): promised secrecy → refer; dismissed/advice → validate; level ≥ 2 and never
  asked → ask_directly; level ≥ 3, asked, no referral → refer; first message without check-in/validation →
  check_in. Up to 3 exemplars tried.
- Guardian-blocked messages are not scored by the critic.
- Occlusion fallback (greedy deletion up to 6 words) because calibrated probs saturate near 1 and single
  words are often redundant; delta reported is the joint drop.

## Requests
- **data:** (1) dedupe: 13 test texts also appear in train (normalized text match); (2) hard negatives
  for follow_up, e.g. check-ins mentioning "lunch"/"tomorrow" ("you seemed off at lunch" → follow_up 0.87);
  (3) push `data/exemplars/*.jsonl` (rewrites need them); (4) counselor labels as
  `data/skills/counselor_labels.jsonl` `{id, labels}` (kappa default path) and the real survey set as
  `data/skills/survey_real.jsonl` with `labels`; a cross-model set as `test_cross_model.jsonl`.
- **integrator:** `make eval`/prod need `FR_EMBED=fastembed` for the ML eval (the artifact refuses hash).
  To retrain after human labels land:
  `git archive origin/wt/data data/skills | tar -x -C /tmp/wtdata`, then
  `FR_EMBED=fastembed uv run python -m backend.app.ml.train --data-dir /tmp/wtdata/data/skills`, then
  `FR_EMBED=fastembed uv run python eval/skills/run_eval.py --data-dir /tmp/wtdata/data/skills`.
  (Once data is merged into the integration branch, plain `FR_EMBED=fastembed make train` works.)

## Known issues
- Labels are provisional "intended" labels on synthetic replies → numbers are optimistic.
- First `predict` with fastembed takes ~2.5 s (model load); then ~60 ms per message, ~0.6 s for a
  5-message critic report. Deploy lane may want a warm-up call.
- Under `FR_EMBED=hash` (tests, `make smoke`) the detector is the keyword stub; the real detector is
  covered by unit tests with a tiny hash-trained model.

## Numbers (test split, n=143, provisional labels, fastembed)
- macro-F1: keyword 0.592 · Model A 0.843 · Model B 0.947 · **ensemble 0.957** (unseen-text n=130: 0.957)
- ECE: 0.133 before stacking → 0.013 after
- Counselor kappa: not yet (no counselor labels)
