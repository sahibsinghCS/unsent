# Safety lane notes

## Done
- `safety/normalizer.py`:
  - NFKC, lowercase, quotes, zero-width
  - leetspeak (including a lone "1" → "i" in leet messages)
  - stretched letters and spaced/dotted letters
  - emoji → tags (💀 marked ambiguous)
  - accent folding
  - misspellings, slang and contractions
  - swapped letters (only into lexicon words)
- `safety/lexicon.yaml` (commented per category) + `safety/lexicon.py`:
  - speaker rules: nearest pronoun, reflection markers, negation, commands vs questions, means + speaker
  - the "me too" rule with history
  - `check_friend` lexicon
- `safety/model.py` + `safety/train_guardian.py` (`make guardian-train`):
  - embedding ⊕ char_wb TF-IDF 2–5 → multinomial LR
  - thresholds grid-searched on val
  - one artifact per embedder: `guardian.joblib` (MiniLM, the app) and `guardian.hash.joblib` (tests); each ~170 KB
  - refuses a mismatched embedder → lexicon-only
- `safety/guardian.py`: `check_user` / `check_friend`, never raises (fails safe). `IMPLEMENTED = True`.
- `safety/dataset.py`: data lane + `data/guardian_extra`, keeping the data lane's own splits.
- Data:
  - `data/guardian_extra/messages.jsonl`: 467 hand-written hard cases, generated from `write_examples.py`
  - `holdout.jsonl`: 59 examples written after freezing, never tuned on
- Eval:
  - `eval/guardian/run_eval.py` → `eval/reports/safety_guardian.json` + `safety_pr_curve.png`
  - `eval/guardian/external_check.py` → `safety_external_data_lane.json` (frozen model on the data lane set, before training on it)
- Tests: `tests/unit/safety/`. There's one normalizer test per rule, plus 53 speaker-awareness pairs. Each pair is checked three ways: risky side flagged, asking side allowed, and allowed by the lexicon alone. Guardian tests cover the tiers, friend lines, fallback, embedder mismatch and fail-safe.
- `docs/how/safety.md`

## In progress
- Nothing. The lane is complete.

## Decisions
- **Combining lexicon and classifier:**
  - The priority is crisis > block > concern.
  - A lexicon "allowed" match (asking the friend, tricky negative, negation, harmless "me too") vetoes the classifier unless p ≥ 0.99.
- **Self-risk + "lol":** still a crisis. We don't downgrade jokes, to be safe.
- **"do you have a plan?":** allowed. Only how/when/where/with-what is method-seeking.
- **Means + helper as speaker ("i have pills"):** concern. Means with no speaker or with "you" as the speaker is method-seeking (block).
- **Method question containing a risk word ("how do u kms"):** method_seeking, not crisis.
- **check_friend:** lexicon only. Feeling-level warning signs ("i don't want to be here anymore") are allowed, as required by SAFE_MESSAGING. Plans, means, encouragement, graphic detail and persona breaks are blocked.
- **Model training:** the model is trained on train only, not train+val, so the val thresholds stay honest.

## Requests
- **Integrator:** after merging wt/data, run `make guardian-train` and then `make eval`. With `data/guardian/` in the repo it's picked up automatically. Until then I trained with `FR_GUARDIAN_DATA=/tmp/wtdata/data/guardian`, a read-only copy of `origin/wt/data`. The committed artifacts were trained on that data (data lane commit as of Oct 22 night).
- **Frontend:** `GuardianResult.evidence` holds readable reasons (matched phrase, or `classifier p(self_risk)=0.83`). These are good for X-ray mode and the "Try the Guardian" box.
- **Data lane (optional):** more *real-sounding* indirect self-risk phrasings would help. The frozen model missed 18% of the data lane's self-risk rows before training. We'd also like more harm_to_other insults. That's the weakest class: recall 0.81 on test (3 of 16 missed). Concern recall is 0.94 (n=17).

## Known issues
- Robustness to emoji: 93% with the normalizer vs 96% without. Emoji tags nudge the classifier on borderline concern and harm messages.
- The test split was looked at while editing lexicon rules (documented in `docs/how/safety.md`). The clean numbers are the external pre-training check and the holdout.
- Context beyond the "me too" rule isn't used.

## Numbers (eval/reports/safety_guardian.json, MiniLM embedder)
- **Asking-friend FPR:**
  - 0.0% on test (n=37)
  - 0.0% on data-lane test rows (n=21)
  - 0.0% on holdout (n=17)
  - 0.0% on the data-lane set before training (n=140)
- **Self-risk recall:**
  - 100% on test (n=37)
  - 100% on holdout (n=14)
  - 81.8% on the data-lane set before training (n=170)
- **Macro F1 on test (n=172):** combined 0.97, lexicon only 0.83, classifier only 0.90
- **Per-class recall on test:**
  - self_risk 1.00 (n=37)
  - concern 0.94 (n=17)
  - harm_to_other 0.81 (n=16)
  - method_seeking 1.00 (n=11)
  - prompt_injection 1.00 (n=10)
  - none 1.00 (n=81)
- **Latency (CPU):** p50 4.6 ms, p95 6.5 ms
- **Friend lines flagged:** 0 / 2,206
- **Robustness, with vs without normalizer:**
  - leetspeak 0.99 vs 0.38
  - spacing 0.98 vs 0.81
  - stretching 0.96 vs 0.92
  - typo 0.98 vs 0.88
  - emoji 0.93 vs 0.96
