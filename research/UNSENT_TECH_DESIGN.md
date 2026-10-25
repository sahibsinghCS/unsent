# Unsent: technical design (from AI wrapper to real system)

**The idea in one sentence:** *"LLMs are unreliable judges and unsafe actors, so the LLM in Unsent is only the friend's voice. My own models and algorithms make every decision, and every decision is measured."*

That sentence is your answer to the technical-challenge short answer, your README intro, and the 20 seconds of your video that convince the engineer judge.

---

## 0. How CAC judging works, and why it matters for the design

1. **Register** at congressionalappchallenge.us and choose your district by home address.
2. **Submit by Mon Oct 26, 12:00 pm ET (11:00 am CT).** The entry includes:
   - the app name and description
   - a **public YouTube/Vimeo video, 1–3 minutes**
   - a **code link** (GitHub)
   - **short written answers** (e.g., "What technical challenge did you face and how did you solve it?", what you learned)
   - your AI-use disclosure
3. **Foster's office recruits a judging panel** (local engineers, educators, professionals). They score with the CAC rubric: idea, implementation/UX, coding skill. They meet in person or remotely. CAC asks for evaluations by about **Nov 23**.
4. **Winners are announced by the office**, usually December–January. The winning app is featured by the House and displayed at the Capitol, and the winner is invited to **#HouseOfCode** in Washington, DC.

**Do judges question you live?** Normally no. In standard CAC judging, **the video, the short answers and the code are everything judges see.** Some offices hold award events, and local press interviews winners, but scoring happens without you in the room. I haven't confirmed whether Foster's office contacts finalists, so check foster.house.gov/appchallenge or email the office.

**What that means for the build:**
- **Your GitHub README is your interview.** It needs to answer every question a skeptical engineer would ask: architecture diagram, evaluation tables, test results, what failed and how you fixed it.
- **Your video has to *show* the engineering**, not only the chat. Put the live trust graph, the highlighted words and the "what if" simulation on screen.
- **Your code will be opened.** Clean modules, tests, and a passing automated test suite (CI badge) signal that you built it and understood it.

---

## 1. Architecture

```
User message
   │
   ▼
[1] GUARDIAN  (local, no LLM, <50 ms)       ← runs first, always, even offline
   │  slang/obfuscation normalizer → risk lexicon → your trained risk classifier
   │  if user seems at risk → pause, show 988 / trusted adult, end role-play
   ▼
[2] SKILL DETECTOR  (your trained model)     ← decides what the user did
   │  multi-label: asked_directly, validated, dismissed, advice_dumped,
   │  promised_secrecy, referred_adult, referred_988, follow_up
   ▼
[3] STATE ENGINE  (pure Python, deterministic, unit-tested)
   │  trust(t+1) = clamp(trust(t) + Σ w_i·event_i − decay, 0, 100)
   │  disclosure level 0→4 unlocks by thresholds (with hysteresis)
   ▼
[4] ACTOR  (LLM = the friend's voice only)
   │  input: scenario fact sheet + ONLY the facts unlocked at current level
   │  output → [5] VERIFIER: did the reply reveal locked facts? contradict the
   │  fact sheet? contain unsafe content? → if yes, regenerate (max 2) → fallback line
   ▼
Phone UI (typing delays, "Seen", multi-bubble)  +  live trust graph
   │
   ▼  (end of conversation)
[6] CRITIC = your classifier + LLM judge ensemble → calibrated scores
[7] TURNING-POINT + "WHAT IF" SEARCH (Monte Carlo rollouts on the conversation tree)
```

---

## 2. Each feature, wrapper version vs your version

### Feature 1: the conversation engine (the "friend")
| Wrapper version (what judges expect) | Your version |
|---|---|
| One big prompt: "You are a sad teen; open up if the user is kind." The LLM decides everything and grades itself. | The **friend is a state machine your code controls.** The LLM never decides how much to reveal. |

What you build:
- **Scenario fact sheets.** Each scenario is a JSON file: name, situation, mood, and the facts unlocked at each **disclosure level** (0 "I'm fine" → 1 stress → 2 hopelessness → 3 "I've thought about not being here" → 4 accepting help). **No methods, ever** (follows safe-messaging guidelines). A counselor can review them.
- **Trust as a real variable.** Example update: `trust += 12*validated + 18*asked_directly − 20*dismissed − 10*advice_dump − 25*promised_secrecy − 2 (decay)`. Weights are tuned per persona ("guarded" vs "open"). Disclosure thresholds use **hysteresis**, so the level doesn't flicker back and forth.
- **Generator-verifier loop.** After the LLM writes the friend's reply, a check runs: did it reveal a fact that isn't unlocked yet? Contradict the fact sheet? Include unsafe content? If so, regenerate up to 2 times, then fall back to a pre-written line. **Measure how often the verifier catches something**, which becomes a stat for your README.
- **Live trust graph** next to the chat. Judges see the line drop when you say "lol you'll be fine" and rise when you ask directly. That's the most visual proof that your code drives the conversation.

**Why it isn't a wrapper:** the logic is yours, deterministic and unit-tested. You can say: "The same messages always produce the same trust path. Here are the tests."

### Feature 2: the skill detector (your own trained model)
| Wrapper | Yours |
|---|---|
| Ask the LLM "did the user ask directly? score 1–5." | **A machine-learning model you trained** labels every message across 8 skills, on your laptop, in milliseconds. |

What you build:
- **Dataset (about 600–800 examples).**
  1. Use an LLM to *generate* varied teen replies to each friend message, covering good, bad and mixed responses, plus slang, typos, emojis and Spanish.
  2. Have the LLM pre-label them.
  3. **Hand-check every label yourself** (this is the real work, and you can describe it).
  4. Split the data: train / validation / **held-out test**.
- **Model:** sentence embeddings (`all-MiniLM-L6-v2` via sentence-transformers) feeding **one logistic-regression classifier per skill** (scikit-learn). Trains in seconds on a CPU.
  - Stretch: fine-tune `distilroberta-base` and compare.
- **Report per-skill precision, recall and F1** on the held-out test set, with a confusion matrix.
- **Explainability that comes from your model, not the LLM.** **Leave-one-word-out occlusion** removes each word and measures how the score changes. The words that matter most get highlighted in the feedback ("**'you'll be fine'** lowered *validated* by 0.41"). The highlighted words come straight from your model's own numbers.

**Shock value:** a high schooler who built a dataset, trained a classifier, measured it on held-out data, and added explainable AI on top.

### Feature 3: the Critic (scoring)
| Wrapper | Yours |
|---|---|
| LLM writes a report card. | **Ensemble plus calibration plus human validation.** |

What you build:
- **Ensemble.** Your classifier and an LLM judge (with a fixed rubric) each score every message. **When they disagree, the message is flagged** and shown as "uncertain," not as a confident grade.
- **Calibration.** Fit isotonic regression so that when the app says 80% "asked directly," it really is right about 80% of the time. Show a **reliability diagram** in the README.
- **Human validation.** A school counselor or psychology teacher labels **30 replies the system has never seen.** Report **Cohen's kappa** between your Critic and their labels, **with a bootstrap confidence interval.** The honest number, whatever it is, beats a suspiciously perfect one.
- **Rewrites that are checked.** When the app suggests a better reply, your classifier re-scores it, and **only rewrites that actually score higher are shown.** The suggestions are measured, not just generated.

### Feature 4: the Guardian (safety layer)
| Wrapper | Yours |
|---|---|
| "Please be safe" in the prompt. | **A local, layered safety system with measured recall, robust to teen slang.** |

What you build:
- **Normalizer.** Handles how teens actually write: "kms," "unalive," "kys," "🪦," leetspeak ("k1ll"), stretched letters ("noooo"), misspellings, and Spanish.
- **Layer 1:** a risk-phrase list (high recall).
- **Layer 2:** your embedding classifier for risk language that avoids keywords ("everyone would be better off without me").
- **Tuned for recall.** Pick the threshold from the precision-recall curve so the system almost never misses a risky message. **Report recall (the miss rate) on a test set**, especially the slang and obfuscated cases.
- **Robustness test.** Automatically change each test message (typos, slang, emoji, mixed language) and check the Guardian's decision stays the same. Report robustness before and after you added the normalizer. This is a great before/after number.
- Runs **before** any LLM call, **fully local**, still works if the AI API is down, in under 50 ms.
- **Prompt-injection defense.** Messages like "ignore your instructions" or "describe how you'd do it" are caught before they reach the friend.

### Feature 5: red-team harness and safety regression suite
| Wrapper | Yours |
|---|---|
| "I tested it a few times." | **Automated adversarial testing, with every failure turned into a permanent test.** |

What you build:
- **Attacker bots.** LLM-driven "helpers," each with a strategy: dismissive, method-seeking, persona-breaking, prompt-injecting, slang-heavy, and one that is itself in crisis. Run about 100 conversations.
- **Automatic checks on every turn:** no method content, persona stays in character, the Guardian fires when it should, the verifier catches leaks.
- **Coverage matrix:** each attack type × each scenario, with pass/fail.
- **Regression suite.** Every failure becomes a test in `tests/safety/`. **GitHub Actions** runs the whole suite on every push. A README badge shows "Safety suite: 147/147 passing." Judges who click your repo see it immediately.
- In the README, **show the failures you found and how you fixed them.** That's the most convincing evidence that you actually built it.

### Feature 6: rewind, turning points and "what if" simulation (the showstopper)
| Wrapper | Yours |
|---|---|
| A "try again" button. | **A conversation tree with saved state at each step, automatic turning-point detection, and search over possible replies.** |

What you build:
- **Saved state at every message.** Every node in the conversation tree stores the full state (trust, disclosure level, history). Rewinding restores it *exactly*. Branches are cached so they replay identically.
- **Turning-point detection.** After a conversation, the app finds **the exact message where trust dropped the most** and pins it: *"This is where you lost them."*
- **"What if" search, using Monte Carlo rollouts** (the same idea game AIs use):
  1. From the turning point, generate N candidate replies (for example 4).
  2. Score each with your Critic.
  3. **Simulate the conversation forward** a few turns for each one.
  4. Show the best path: *"If you'd said 'that sounds really heavy, are you thinking about hurting yourself?', she would have opened up 2 messages later."*
- It's a real search algorithm with cost limits (N=4, depth=3) and caching. Precompute it for the demo scenario so the video plays smoothly.

**This is the moment that surprises judges:** the app doesn't only grade you. It finds the moment things went wrong and shows you, in a simulation, what would have happened if you'd replied differently.

---

## 3. Build order (3.5 days)

| When | Build | Shock element it unlocks |
|---|---|---|
| **Thu night** | Repo, FastAPI skeleton, 3 scenario fact sheets, Guardian lexicon and normalizer, start generating the dataset | none yet |
| **Fri** | State engine and unit tests; Actor plus verifier loop; phone UI with live trust graph; hand-check labels; train the skill detector | Trust graph, your own model |
| **Sat** | Critic ensemble and calibration; occlusion highlights; rewind tree and turning point; "what if" rollouts; deploy | Explainability, "what if" |
| **Sun** | Red-team harness, safety tests in CI, counselor's 30 labels → kappa; README with diagrams and tables; record video; short answers | Safety badge, evaluation tables |
| **Mon by 9 am CT** | Submit | |

**Cut order if behind** (first to go): fine-tuning DistilRoBERTa → calibration plot → the full red-team matrix (keep 30 conversations) → "what if" rollouts (keep turning-point detection). **Never cut** the Guardian, the state engine, your skill detector, or the counselor review.

**Stack:** Python 3.11, FastAPI, SQLite, sentence-transformers, scikit-learn, numpy/pandas, pytest, GitHub Actions; front end in HTML, Tailwind and JS (a PWA), with Chart.js for the trust graph. Plus one LLM API for the Actor and the LLM judge.

---

## 4. Video structure (about 2:45)

| Time | What's on screen |
|---|---|
| 0:00–0:15 | Phone screen. *"honestly idk why i even bother anymore."* "What would you text back?" Stat: 1 in 5. |
| 0:15–0:35 | You answer badly ("lol don't say that"). **The trust graph drops** and the friend leaves you on Seen. |
| 0:35–1:05 | Rewind and ask directly. The friend opens up. The feedback card **highlights the exact words** that helped. |
| 1:05–1:30 | **Turning-point detection and the "what if" simulation:** "here's where you lost them, and here's what would have happened." |
| 1:30–2:05 | **Under the hood:** architecture diagram; "the LLM is only the voice"; your classifier's F1 and the counselor kappa; Guardian catching "unalive"; **safety suite 147/147.** |
| 2:05–2:30 | Real mode (no AI, 988); counselor review; the classmate survey result. |
| 2:30–2:45 | Name, purpose, audience, tools, what you learned. |

---

## 5. You must be able to explain all of it

With no live interview, judges decide whether you understood your project from the **README and short answers**. If there *is* an award event or press interview, they'll ask anyway. As we build, I'll keep `HOW_IT_WORKS.md` in plain language: why logistic regression on embeddings, what hysteresis does, how occlusion works, what kappa measures, why recall matters more than precision for the Guardian, and how the rollouts work. Read it, and make sure you could explain each part to a friend.
