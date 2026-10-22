# CAC 2026, round 2: 10 generalized community ideas

*Thu Oct 22, 2026. This replaces the idea list in `CAC_2026_WINNING_IDEAS.md`, whose rules and judging sections still apply.*

*Six parallel researchers vetted 13 candidates. Each one checked the problem with sourced statistics, searched past CAC winners for duplicates (about 1,050 winning app titles from 2023–25 scanned, plus targeted searches back to 2019), and **tested the data APIs live**. Weak ideas were cut: the scam detector (6+ prior winners, including SCAMBIO CA-43 2025), the photo-to-311 router (Pothole Patrol IN-7 2025, CitizenReport PA-5 2023), radon on its own, unclaimed money, broadband, naloxone, ballot explainers, air quality (5 winners), and heat.*

**Requirements every idea had to meet:**
- works in **any US community**
- AI does work the data alone can't
- no CAC winner has done it
- a solo Python developer can ship it by **Mon Oct 26, 11:00 am CT**

**Reminders:**
- Judges are a panel the office recruits (engineers, educators). They are not Foster himself.
- The rubric is originality, UX, and coding skill, plus a scored short answer: "What technical challenge did you face?"

---

## Rankings

| # | App | Problem it solves | Score | CAC precedent |
|---|---|---|---|---|
| 1 | **Gavel** | AI watchdog for any town's council and school-board meetings | **8.5** | none |
| 2 | **SecondHand Safe** | Recall check before you buy or accept used baby gear and goods | **8.5** | none |
| 3 | **IEP Ally** | Special-education plan explainer and compliance checker for parents | **8** | none (teacher-side tool only, FL-11 2021) |
| 4 | **StayCovered** | Medicaid and SNAP work-requirement survival kit (law takes effect Jan 1, 2027) | **8** | none |
| 5 | **Shutoff Shield** | Utility-shutoff notice reader that finds your state's protections | **8** | none |
| 6 | **TapCheck** | "What's in my tap?" for any US address, plus an AI reader for your water report | **7.5** | partial (Maji 2021, Know H2O 2023) |
| 7 | **AppealAid** | Reads a FEMA disaster-aid denial letter and drafts the appeal | **7.5** | none, but IL-11 had a disaster winner in 2024 |
| 8 | **BillCheck** | Medical bill auditor and charity-care finder | **7** | partial (Hospified, HealthBridge) |
| 9 | **AccessCheck Local** | ADA accessibility audit of any town's or school district's website | **7** | none |
| 10 | **Renter Shield** | Flags illegal lease clauses and explains eviction notices by state law | **6.5** | none, but a paid 50-state competitor exists |

---

## #1 Gavel: an AI watchdog for local government ⭐ RECOMMENDED

**Pitch:** Paste any city council, school board or county board meeting. In about 60 seconds you get every decision, vote and dollar amount, each linked to the exact second in the video where it happened. You can subscribe to topics ("property taxes," "my school," "my street") and get results in English or Spanish.

**The problem (sourced):**
- **213 US counties are news deserts** and 1,524 more have only one news source. **136 newspapers closed in the past year**, more than 2 per week, and about **50M Americans** have limited or no local news. [Medill 2025](https://www.medill.northwestern.edu/news/2025/news-deserts-hit-new-high-and-50-million-have-limited-access-to-local-news-study-finds.html)
- **Only 13% of Americans attended (in person or online) even one city council or school board meeting in the past year.** [Pew 2025 engagement topline](https://www.pewresearch.org/wp-content/uploads/sites/20/2026/07/PJ_26.07.16_engagement_topline.pdf)
- Mayoral turnout averages about 20% in the 30 largest cities, and voters 65+ have about **20x** the influence of voters 18–34. [Who Votes for Mayor](https://datasmart.hks.harvard.edu/news/article/map-of-the-month-who-votes-for-mayor-1157)
- A real local example: **IPSD 204 faces a $5.8M gap and is cutting about 20 positions** ([NCTV17](https://www.nctv17.org/?p=178910)), and **D131 (East Aurora) has a $6.8M shortfall** ([Hoodline](https://hoodline.com/2026/09/east-aurora-school-board-approves-272m-budget-with-6-8m-shortfall/)). These decisions happened in public meetings few people watched.

**Why it wins:**
- *Idea:* civic engagement in a contest run by Congress, solving a national problem (news deserts) that shows up in every judge's own town. No CAC winner has done meeting intelligence. The closest are TownLink (CT-2 2025, a resident forum) and Jonesboro 411 (AR-1 2024 runner-up).
- *Coding skill:* this idea has the deepest technical story of the ten (below).
- *Demo:* judges can watch it work on their own town's meeting.

**Existing tools and how Gavel differs:**
- **Citymeetings.nyc** covers NYC only.
- **Hamlet** is paid and sold to cities, not residents.
- **CivicSearch** offers search and alerts, but no extraction of decisions and votes.
- **Documenters** uses paid human note-takers in a limited set of cities.
- Gavel is the only one that is **free, resident-facing, works for any town, and has a citation for every claim**.

**Why the AI is essential:**
- A 2–4 hour meeting is 20,000–40,000 words of messy auto-captions.
- The AI splits it into chunks, then pulls structured fields from each: `{agenda item, motion, vote Y/N/abstain, $ amount, verbatim quote, timestamp}`.
- It then merges the results, translates them, and answers questions.

**The technical challenge for the short answer (all of this really happened during testing):**
1. **Long transcripts:** the transcript is too long for one AI request, so it's processed in pieces and then combined, with each piece keeping its timestamps.
2. **Stopping made-up facts:** every extracted claim must include a verbatim quote that fuzzy-matches (`rapidfuzz`) the transcript inside its cited timestamp window. Claims that fail are dropped. **Measure and report the rejection rate.**
3. **YouTube blocks cloud servers:** live testing hit "RequestBlocked" from a server IP. The fix is to fetch transcripts on your home laptop and cache them as JSON, and to accept an uploaded .srt, .vtt or audio file as a fallback.
4. **Misheard names in auto-captions:** pass in the agenda (Legistar API, tested live for Seattle) as a glossary of correct spellings.

**Data and tools:**
- Transcripts: `youtube-transcript-api`, run from your home IP. It works for normal videos, but council videos were blocked from the cloud during testing.
- Optional: Whisper (local, or the Groq Whisper API) for uploaded audio.
- Optional: Legistar Web API `webapi.legistar.com/v1/{city}/events` for agendas. Coverage varies by city.
- AI: Gemini API (check its current free tier) or Claude API, with structured JSON output.
- App: Python, Streamlit, `rapidfuzz`, `pydantic`. Deploy on Streamlit Community Cloud with the demo meetings pre-cached.

**MVP plan:**
- **Thu night:**
  - Register on the CAC site.
  - Pick 3 demo meetings: an IPSD 204 or D131 board meeting about the budget, an Aurora City Council meeting, and one from another town to show it works anywhere.
  - On your laptop, fetch and save their transcripts.
  - Create the Streamlit skeleton and get an AI API key.
- **Fri:**
  - Chunking, extraction into the schema, combining results, and the citation verifier.
  - Decision cards with clickable `youtube.com/watch?v=…&t=1234s` links.
- **Sat:**
  - "Ask this meeting" Q&A that answers only from cited lines.
  - Topic watchlist matched across meetings.
  - Spanish toggle.
  - "How to speak at the next meeting" card (from the agenda, or the city site link).
  - Upload fallback, then deploy.
- **Sun:**
  - Evaluation: hand-label the decisions in one meeting, then report precision/recall and the rejection rate.
  - Test with 3–5 real people (parents, a teacher).
  - Record the video, write the short answers and README.
- **Mon by 9 am CT:** submit.

**Video hook:** *"Last month my school district talked about cutting $5.8 million and 20 jobs. The meeting was three hours long and posted on YouTube. Do you know anyone who watched it? 87% of Americans didn't attend a single local meeting last year. So I built Gavel."* Then paste the link and watch the decisions appear.

**Your true angle:** you're an IPSD 204 or Aurora-area student. The budget cuts directly affect your school. Before claiming in the video that "nobody you know watched," ask your friends and family whether they did.

**Risks:**
- AI accuracy: the verifier, the "verify at timestamp" links, and disclaimers address this.
- Long-meeting AI cost and wait time: cache results and use a fast model.
- YouTube blocking: pre-cache meetings plus the upload fallback.
- Scope creep: email alerts are a stretch goal, so keep a simple in-app list of followed topics.

---

## #2 SecondHand Safe: recall check before you buy or accept used goods

**Pitch:** Snap the label on a used car seat, crib, stroller or Marketplace listing. The app tells you in seconds whether it's under a federal safety recall and what the free fix is.

**The problem:**
- Only about **6%** of recalled products get returned or fixed, and about **4%** for items under $20. [Kids In Danger](https://kidsindanger.org/wp-content/uploads/2024/09/KID-Recall-Reality-Report.pdf)
- CPSC reported hundreds of recalled infant sleepers (Rock 'n Play) selling on resale sites every month, **93% of them on Facebook**, and sent about 60,000 takedown requests in 13 months. [ABC7](https://abc7ny.com/post/cpsc-calls-on-meta-mattel-to-get-fisher-price-rock-n-play-sleeper/13118930/)
- NHTSA: **997 vehicle recalls covering 29M+ vehicles in 2025.**

**Why the AI is essential:**
- **Of 485 CPSC recalls in 2026, none has a structured model field and only 15 have UPCs.** Model numbers and date ranges sit in free text.
- The AI reads the photographed label (brand, model, manufacture date).
- It extracts affected model and date ranges from the recall text.
- It decides whether there's a match and gives a confidence level.

**Data (tested live):**
- CPSC `saferproducts.gov/RestWebServices/Recall?format=json`
- NHTSA `api.nhtsa.gov/recalls/recallsByVehicle` and the vPIC VIN decoder
- openFDA `food/enforcement` and `drug/enforcement`

**Technical challenge:** fuzzy matching between noisy photos and unstructured government text, with a confidence score and a "can't tell, check X" fallback. Cache all CPSC recalls locally and build an index of the extracted model numbers.

**How it differs from existing tools:** RecallSentry (launched March 2026) scans your home inventory. SecondHand Safe is aimed at the **moment before you buy used**:
- paste a Marketplace link
- a "sweep" mode for thrift stores, daycares and Buy Nothing groups
- car-seat expiration dates
- a polite message to send the seller

**Video hook:** a $20 Marketplace infant sleeper turns red: *"RECALLED: linked to infant deaths."*

**Your true angle:** parents in your area's Buy Nothing or Marketplace groups, or younger siblings or cousins with hand-me-down gear.

**Risks:**
- A false "safe" result: never say "safe," only "no recall found, here's what to check."
- The competitor RecallSentry.

**Why #2 and not #1:** less technical depth than Gavel and a weaker civic angle, but the strongest emotional hook and the easiest of the ten to build.

---

## #3 IEP Ally: a copilot for special-education parents

**Pitch:** Upload your child's IEP (Individualized Education Program, the legal plan a public school writes for a student with a disability). In English or Spanish it explains what the plan says, checks it against federal special-education law (IDEA), flags possible gaps, and prepares your questions for the next meeting.

**The problem:**
- **7.5M students (15% of public school enrollment)** are served under IDEA. [NCES](https://nces.ed.gov/fastfacts/display.asp?id=64)
- **Formal state complaints reached 9,927 in 2023–24**, about 79% above the 10-year average. [CSBA/CADRE](https://blog.csba.org/?p=10030)
- In NYC, **76,000 of 228,000** students with disabilities speak another language at home. [Chalkbeat](https://www.chalkbeat.org/posts/ny/2019/06/06/why-dont-you-learn-english-lawsuit-blasts-nyc-translation-services-for-special-education-families)
- Maine monitoring found **more than 50% of reviewed IEPs out of compliance.**

**Why it's generalized:** **one federal law covers every state**, so the checklist works everywhere.

**Data (tested):**
- The eCFR API returns the federal rule on IEP contents (34 CFR 300.320) with stable paragraph IDs.
- Real sample IEPs downloaded and parsed for testing: Montana, 17 pages; Fontana SELPA, 26 pages. [NASET list](https://www.naset.com/ieps-from-around-the-country/)

**AI and technical challenge:**
- The AI maps IEPs from different states into standard sections.
- A rules engine checks the required elements and deadlines.
- An AI judge scores whether each goal is measurable (baseline, criterion, method, timeframe).
- **Every flag must quote the IEP word for word and cite the regulation paragraph.**
- Names and other identifying details are redacted locally before any AI call.
- Evaluate against hand-labeled sample IEPs.

**Existing tools:** Undivided (paid), IEP Says, and AiEP (free, SF). None advertises regulation-cited compliance checks or meeting questions tied to the specific gaps it found.

**Video hook:** *"This is a real 26-page IEP. Parents get about a week to understand it before signing. Watch."*

**Risks:**
- Your personal angle is weak unless you actually know a family in special education.
- Accuracy: always say "possible gap, ask your team."

---

## #4 StayCovered: Medicaid and SNAP work-requirement kit

**Pitch:** The new federal law takes effect **January 1, 2027**. In 5 minutes it tells you whether you're exempt, what counts toward your hours, what proof to keep, and what to do if you get a notice. English and Spanish.

**The problem:**
- **Medicaid:** expansion adults ages 19–64 need **80 hours a month** of work, school, training or volunteering, or **$580 a month** in income. [CMS interim final rule, Jun 3 2026](https://www.federalregister.gov/documents/2026/06/03/2026-11094/medicaid-program-community-engagement-requirement-for-certain-individuals), [CHCS summary](https://www.chcs.org/resource/a-summary-of-national-medicaid-work-requirements/)
- **CBO: about 5.2M people lose Medicaid by 2034. CMS estimates 2.3M in 2027 alone.**
- **Nebraska went live in May 2026, and 92% of renewal losses were for "failing to provide requested information."** That is paperwork, not ineligibility. [Georgetown CCF](https://ccf.georgetown.edu/2026/09/30/nebraska-releases-first-data-on-medicaid-work-reporting-requirement-as-expected-coverage-losses-start-to-mount-due-to-red-tape/)
- **SNAP:** the work-rule age limit rose to 64; exemptions for veterans, homeless people and former foster youth were removed. [USDA FNS](https://www.fns.usda.gov/snap/obbb-abawd-exemptions-implementation)

**AI and technical challenge:**
- Turn the legal text into a **deterministic decision tree** that you can test.
- The AI's job is limited to reading pay stubs, doctor's notes and state notices, and mapping a person's free-text situation to exemption categories.
- **The rules make the decision, never the AI.** Every answer cites the statute.

**Existing tools:** Fortuna Health (sold to health plans) and state portals, plus CMS's "Emmy" app (in development). No free tool works for any state from the person's side.

**Video hook:** *"In Nebraska, 92% of the people who lost Medicaid at renewal didn't lose it because they weren't working. They lost it over paperwork. On January 1, every state starts."*

**Risks:**
- State rules are still being written.
- A wrong "you're exempt" answer is harmful, so show confidence and "confirm with your caseworker."
- Politically charged: frame it as "comply and stay covered."
- Little public data, so less data work to show judges.

---

## #5 Shutoff Shield: reads a utility shutoff notice

**Pitch:** Photograph the shutoff notice on your door. The app finds the protections you have in your state (medical-certificate delays, winter moratoriums, payment plans, LIHEAP) and fills in the letters for you.

**The problem:**
- **EIA's first national dataset: 13.4M electric and 1.7M gas shutoffs in 2024, and 94.9M final notices.** [EPI](https://energyandpolicy.org/thirteen-million-electric-shutoffs-as-industry-posts-record-profits/)
- **1 in 6 families are behind on energy bills**, owing about $21B. LIHEAP is proposed for elimination in the FY27 budget. [NEADA](https://neada.org/wp-content/uploads/2026/07/housetestimonyFY27.pdf)
- Timely: you'd submit right as winter starts.

**AI:** reads the notice (deadline, amount, utility), reasons over the state's rules using retrieval over rule documents, and drafts a doctor letter and a payment-plan request.

**No CAC precedent.**

**Risks:**
- Curating rules for 50 states: do 5 states deeply and say so.
- The state-protection tables (LIHEAP Clearinghouse) couldn't be reached during testing.

---

## #6 TapCheck: "What's in my tap?" for any US address

**Pitch:** Enter your address. The app finds the exact water system serving you, shows its health violations separately from paperwork violations, PFAS results and lead results, then reads your utility's annual water-quality report (CCR) and explains it in plain English or Spanish.

**The problem:**
- About **22M** people drank water from systems with health-based violations.
- **EPA's new estimate is 4.0M lead service lines** (Nov 2025).
- **1,739 systems serving about 80M people had a PFOA or PFOS sample at or above 4 ppt** (computed from EPA's UCMR 5 PFAS testing data).
- Lead-line notices to customers start **Dec 1, 2026**.

**Data (tested; the full chain works):**
- Census geocoder → EPA Water System Boundaries layer (gives the system ID, PWSID) → Envirofacts violations and lead 90th percentile, ECHO, and UCMR 5.
- Tested on Naperville IL0434670, Chicago, Flint and LA.

**AI:** extracts the CCR's PDF tables, then **cross-checks the AI's numbers against the federal records and flags any mismatch.** A great technical story.

**Why #6:** a few water winners already exist (Maji, Know H2O), EWG's database is well known, and CCRs often can't be fetched automatically (user upload instead).

---

## #7 AppealAid: FEMA disaster-aid denial and appeal helper

**Pitch:** Photograph your FEMA denial letter. The app explains why you were denied, whether it's fixable, which documents to gather, and drafts your appeal before the 60-day deadline.

**The problem:**
- **GAO: 1.7M of 4.4M applicants (39%) found ineligible in 2016–18.** The top reasons include missing documents and missed inspections, which are often fixable.
- Only about **4–6%** of denied applicants appeal (SBP, unverified).
- Illinois example: of the DR-4819 renter registrations, **65.6%** were approved.

**Data (tested):**
- OpenFEMA DisasterDeclarationsSummaries (gives the county's registration deadline).
- Housing Assistance data by ZIP.
- The registrations dataset is very slow, so cache it offline.

**Why #7:** IL-11's 2024 winner was disaster-related (PrepShield). There are no real denial letters to test with, so you'd have to make synthetic ones. And unless there's an active disaster, the demo feels less urgent.

---

## #8 BillCheck: medical bill auditor and charity-care finder

**What it does:**
- AI reads an itemized bill.
- Compares each charge with Medicare rates (an ER level-5 visit averages **$1,232 billed vs $170 allowed**).
- Checks whether the hospital is a nonprofit legally required to offer financial assistance (**2,939 nonprofit hospitals** in CMS data).
- Drafts a letter.

**The problem:** US medical debt is at least **$220B** (KFF).

**Data (tested live):** CMS Hospital General Information, the CMS Medicare-by-code API, and the ProPublica Nonprofit Explorer API.

**Why #8:**
- The popular claim that "80% of bills have errors" has no solid source.
- It's close to InsureLit (IL-11 2025).
- It can't detect upcoding without medical records.

---

## #9 AccessCheck Local: ADA accessibility audit for any town's website

**What it does:** scans any town's or school district's .gov site with automated accessibility checks (axe-core via Playwright). The AI judges what those rules can't: whether alt text is meaningful and whether PDF forms are usable. It writes plain-language fixes for the town's ADA coordinator.

**Data:** the CISA .gov registry, tested: **16,923 domains** (9,212 cities, 75 school districts).

**Timing:** the DOJ pushed the ADA Title II web deadline to **Apr 2027** for entities serving 50k+ people.

**Why #9:** strong commercial competitors exist (WAVE, Silktide), and the deadline moving away from now weakens the urgency.

---

## #10 Renter Shield: flags illegal lease clauses and explains eviction notices

**What it does:** AI pulls clauses from a lease or eviction notice and checks them with a rules engine against the **LSC Eviction Laws Database** (downloaded and tested: 60 jurisdictions, 168 columns with citations).

**The problem:** about 3.6M eviction filings a year; about 3% of tenants have lawyers vs about 80% of landlords.

**Why #10:**
- The data is frozen as of 2021 and has no security-deposit or landlord-entry columns.
- LeaseGuard already covers all 50 states for $9.99.
- The highest legal-advice risk of the ten.

---

## Final recommendation

**Build #1, Gavel.**

1. **Originality:** no CAC winner has done it, and it works in every judge's own town.
2. **Coding skill:** it has the strongest technical-challenge answer of the ten (long-transcript processing, the quote-verified citation check with a measured rejection rate, the YouTube-blocking fix). That is exactly what the scored short answer and the coding criterion reward, and what separates you from the 56% of entries that only call an AI API.
3. **Civic fit:** it's a civic-engagement tool in a contest run by Congress.
4. **Your true story:** your own district's budget cuts happened in a meeting almost nobody watched.

**Backup: #2 SecondHand Safe.** Switch to it if Gavel's extraction isn't working by **Friday night**. It's the easiest to build and has the most emotional demo.

Same submission checklist as before:
- [ ] Confirm your district from your street address
- [ ] Register today
- [ ] Core working by Fri night, deployed by Sat
- [ ] Real users and evaluation numbers on Sun
- [ ] Video under 3:00, hook in the first 15 seconds
- [ ] Disclose AI-tool use
- [ ] **Submit by 9 am CT Monday**
