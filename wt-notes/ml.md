# ml lane notes

## Done
- Skill detector: Model A (fastembed reply ⊕ last friend message → LR per label, balanced), Model B
  (char_wb 2–5 + word 1–2 TF-IDF → LR per label), per-label Platt stacker on val. Explicit-term rule
  caps asked_directly at 0.2 (`ml/rules.py`, on the safety normalizer's output, EN+ES).
- Uncertain = A and B on opposite sides of 0.5 AND final p in a band tuned on val (`ml/uncertainty.py`;
  current band 0.35–0.65, stored in the artifact + meta).
- Highlights: phrase occlusion in log-odds (1–5 words within punctuation, crisp core ≥ 80% of the drop,
  ≤ 2 spans per label, neighbours merged); `Highlight.delta` = log-odds drop.
- Critic (IMPLEMENTED): per-message probs/uncertain/highlights; verified rewrites (exemplars first, LLM
  fallback via `llm.chat_json("rewrite", role="judge")`, both must gain ≥ 0.2 on our detector and pass the
  Guardian); `rewrite_source` + `rewrite_skill`; 7-skill summary; turning point; template summary
  ("You never lost their trust…" when there is none).
- Train (`make train`, seeded) → `models/skill_detector.joblib` (0.53 MB) + meta. Retrained ONCE on the new
  splits at integration 9f36790 (train 615 / val 142 / test 124, all `agreed`; queue.jsonl never used).
- Eval (`eval/skills/run_eval.py`): val, composed test, test_unseen_text, test_freeform (+ survey/cross-model
  when present): per-label P/R/F1 + macro-F1 for keyword/A/B/ensemble, ECE + Brier, uncertain stats, probes,
  top-10 errors → `eval/reports/ml_skills.json`, `eval/skills/results.json`, PNGs (`*_freeform.png` too).
- Kappa CLI (`python -m backend.app.ml.kappa`), seeded 1,000-resample bootstrap CI.

## In progress
- HOLD (integrator amendment): retrain ONCE when the adjudicated labels land (label-guide rule 10c406e:
  referral ≠ encouraged_help ≠ follow_up), then full eval + re-run `eval/skills/pooling_experiment.py`.
  Eval-only re-run when the ~20 free-form referred_988 rows land. Kappa when counselor labels exist.
- Ready now (code, no new artifact): truthful critic text (refer-without-persuade sentence, label-specific
  listen reasons), clause-rounded highlights, pooling experiment (not adopted), probe "i'm really glad you told me".

## Decisions
- Clause pooling NOT adopted (pre-registered rule: val out-of-fold macro-F1 must improve, ECE ≤ +0.01):
  whole 0.921 vs pooled 0.916 macro-F1; ECE 0.013 vs 0.011; validated F1 0.938 vs 0.950; freeform (info)
  0.818 vs 0.802. `SkillModel.pooling` stays False; experiment re-runs after the next data update.
- Highlights are rounded out to the clause edge when ≤ 2 words per side ("hey are" → "hey are you ok",
  "i'll go with" → "i'll go with you"); checked on the probe messages, all read as natural phrases.
- Critic: when refer ≥ 0.5 and persuade < 0.5, say "You connected them with someone who can help. Next
  time, also tell them why…" (never "never got to encouraging"). Listen reasons: dismissed → "brushed off
  the feeling", advice_dump → "jumped to fixing it before listening".
- test_freeform is the honest headline number; composed test is reported but called optimistic.
- Every tuned number (stacker, uncertain band) is fitted on val only; tests are only scored.
- Rubric "listen" per message (validated × (1 − max(dismissed, advice)) within the message), best message.
- `Highlight.delta` is a log-odds drop (probabilities saturate near 1). Frontend: treat as relative strength.
- No code change for the "thinking about killing yourself" highlight: after the retrain the real model
  highlights the full phrase "thinking about killing yourself" (end-to-end check), so the 80%-core trim stays.
- asked_directly rule terms were widened only from TRAIN misses (dying, not waking up, stay alive, done…
  with life); 0 labeled direct asks missed in any split, 0 non-asks matched.

## Error analysis: top 10 test_freeform errors (most confident first)
| id | text (short) | label | truth / p | why |
|---|---|---|---|---|
| f0283 | "almorzar sola cansa. mañana te acompaño" | validated | yes / 0.00 | Spanish implicit validation, no "that sounds" cue; few Spanish free-form rows in train |
| f0308 | "at night is when everything feels bigger. can i text you tonight…" | validated | yes / 0.00 | validation by normalizing the feeling, no stock phrase |
| f0225 | "…se nota que no. cuenta conmigo" | follow_up | yes / 0.00 | "cuenta conmigo" (count on me) is unseen Spanish follow-up wording |
| f0067 | "hell yes. let's do it. i'll text you tonight…" | encouraged_help | yes / 0.01 | encouragement only by agreeing with the friend's plan (context-dependent) |
| f0065 | "that sounds like a plan. counselor, then lunch, then maybe boba" | follow_up | yes / 0.01 | follow-up expressed as a plan list; "lunch" was a negative cue after hard negatives |
| f0267 | "pues no se lo digas todavía, mejor espera…" | advice_dump | yes / 0.02 | Spanish advice; few Spanish advice_dump rows |
| f0421 | "¿has pensado en dejar el chat? yo lo dejaría" | advice_dump | yes / 0.02 | Spanish advice phrased as a question |
| f0028 | "…you don't have to be alone in it. i'll text you every night" | encouraged_help | yes / 0.02 | "not alone in it" paraphrase; model wants "deal with this alone"/"talk to someone" |
| f0318 | "honestly lots of people feel like that after moving, you'll be fine!" | validated | no / 0.97 | minimizing dressed as normalizing; looks like validation |
| f0188 | "yes. let's go right now. i'm with you all the way" | referred_adult | yes / 0.04 | referral only via agreeing to the friend's counselor idea (context-dependent) |

Systematic: (1) Spanish free-form under-represented; (2) agreement replies whose label comes from the
friend's previous message; (3) implicit validation / minimizing-as-normalizing. No test example was patched.

## Requests
- **data:** (1) more Spanish free-form TRAIN rows, especially validated / follow_up / advice_dump;
  (2) agreement replies in train ("yes let's go", "let's do it") with contexts where the friend proposed
  help, labeled from context; (3) hard negatives for follow_up: goodbyes without commitment ("talk later
  maybe", "gotta go, ttyl"); probe "ok i gotta go to school early tomorrow, talk later maybe" still scores
  follow_up 0.93; (4) minimizing-as-normalizing negatives for validated ("lots of people feel like that,
  you'll be fine"); (5) counselor labels as `data/skills/counselor_labels.jsonl` `{id, labels}`.
- **integrator:** the ML eval and the app need `FR_EMBED=fastembed` (the artifact refuses `hash`).

## Known issues
- First fastembed call takes ~2.5 s (model load); then ~60–110 ms per message for predict + highlights.
- Under `FR_EMBED=hash` (tests, `make smoke`) the detector is the keyword stub; the real detector is
  covered by unit tests with a tiny hash-trained model.

## Numbers (seed 0, fastembed, retrained at integration 9f36790)
| macro-F1 | val (n=142) | composed test (n=124, optimistic) | **test_freeform (n=171, honest)** |
|---|---|---|---|
| keyword baseline | 0.548 | 0.557 | 0.480 |
| Model A | 0.812 | 0.849 | 0.700 |
| Model B | 0.895 | 0.948 | 0.735 |
| **ensemble** | 0.926 | 0.959 | **0.818** |
- ECE before → after: val 0.128 → 0.017 · test 0.125 → 0.016 · freeform 0.115 → 0.019.
  Brier: val 0.041 → 0.015 · test 0.032 → 0.009 · freeform 0.055 → 0.035.
- Uncertain (band 0.35–0.65): flag rate per message val 8.5% / test 8.1% / freeform 18.1%; error rate of
  flagged vs unflagged decisions val 75% vs 1.6%, test 45% vs 0.7%, freeform 62.5% vs 3.5%.
- Probes: 9/10 as expected ("i'm really glad you told me" → validated 0.995); "talk later maybe" →
  follow_up 0.93 is the miss.
- Counselor kappa: not yet (no counselor labels).
