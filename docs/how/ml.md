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
  yes, the other no) **and** the final calibrated probability is in a middle band. The band is
  picked on the validation set: the band where flagged decisions are clearly more error-prone, with at
  most 15% of messages flagged. It's 0.20–0.80 for the current model. On the free-form test, flagged
  decisions were wrong 39% of the time and unflagged ones 2.9%, so the flag really means "check this
  one".

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
only if it's at least half as important. Finally each phrase is rounded out to the edge of its clause
(punctuation or the end of the message) when that adds at most 2 words on a side, so "hey are"
becomes "hey are you ok" and "i'll go with" becomes "i'll go with you". The delta is re-measured for
the final phrase. `delta` is that log-odds drop: 1 ≈ odds cut 2.7×, 2.3 ≈ 10×.
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

**Feedback text is never false.** If the friend shut down and the chat ended badly, the summary opens
honestly and kindly ("This one slipped away, and that's exactly what practice is for.") instead of
pretending it went fine. The whole-chat "you never got to…" notes are capped at the 3 most important,
so a short chat isn't buried in a list. Every note about a specific message is kept. The template
sentences check what actually happened. If the helper
connected the friend with a counselor or 988 but never said why ("you don't have to handle this
alone"), the report says "You connected them with someone who can help. Next time, also tell them why:
they don't have to handle it alone." It does not claim they "never got to" helping. Mistakes are named
exactly: a dismissive reply "brushed off the feeling", an advice reply "jumped to fixing it before
listening".

**Spanish chats get Spanish feedback.** Every sentence the critic writes comes from a template table
in English and Spanish (`backend/app/ml/critic_text.py`). The Spanish is written the way teens text,
not translated word for word. In a Spanish chat, rewrites come only from the Spanish exemplar bank.
If the AI fallback runs, it's asked for Spanish, and any suggestion that isn't Spanish is dropped
before our detector even checks it. A Spanish chat never shows an English rewrite. If nothing passes,
it shows none.

**7-skill summary.** The 10 labels map to the rubric (`contracts.RUBRIC_SKILLS`). Each skill gets the
helper's best message. "Listen" counts only when that message validates *and* doesn't also dismiss or
lecture. "No secrecy" breaks if any message promises secrecy.

**Training** (`make train`): seeded, fits A and B on **train** and the stackers on **val**, and only
*scores* **test**. It saves `models/skill_detector.joblib` (0.65 MB) and a `.meta.json` with the data
hash, row counts, date, metrics and the embedder name. The app refuses to load an artifact trained
with a different embedder, because its numbers would be meaningless.

**Making the report fast.** Highlights mean re-scoring dozens of slightly shortened copies of every
message, which made the end-of-chat report slow (2.4 s on a 6-message chat). Three fixes, none of which
change a single output (a test compares the full report before and after on a fixed conversation):
1. **Embedding cache.** The shortened copies share most of their sentences, and every copy shares the
   friend's message, so each text is embedded once and reused. We use the app's shared per-text cache
   (`embed.cached_scope()`), which forgets anything unused for 60 minutes, just like conversations.
2. **One matrix product** computes all 10 labels' logistic regressions at once, instead of 10 separate
   calls per model.
3. **Explain while the chat happens.** When a message is scored during the chat, its highlights start
   computing on one background worker. At the end the report just reuses them. If it's asked for before
   they're done, it waits for that same computation rather than starting over. These remembered
   explanations also expire after 60 minutes unused: the session cleanup sweeps them, so no text from a
   conversation outlives it. (`FR_PREWARM_EXPLAIN=0` turns this off.)

| `/finish` on a 6-message chat (fastembed, 1 user) | p50 |
|---|---|
| before | 2.42 s |
| all three, user pauses 2 s before finishing | **0.24 s** |
| all three, "finish" sent the instant the last message returns | 1.66 s |

The background work makes sending a message a bit slower (p50 about 150 ms on this machine).

 (and what we considered instead)
- **Why not keywords?** A keyword list misses "have you thought about not being around anymore" and
  fires on "lol" in a kind message. On the free-form test, keywords score macro-F1 0.49 and the
  ensemble scores 0.82.
- **Why two models?** They make *different* mistakes. Meaning-based A handles paraphrases and Spanish.
  Spelling-based B handles slang and typos. On the free-form test, A alone gets 0.70, B alone 0.75,
  and together 0.82. When they disagree, that's an honest "we're not sure" signal.
- **Why not a big neural network or an LLM?** It has to be free, fast (about 60 ms per message on a
  laptop CPU), offline, deterministic and explainable. Also, an LLM would make this an "AI wrapper".
  Logistic regression is the standard tool when you have about 800 examples.
- **Why calibrate?** The engine and X-ray mode treat the numbers as probabilities. Uncalibrated models
  are overconfident. Calibration cut the average gap between "what it says" and "how often it's right"
  from 0.124 to 0.012 on the free-form test.

## How we measured it (real numbers, with n and the split)
Data: the data lane's splits. Train 824, val 152, composed test 133, free-form test 221, all
human-agreed labels, grouped by conversation so no friend context appears in two splits. Embedder:
fastembed MiniLM. Threshold 0.5, seed 0. Model A and B are fitted on train. The stacker, the uncertain
band and the pooling decision are fitted on val. Both test sets are only scored.
Full records are in `eval/reports/ml_skills.json` (and `ml_pooling.json`); details, probes and errors
are in `eval/skills/results.json`. Charts: `eval/skills/f1_comparison*.png`, `reliability*.png`,
`confusion*.png` (no suffix = composed test, `_freeform` = free-form test).

**Two test sets, and which one to believe.**
- **Composed test (n=133):** replies written the same way as the training replies. Many reuse
  training phrases, so these numbers are **optimistic**.
- **Free-form test (n=221): the honest number.** Hand-written replies in people's own words, never
  trained on, 0% phrase overlap with training. It's the best estimate of how the detector does on
  real teen messages.

| macro-F1 | val (n=152) | Composed test (n=133) | **Free-form test (n=221)** |
|---|---|---|---|
| Keyword baseline (the stub) | 0.551 | 0.561 | 0.490 |
| Model A (embeddings + LR) | 0.775 | 0.830 | 0.695 |
| Model B (char/word TF-IDF + LR) | 0.896 | 0.966 | 0.752 |
| **Stacked + calibrated ensemble** | **0.951** | **0.969** | **0.822** |

| Ensemble per label, free-form test | precision | recall | F1 | positives | keyword F1 |
|---|---|---|---|---|---|
| checked_in | 0.80 | 0.57 | 0.67 | 28 | 0.40 |
| validated | 0.83 | 0.63 | 0.72 | 46 | 0.32 |
| asked_directly | 1.00 | 1.00 | 1.00 | 18 | 0.50 |
| encouraged_help | 0.90 | 0.56 | 0.69 | 16 | 0.12 |
| referred_adult | 1.00 | 0.94 | 0.97 | 35 | 0.79 |
| referred_988 | 1.00 | 0.92 | 0.96 | 26 | 1.00 |
| follow_up | 0.89 | 0.72 | 0.80 | 46 | 0.29 |
| dismissed | 0.80 | 0.76 | 0.78 | 21 | 0.63 |
| advice_dump | 0.68 | 0.81 | 0.74 | 21 | 0.25 |
| promised_secrecy | 0.82 | 1.00 | 0.90 | 9 | 0.62 |

**Calibration** (lower is better; the stacker was fitted on val):

| | ECE before → after | Brier before → after |
|---|---|---|
| val (n=152) | 0.130 → 0.010 | 0.043 → 0.012 |
| composed test (n=133) | 0.128 → 0.012 | 0.032 → 0.007 |
| free-form test (n=221) | 0.124 → 0.012 | 0.053 → 0.029 |

**Uncertain flag** (band 0.20–0.80, chosen on val):

| | messages with a flag | error rate, flagged decisions | error rate, unflagged |
|---|---|---|---|
| val | 13.8% | 17% (n=23) | 1.2% (n=1,497) |
| composed test | 11.3% | 7% (n=15) | 0.6% (n=1,315) |
| free-form test | 29.9% | 39% (n=74) | 2.9% (n=2,136) |

- **Explicit-term rule for `asked_directly`:** included in the ensemble numbers above. Free-form F1
  1.00. The rule never blocks a labeled direct ask in any split.
- **Probes** (hand-written sentences from reviewers, not a test set): 13 of 14 behave as expected.
  "you seemed off at lunch" → follow_up 0.06. "talk later maybe" → 0.11. "lots of people feel like
  that, you'll be fine" → dismissed 0.98, validated 0.30, advice 0.14. Still wrong: "can we talk to the
  counselor tomorrow? i'll go with you" → follow_up 0.67. By the label guide a referral with "i'll go
  with you" isn't a follow-up.
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

**Clause pooling: an experiment with a rule we fixed in advance.** Messages that do two things
("i'm really glad you told me. can we talk to the counselor tomorrow?") can water down the first
skill. Pooling scores each sentence separately and takes the strongest sentence for the positive skills
only. Negative labels stay on the whole message, so "i won't tell anyone… except the counselor" can't
turn into a promise of secrecy. The stacker is refitted after pooling. We wrote the rule before running
it: adopt only if validation macro-F1 (5-fold out-of-fold on val) improves and calibration (ECE) gets
no more than 0.01 worse. Training now applies that rule automatically (`make train`; `--pooling
on|off` overrides it). Results (`eval/reports/ml_pooling.json`):

| Data version | val macro-F1, whole → pooled | val ECE, whole → pooled | Decision | free-form macro-F1, whole → pooled (info only) |
|---|---|---|---|---|
| first splits (train 615) | 0.921 → 0.916 | 0.013 → 0.011 | not adopted | 0.818 → 0.802 |
| current splits (train 824) | 0.923 → 0.931 | 0.011 → 0.010 | **adopted** | 0.841 → 0.822 |

In plain words:
- **We pre-registered the rule.** We wrote down "adopt pooling only if validation improves without
  hurting calibration" *before* running the experiment.
- **The rule chose pooling, on validation data only.** With more training data, pooling started helping
  on validation (0.923 → 0.931) and fixed one more reviewer probe (13 of 14 vs 12 of 14).
- **The whole-message model would have scored 0.841 on the free-form test; the pooled one scores 0.822.
  We kept the rule anyway.** Switching after seeing the test score would quietly turn the test set into
  a second validation set. Then 0.822 (or 0.841) would no longer be an honest estimate of how the model
  does on new messages. With n=221 the 0.02 gap is within noise anyway.

The cost we accept: pooled scores flag more messages as "uncertain" on free-form text (30% vs 17%).

## Limitations
- **Real messages are harder.** Composed test 0.97 vs free-form 0.82. The free-form number is the one to
  quote. Real teens may be messier still. A real-survey set would be the next check.
- **Implicit skills are hardest.** Free-form recall is lowest for encouraged_help (0.56), checked_in
  (0.57) and validated (0.63). People check in or brush off feelings in many indirect ways ("almorzar sola
  cansa" validates without any "that sounds…").
- **Replies that only make sense with context.** "yes. let's go right now" is a referral only because
  the friend just agreed to see the counselor. The model sees the friend's last message, but these
  are still the most common misses.
- **Indirect encouragement** ("i'd find a therapist if i were you", "you don't have to be alone in it")
  and **permission-giving validation** ("it's okay to not be fine") are the most common free-form misses.
- **A referral with a time word** ("…the counselor tomorrow? i'll go with you") still scores follow_up
  0.67, though the label guide says it isn't one.
- Our detector judges AI rewrite suggestions, so a suggestion that games our model's quirks could
  pass. The Guardian check and the exemplars-first order limit this.

## Questions a judge might ask (with answers)
1. **"Isn't this just ChatGPT?"** No. Every score comes from our own models: two logistic-regression
   models we trained on about 800 labeled replies, plus a small local embedding model that runs
   offline. You can open `backend/app/ml/model.py` and see every step. The only AI use in this lane is
   optional rewrite *suggestions*, and our detector decides whether to show them.
2. **"Your F1 is 0.96. Isn't that too good?"** Yes, for the composed test, and we say so: 21% of those
   replies reuse training phrases. That's why we built a second, free-form test set written in people's
   own words with zero overlap. There the ensemble scores 0.82, against 0.49 for keyword matching. 0.82
   is the number we stand behind.
3. **"How do you know which words mattered?"** Occlusion. We delete phrases and measure how much the
   odds fall, so the highlight is an actual measurement of the model, not a guess. The tests check that
   every highlight's offsets point at exactly those characters.
4. **"What if your suggested reply is worse, or the AI writes something bad?"** We don't show it.
   Every rewrite, from the exemplar bank or the AI, must raise the missing skill's probability by at
   least 0.2 according to our own detector, and the Guardian must pass it. If nothing passes both
   checks, we show none.
5. **"Why trust the probabilities?"** They're calibrated on data the base models never saw. The
   reliability diagram shows that predicted and observed rates line up (calibration error 0.012 on the
   free-form test). When our two models disagree and the answer is close, we say "uncertain". Those
   flagged decisions really are wrong far more often (39% vs 2.9%), so the flag is earned.
