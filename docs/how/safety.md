# The Guardian (safety layer)

*Owner: safety lane. Plain language, so Sahib can explain every part to a judge.*

## What it does

Every message the user types goes through the Guardian **before anything else runs**. It returns one of four answers:

| Answer | When | What the app does |
|---|---|---|
| **none / continue** | normal practice, including asking the friend about suicide | keep going |
| **concern / show resources** | the user (the helper) sounds like they are struggling, but it's unclear ("i can't do this anymore either") | show 988 and "talk to a trusted adult" gently, keep practicing |
| **crisis / pause** | the helper themself sounds at risk ("honestly i want to die too", "kms") | pause the role-play and show crisis resources |
| **block** | the message would hurt the friend ("kys", "just do it"), asks *how/when/with what* (method-seeking), or tries to break the app (prompt injection) | don't send it; show a short teaching note |

It also checks every **friend** line (`check_friend`), including the replies OpenAI writes in v3. Those are natural sentences, so the lexicon also covers natural phrasings of plans ("i already know how i'd do it"), inevitability ("my mind is made up"), suicide as a relief or solution, graphic detail, and AI refusals or persona breaks ("I'm sorry, but I can't help with that", "As an AI…"). A line that mentions a plan, a means, encouragement, graphic detail or "I'm an AI" is never shown. All 2,206 friend lines we have (scenario files plus the data lane's line bank) pass.

## How it works

Four steps, all on the computer running the app (no internet, no AI service):

1. **Normalizer** (`backend/app/safety/normalizer.py`): turns how teens text into plain words, and writes down every change it made.
   - leetspeak: `k1ll mys3lf` → `kill myself`; a lone `1` in a leetspeak message is `i`
   - spaced or dotted letters: `k m s`, `k.m.s` → `kms`
   - stretched letters: `diiiie` → matches `die`
   - swapped letters: `wnat` → `want`, but only if the fix produces a word in our lexicon
   - slang and misspellings: `u` → you, `wanna` → want to, `suiside` → suicide, `dont` → do not
   - emoji become words: 🪦 → `emoji_grave`, 😭 → `emoji_crying`. 💀 becomes `emoji_skull` but is marked **ambiguous** and never decides anything alone, because teens use it to mean "I'm dying laughing".
   - Spanish accents are removed for matching: `mátate` = `matate`
   - invisible zero-width characters are deleted, and curly quotes become straight ones
2. **Lexicon** (`lexicon.yaml`): a list of phrases a counselor can read and edit, grouped by category. The comments in the file explain each group. **`lexicon.py`** adds the speaker rules:
   - **Who is talking?** The nearest pronoun before a phrase decides. `i want to die` → the helper (crisis). `do you want to die?` → asking the friend (allowed).
   - **Repeating the friend's words back** (`you said you don't want to be here?`) is good listening, so it's allowed.
   - **Negation:** `i would never kill myself` doesn't count. A comma stops a negation, so `i don't care, kill yourself` still counts.
   - **Commands vs questions:** `kill yourself` counts as harm only as a command (`just…`, `you should…`, or at the start of a sentence). `do you want to kill yourself?` is a question, not a command.
   - **"me too":** a short "me too" right after the friend shares suicidal thoughts is the helper's own distress (concern). After "i failed my test" it's just small talk.
3. **Classifier** (`model.py`, trained by `train_guardian.py`): catches phrasings that aren't in the lexicon.
   - Input: the normalized message.
   - Features: a sentence embedding (the multilingual MiniLM model, run locally) joined with character n-grams (2–5 letters, TF-IDF).
   - Model: one logistic regression over 6 classes: none, concern, self_risk, harm_to_other, method_seeking and prompt_injection.
   - The thresholds are picked on the validation split so that it catches ≥95% of helper-at-risk messages and flags ≤2% of asking-the-friend questions.
4. **Combine** (`decide()` in `model.py`):
   - The priority order is **crisis > block > concern > none**.
   - Lexicon hits are trusted, because the lexicon is speaker-aware and reviewed by people.
   - The classifier can add flags. But if the lexicon recognized an **allowed** phrase (asking the friend, everyday hyperbole, a negation) and found nothing risky, the classifier needs 99% confidence to overrule it. That protects the skill we teach.

**Optional fifth step: OpenAI moderation** (`moderation.py`). In v3 the friend's wording comes from OpenAI, and the Guardian can also ask OpenAI's **free** moderation endpoint for a second opinion. It is only supporting evidence:
- If our Guardian flags a message and moderation agrees, the result lists `moderation` as a source, next to its score.
- If our Guardian finds nothing at all and moderation is very sure about self-harm (≥ 0.8), the result goes up to **concern** (show resources, keep practicing). Moderation alone can never pause the practice or block a message.
- **Our speaker rules always win.** Moderation reads "are you thinking about killing yourself?" as self-harm content, because it doesn't know who is talking. For us that question is the skill we teach. When our lexicon recognizes it as asking the friend, moderation's score only appears in the evidence as "overruled by speaker rules". This is a good thing to show a judge: a big company's general filter would punish the most important thing a helper can say, and ours doesn't.
- Offline (no key, `FR_LLM=0`, budget spent, API error) moderation is simply skipped, and the Guardian decides exactly as before. A test checks this. `FR_GUARDIAN_MODERATION=0` turns it off.
- All the numbers below are for the **local** Guardian. `eval/guardian/moderation_compare.py` compares local vs moderation vs combined on the slang, Spanish and asking-the-friend subsets. It needs `OPENAI_API_KEY`, and it **has not been run yet** (no key in the build environment). `eval/reports/safety_moderation.json` says "not run (no key)".

If the trained model file is missing, or was built with a different embedder, the Guardian runs on the lexicon alone. If anything inside it crashes, it **fails safe**: the helper gets resources and the friend line is blocked. It never crashes the app.

## Why this approach (and what we considered instead)

- **Why recall beats precision for crisis.** Missing a helper who is really at risk is far worse than showing 988 to someone who was fine. So the crisis threshold is tuned for recall first (≥95%), and we only then try to reduce false alarms.
- **Why speaker awareness matters.** The main lesson of FirstReply is to *ask directly*: "are you thinking about killing yourself?" A keyword filter would flag that question every time. Teens would learn that the best question is "wrong", which is the opposite of what suicide-prevention trainers teach. So our headline number is the **asking-friend false-positive rate**, and it's 0 on every set we've measured.
- **What are tricky negatives?** Everyday teen hyperbole that *looks* risky: "this test is killing me", "i'm dead 💀", "i'd die for those shoes", "killed it". They're in the training data as "none", and the lexicon lists them so the classifier can't flag them on a hunch.
- **Why local, not a chatbot or moderation API?** A local model:
  - is free
  - works offline
  - responds in about 5 ms
  - never sends a teen's private message to a company
  - is deterministic (the same input gives the same answer)
  - can be inspected line by line

  An LLM safety filter would cost money, can change without warning, and can't be fully explained to a judge.
- **Why lexicon *and* classifier?** On the test split:

  | Approach | Self-risk recall | Macro F1 |
  |---|---|---|
  | Lexicon alone | 84% | 0.83 |
  | Classifier alone | 100% | 0.90 |
  | Combined | 100% | 0.97 |

  The lexicon gives exact, explainable evidence ("matched: *kill myself*, first person"). The classifier generalizes to new phrasings.

## How we measured it (real numbers, with n and the split)

Run `uv run python eval/guardian/run_eval.py`. Results go to `eval/reports/safety_guardian.json`, and the PR curve goes to `eval/reports/safety_pr_curve.png`.

**Data:** 698 examples written by the data lane plus 467 hard cases we wrote ourselves (1,140 after removing duplicates). The data lane's own train/val/test split is kept, so their test rows were never trained on.

| Metric | Value | n | Set |
|---|---|---|---|
| **Asking-friend false-positive rate** (headline) | **0.0%** | 37 | test |
| **Self-risk recall** (helper at risk → crisis) | **100%** | 37 | test |
| Benign false-positive rate (asking + tricky + neutral) | 0.0% | 81 | test |
| Macro F1 over the 6 classes | 0.97 | 172 | test |
| Recall, per class: concern / harm / method / injection | 0.94 / 0.81 / 1.0 / 1.0 | 17 / 16 / 11 / 10 | test |
| Self-risk average precision (classifier only) | 0.996 | 172 | test |
| Latency p50 / p95 (CPU, includes the embedding) | 4.6 / 6.5 ms | 516 | test ×3 |
| Friend lines flagged | 0 | 2,206 | scenarios + line bank |
| Speaker pairs: risky caught / asking flagged | 100% / 0% | 53 pairs | unit-test set |
| Frozen holdout: asking FPR / self-risk recall | 0% / 100% | 17 / 14 | holdout |

**The most honest number:**
- Before we trained on the data lane's examples at all, we ran the frozen Guardian on all 698 of them (`eval/reports/safety_external_data_lane.json`). They were written by a different author, so the Guardian had never seen this kind of phrasing.
- **Asking-friend false positives were 0 of 140.** The headline held on unseen data.
- **Self-risk recall was only 82% (n=170).** The misses were indirect phrasings ("some days i wish i would just not wake up", "me dan ganas de morir").
- We added those *kinds* of phrases to the lexicon and trained on the data lane's train split. Recall on their test split is now 100% (n=26).

**Robustness:** we changed each risky or asking message (test, n=128) and counted how often the decision stayed the same.

| Change | With normalizer | Without normalizer |
|---|---|---|
| leetspeak | 99% | 38% |
| spaced letters | 98% | 81% |
| stretched letters | 96% | 92% |
| typos (swapped letters) | 98% | 88% |
| emoji added | 93% | 96% |

Emoji is the one place the normalizer makes things slightly worse. It turns 😭 into a word the classifier reacts to, and that flipped a few borderline concern and harm messages. We report it rather than hide it.

## Limitations

- **Small, synthetic data.** All examples were written for this project (by agents and by us), not collected from real teens. The test and holdout sets come from the same few authors as the training data, so real-world numbers will be lower. The pre-training check on the data lane's set (82% recall) is the best estimate of how it handles new phrasing.
- **Test-set hygiene.** We changed some lexicon rules after looking at mistakes on our own test split (e.g. "wanting to die?"). We also changed rules after seeing misses on the data lane's full set, including their test rows. That's why we also report the pre-training external check and a holdout written *after* freezing that we never tuned on.
- **Context is mostly one message.** The only rule that uses earlier messages is the "me too" rule.
- **Sarcasm and mixed messages are hard.** For example: "kys lol jk are you ok". Insults aimed at the friend are the weakest class (recall 81%): new insults the lexicon doesn't list depend on the classifier alone.
- **"just do it" is always blocked.** That includes harmless advice like "just do it, tell your mom". We accept that cost.
- **"Do you have a plan?" is allowed.** It isn't treated as method-seeking, but asking *how, when or with what* is blocked.
- **Only English and Spanish.**
- Words for means appear in `lexicon.yaml` only so they can be blocked.

## Questions a judge might ask (with answers)

1. **"Is this safe? What if a real kid in crisis uses it?"** If the user says anything that sounds like they are at risk, even in slang ("kms", "sewerslide", "k.m.s"), the practice stops and shows 988 and "talk to a trusted adult". We tuned for recall: 100% on the test split, and we report the 82% we got on unseen data before training. If the Guardian itself breaks, it fails safe and shows resources.
2. **"Won't it flag teens for asking 'are you suicidal?'"** No. That's the skill we teach, so it's our headline metric: 0 false flags out of 37 test questions, 0 of 140 on the data lane's set before we trained on it, and 0 of 53 in our paired tests. The speaker rules look at who the sentence is about: "i want to die" is the helper, "do you want to die?" is asking the friend.
3. **"Why not just use ChatGPT or OpenAI's moderation API?"** We do use OpenAI's free moderation as an *optional second opinion*, but it can't decide on its own. It flags "are you thinking about killing yourself?" as self-harm because it can't tell who is speaking, and our speaker rules overrule it. We don't send teens' private messages to a company. Our Guardian is also free, works offline, takes ~5 ms, gives the same answer every time, and every decision shows its evidence (the matched phrase or the classifier's confidence). Judges can read the whole lexicon.
4. **"How do you know your numbers aren't fake?"** `eval/guardian/run_eval.py` regenerates every number from the data in the repo. The data lane's test split was never trained on, and we report the uncomfortable numbers too (82% before training, the emoji robustness dip).
5. **"What about kids who try to sneak past it ('k1ll mys3lf', 'k i l l')?"** The normalizer undoes leetspeak, spacing, stretching and swapped letters before checking. Without it, only 38% of leetspeak decisions stayed correct; with it, 99% do.
