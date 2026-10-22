# FirstReply: the complete idea (final design, v3)

*Updated Thu Oct 22, 2026, late night. This is the single source of truth for what we're building. Build details for agents are in `docs/LANES.md`.*

---

## 1. One sentence
**FirstReply lets teens practice the text that could save a friend's life: they chat with a realistic AI friend who's struggling while models we built score every reply, keep it safe, and show exactly where they lost the friend and what would have worked.**

Short version: *a safety-first simulator that trains teens to respond when a friend texts that they're not okay.*

## 2. The problem
- **CDC YRBS 2023:** 39.7% of US high schoolers had persistent sadness or hopelessness. **20.4% seriously considered suicide.** 9.5% attempted.
- Teens with suicidal thoughts tend to **tell a friend before a counselor**, and often hide it from parents.
- Adults get gatekeeper training like **QPR (Question, Persuade, Refer)**, but its effect **fades within about 6 months**. Teens, who actually get the texts, almost never get trained, and nobody gets to *practice*.

## 3. Who it's for
**High-school students who are the first to hear that a friend isn't okay.** Secondary audience: school counselors and teachers who want a free, safe practice tool.

## 4. Why it can win the Congressional App Challenge
- **Mental health reaches the podium every year**, but every past winner helps the *person who is struggling* (mood trackers, chatbots). **No CAC winner trains the friend.**
- **It isn't an AI wrapper.** The AI only writes the friend's words. Our own deterministic engine, verifier, safety model and trained scoring models make every decision, and we measured each one.
- **Safety is engineered and measured,** not promised: a speaker-aware Guardian, a fact-leak verifier, automated red-team tests and a counselor review.
- **True personal angle:** Sahib is a high schooler, so he *is* the audience (backed by a classmate survey).
- **Solo works:** 56% of 2021–2025 CAC winners worked alone, and IL-11's last 3 winners were solo.

---

## 5. What the user experiences (every feature)

### Practice
1. **Landing page:** the one-liner, a phone mockup, the CDC stat, "Start practicing."
2. **Pick a friend.** 5 scenarios, each a different person and situation:
   | Friend | Situation | Style |
   |---|---|---|
   | Maya, 16 | after a breakup | guarded |
   | Jordan, 17 | failing chemistry, parent pressure | open |
   | Priya, 15 | moved schools, lonely | guarded |
   | Eli, 14 | mocked in a group chat | guarded |
   | Sam, 16 | says "all good" but is giving their stuff away (a real warning sign) | open |
3. **Content warning** before every scenario ("you can stop anytime; if you're struggling yourself, call or text 988").
4. **The chat.** A phone-style text conversation:
   - the friend texts like a real teen, in 1–3 short bubbles
   - realistic "typing…" delays
   - **"Seen" with no reply** when you say something hurtful
5. **The friend reacts realistically:**
   - **opens up in layers** (surface → stress → hopelessness → thoughts of suicide → open to help), but only when you've earned trust
   - **only discloses suicidal thoughts if you ask directly,** just like real gatekeeper training teaches
   - shuts down if you brush them off ("lol you'll be fine")
   - pushes back if you jump to "tell an adult" before building trust
   - gets upset if you promised secrecy and then tell an adult, but you can still recover
6. **Live trust graph** next to the chat: the line rises and falls with every message. A **disclosure ladder** shows how far the friend has opened up, and **skill chips** light up as you use each skill.
7. **"I need help now"** is on every screen and opens Real mode.

### X-ray mode (see the engine work)
8. Toggle it in the chat. Under every message you send, you see:
   - the **Guardian's** safety decision and how many milliseconds it took
   - the **skills detected,** with probabilities
   - the **trust math** ("+12 validated · −2 decay = +10")

   Under every friend message: **who wrote the words** (AI, verified, or a reviewed bank line) and **which checks it passed.** *This is the signature "under the hood" shot for the video.*

### Safety moments
9. **If *you* seem to be at risk** ("honestly i want to die too"), the practice pauses and shows resources (988, a trusted adult). You can't skip past it without acknowledging.
10. **Harmful messages are blocked** ("kys", "just do it", asking for methods, "ignore your instructions") and replaced by a short teaching note.
11. **Asking directly is never blocked:** "are you thinking about killing yourself?" is the most important skill.

### Feedback
12. **End of conversation:** success ("she agreed to talk to the counselor with you") or fail ("they shut down"). Both lead to the feedback report.
13. **Feedback report:**
    - **7-skill radar chart:** Check in · Listen without judging · Ask directly · Don't promise secrecy · Persuade · Refer · Follow up
    - **per-message cards** with **highlighted words** (green = what helped, red = what hurt), taken from our model's explanations
    - **"uncertain" tags** where our two models disagreed (honest uncertainty)
    - **verified rewrites,** e.g. "Try instead: *'that sounds really heavy… are you thinking about killing yourself?'* (+0.4 ask directly)." A rewrite is shown **only if our model confirms it scores higher**
    - **"This is where you lost them":** the exact message where trust dropped the most
    - **missed opportunities** ("Maya hinted at hopelessness at turn 4, and you didn't ask directly")
    - a short summary
14. **Rewind and branch:** tap any of your messages → "Rewind to here" → try a different reply. A **tree view** shows all your branches.
15. **"What if?" simulation:** from the turning point, FirstReply tries several better replies, **simulates each conversation forward** through the real engine, and shows the alternate futures side by side with their trust curves. *"If you'd said this, she would have opened up two messages later."*

### Real life
16. **Real mode ("It's real right now"):** fixed, counselor-reviewable steps with **no AI**:
    - stay with them
    - ask directly
    - don't keep it secret
    - tell a trusted adult today
    - **call or text 988**
    - **911** if they're in immediate danger

    It has big call/text buttons and crisis lines by country (US, Canada, UK, Australia, plus an international directory), in English and Spanish, and **works even offline.**
17. **After-session check-in:** "How are you feeling after that?" A 😔 answer shows resources.

### Trust and transparency
18. **"How it works" page:**
    - an architecture diagram
    - **live evaluation numbers** (model accuracy, safety recall, false-positive rate, safety tests passing)
    - "what the AI does and doesn't do"
    - a **"Try the Guardian" box** (watch "are you thinking about suicide?" pass while "kms" is caught)
19. **Privacy page:** no accounts, no analytics. Conversations live only in server memory and are deleted after 60 minutes. Nothing is used for training.
20. **English and Spanish,** accessible (keyboard, screen-reader labels, contrast, reduced motion), mobile-first, installable.

---

## 6. How it works (architecture)
```
Your message
 │
 ├─▶ 1. GUARDIAN (safety, runs first, local, <50 ms)
 │      slang normalizer → speaker-aware lexicon → trained safety classifier (+ OpenAI's free moderation
 │      as an extra signal when online) → crisis: pause + resources │ block: teaching note │ ok: continue
 │
 ├─▶ 2. SKILL DETECTOR (our trained ML, local)
 │      probability for each of 10 behaviours: checked in · validated · asked directly · encouraged help ·
 │      referred to an adult · referred to 988 · followed up · dismissed · advice-dumped · promised secrecy
 │
 ├─▶ 3. STATE ENGINE (deterministic rules = the friend's "mind")
 │      trust 0–100 (weighted skills − decay, diminishing returns), disclosure level 0–4 with gates
 │      (level 3 only after a direct ask; level 4 only after a referral) and hysteresis, silence ("Seen"),
 │      the secrecy flag, success/fail endings
 │
 ├─▶ 4. FRIEND VOICE (OpenAI writes the words; it decides nothing)
 │      the prompt contains only: the persona and texting style, the facts unlocked at the current level,
 │      the reaction the engine chose, and examples from the reviewed line bank
 │
 ├─▶ 5. VERIFIER (our code checks every AI reply)
 │      leaked a locked fact? (embedding similarity) · failed the Guardian? · broke character or gave advice? ·
 │      too long? → regenerate once → else the best REVIEWED LINE-BANK line → else a safe fallback line
 │
 └─▶ phone UI + live trust graph + X-ray mode

End of chat ─▶ CRITIC: calibrated scores, word highlights, uncertainty, verified rewrites, 7-skill summary,
               turning point, missed opportunities
"What if"   ─▶ ROLLOUTS: better candidate replies simulated forward through the real engine + voice
```
**Why this matters:** the AI makes the friend sound real, but **our code controls what the friend may say and when, checks every reply, and does all the scoring.** If the API key is missing, the budget is reached or OpenAI is down, the friend switches to the **reviewed line bank** and everything still works safely.

---

## 7. The machine learning (what we trained and how)

### 7a. Skill detector: what the user did
- **Input:** your message plus the friend's last message.
- **Output:** a probability for each of the **10 labels**, defined in `docs/LABEL_GUIDE.md`.
- **Two different models, combined:**
  - **Model A, meaning:** a multilingual sentence-embedding model running locally (`paraphrase-multilingual-MiniLM-L12-v2`, so English and Spanish work), then one logistic regression per label.
  - **Model B, wording:** character and word n-gram TF-IDF, then logistic regression. It's robust to slang, typos and "u ok??".
  - **Stacking + calibration:** a small model learns how to combine A and B on a validation set. Platt scaling makes the probabilities honest, so "80%" really means right about 80% of the time.
  - **Uncertainty:** when A and B strongly disagree, the feedback says "uncertain" instead of pretending.
- **Explanations:** *leave-one-word-out occlusion.* Remove each word, see how much the score drops, and highlight the words that mattered. The highlights come from our model's math, not from an AI's opinion.
- **Measured against baselines** on held-out test data: a keyword baseline, Model A alone, Model B alone, and the ensemble. We report per-label precision, recall, F1, macro-F1, a reliability (calibration) diagram and confusion matrices.

### 7b. Guardian: is this message safe?
- **Speaker-aware.** The user plays the helper, so "are you thinking about killing yourself?" is *good* (allowed). "i want to kill myself too" means the **user** may be at risk (crisis). "kys" is harmful toward the friend (blocked).
- **Layers:**
  1. a **normalizer** for teen text (leetspeak "k1ll", spacing "k m s", stretched letters, emoji, Spanish accents, misspellings)
  2. a **human-reviewable lexicon,** including algospeak like "unalive"/"sewerslide" and a whitelist of **tricky negatives** ("this test is killing me", "i'm dead 💀")
  3. a **trained classifier** (embeddings + TF-IDF, logistic regression)
  4. **OpenAI's free moderation endpoint** as an extra signal when online
- **Tuned for recall:** it should almost never miss a real risk. **The headline number is the false-positive rate on good helper questions,** because a Guardian that blocks "are you thinking about suicide?" would punish the exact skill we teach.
- **Measured:** recall and precision per category, robustness to slang and disguised wording (with vs without the normalizer), latency, and a comparison with OpenAI moderation on teen slang.

### 7c. State engine: the friend's mind (rules, not ML)
- Fully deterministic and unit-tested: the same messages always give the same trust path.
- The weights, thresholds, gates, hysteresis, silence and secrecy rules all live in one config file, so they're easy to explain and tune.

### 7d. Verifier: guarding the AI
- **Fact-leak detection:** each AI reply is compared (embedding similarity) with the facts the friend is **not yet allowed** to reveal. Too similar means it's rejected.
- It also checks every bubble with the Guardian and catches persona breaks or advice-giving.
- We report **how often the verifier caught a bad AI reply.**

---

## 8. The data (no API money spent)
All written by AI coding agents into files, and checked by people:
| Dataset | Size | Used for |
|---|---|---|
| Practice replies, labeled with the 10 labels | ~800 (incl. ~15% Spanish/Spanglish) | Training and testing the skill detector |
| Guardian examples | ~700 (incl. ~140 "asking the friend directly" hard negatives and ~120 tricky negatives) | Training and testing the Guardian |
| Reviewed friend line bank | ~1,000 lines (5 friends × 5 levels × every reaction) | The AI's style examples **and** the safe fallback voice |
| Exemplar replies | ~200 | Rewrite suggestions and "what if" candidates |
| Attack messages | ~250 | Red-team testing |

**Labeling quality:**
- The writer's intended labels plus a **second, independent "blind" labeling pass.** Disagreements and a random audit sample go to **Sahib, who hand-labels them** with a fast keyboard labeling tool.
- Agreement is reported.

**Extra test sets:**
- **real anonymous classmate replies** (survey, with consent), test-only
- an optional **cross-model set** written in ChatGPT, to show the model generalizes beyond one AI's writing style

**Expert check:** a school counselor labels 30 replies. We report agreement with them (Cohen's kappa, with a 95% confidence interval).

---

## 9. Numbers we will publish (real values, whatever they are)
| Metric | Where it shows up |
|---|---|
| Skill-detector macro-F1 vs the keyword baseline (held-out test; real-survey subset) | README, How-it-works page, video |
| Agreement with a school counselor (kappa, 95% CI) | README, video, short answer |
| Guardian: self-risk recall · **false-positive rate on good questions** · slang robustness · latency · vs OpenAI moderation | README, video |
| Verifier: % of AI replies caught and replaced | README |
| Red-team: attacks blocked; method-content leaks (target **0**) · safety tests passing (CI badge) | README, GitHub |
| Response time under load | README |

---

## 10. Cost and safety of the API
- OpenAI is used **only** for the friend's wording, plus optional rewrite suggestions, free moderation and a small red-team run.
- A small model, **every response cached,** a **daily budget** (automatic fallback to the line bank) and per-IP rate limits on the public demo.
- **Set a monthly spending limit in the OpenAI dashboard.**
- Expect fractions of a cent per message. **No API money is spent generating data.**

---

## 11. What judges will see
- **Video (≤3 min):**
  1. phone hook ("honestly idk why i even bother anymore"), then the CDC stat
  2. a bad reply → the trust graph drops → "Seen"
  3. rewind → ask directly → the friend opens up → **highlighted words**
  4. **"here's where you lost them" plus the what-if simulation**
  5. **X-ray mode** with the numbers
  6. Real mode
  7. the required items (name, purpose, audience, tools, what I learned)
- **Short answers:** "The LLM is only the voice": our engine, verifier, Guardian and trained models make every decision, and here are the measured numbers.
- **GitHub:** clean modules, tests, CI badge, evaluation tables, `HOW_IT_WORKS.md`, an honest AI-use disclosure.

## 12. How it's being built
- **Parallel lanes** on separate branches, each owning its own files. Shared contracts mean the pieces fit together.
- **Wave A (running now):** engine, safety, data, ML, frontend.
- **Wave B (from Friday):** what-if, red-team + CI, deploy.
- **Merge windows:** Fri 10 pm first full playable build · Sat 10 pm feature freeze · Sun 2 pm code freeze.
- **Submit Sunday by 10 pm CT** (the deadline is Mon 11 am CT, during school).

## 13. What only Sahib does
1. Confirm the district by street address and **register** on congressionalappchallenge.us.
2. Add `OPENAI_API_KEY` to the cloud environment settings and set a spending limit.
3. Make the 5 friends' texting voices sound like real teens (edit `data/scenarios/*.json`).
4. **Label** the disagreement queue (~1 hour, Friday after school).
5. Ask a **school counselor** to review the rubric and scenarios and label 30 replies. Run the **classmate survey.**
6. Check every crisis number on its official website.
7. Merge, play-test, record the **video,** write the **short answers** and an **honest AI-use disclosure.**

---

## 14. Short-answer draft: "What technical challenge did you face?"
> *Fill in the real numbers after the build.* Large language models are great at sounding human but can't be trusted to decide anything in a suicide-prevention tool. So in FirstReply the AI only writes the friend's words. A deterministic state engine I designed decides what the friend is allowed to reveal. A verifier rejects any AI reply that leaks a locked fact or fails our safety check, and falls back to a reviewed line. A speaker-aware Guardian catches risk, including teen slang like "unalive," without flagging the most important question: "are you thinking about suicide?" (false-positive rate [x]%). Two models I trained detect seven helping skills (macro-F1 [x] vs [y] for keywords), with calibrated probabilities and word-level explanations. Their scores agree with a school counselor at kappa [x]. [N] automated attack conversations found [k] failures, which are now permanent tests.
