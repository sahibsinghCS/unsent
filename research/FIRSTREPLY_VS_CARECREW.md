# FirstReply vs CareCrew: side-by-side comparison and final pick

*Thu Oct 22, 2026.*

**Method:**
- Both apps were written up at their most technically advanced and labeled "App A" and "App B."
- Three independent AI judges scored them blind on the official CAC rubric. Each played a typical IL-11 panelist: a senior software engineer, a high-school CS teacher who has judged CAC before, and a public-health nonprofit director.
- The blind write-ups are in the scratchpad file `blind_pitches.md`.
- These are simulated judges, not real ones. They're useful as a read that isn't anchored on my opinion, but they aren't evidence of how real judges will vote.

---

## 1. Blind judge panel results

| Judge | CareCrew (Idea / UX / Code) | FirstReply (Idea / UX / Code) | Who ranked higher |
|---|---|---|---|
| Software engineer | 4 / 4 / 4 = **12** | 5 / 5 / 3 = **13** | FirstReply, slightly |
| CS teacher (past CAC judge) | 4 / 3 / 4 = **11** | 5 / 5 / 4 = **14** | **FirstReply, clearly** |
| Public-health director | 4 / 4 / 5 = **13** | 5 / 5 / 4 = **14** | FirstReply, slightly |
| **Total** | **36 / 45** | **41 / 45** | **FirstReply 3–0** |
| Estimated chance of 1st in a strong district | 20% / 20% / 20% → **avg 20%** | 30% / 35% / 27% → **avg 31%** | |

**What all three agreed on:**
1. **FirstReply's idea and demo are stronger.** A friend leaving you on "Seen" after you say the wrong thing lands in seconds. CareCrew has to explain sundowning and DICE before the demo makes sense.
2. **CareCrew is the deeper statistics and engineering job**: retrieval with citations checked by a second model, change-point detection on the logs. But it shows up as dashboards, and its statistics run on data too thin to mean much (20–60 incidents a month from one family).
3. **Both had too many features.** All three judges said 10+ systems built solo in 3.5 days *looks AI-generated* and makes them doubt who built it. **Depth beats breadth.** In an interview they would ask "how is the hidden trust state updated?" and "who labeled your 50 test replies?" If the student can't answer without notes, they'd score coding at 2 or lower.
4. **FirstReply's main risk is safety and comfort**: an AI playing a suicidal teen, used by teens. The fix is outside review by a school counselor or QPR/MHFA instructor, mentioned in the video, plus vetted scenario templates and content warnings.
5. **CareCrew depends on a real family story.** Without one, it "looks reverse-engineered from a gap in past winners." It's also the 14th dementia or caregiver app since 2023.

---

## 2. Side by side

| Criterion | FirstReply | CareCrew | Edge |
|---|---|---|---|
| Problem | Teen suicide and mental health (20.4% seriously considered it, CDC 2023) | Dementia caregiving (13M caregivers, 5.4M+ child caregivers) | Tie: both universal |
| Specific audience | Teens who get the worrying text | Teens and young adults helping care for a grandparent | Tie |
| CAC originality | Mental health is common, but **no winner trains the peer** | About 13 dementia/caregiver winners since 2023; none does behavior coaching or teen caregivers | **FirstReply** |
| First-15-second demo | A text pops up and the friend shuts down when you answer wrong | Needs context explained first | **FirstReply** |
| Is the AI essential? | Yes: role-play plus grading free-form replies | Yes: extracting incidents plus advice backed by citations | Tie |
| How advanced it can get | High | Higher (statistics, retrieval, a verification model) | CareCrew |
| Data available to prove it works | You create it (labeled replies, simulated conversations) | Only synthetic logs; real logs too small | **FirstReply** |
| Build risk in 3.5 days | Lower: no outside data, no voice pipeline needed | Higher: voice, document retrieval, statistics, PDF | **FirstReply** |
| Your honest personal angle | **You are the audience**, and a classmate survey proves it | Only works if you really have a family member with dementia | **FirstReply** (unless you do) |
| Safety / judge discomfort | Higher (suicide topic); fixable with counselor review and guardrails | Medical-advice risk (delirium flag) | CareCrew slightly |
| Product potential | Schools would use it (a free alternative to Kognito) | Families and clinics | Tie |
| Simulated chance of 1st | **~31%** | ~20% | **FirstReply** |

---

## 3. More advanced, but deep instead of wide

The judges' message was clear: **"advanced" means a few systems you can fully explain and that you measured, not 12 features.** Here's the upgraded version of each, cut down to what one person can build and defend.

### FirstReply: advanced build (recommended)
| Component | The advanced part | Why judges will respect it |
|---|---|---|
| **1. Conversation engine where code controls the state** | The AI only *labels* each user message into skill events (asked directly? dismissed? promised secrecy?). **Your Python code** updates trust and how much the friend reveals, using rules you wrote. The friend's reply then reflects the current level. | It answers the engineer's question "is the state deterministic?" with yes. The AI isn't grading itself. This is your best technical-challenge answer. |
| **2. Critic validated on held-out examples** | Label 50 replies yourself to build the grader, then have **a counselor or second person label 30 the grader has never seen.** Report agreement (kappa) **only on those 30.** | It fixes the "you tuned it on your own test set" problem the engineer judge flagged. |
| **3. Guardian safety layer with a reported miss rate** | Fixed rules plus a small classifier you train yourself (sentence embeddings plus logistic regression in scikit-learn) on a labeled set you write. It runs **before** any AI call and still works if the AI API is down. Report its **false-negative rate**: how often it missed a risky message. | It answers the safety judge's main demand. A model you trained yourself is real machine-learning work. |
| **4. Red-team harness** | A script runs 100 adversarial conversations: someone dismissive, someone trying to extract method content, someone trying to break the persona ("ignore your instructions"). **Show the failures you found and how you fixed them**, not just a pass rate. | It shows engineering maturity. All three judges asked about this. |
| **5. Rewind and branch** | A tree of the conversation. Tap any of your messages, rewind, and try again, and see how the friend's path changes. | Visual "wow" for the video, and it's plain software engineering (a tree data structure) that you can explain. |
| **Safety design** | Scenarios come from **counselor-reviewable templates** (no unlimited generation), a content warning before you start, a check-in after each session ("how are you feeling?"), 988 always visible, and the "It's real" mode uses no AI. | Directly addresses all three judges' discomfort. |
| *Stretch only* | Voice-call mode using the browser's built-in speech; spaced-practice reminders | |
| *Roadmap slide only, don't build* | Teacher dashboard | Mention it as "next" in the video. |

**The single most valuable outside action:** **email a school counselor or psychology teacher on Friday morning.** Ask them to (1) review the 7-skill rubric and the scenario templates, and (2) label 30 test replies. One sentence in the video, "reviewed by [title] at [school]," addresses the safety concern and the authenticity concern at the same time.

### CareCrew: advanced build (if you choose it)
| Component | The advanced part |
|---|---|
| **1. Voice → structured incident** | Whisper, then the AI extracts a schema (behavior, time, what happened before, response, outcome), then one-tap confirmation. Measure extraction accuracy. |
| **2. Coaching with verified citations** | Search over NIA, Alzheimer's Association and DICE texts. A local verification model checks that each cited passage really supports the suggestion; anything unsupported is rejected. Report how many are rejected. |
| **3. Honest pattern statistics** | Show counts and **"not enough data yet"** until there are enough incidents, with error bars. Use a rolling baseline for sudden changes and a minimum-data rule. Clearly say **"no alert does not mean she's fine."** |
| **4. Red flags before any AI** | Hard-coded routing to 911, the doctor, or the 800-272-3900 helpline, which works even if the network is down. |
| **5. Doctor-visit PDF** | Charts plus questions to ask the doctor. |
| *Cut* | Care circle, redirection cards, burnout check-in (roadmap only) |
| **Must have** | A real family using it (with consent) and their quote. Without that, all three judges' concerns stand. |

---

## 4. Verdict: build FirstReply

- **It won the blind panel 3–0** (41 vs 36 points; about 31% vs 20% estimated chance of 1st).
- It has the stronger idea and demo, a lower risk of not finishing in time, an honest personal angle (you are the user), and the evidence to prove it works can be created this week.
- Its biggest weakness, safety and comfort, can be fixed with guardrails and **one counselor's review**.
- CareCrew's biggest weakness, a crowded category plus thin data plus needing a real family story, can't be fixed by Monday unless you already have that connection.

**When CareCrew would be the better pick:** only if you personally help care for a relative with dementia *and* that family will use it this weekend and let you quote them. Even then, the judges preferred FirstReply's idea and demo, so it would be closer to a tie.

### Authenticity rule for the build (the judges insisted on this)
Whatever we build, **you need to understand and be able to explain every component**: how the state machine updates trust, why kappa, what the classifier was trained on, and what the red-team found. I'll write a plain-language `HOW_IT_WORKS.md` as we build, so you can answer any judge question without notes. Also disclose AI-assisted development, as the rules require.
