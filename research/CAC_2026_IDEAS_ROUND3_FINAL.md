# CAC 2026, round 3 (final): universal problems for one specific audience

*Thu Oct 22, 2026. This builds on `CAC_2026_IDEAS_ROUND2.md`, and the rules and judging details in `CAC_2026_WINNING_IDEAS.md` still apply. This round vetted 10 more ideas. Researchers searched about 1,050 district winner pages from 2023–2025 for anything similar, checked competitors and tested the data.*

**What we looked for:** a problem people all over the world struggle with (mental health, hunger, caregiving, disability), aimed at one specific group nobody serves well, where AI does work a database couldn't, and with no past CAC winner doing the same thing.

**Cut this round:**
- **Pantry to Plate (6/10).** "Photo of ingredients, AI makes recipes" has already won as Snap Cook (CT-04 2023) and Food Saver (MA-09 2025), and also exists as MealMate and Grocery Genius.
- **AgeOut (6/10).** The federal site FosteringTheFuture.gov launches this fall and does the same thing, and FCHome (CA-18 2025) won with a similar idea.
- **Sextortion first-aid (6/10).** The AI isn't essential, there's legal risk around images, and Meta already detects this on Instagram.
- **Low-literacy reader (5.5/10).** Lexia, MedReader and ViziBox are close past winners, and there are at least six commercial apps.

---

## Final top 10

| # | App | Problem | Specific audience | Score |
|---|---|---|---|---|
| **1** | **Unsent** | Teen suicide and mental health | **Teens who get the worrying text from a friend** | **8.5** |
| 2 | **CareCrew** | Dementia caregiving | **Teens and young adults helping care for a grandparent** | 8 |
| 3 | **Prove $35** | Hunger among seniors | **Older adults missing SNAP money they qualify for** | 8 |
| 4 | **Gavel** (round 2) | Local news deserts and civic exclusion | Residents of any town | 8.5* |
| 5 | **SecondHand Safe** (round 2) | Recalled products still in use | Families buying used baby gear | 8.5* |
| 6 | **IEP Ally** (round 2) | Special-education gaps | Parents of kids with disabilities | 8 |
| 7 | **Aphasia communicator** | Losing the ability to speak after a stroke | About 2M people with aphasia | 7.5 |
| 8 | **StayCovered** (round 2) | Losing Medicaid or SNAP over paperwork | Adults facing the new work rules | 8* |
| 9 | **Letters Home** | Kids separated from an incarcerated parent | 5.1M kids and their caregivers | 7 |
| 10 | **Shutoff Shield** (round 2) | Losing heat or power | Households with a shutoff notice | 8* |

\* Strong ideas, but they're civic or safety tools rather than the "universal human struggle for one group" shape you asked for, so they rank lower here.

---

## #1 Unsent: practice the text that could save a friend ⭐ RECOMMENDED

**Pitch:** When a friend is struggling, another teen usually hears about it first, by text, and most of us freeze or say the wrong thing. Unsent is an AI simulator. You text with a realistic struggling "friend," then get scored feedback based on the suicide-prevention methods adults are trained in. When it's real, it gives you a step-by-step plan.

**The problem:**
- **CDC YRBS 2023:**
  - 39.7% of US high schoolers had persistent sadness or hopelessness.
  - **20.4% seriously considered suicide** (27% of girls, 14% of boys).
  - 9.5% attempted.
  - [CDC MMWR](https://www.cdc.gov/mmwr/volumes/73/su/su7304a9.htm)
- Young people who disclose suicidal thoughts **prefer telling peers and family over professionals** ([McGillivray 2022, n=513](https://bmcpsychiatry.biomedcentral.com/track/pdf/10.1186/s12888-021-03636-x)), and teens often deliberately hide it from parents ([2025 study](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12414306/)).
- **Gatekeeper training** (QPR: Question, Persuade, Refer) teaches people to spot warning signs and get someone to help. It reliably raises knowledge and confidence, but **the gains fade within about 6 months** ([Orygen review](https://www.orygen.org.au/Research/Research-Areas/Suicide-Prevention/Orygen_Suicide_prevention_research_bulletin), [QPR research](https://qprinstitute.com/research-theory)). That fade is the gap: people need practice they can repeat. Teens rarely get this training at all, even though they're the ones getting the texts.
- **Worldwide:** suicide is a leading cause of death among young people globally (WHO). The app can switch crisis lines by country (988 in the US).

**Why it wins:**
- **Podium theme with a new approach.** Mental health wins every year, but those winners are mood trackers and chatbots for the person who is struggling. Examples: Free Mind Bot (FL-08 2023), The Help Desk (CT-01 2022), Mental Moji, MindWell Connect, NeuroCalmAI, SafeHavenAI. **None trains the friend.** No CAC winner does peer-support practice.
- **The AI is essential.** It can't be built from a database or fixed decision tree. It needs a character who reacts realistically to what you type, and a judge that scores free-form replies.
- **The truest personal angle of any idea we've looked at:** you're a high schooler, so *you* are the audience. Quick validation you can actually run this week: ask 10 classmates, "If a friend texted 'idk why I even bother anymore,' would you know what to say?" Put the real numbers in your video.
- **Zero external data to wrangle**, so all 3.5 days go into the product and the evaluation.

**Competitor and how you differ:**
- **Kognito Friend2Friend** is sold to schools. It's a 25-minute avatar simulation with scripted multiple choice.
- Unsent is **free, open-ended texting like a real phone conversation, with unlimited scenarios and feedback on each message.**
- Static guides (Seize the Awkward, Jed) and crisis lines (Crisis Text Line) don't let you practice.

**How it works:**
1. **Pick a scenario.** Examples: a friend after a breakup, after failing a class, after moving schools, being bullied, grieving, or "fine" but giving things away. Each scenario uses realistic teen texting style.
2. **Text with the friend.** An AI persona with a **hidden trust meter**. The friend only opens up if you validate their feelings and **ask directly** ("are you thinking about killing yourself?"). If you shrug it off ("lol don't say that") or jump straight to advice, they shut down, like real people do.
3. **Get scored feedback.** An AI judge scores each of your messages on a rubric drawn from QPR and teen Mental Health First Aid:
   - noticed and checked in
   - listened without judging
   - asked directly
   - **didn't promise to keep it secret**
   - persuaded them toward help
   - **referred them to a trusted adult or 988**
   - planned a follow-up

   You see your best and worst message, with suggested rewrites.
4. **"It's real right now" mode.** **Fixed, vetted content with no AI:**
   - what to say
   - tell an adult *today*
   - call or text 988
   - 911 if there's immediate danger

**The technical challenge for the short answer (strong):**
1. **Calibrating the AI judge.** Hand-label 50 sample replies per skill using the QPR guidance. Measure how often the AI judge agrees with your labels (accuracy and Cohen's kappa with `sklearn`). Improve the rubric prompt and examples, then report before and after numbers.
2. **A persona that stays consistent.** A structured hidden state (trust, what's been revealed so far, risk level) is updated each turn and passed back to the model, so the friend doesn't contradict themselves.
3. **Safety rules that don't rely on the AI.** A keyword-and-classifier check runs before any AI call. If *you* seem at risk, it shows 988 and pauses the role-play. The persona follows safe-messaging guidelines and never describes methods. No conversations are stored.

**Tools:** Python, Streamlit (`st.chat_message` styled as a phone), and an AI API with JSON output (Claude, Gemini or OpenAI; check free tiers). Also `pydantic`, `pandas` and `scikit-learn` (kappa). Deploy on Streamlit Community Cloud with the API key stored in its secrets settings.

**Build plan:**
- **Thu night:** register for CAC. Draft 5 scenarios and the rubric (use QPR and teen MHFA materials). Build the Streamlit chat skeleton.
- **Fri:**
  - persona engine with the hidden trust/risk state
  - judge with per-message JSON scores
  - feedback screen
  - the keyword safety check
- **Sat:**
  - "It's real" mode (fixed content)
  - phone-style UI polish
  - crisis-line switch by country
  - deploy
  - **Email a school counselor or psychology teacher to review the rubric** (big credibility if they reply)
- **Sun:**
  - hand-label 50 replies and run the calibration (report the numbers)
  - classmate survey and user tests
  - record the video, write the README
- **Mon by 9 am CT:** submit.

**Video hook:** a phone screen. A text pops up: *"honestly idk why i even bother anymore."* Cursor blinks. *"What would you text back? One in five high schoolers seriously considered suicide last year, and the first person they tell is usually a friend. Not a counselor. Us. Nobody teaches us what to say. So I built Unsent."*

**Risks and how to handle them:**
- Sensitive topic: follow safe-messaging guidelines, avoid methods, put 988 on every screen, and say clearly that the AI never counsels real people. "Real" mode has no AI.
- Kognito exists: say up front "scripted multiple choice vs real texting."
- AI judge errors: the calibration numbers are your answer.

---

## #2 CareCrew: dementia behavior coach for teens who help care for a grandparent

**Pitch:**
- **The problem it covers:** Grandma asks the same question 14 times, won't bathe, or gets agitated every evening.
- **What you do:** describe what happened in your own words, or by voice.
- **What you get back:**
  - likely triggers
  - responses backed by research, with citations
  - patterns over time
  - a one-page summary for the next doctor visit
- **Teen mode** explains things simply and helps you write a school-accommodation letter.

**The problem:**
- **Nearly 13M unpaid dementia caregivers gave more than 19B hours in 2025**, and 59% report high stress ([Alzheimer's Association 2026](https://www.alz.org/facts-and-figures)).
- **At least 5.4M US children care for an adult at home.**
  - Caregivers aged 15–18 spend 42 fewer minutes a day on education ([MPR/KFF](https://www.mprnews.org/story/2025/06/04/kff-role-reversal-millions-of-kids-are-caregivers-for-elders-why-their-numbers-might-grow)).
  - Rhode Island now requires every middle and high school to have a policy for students who are caregivers.

**The method:**
- It uses **DICE** (Describe, Investigate, Create, Evaluate), a method for handling dementia behaviors.
- In a **2026 randomized trial**, WeCareAdvisor, a DICE app, lowered caregiver distress ([UC Davis](https://health.ucdavis.edu/news/headlines/app-helps-caregivers-manage-dementia-related-behavioral-symptoms-improves-well-being/2026/08)).
- That app is iPad-only, has no AI, and only study participants can use it.

**CAC precedent:**
- About 13 dementia or caregiver winners since 2023. Examples: CareLoop, Memory Buddy, Care Companion TX-16 2024, and MemoryLane CA-36 2025.
- **None does behavior coaching, and none is for teen caregivers.**

**AI and technical challenge:**
- The AI pulls structured details from messy free-text incidents (behavior, time, what happened before).
- Its suggestions come only from NIA, Alzheimer's Association and DICE texts, and **each suggestion must cite a passage that supports it, or it's rejected.**
- pandas finds patterns, like "agitation clusters 4–7 pm after a skipped lunch."
- Hard-coded red flags (a sudden change, wandering, aggression) send you to a doctor, 911, or the 24/7 helpline at 800-272-3900 before the AI says anything.

**Video hook:** *"Grandma asked me the same question 14 times today."* Type it in, get a cited plan, then show the evening heatmap.

**Risk:** this works best if you really do have a grandparent with dementia. Without that, the personal angle is weak. It's also medically sensitive.

---

## #3 Prove $35: getting seniors the SNAP money they're owed

**Pitch:**
- **What you do:** photograph Grandma's pharmacy receipts, Medicare letters and medical bills.
- **What the app does:**
  - finds the medical expenses SNAP lets her deduct
  - calculates how much more food money she'd likely get
  - prints a ready-to-hand-in proof packet for the caseworker, in English or Spanish

**The problem:**
- **Only 48% of eligible seniors get SNAP, compared with 82% of all eligible people** ([USDA ERS](https://www.ers.usda.gov/amber-waves/2022/july/state-snap-policies-unlikely-to-close-participation-gap-between-seniors-and-non-seniors-study-shows)).
- SNAP households with an older or disabled member can deduct medical costs. **Only 14% of senior SNAP households claim it** ([FRAC](https://frac.org/wp-content/uploads/SNAP-SMD-National-Report-1.pdf)).
- **Illinois offers a $185/month standard medical deduction to anyone who proves more than $35/month in costs.** That's where the name comes from. The $185 is FRAC's 2023 figure, so check the current amount on the Illinois DHS site.
- The 2026 Medicare Part B premium alone is about $203/month.
- The deduction exists nationwide under federal rules (7 CFR 273.9(d)(3)); about half the states use a flat "standard" amount like Illinois.

**CAC precedent:** only SNAPApp (NJ-11 2019, a general eligibility checker). **No senior or medical-deduction app has won.**

**AI and technical challenge:**
- The AI reads receipts, Explanation of Benefits forms and Social Security letters, and sorts each expense into allowed or not allowed, with a confidence level.
- **The AI never does the math.** A separate calculator with unit tests, checked against worked examples, computes the benefit.
- You confirm every line, and the app records which document each number came from.

**Video hook:** *"My grandma's $203 Medicare premium is worth about $55–80 a month in groceries she isn't getting."* (Check these figures first.)

**Risks:**
- Less visual than the others.
- The benefit numbers must be checked against Illinois DHS for FY2027.
- It's an estimate, not an official decision.

---

## #4–#10 (details in round 2 unless noted)

**4. Gavel**
- An AI watchdog for any town's council and school board meetings.
- The most original idea overall, with the deepest technical work.

**5. SecondHand Safe**
- Recall check for used baby gear.
- The easiest to build, with the most emotional demo.

**6. IEP Ally**
- A special-education plan explainer and checker under federal special-education law (IDEA).

**7. Aphasia communicator** (new this round, 7.5)
- About 2M Americans have aphasia, mostly after a stroke ([NIDCD](https://www.nidcd.nih.gov/health/aphasia)), and **84.5% of people had never heard the word** in 2016.
- It turns fragments plus context into ranked full sentences that are spoken aloud. Example: "cup… cold… no" at 8 am, talking to your daughter, becomes *"Can you warm up my coffee?"*
- **Downsides:**
  - Related winners exist: CommunAphasia (MA-04 2022) and SpeakEase (GA-07 2025).
  - The research dataset (AphasiaBank) needs a supervising advisor to get access, so testing would rely on made-up examples.

**8. StayCovered**
- Helps people meet the Medicaid and SNAP work requirements that start Jan 1, 2027.
- In Nebraska, 92% of the people who lost coverage at renewal lost it over paperwork.

**9. Letters Home** (new this round, 7)
- For 5.1M kids who've had a parent in prison.
- It looks up the facility's visit, mail and phone rules using the federal prison system's live data (tested), explains them at the child's age, and checks a letter before it's sent. Example: *"FCI Milan rejects stickers."*
- **No CAC precedent.**
- **Downsides:**
  - The federal system covers only about 8% of people behind bars; state prisons and jails would need rules entered by hand.
  - A very sensitive audience.

**10. Shutoff Shield**
- Reads a utility shutoff notice and finds the protections the household has in that state.
- 13.4M electric shutoffs happened in 2024.

---

## Recommendation: build Unsent

1. **The theme** (teen mental health) is the kind that reaches the podium, and **the angle** (training the friend, not treating the patient) is new for CAC.
2. **The AI is essential:** realistic role-play plus scoring of free-form replies can't be done with a database or fixed decision tree.
3. **The best technical-challenge answer of any idea:** a calibrated AI judge with real agreement numbers, a persona that stays consistent, and safety checks that run outside the AI.
4. **No data pipeline to build**, which makes it the most realistic idea to finish polished by Monday.
5. **The most honest story:** you're the audience. Your classmate survey turns that into evidence.

**Backup:** #2 CareCrew if you have a real family connection to dementia, or #5 SecondHand Safe if you just want the safest build.
