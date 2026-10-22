# FirstReply: master plan

*Everything decided so far, in one place. Last updated Thu Oct 22, 2026. Deadline: **Mon Oct 26, 11:00 am CT** (12:00 pm ET). Plan to submit by 9 am CT.*

---

## The idea in one sentence
**FirstReply lets teens practice the text that could save a friend's life: they chat with a realistic AI friend who's struggling while models I built score every reply, keep it safe, and show exactly where they lost the friend and what would have worked.**

Short version (for the video and short answers): *A safety-first simulator that trains teens to respond when a friend texts that they're not okay.*

---

## 1. The problem
- **CDC YRBS 2023:** 39.7% of US high schoolers had persistent sadness or hopelessness, **20.4% seriously considered suicide** (27% of girls, 14% of boys), and 9.5% attempted. [CDC](https://www.cdc.gov/mmwr/volumes/73/su/su7304a9.htm)
- Young people **prefer telling peers over professionals** when they have suicidal thoughts ([McGillivray 2022](https://bmcpsychiatry.biomedcentral.com/track/pdf/10.1186/s12888-021-03636-x)), and they often hide it from parents ([2025 study](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12414306/)). The first person to know is usually a friend.
- Adults get gatekeeper training (**QPR**: Question, Persuade, Refer), but its effect on knowledge and confidence **fades within about 6 months** ([Orygen](https://www.orygen.org.au/Research/Research-Areas/Suicide-Prevention/Orygen_Suicide_prevention_research_bulletin), [QPR Institute](https://qprinstitute.com/research-theory)). Teens, who actually get the texts, almost never get this training, and nobody gets to practice.
- Worldwide: suicide is a leading cause of death among young people (WHO). The app switches crisis lines by country (988 in the US).

## 2. Audience
High-school students who are the first to hear that a friend isn't okay. Secondary audience: school counselors and teachers who want a free, safe practice tool for students.

## 3. Why it can win
- **Mental health keeps reaching the podium**, but past winners help the person who is struggling: Free Mind Bot FL-08 2023, The Help Desk CT-01 2022, Mental Moji, MindWell Connect, NeuroCalmAI, SafeHavenAI. **No CAC winner trains the friend.**
- **The AI is essential:** realistic role-play plus scoring of free-form replies can't be done with a database or fixed decision tree.
- **Real engineering, not a wrapper:** trained models, a state engine, safety measurements, automated testing, search.
- **True personal angle:** I'm a high schooler, so I'm the audience. The classmate survey (see checklist) turns that into evidence.
- **No outside data needed**, so all the time goes into the product and the evaluation.

**Competitor:** Kognito Friend2Friend is sold to schools. It's a scripted multiple-choice avatar simulation that takes about 25 minutes. FirstReply is **free, open-ended texting with unlimited practice, scores on each message, and a "what if" simulation.** Static guides (Seize the Awkward, Jed) and crisis lines don't let you practice.

**Solo is fine:** 56% of 2021–2025 CAC winners worked alone (905 of 1,607). IL-11's last 3 winners were solo.

---

## 4. How CAC works
1. Register at congressionalappchallenge.us and confirm the district by street address. ZIP 60502 is split between IL-11 (Foster) and IL-14 (Underwood).
2. Submit:
   - app name and description
   - a **public YouTube video, 1–3 min** (must include: my name, app name, one-sentence purpose, target audience, languages/tools used, the app working, what I learned)
   - a **GitHub link**
   - **short answers** (e.g., "What technical challenge did you face and how did you solve it?")
   - an **AI-use disclosure**
3. The office recruits a judging panel (engineers, educators, professionals). They score on: **quality of idea** (creativity, originality, real problem), **implementation** (UX and design), and **coding skill**. Evaluations are due around Nov 23.
4. Winners are announced around December–January. The app is featured by the House and displayed at the Capitol, and the winner is invited to #HouseOfCode in DC.
5. **Usually no live Q&A.** Judges see only the video, the short answers and the code. → **The README is my interview.** The video has to show the engineering.

---

## 5. Product features
| Feature | What the user sees |
|---|---|
| **Practice chat** | A phone-style text conversation with a struggling "friend": typing bubbles, realistic delays, several texts in a row, "Seen" when I mess up, teen texting style. 5 scenarios (breakup, failing a class, moving schools, being bullied, "fine" but giving things away). |
| **The friend opens up in layers** | The friend only reveals more when I validate their feelings and **ask directly**. Dismissing them ("lol you'll be fine") makes them shut down. |
| **Live trust graph** | A line next to the chat that rises and falls with every message I send. |
| **Feedback card** | Scores on 7 skills: check in, listen without judging, **ask directly**, **don't promise secrecy**, persuade, **refer to a trusted adult or 988**, follow up. Shows the exact words that helped or hurt, plus suggested rewrites that are checked before they're shown. |
| **Rewind and branch** | Tap any message, rewind, try a different reply, and see the conversation tree. |
| **"Here's where you lost them" + "what if"** | Finds the message where trust dropped most, then simulates better replies forward: *"If you'd said this, she would have opened up 2 messages later."* |
| **"It's real right now" mode** | **No AI.** A fixed, vetted step-by-step plan: what to say, tell an adult today, call or text 988, 911 if there's immediate danger. |
| **Safety design** | Content warning before starting, a check-in after each session, 988 always visible, crisis line chosen by country, no conversations stored, Spanish support. |
| *Stretch* | Voice-call mode (browser speech), spaced practice reminders for weak skills |
| *Roadmap only (mention in video)* | Teacher/counselor class dashboard |

---

## 6. Technical design (how it isn't an AI wrapper)
**The idea:** *LLMs are unreliable judges and unsafe actors, so in FirstReply the LLM is only the friend's voice. My own models and algorithms make every decision, and every decision is measured.*

### Architecture
```
User message
   │
   ▼
[1] GUARDIAN  (local, no LLM, <50 ms)        ← always first, works offline
   │  slang normalizer → risk phrases → my trained risk classifier
   │  user at risk → pause, show 988 / trusted adult, end role-play
   ▼
[2] SKILL DETECTOR  (my trained model)        ← decides what the user did
   │  asked_directly, validated, dismissed, advice_dumped,
   │  promised_secrecy, referred_adult, referred_988, follow_up
   ▼
[3] STATE ENGINE  (pure Python, deterministic, unit-tested)
   │  trust(t+1) = clamp(trust(t) + Σ w_i·event_i − decay, 0, 100)
   │  disclosure level 0→4 unlocks at thresholds (with hysteresis)
   ▼
[4] ACTOR  (LLM = the friend's voice only)
   │  gets the scenario fact sheet, limited to the facts unlocked at the current level
   ▼
[5] VERIFIER: leaked locked facts? contradicted fact sheet? unsafe content?
   │  → regenerate (max 2) → otherwise a pre-written fallback line
   ▼
Phone UI + live trust graph
   │  (end of conversation)
   ▼
[6] CRITIC: my classifier + LLM judge ensemble → calibrated scores
[7] TURNING POINT + "WHAT IF" search (Monte Carlo rollouts on the conversation tree)
```

### Each component in detail
1. **State engine (the friend)**
   - **What's built:** scenario JSON fact sheets with facts at disclosure levels 0–4 (never methods) that a counselor can review; trust weights for each persona (guarded or open); hysteresis on the thresholds so the level doesn't flicker; the generator-verifier loop.
   - **What gets measured:** unit tests showing the same messages always produce the same trust path; how often the verifier catches a leak.
2. **Skill detector (my model)**
   - **What's built:** about 700 replies (LLM-generated, including slang, typos, emoji and Spanish), **every label hand-checked**, split into train, validation and held-out test sets. Sentence embeddings (`all-MiniLM-L6-v2`) feed one logistic regression per skill. Leave-one-word-out occlusion highlights the words that mattered.
   - **What gets measured:** precision, recall and F1 per skill on the held-out set, plus a confusion matrix.
3. **Critic (scoring)**
   - **What's built:** my classifier and an LLM judge score every message, and disagreements are shown as "uncertain." Isotonic calibration. Suggested rewrites are re-scored and shown only if they score higher.
   - **What gets measured:** a reliability diagram, and **Cohen's kappa against 30 replies labeled by a counselor that the system never saw**, with a bootstrap confidence interval.
4. **Guardian (safety)**
   - **What's built:** a normalizer for teen slang ("kms," "unalive," "kys," 🪦, leetspeak, stretched letters, Spanish); a risk-phrase list; an embedding classifier; a threshold chosen for high recall; prompt-injection blocking.
   - **What gets measured:** recall (how often it misses a risky message) on a test set full of slang and disguised wording; robustness before and after adding the normalizer; latency under 50 ms.
5. **Red-team harness**
   - **What's built:** attacker bots that are dismissive, try to get method content, try to break the persona, try prompt injection, use heavy slang, or are in crisis themselves. About 100 conversations, checked automatically every turn.
   - **What gets measured:** a coverage matrix of attack type × scenario. **Every failure becomes a test** in `tests/safety/`, and **GitHub Actions** runs the suite on every push (README badge). The README shows the failures found and how they were fixed.
6. **Rewind, turning point, "what if"**
   - **What's built:** saved state at every message; turning-point detection (the message with the biggest trust drop); Monte Carlo rollouts (N=4 candidate replies, scored by the Critic, simulated 3 turns forward, cached).
   - **What gets measured:** a demo where the best simulated reply actually improves the friend's trust path.

### Tech stack
Python 3.11, FastAPI, SQLite, sentence-transformers, scikit-learn, numpy/pandas, pytest, GitHub Actions; front end in HTML, Tailwind and JS as an installable PWA; Chart.js for the trust graph; one LLM API for the Actor and the LLM judge.

---

## 7. Build plan
| When | Build |
|---|---|
| **Thu night** | Register for CAC. Repo and FastAPI skeleton. 3 scenario fact sheets. Guardian phrase list and normalizer. Start generating the dataset. |
| **Fri** | State engine and tests. Actor and verifier loop. Phone UI and live trust graph. Hand-check labels. Train the skill detector. **Email the school counselor or psych teacher (morning).** |
| **Sat** | Critic ensemble and calibration. Word highlights. Rewind tree and turning point. "What if" rollouts. Deploy. |
| **Sun** | Red-team harness and safety tests in CI. Counselor's 30 labels → kappa. Classmate survey. README with diagrams and evaluation tables. Record the video. Write the short answers. |
| **Mon by 9 am CT** | Submit. |

**Cut order if behind:** DistilRoBERTa fine-tune (stretch) → calibration plot → full red-team matrix (keep 30 conversations) → "what if" rollouts (keep turning-point detection).
**Never cut:** the Guardian, the state engine, my own skill detector, the counselor review, the "It's real" mode.

---

## 8. Video plan (about 2:45)
| Time | Shot |
|---|---|
| 0:00–0:15 | Phone screen: *"honestly idk why i even bother anymore."* "What would you text back? One in five high schoolers seriously considered suicide last year, and the first person they tell is usually a friend. Nobody teaches us what to say." |
| 0:15–0:35 | I reply badly ("lol don't say that"). The **trust graph drops** and the friend leaves me on Seen. |
| 0:35–1:05 | Rewind, ask directly. The friend opens up. The feedback card **highlights the exact words.** |
| 1:05–1:30 | **"Here's where you lost them" plus the "what if" simulation.** |
| 1:30–2:05 | **Under the hood:** architecture diagram; "the LLM is only the voice"; the skill detector's F1; the counselor kappa; the Guardian catching "unalive"; the **safety suite badge.** |
| 2:05–2:30 | "It's real" mode (no AI, 988), counselor review, classmate survey result. |
| 2:30–2:45 | Name, app name, purpose, audience, languages and tools, what I learned. |

---

## 9. Short-answer draft: "What technical challenge did you face?"
> *Draft, finish with real numbers after the build.* Large language models are unreliable judges and can be unsafe actors, which is unacceptable for a suicide-prevention tool. So I designed FirstReply so the LLM only writes the friend's messages, and my own components make every decision. A safety layer that runs locally catches risk language, including teen slang like "unalive," before any AI call. I trained a classifier on [N] hand-checked replies to detect seven helping skills (F1 = [x] on held-out data). A deterministic state engine I wrote decides how much the friend opens up. A verifier blocks the AI from revealing too much or saying anything unsafe. I tested it with [100] automated adversarial conversations; every failure became a permanent test, and [147/147] now pass in CI. My scoring agrees with a school counselor's labels at kappa = [x].

---

## 10. Checklist
- [ ] Confirm district by street address, then **register today**
- [ ] Email a school counselor or psych teacher Friday morning: review the rubric and scenarios, label 30 replies
- [ ] Classmate survey (10+): "If a friend texted 'idk why I even bother anymore,' would you know what to say?"
- [ ] Core working by Fri night, deployed by Sat night
- [ ] Real numbers (F1, kappa, Guardian recall, safety suite) in the README
- [ ] `HOW_IT_WORKS.md`: understand every component well enough to explain it without notes
- [ ] Video under 3:00 with the required items; set to **public**
- [ ] AI-use disclosure written honestly
- [ ] **Submit by 9 am CT Monday**

---

## Build plan
- `PLAN_WORKTREES.md`: the parallel build plan (worktrees, lanes, tools, mission prompts, merge protocol, schedule)

## Related research files
- `research/CAC_2026_WINNING_IDEAS.md`: rules, rubric, IL-11 winners, round-1 ideas
- `research/CAC_2026_IDEAS_ROUND2.md`: round-2 ideas
- `research/CAC_2026_IDEAS_ROUND3_FINAL.md`: final top 10
- `research/FIRSTREPLY_VS_CARECREW.md`: comparison (the panel scores there are **simulated AI-judge estimates, not real data**)
- `research/FIRSTREPLY_TECH_DESIGN.md`: the detailed technical design (merged into this file)
