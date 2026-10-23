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
- Done: /finish speed-up (see Numbers). No pipeline hook needed.
- Later: kappa when counselor labels exist.

## Decisions
- Embedding cache misses stay one text at a time (integrator's decision, not an open request). Batched rows
  differ from per-text vectors by ~1e-6, so a cached vector would depend on which request first embedded the
  text, and the same chat could score differently depending on earlier traffic; that breaks "same input → same
  output". The cost is accepted: /finish 0.24 s with think time (target ≤ 0.4 s), /messages ~150 ms.
- Once the friend was asked directly (flags.asked_directly_ever before the message), the critic never suggests a
  rewrite that asks again: exemplars with strategy ask_directly or the asked_directly label are skipped, and LLM
  candidates the detector scores asked_directly ≥ 0.5 are dropped (same rule as what-if).
- Integrator + Sahib: keep the pooled model the pre-registered rule chose (freeform 0.822 vs whole 0.841,
  within noise at n=221); docs/how/ml.md states the rule, the val decision and the 0.841 we gave up.
- Critic: ended_fail chats open with "This one slipped away, and that's exactly what practice is for." (ES:
  "Esta vez se te escapó, y justo para eso sirve practicar."); whole-chat "never got to" notes capped at 3 by
  TIP_ORDER; per-message notes all kept.
- Retrain at integration e8a9a1f (train 824 / val 152 / test 133 / test_freeform 221). Training now applies
  the pre-registered pooling rule itself (`--pooling auto`, default). On this data it ADOPTED pooling (val OOF
  macro-F1 0.923 → 0.931, ECE 0.011 → 0.010). Info-only cost: test_freeform 0.841 (whole) → 0.822 (pooled),
  uncertain flag rate on freeform 17% → 30%; benefit: probes 12/14 → 13/14. Kept the rule's decision rather
  than overriding it after seeing test numbers. `--pooling off` gives the whole-message model (one command)
  if Sahib/integrator prefer the higher freeform number.
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

## Error analysis: top 10 test_freeform errors (most confident first, current model)
| id | text (short) | label | truth / p | why |
|---|---|---|---|---|
| f0471 | "i'd find a therapist if i were you" | encouraged_help | yes / 0.00 | encouragement phrased as personal advice; reads as advice_dump |
| f0131 | "great plan. we'll go together right after first period" | follow_up | yes / 0.00 | agreement reply; "go together" read as referral, commitment is implicit |
| f0067 | "hell yes. let's do it. i'll text you tonight so you're not by yourself" | encouraged_help | yes / 0.01 | encouragement only via agreeing + "not by yourself" paraphrase |
| f0008 | "you don't have to be fine with me, you know. i'm not going to judge you" | validated | yes / 0.01 | permission-giving validation, no feeling words |
| f0308 | "at night is when everything feels bigger. can i text you tonight…" | validated | yes / 0.01 | validation by normalizing the feeling; follow-up dominates |
| f0111 | "gracias por decírmelo… tampoco quiero que lo cargues solo…" | encouraged_help | yes / 0.02 | Spanish "no lo cargues solo" paraphrase |
| f0148 | "it's okay to not be fine. you don't have to say all good with me" | validated | yes / 0.02 | permission-giving validation |
| f0248 | "…it's a big deal because you matter" | validated | yes / 0.02 | validation through reassurance of worth |
| f0166 | "it's hard to see change from inside it. would you let me go with you to the counselor" | validated | yes / 0.02 | validation clause overshadowed by referral (pooling helps only if the clause is its own sentence) |
| f0028 | "…you don't have to be alone in it. i'll text you every night" | encouraged_help | yes / 0.02 | "not alone in it" paraphrase |

Systematic: (1) indirect encouragement ("not alone in it", "i'd find a therapist"); (2) permission-giving or
worth-affirming validation without feeling words; (3) agreement replies. No test example was patched.

## Requests
- **data (new):** train rows for indirect encouraged_help ("you don't have to be alone in it", "i'd find a
  therapist if i were you" style), permission-giving validation ("it's okay to not be fine", "you don't have
  to be fine with me"), and referrals with time words that are NOT follow_up ("counselor tomorrow? i'll go
  with you") per the label-guide referral rule (probe still follow_up 0.67).
- **data:** (1) more Spanish free-form TRAIN rows, especially validated / follow_up / advice_dump;
  (2) agreement replies in train ("yes let's go", "let's do it") with contexts where the friend proposed
  help, labeled from context; (3) hard negatives for follow_up: goodbyes without commitment ("talk later
  maybe", "gotta go, ttyl"); probe "ok i gotta go to school early tomorrow, talk later maybe" still scores
  follow_up 0.93; (4) minimizing-as-normalizing negatives for validated ("lots of people feel like that,
  you'll be fine"); (5) counselor labels as `data/skills/counselor_labels.jsonl` `{id, labels}`.
- **integrator:** the ML eval and the app need `FR_EMBED=fastembed` (the artifact refuses `hash`).

## Known issues
- /finish worst case: if "finish" arrives the instant the last message returns after a burst of messages,
  it waits for the background explanations still queued (p50 1.66 s); with ≥ 2 s of think time it's 0.24 s.
  The deploy lane's load test should include think time between messages, or it measures this worst case.
- Background explanations add CPU during the chat: /messages p50 50 → ~150 ms on this machine.
- Privacy: the memoized explanations expire after the session TTL (registered with session.register_sweeper);
  embeddings use embed.py's shared TTL'd cache. No ml-local cache keeps conversation text longer.
- First fastembed call takes ~2.5 s (model load); then ~60–110 ms per message for predict + highlights.
- Under `FR_EMBED=hash` (tests, `make smoke`) the detector is the keyword stub; the real detector is
  covered by unit tests with a tiny hash-trained model.

## Numbers (seed 0, fastembed, retrained at integration e8a9a1f, pooling adopted by rule)
| macro-F1 | val (n=152) | composed test (n=133, optimistic) | **test_freeform (n=221, honest)** |
|---|---|---|---|
| keyword baseline | 0.551 | 0.561 | 0.490 |
| Model A | 0.775 | 0.830 | 0.695 |
| Model B | 0.896 | 0.966 | 0.752 |
| **ensemble** | 0.951 | 0.969 | **0.822** |
- Previous model (trained at 9f36790) on the SAME new splits: val 0.926 / test 0.963 / freeform 0.820.
  Retrained whole-message model (same run, pooling off): val 0.946 / test 0.965 / freeform 0.841.
- ECE before → after: val 0.130 → 0.010 · test 0.128 → 0.012 · freeform 0.124 → 0.012.
  Brier: val 0.043 → 0.012 · test 0.032 → 0.007 · freeform 0.053 → 0.029.
- Uncertain (band 0.20–0.80 tuned on val): flag rate per message val 13.8% / test 11.3% / freeform 29.9%;
  error rate flagged vs unflagged: val 17% vs 1.2%, test 7% vs 0.6%, freeform 39% vs 2.9%.
- Probes: 13/14 (miss: "can we talk to the counselor tomorrow? i'll go with you" → follow_up 0.67).
- Counselor kappa: not yet (no counselor labels).
- /finish p50 on a fixed 6-message chat (fastembed, FR_LLM=0, 1 user, cold caches each run, n=5), after the
  privacy fix (shared TTL'd per-text cache from embed.py + TTL'd explanation memo): before 2.42 s → 0.24 s with
  a 2 s pause before finish / 1.66 s with finish sent immediately; /messages p50 ~150 ms. (My earlier private
  batched LRU gave 0.09 / 0.94 s; the shared cache embeds misses one text at a time.) Output identical (unit test on a fixed conversation;
  real-model API report compared field by field, 0 differences > 1e-6).
