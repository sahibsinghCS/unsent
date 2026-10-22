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

No AI writes any text here. Better replies come from an exemplar bank that people wrote. The summary
is fill-in-the-blank templates.

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
- **Uncertain:** if Model A and Model B differ by more than 0.5 on a label, we flag it.

**Highlights (occlusion).** We delete one word at a time and re-score the message. If deleting
"suicide" drops `asked_directly` from 0.97 to 0.30, that word gets highlighted (delta 0.67). Neighbouring
important words merge into one highlight, and each label keeps its top 3. Sometimes a message makes its
point twice ("lol ur fine dont be dramatic"), so no single word matters on its own. Then we delete the
most important word, then the next, until the probability drops, and highlight that set. The offsets
point at the exact characters, so the UI can underline them.

**Verified rewrites.** For each message the critic checks for a missing key skill. The friend sounds
hopeless (level ≥ 2) and nobody asked directly yet? Asking directly is missing. The message dismissed
or lectured? Listening is missing. The helper promised secrecy? A referral is missing. It then picks a
human-written exemplar: same scenario, nearest friend level, teaches that skill, and most similar to
what the friend just said. It shows the exemplar **only if**:
1. our detector scores the missing skill at least **0.2 higher** on the exemplar than on what the
   helper wrote, and
2. the **Guardian** passes it.

Otherwise it tries the next exemplar (up to 3) or shows nothing. We never suggest a reply we can't
show is better or safe.

**7-skill summary.** The 10 labels map to the rubric (`contracts.RUBRIC_SKILLS`). Each skill gets the
helper's best message. "Listen" counts only when that message validates *and* doesn't also dismiss or
lecture. "No secrecy" breaks if any message promises secrecy.

**Training** (`make train`): seeded, fits A and B on **train** and the stackers on **val**, and only
*scores* **test**. It saves `models/skill_detector.joblib` (0.45 MB) and a `.meta.json` with the data
hash, row counts, date, metrics and the embedder name. The app refuses to load an artifact trained
with a different embedder, because its numbers would be meaningless.

## Why this approach (and what we considered instead)
- **Why not keywords?** A keyword list misses "have you thought about not being around anymore" and
  fires on "lol" in a kind message. On the same test set, keywords score macro-F1 0.59 and the
  ensemble scores 0.96.
- **Why two models?** They make *different* mistakes. Meaning-based A handles paraphrases and Spanish.
  Spelling-based B handles slang and typos. On test, B alone gets 0.947, A alone 0.843, and together
  0.957. When they disagree, that's an honest "we're not sure" signal.
- **Why not a big neural network or an LLM?** It has to be free, fast (about 60 ms per message on a
  laptop CPU), offline, deterministic and explainable. Also, an LLM would make this an "AI wrapper".
  Logistic regression is the standard tool when you have about 800 examples.
- **Why calibrate?** The engine and X-ray mode treat the numbers as probabilities. Uncalibrated models
  are overconfident. Calibration cut the average gap between "what it says" and "how often it's right"
  from 0.133 to 0.013.

## How we measured it (real numbers, with n and the split)
Data: the data lane's provisional splits (825 replies: train 572 / val 110 / test 143, grouped by
conversation so no friend context appears in two splits). Embedder: fastembed MiniLM. Threshold 0.5.
Full records are in `eval/reports/ml_skills.json`. Charts: `eval/skills/f1_comparison.png`,
`reliability.png`, `confusion.png`.

| System (test, n=143) | macro-F1 |
|---|---|
| Keyword baseline (the stub) | 0.592 |
| Model A (embeddings + LR) | 0.843 |
| Model B (char/word TF-IDF + LR) | 0.947 |
| **Stacked + calibrated ensemble** | **0.957** |

| Ensemble per label (test) | precision | recall | F1 | positives |
|---|---|---|---|---|
| checked_in | 0.93 | 0.93 | 0.93 | 14 |
| validated | 1.00 | 0.98 | 0.99 | 53 |
| asked_directly | 1.00 | 1.00 | 1.00 | 31 |
| encouraged_help | 1.00 | 0.93 | 0.96 | 28 |
| referred_adult | 1.00 | 1.00 | 1.00 | 27 |
| referred_988 | 1.00 | 1.00 | 1.00 | 17 |
| follow_up | 0.91 | 0.88 | 0.90 | 34 |
| dismissed | 1.00 | 0.75 | 0.86 | 16 |
| advice_dump | 1.00 | 1.00 | 1.00 | 16 |
| promised_secrecy | 1.00 | 0.88 | 0.93 | 16 |

- **Calibration** (ECE, lower is better, test): 0.133 before stacking → **0.013** after.
- **Leak check:** 13 test replies also appear word-for-word in train. Without them (n=130) the
  ensemble still scores 0.957, so the result isn't memorization.
- **Counselor agreement (kappa):** the tool is ready (`python -m backend.app.ml.kappa`), but there are
  no counselor labels yet.

**What the words mean:**
- **Precision:** when it says "yes", how often it's right.
- **Recall:** of all the real "yes" cases, how many it caught.
- **F1:** one number that is high only if both are high. **Macro-F1** averages F1 over the 10 labels,
  so rare labels count as much as common ones.
- **Calibration / ECE:** if the model says 70% a hundred times, the label should be there about 70
  times. ECE is the average miss.
- **Cohen's kappa:** agreement between two labelers after removing the agreement you'd get by luck.
  1 = perfect, 0 = luck. The 95% confidence interval comes from re-sampling the rows 1,000 times
  (seeded).

## Limitations
- **These numbers are optimistic.** The provisional labels are the writer's *intended* labels, not yet
  checked by a human, and the replies were written for this dataset. Real teens write messier
  messages. The real-survey test set (when it exists) is the honest number. `run_eval.py` reports it
  separately.
- The model learns quirks of its data. Example: "you seemed really off **at lunch**" also gets
  `follow_up` (0.87), because "lunch" mostly appeared in meet-up plans. More varied data fixes this.
- `dismissed` has the lowest recall (0.75). Subtle brush-offs ("anyway…") are the hardest.
- Rewrites need the exemplar bank (data lane). Without exemplars the report has no rewrites, and
  everything else still works.

## Questions a judge might ask (with answers)
1. **"Isn't this just ChatGPT?"** No. No LLM runs anywhere. The detector is two logistic-regression
   models we trained on about 800 labeled replies, plus a small local embedding model that runs
   offline. You can open `backend/app/ml/model.py` and see every step.
2. **"Your F1 is 0.96. Isn't that too good?"** On this provisional, synthetic test set, yes, and we
   say so. We checked for leaks: conversations are never split across train and test, and removing
   exact duplicates gives the same score. Real teen messages will score lower. That's why we measure
   on a separate real-survey set and against counselor labels.
3. **"How do you know which words mattered?"** Occlusion. We delete words and watch the probability
   fall, so the highlight is an actual measurement of the model, not a guess. The tests check that
   every highlight's offsets point at exactly those characters.
4. **"What if your suggested reply is worse?"** We don't show it. A rewrite must raise the missing
   skill's probability by at least 0.2 according to our own detector, and the Guardian must pass it.
   If no exemplar passes both checks, we show none.
5. **"Why trust the probabilities?"** They're calibrated on data the base models never saw. The
   reliability diagram shows that predicted and observed rates line up (error 0.013 on test). When
   our two models disagree, we say "uncertain" instead of pretending.
