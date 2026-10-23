# The skill detector and critic

*Owner: ml lane. Plain language, so Sahib can explain every part to a judge.*

## What it does
Every time the helper sends a message, the **skill detector** reads it (plus the friend's last message)
and gives a probability for each of 10 behaviours: checked in, validated, asked directly about suicide,
encouraged help, referred to an adult, referred to 988, followed up, and the three mistakes: dismissed,
advice dump, promised secrecy. The state engine uses those probabilities to decide how the friend reacts.
X-ray mode shows them live.

At the end of the chat the **critic** turns them into the feedback report:
- a score per message, with **highlighted words** that made the model decide;
- an **"uncertain"** flag when our two models disagree;
- a **better reply** where a key skill was missing, but only if we could check that it's better;
- a **7-skill summary** (the radar chart), the **turning point** (where trust dropped most) and a
  2–3 sentence summary.

Our models are 100% local: no AI service decides any score. Better replies come first from an exemplar
bank that people wrote. Only if none of those passes may the critic ask an AI (OpenAI, through
`backend/app/llm.py`) for two suggestions, and our own detector then checks them: **the AI suggests,
our model verifies.** The summary is fill-in-the-blank templates.

## How it works
**Two different models, then a referee.**
- **Model A, meaning:** a small local language model (`paraphrase-multilingual-MiniLM-L12-v2`, run
  offline through fastembed) turns the reply into 384 numbers that capture its *meaning*. It does the
  same for the friend's last message. We glue the two together (768 numbers) and train one logistic
  regression per label. It knows "are you having thoughts of ending it?" means the same as "are you
  thinking about suicide?", even in Spanish.
- **Model B, spelling:** TF-IDF over chunks of 2–5 characters and over single words and word pairs,
  then one logistic regression per label. It's good with slang and typos ("r u ok", "thats rlly heavy")
  because chunks like "rlly" still match.
- **Stacking + calibration:** for each label a third, tiny logistic regression looks at both models'
  answers and makes the final call. We fit it on the **validation** set, which neither base model saw.
  A logistic regression on top of model scores is called **Platt scaling**. It makes the output
  *calibrated*: when it says 0.8, the label really is there about 80% of the time.
- **Uncertain:** we flag a label only when the two models land on **opposite sides** of 0.5 (one says
  yes, the other no) **and** the final calibrated probability is in a middle band. The band
  (0.35–0.65) was picked on the validation set: the band where flagged decisions are clearly more
  error-prone, with at most 15% of messages flagged. On the free-form test, flagged decisions were wrong
  62.5% of the time and unflagged ones 3.5%, so the flag really means "check this one".

**ML + a rule from the label definition.** The label guide says `asked_directly` needs an *explicit*
mention of suicide, killing oneself, ending one's life, not wanting to be alive or here, or self-harm
(English or Spanish). The models learned a shortcut: most direct asks in our data start with
"thinking about", so "ok but have you tried just not thinking about him" scored 0.98. A false "asked
directly" would unlock the friend's deepest level, so we added the definition as a rule
(`backend/app/ml/rules.py`). It runs on the safety lane's normalizer output, so "k1lling urself" still
counts. If none of the explicit terms is present, `asked_directly` is capped at 0.2. The rule can only
lower that one probability, never raise anything. On our labeled data it never blocks a real direct ask
(0 of 178 missed) and none of the 647 other replies contain a term. Test F1 stayed at 1.00.

**Highlights (occlusion).** We delete a phrase (1–5 neighbouring words that don't cross punctuation)
and re-score the message. If deleting "killing yourself" makes `asked_directly` much less likely, that
phrase gets highlighted. We measure the drop in **log-odds**, not probability, because a confident
model sits at 0.9999. Going from 0.9999 to 0.99 looks tiny as a probability but is a 100× drop in the
odds. The biggest-drop phrase wins, and we trim it to its shortest part that keeps 80% of the drop, so
the highlight is crisp ("how's the new school going", not the whole message). A second phrase is kept
only if it's at least half as important. `delta` is that log-odds drop: 1 ≈ odds cut 2.7×, 2.3 ≈ 10×.
The offsets point at the exact characters, so the UI can underline them.

**Verified rewrites.** For each message the critic checks for a missing key skill. The friend sounds
hopeless (level ≥ 2) and nobody asked directly yet? Asking directly is missing. The message dismissed
or lectured? Listening is missing. The helper promised secrecy? A referral is missing. It then picks a
human-written exemplar: same scenario, nearest friend level, teaches that skill, and most similar to
what the friend just said. It shows the exemplar **only if**:
1. our detector scores the missing skill at least **0.2 higher** on the exemplar than on what the
   helper wrote, and
2. the **Guardian** passes it.

Otherwise it tries the next exemplar (up to 3). If no exemplar passes, it may ask the AI for 2 suggested
replies (prompt in `backend/app/ml/prompts/rewrite.md`). Each one goes through **the same two checks**, and
we keep the one with the biggest verified gain. The report records where the rewrite came from
(`rewrite_source`: "exemplar" or "llm") and which skill it improves (`rewrite_skill`, e.g. "ask_directly").
The frontend uses these to show "Try instead: … (+0.4 ask directly)". With no API key, or with
`FR_LLM=0`, it uses exemplars only and everything else works the same. We never suggest a reply we can't
show is better or safe.

**7-skill summary.** The 10 labels map to the rubric (`contracts.RUBRIC_SKILLS`). Each skill gets the
helper's best message. "Listen" counts only when that message validates *and* doesn't also dismiss or
lecture. "No secrecy" breaks if any message promises secrecy.

**Training** (`make train`): seeded, fits A and B on **train** and the stackers on **val**, and only
*scores* **test**. It saves `models/skill_detector.joblib` (0.53 MB) and a `.meta.json` with the data
hash, row counts, date, metrics and the embedder name. The app refuses to load an artifact trained
with a different embedder, because its numbers would be meaningless.

## Why this approach (and what we considered instead)
- **Why not keywords?** A keyword list misses "have you thought about not being around anymore" and
  fires on "lol" in a kind message. On the free-form test, keywords score macro-F1 0.48 and the
  ensemble scores 0.82.
- **Why two models?** They make *different* mistakes. Meaning-based A handles paraphrases and Spanish.
  Spelling-based B handles slang and typos. On the free-form test, A alone gets 0.70, B alone 0.74,
  and together 0.82. When they disagree, that's an honest "we're not sure" signal.
- **Why not a big neural network or an LLM?** It has to be free, fast (about 60 ms per message on a
  laptop CPU), offline, deterministic and explainable. Also, an LLM would make this an "AI wrapper".
  Logistic regression is the standard tool when you have about 800 examples.
- **Why calibrate?** The engine and X-ray mode treat the numbers as probabilities. Uncalibrated models
  are overconfident. Calibration cut the average gap between "what it says" and "how often it's right"
  from 0.115 to 0.019 on the free-form test.

## How we measured it (real numbers, with n and the split)
Data: the data lane's splits. Train 615, val 142, test 124 (all `label_source: agreed`), grouped by
conversation so no friend context appears in two splits. Embedder: fastembed MiniLM. Threshold 0.5,
seed 0. Model A and B are fitted on train. The stacker, the uncertain band and every other tuned
number are fitted on val. Both test sets are only scored.
Full records are in `eval/reports/ml_skills.json`; details, probes and errors in
`eval/skills/results.json`. Charts: `eval/skills/f1_comparison*.png`, `reliability*.png`,
`confusion*.png` (no suffix = composed test, `_freeform` = free-form test).

**Two test sets, and which one to believe.**
- **Composed test (n=124):** replies written the same way as the training replies. 21% of them are
  fully covered by phrases from training, so these numbers are **optimistic**.
- **Free-form test (n=171): the honest number.** Hand-written replies in people's own words, never
  trained on, 0% phrase overlap with training. It's the best estimate of how the detector does on
  real teen messages.

| macro-F1 | Composed test (n=124) | **Free-form test (n=171)** |
|---|---|---|
| Keyword baseline (the stub) | 0.557 | 0.480 |
| Model A (embeddings + LR) | 0.849 | 0.700 |
| Model B (char/word TF-IDF + LR) | 0.948 | 0.735 |
| **Stacked + calibrated ensemble** | **0.959** | **0.818** |

On the free-form test the ensemble beats each model alone by 8–12 points. That's the point of stacking
two different models.

| Ensemble per label, free-form test | precision | recall | F1 | positives | keyword F1 |
|---|---|---|---|---|---|
| checked_in | 0.94 | 0.57 | 0.71 | 28 | 0.40 |
| validated | 0.77 | 0.63 | 0.69 | 43 | 0.31 |
| asked_directly | 1.00 | 1.00 | 1.00 | 18 | 0.50 |
| encouraged_help | 1.00 | 0.67 | 0.80 | 9 | 0.00 |
| referred_adult | 1.00 | 0.75 | 0.86 | 16 | 0.71 |
| referred_988 | 1.00 | 1.00 | 1.00 | 3 | 1.00 |
| follow_up | 0.87 | 0.74 | 0.80 | 35 | 0.33 |
| dismissed | 0.90 | 0.56 | 0.69 | 16 | 0.69 |
| advice_dump | 0.74 | 0.81 | 0.77 | 21 | 0.25 |
| promised_secrecy | 0.75 | 1.00 | 0.86 | 9 | 0.62 |

The composed-test per-label table is in `eval/skills/results.json`. There every label scores 0.80–1.00.

**Calibration** (lower is better):

| | ECE before → after | Brier before → after |
|---|---|---|
| val (n=142; the stacker was fitted here) | 0.128 → 0.017 | 0.041 → 0.015 |
| composed test (n=124) | 0.125 → 0.016 | 0.032 → 0.009 |
| free-form test (n=171) | 0.115 → 0.019 | 0.055 → 0.035 |

**Uncertain flag** (band 0.35–0.65, chosen on val):

| | messages with a flag | error rate, flagged decisions | error rate, unflagged |
|---|---|---|---|
| val | 8.5% | 75% (9 of 12) | 1.6% |
| composed test | 8.1% | 45% (5 of 11) | 0.7% |
| free-form test | 18.1% | 62.5% (20 of 32) | 3.5% |

- **Explicit-term rule for `asked_directly`:** included in the ensemble numbers above. On the free-form
  test `asked_directly` scores F1 1.00. The rule never blocks a labeled direct ask in any split.
- **Probes** (hand-written sentences from a reviewer, not a test set): 8 of 9 behave as expected.
  "you seemed off at lunch" → follow_up 0.30 (was 0.77). "are you thinking about quitting the group
  chat?" → asked_directly 0.17. "when you said disappear, did you mean you want to die?" → 0.998.
  Still wrong: "ok i gotta go to school early tomorrow, talk later maybe" → follow_up 0.93. A goodbye
  isn't a commitment.
- **Counselor agreement (kappa):** the tool is ready (`python -m backend.app.ml.kappa`). The
  counselor sheet hasn't come back yet.

**What the words mean:**
- **Precision:** when it says "yes", how often it's right.
- **Recall:** of all the real "yes" cases, how many it caught.
- **F1:** one number that is high only if both are high. **Macro-F1** averages F1 over the 10 labels,
  so rare labels count as much as common ones.
- **Calibration / ECE:** if the model says 70% a hundred times, the label should be there about 70
  times. ECE is the average miss. **Brier** is the average squared gap between the probability and
  the truth (0 = perfect).
- **Cohen's kappa:** agreement between two labelers after removing the agreement you'd get by luck.
  1 = perfect, 0 = luck. The 95% confidence interval comes from re-sampling the rows 1,000 times
  (seeded).

## Limitations
- **Real messages are harder.** Composed test 0.96 vs free-form 0.82. The free-form number is the one to
  quote. Real teens may be messier still. A real-survey set would be the next check.
- **Implicit skills are hardest.** Free-form recall is lowest for checked_in (0.57), dismissed (0.56)
  and validated (0.63). People check in or brush off feelings in many indirect ways ("almorzar sola
  cansa" validates without any "that sounds…").
- **Replies that only make sense with context.** "yes. let's go right now" is a referral only because
  the friend just agreed to see the counselor. The model sees the friend's last message, but these
  are still the most common misses.
- **Spanish free-form replies** are under-represented in training, and several of the top errors are
  Spanish.
- **Goodbyes can look like follow-ups** ("talk later maybe" → 0.93). Needs more counter-examples in
  the data.
- Our detector judges AI rewrite suggestions, so a suggestion that games our model's quirks could
  pass. The Guardian check and the exemplars-first order limit this.

## Questions a judge might ask (with answers)
1. **"Isn't this just ChatGPT?"** No. Every score comes from our own models: two logistic-regression
   models we trained on about 800 labeled replies, plus a small local embedding model that runs
   offline. You can open `backend/app/ml/model.py` and see every step. The only AI use in this lane is
   optional rewrite *suggestions*, and our detector decides whether to show them.
2. **"Your F1 is 0.96. Isn't that too good?"** Yes, for the composed test, and we say so: 21% of those
   replies reuse training phrases. That's why we built a second, free-form test set written in people's
   own words with zero overlap. There the ensemble scores 0.82, against 0.48 for keyword matching. 0.82
   is the number we stand behind.
3. **"How do you know which words mattered?"** Occlusion. We delete phrases and measure how much the
   odds fall, so the highlight is an actual measurement of the model, not a guess. The tests check that
   every highlight's offsets point at exactly those characters.
4. **"What if your suggested reply is worse, or the AI writes something bad?"** We don't show it.
   Every rewrite, from the exemplar bank or the AI, must raise the missing skill's probability by at
   least 0.2 according to our own detector, and the Guardian must pass it. If nothing passes both
   checks, we show none.
5. **"Why trust the probabilities?"** They're calibrated on data the base models never saw. The
   reliability diagram shows that predicted and observed rates line up (calibration error 0.019 on the
   free-form test). When our two models disagree and the answer is close, we say "uncertain". Those
   flagged decisions really are wrong far more often (62.5% vs 3.5%), so the flag is earned.
