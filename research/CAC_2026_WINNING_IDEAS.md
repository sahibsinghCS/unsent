# Congressional App Challenge 2026: what wins, and 10 ideas for IL-11

*Research date: Thu Oct 22, 2026. Sources: about 25 primary pages (congressionalappchallenge.us, foster.house.gov, other House offices, City of Aurora, IEMA, USGS/NOAA, Census). 24 of 25 claims passed 3-reviewer adversarial checks. The data endpoints were tested live today.*

---

## 0. Read this first

| | |
|---|---|
| **Deadline (IL-11)** | **Mon Oct 26, 2026, 12:00 pm EDT = 11:00 am Central.** That leaves ~3.5 days, not 5. Some districts close at 8 pm; **IL-11 closes at noon ET.** Plan to submit by **9 am CT Monday.** [foster.house.gov/appchallenge](https://foster.house.gov/appchallenge) |
| **Your district** | **ZIP 60502 is split between IL-11 (Foster) and IL-14 (Underwood).** Enter your exact address at [house.gov/representatives/find-your-representative](https://www.house.gov/representatives/find-your-representative) before you register. Everything below still works if you turn out to be in IL-14: both districts cover parts of Aurora. |
| **Submit** | Register and submit at [congressionalappchallenge.us](https://www.congressionalappchallenge.us). You need: the source code (a GitHub link), a **1–3 min public YouTube video**, and the short answers. |
| **Eligibility** | The app must be built Oct 30 2025 – Oct 26 2026. Any platform is allowed, and Python web apps are fine. Solo entries are fine (teams of up to 4). If you used AI tools, disclose it; AI cannot be the entire technical work. |

### How judging works
Each district has its own panel, usually local engineers, teachers and tech people picked by the congressional office. Judges watch your video, read your short answers, and may look at your code. They score you on three things:
1. **Quality of idea:** creativity, originality, and whether it solves a real problem.
2. **Implementation:** UX and design.
3. **Coding skill:** text code beats block code, and judges check that you actually understand the tools you used.

One short answer literally asks **"What technical challenge did you face and how did you solve it?"** and it gets scored. So the app needs at least one real engineering problem you can explain, not just a call to ChatGPT. [CAC judges page](https://www.congressionalappchallenge.us/get-involved/judges/)

### Video requirements
The video must state:
- your name
- the app name
- a one-sentence purpose
- the target audience
- the languages and tools you used
- the app working on screen
- what you learned

Keep it **under 3:00**. Judges often decide in the **first 30 seconds**, so show the problem immediately. [Khanna office rules](https://khanna.house.gov/services/congressional-app-challenge), [Lumiere](https://www.lumiere-education.com/post/winning-the-congressional-app-challenge-everything-you-need-to-know)

---

## 1. What wins: evidence

### IL-11 (Foster) winners
| Year | App | What it does | School |
|---|---|---|---|
| 2025 | **InsureLit** | Explains health coverage and routes uninsured people to free clinics and Medicaid | Metea Valley (IPSD 204), solo |
| 2024 | **PrepShield** | Emergency preparedness | Bolingbrook HS, 9th grade, solo |
| 2023 | **DermiDetect** | AI skin-symptom analysis | IMSA, solo |
| 2022 | **QuizMania** | Free quiz *website* (features other sites charge for) | middle schoolers |
| 2021 | **What Bit Me?** | Bug-bite identification and bed-bug checks for hotels | Metea Valley, team of 4 |

**Pattern:** a practical health, safety or access tool for ordinary residents, plus a personal "I saw this gap" story. Solo winners three years in a row. Your competition includes IMSA and IPSD 204 students, so expect a stronger field than average.

### Nearby Illinois winners (2023–25)
- **Health/AI:** CerebraX (glioblastoma AI, IL-8), Oculare AI (eye screening, IL-5), HeadacheWise (migraine + Gemini, IL-6), HAAL (teen mental health, IL-14)
- **Civic/food:** Bridge 2 Meal (food rescue, IL-14 2025), BeeKind (volunteer hours, IL-10)
- **Safety:** SafetyQuest (IL-8)
- **Inclusion:** PIE (disability inclusion, IL-10)
- **Environment:** EcoSense (trash classifier, IL-14)
- **Education:** StudyHive, QuickLearn, ConQuest, QuizMania. Study apps are very crowded in Illinois.

### National 2025 patterns ([2025 winners list](https://www.congressionalappchallenge.us/2025-winners/))
- **What keeps winning: a specific local group of people plus a specific local data source.**
  - AK Bush Weather: risk scores for Alaska bush pilots
  - Hurricane Helper: Florida
  - Find My Food Drive: Roosevelt, NY
  - TownLink: a CT town council
  - Civic AI Action Hub (NY-25): a *web app* that turns local environmental data into neighborhood projects
  - LeftoSense (CA-19): a *website* that beat 44 apps
- **Saturated** (avoid, or you need a sharp twist):
  - photo-based AI disease detectors (skin cancer has won in at least 4 districts)
  - mental-health/mood trackers
  - study and quiz apps
  - recycling classifiers
  - financial-literacy games
  - pill reminders
  - generic "AI tutor"
- **AI alone doesn't stand out:** about 56% of 2025 entries used AI, and about 70% were civic/social-good. What sets you apart is **real local data and a real user**, not the fact that you used AI.
- **A small app that works beats an ambitious one that breaks.** How finished it is matters.

### Rep. Bill Foster: what lines up with him
- **The only PhD physicist in Congress**, formerly at Fermilab. He defends Fermilab, Argonne and the NSF budget. Science framing lands with him.
- **Secured $1.092M for Aurora's remaining lead service lines** in the FY26 Community Project Funding (Mar 2026), plus lead-line money for Crystal Lake and Wauconda. [press release](https://foster.house.gov/media/press-releases/foster-delivers-over-163-million-11th-district-community-project-funding)
- **Notario fraud bill** (Protecting Immigrants from Legal Exploitation Act, Jul 21 2026). He also wrote a letter on poor USCIS correspondence (Aug 2026), and his office reports a surge in immigration casework.
- He chaired the Financial Services **AI Task Force** and has an AI fintech-security bill (Sep 2026). He also focuses on digital identity.
- FY27 requests include Metra signage, Woodridge water mains, and St. Charles flood work.

### Problems in IL-11 backed by real, live data
| Problem | Evidence | Data you can pull now (checked live) |
|---|---|---|
| **Lead water pipes (Aurora)** | **14,988 lead service lines.** Action Level Exceedances in 2025 and again in 2026; the 90th percentile hit 43 ppb in one round (Fox 32) | **Address-level ArcGIS API.** `services1.arcgis.com/79UxTxnBeBW8JHY4/.../WaterServiceMaterialInventory_view/FeatureServer/0`, about 50k rows with `ServiceAddress, IsLead, StreetSide/HouseSideMaterial, LeadServiceReplacedAtThisLoc, WARD`. Naperville also has one: `portal.naperville.il.us/arcgis/rest/services/Water/LeadService/FeatureServer/0` |
| **Radon** | **In ZIP 60502, 1,119 of 3,980 tested homes (28%) are at or above EPA's 4.0 pCi/L action level** (avg 3.29). Radon is EPA's #1 cause of lung cancer in non-smokers. | **IEMA ArcGIS API:** `services2.arcgis.com/QUAsjBqieHEMNnZW/.../Radon_Full/FeatureServer/0`, 544k tests statewide. **Rows include home addresses, so publish only ZIP or hex-grid aggregates.** |
| Spanish-language access | **28.3% of Aurora households speak Spanish; 7.3% are limited-English** (ACS 2024) | Census Reporter API (no key), table C16002 |
| Immigration and notario fraud | Foster's July 2026 bill; Operation Midway Blitz enforcement in Aurora (2025) | Fraud-warning lists from the Illinois AG; DOJ EOIR accredited-representative roster (format not yet verified) |
| 311 service equity | myAurora 311 open-data portal | 311 requests: 23k rows with `DaystoClose`, `ZipCode`, `CategoryName`. Ward polygons available. |
| Fox River flooding / sewer overflows | Combined sewers back up into basements; minor flood warning Apr 2026 | USGS 05551540 (Montgomery), real-time; NWS gauge MNGI2 flood stages; FEMA NFHL flood-zone API |
| Traffic safety (Rt 59) | Pedestrian killed near Fox Valley Mall, Feb 2025 | Aurora Police Combined Traffic layer, Police Incidents (83k) |
| School budgets | D131 $6.8M shortfall; IPSD 204 $5.8M gap, about 20 positions cut | District budget PDFs |
| Food insecurity | About 61k Kane Co. SNAP recipients; pantry surges in fall 2025 | Weak: no NIFB API; the city pantry layer is stale (2020) |
| Data centers and power bills | Aurora has 5 data centers and a 180-day moratorium; ComEd demand could double by 2040 | Weak: mostly news and reports |

---

## 2. The 10 ideas, ranked

Scoring factors: verified data, IL-11 winner pattern, Foster fit, originality, whether it can be built solo in ~3.5 days, and how strong the technical-challenge story is.

### #1. **Unseen**: the invisible-hazard check for Aurora homes ⭐ RECOMMENDED
**Pitch:** Type your address and see, in English or Spanish, whether your home has a lead water pipe, how bad radon is in your area, and whether you're in a flood zone. You get a step-by-step plan for what to do about each one.

- **Problem and who it hurts**
  - 14,988 Aurora homes have lead service lines, and the city exceeded the lead action level in both 2025 and 2026.
  - There is no safe blood lead level for children.
  - In 60502, 28% of tested homes are over the radon action level, and most homes have never been tested.
  - The people at highest risk are renters, Spanish-speaking families (28% of households) and parents of young kids. They are the least likely to find a city ArcGIS map or understand "gooseneck" and "pCi/L."
- **Why it scores**
  - *Idea:* it's hyper-local and life-safety, and nobody in IL-11 has done it. Foster personally funded Aurora lead-line replacement, and radon is literally radioactive decay (U-238 → Ra-226 → Rn-222), which suits a physicist.
  - *Implementation:* one search box, three color-coded cards, a bilingual toggle.
  - *Coding:* you merge 3–4 real government datasets. You get a strong technical-challenge answer (below).
- **Why it isn't overdone:** this is not "AI detects X from a photo." It's a real civic data product. The pattern of local data plus a specific local group is what wins nationally (AK Bush Weather, Hurricane Helper).
- **True angle you can claim:** you live in 60502 on Aurora city water. You looked up your own house and your neighbors' houses (say what you actually found). Tell the judges you were surprised by how hard the city map was to use, and that most of your neighbors had no idea. **Get 3–5 real people** (family, a Spanish-speaking classmate's parent, a neighbor) to try it, and quote them in the video. That's your real story. You don't need to invent one.
- **Technical challenge for the short answer (it's real):**
  1. **Address matching:** users type "56 East Galena Boulevard" but the city stores "56 E GALENA BL." Solve it by normalizing with `usaddress` plus fuzzy matching with `rapidfuzz` against a cached copy of all 50k records.
  2. **Coordinate systems:** the lead data is in Illinois State Plane (EPSG:3435) and the radon and FEMA data are in WGS84. Convert with `pyproj`.
  3. **Privacy:** radon rows contain private home addresses, so you aggregate to ZIP or hex grid and never show individual results.
  4. **Reliability:** the FEMA API drops connections. Solve it with retries and caching.
- **MVP (3.5 days)**
  - **Thu night:** confirm your district and register. Download the full lead inventory to a local parquet file (page through with `resultOffset`). Pull radon stats grouped by ZIP for the Aurora-area ZIPs.
  - **Fri:**
    - Streamlit app with an address search box and fuzzy matching.
    - Lead card: street-side and house-side material, whether it was replaced, gooseneck.
    - Radon card: % of homes over 4.0 in your ZIP, the average, and the number of tests.
  - **Sat:**
    - FEMA flood-zone card.
    - A rule-based action checklist for each result: flushing, NSF/ANSI 53 lead filters, how to request the city's free replacement, how to get a radon test, mitigation basics.
    - Spanish strings (have a native speaker check them).
    - A ward map of remaining lead lines (folium), which works as an equity view for city council.
    - Deploy to Streamlit Community Cloud.
  - **Sun:** user tests with 3–5 real people. Record the video, write the short answers and README, and push to GitHub.
  - **Mon 9 am CT:** submit.
  - *Stretch, only if ahead:* a "Why is radon in my basement?" physics explainer, or an LLM Q&A answering only from city and EPA documents, with citations.
- **Stack:** Python, Streamlit, `requests`, `pandas`/`pyarrow`, `rapidfuzz`, `usaddress`, `pyproj`, `folium` + `streamlit-folium`.
  - Data: Aurora `WaterServiceMaterialInventory_view`, IEMA `Radon_Full` (aggregated), FEMA NFHL layer 28, and optionally USGS 05551540.
  - Deploy on Streamlit Community Cloud (free).
- **Video hook (first 15 sec):** *"Right now, almost 15,000 homes in Aurora get their drinking water through a lead pipe. In my ZIP code, more than 1 in 4 tested homes has radon above the EPA's danger line. You can't see, smell, or taste either one. So I built Unseen."* Then type your own address live.
- **Risks**
  - Medical or legal accuracy: show "Not a substitute for testing," link official sources, and never say water is "safe."
  - Scope creep: lead and radon are the MVP. Flood is a bonus.
  - Data freshness: show the date the data was last updated.
  - Radon privacy: aggregates only.

### #2. **Ayuda Legítima**: notario-fraud shield (bilingual)
**Pitch:** Before you pay someone to help with your immigration case, check in 30 seconds whether they're legally allowed to give that help, and learn the red flags of notario fraud.
- **Problem:** in Latin America, "notario público" means a lawyer; in the US it doesn't. Fake notarios charge thousands and wreck cases. **Foster introduced a bill on exactly this in July 2026** and reports a surge in immigration casework. 28% of Aurora households speak Spanish.
- **Why it scores:** it lines up with the representative's own bill, which is rare. It serves a large local population, and nobody has entered it before.
- **MVP:**
  - A Spanish-first wizard: "What did they promise? What did they charge?" leads to a risk score with red flags explained.
  - A lookup against the DOJ EOIR recognized organizations and accredited representatives roster (parse the PDF or list into a table).
  - A link to the Illinois ARDC lawyer search.
  - A map of free, legitimate legal-aid organizations near Aurora.
  - A one-tap "report fraud" guide.
- **Technical challenge:** parsing the government roster and fuzzy-matching names and organizations.
- **Hook:** *"In Mexico, a notario is a lawyer. In Aurora, it can be a scam that gets you deported."*
- **Risks:**
  - **Verify the EOIR roster format first** (the URL I tested returned 404, so find the current one).
  - Must never give legal advice.
  - Sensitive population: no accounts, no data stored. Say so in the video.
  - Your angle is weaker unless you truly know affected families. Talk to a local legal-aid group or a Spanish-speaking family to make it real.

### #3. **311 Pulse**: is Aurora fixing every neighborhood equally?
**Pitch:** An equity dashboard on Aurora's own 311 data. How long do potholes, streetlights and code complaints take to fix in each ward? Plus a bilingual "report it right" helper.
- **Data:** myAurora 311 layer, 23k requests with `DaystoClose`, `ZipCode`, `CategoryName`, plus ward polygons.
- **Why it scores:** civic transparency, and judges see real data science (medians, outliers, maps), not a demo. TownLink won CT-2 in 2025 with a similar idea.
- **MVP:** load, clean and aggregate the data; map median days-to-close by ward and category; show trends over time; add a "your block" view and a bilingual guide for filing a request (category picker plus a photo checklist).
- **Technical challenge:** messy timestamps, open vs. closed requests (censored data), and making the comparison fair.
- **Hook:** *"If a streetlight goes out on my street, it gets fixed in X days. Across town, it takes Y."* Find the real numbers first.
- **Risks:**
  - The data may show no disparity. That's fine: frame it as transparency.
  - It's less emotional than health or safety.

### #4. **ScamShield Senior**: AI scam checker built for grandparents
**Pitch:** Grandma pastes a suspicious text or email, or describes a phone call. The app explains in plain language (or Spanish) whether it's a scam, and with one tap texts a family member.
- **Fit:** Foster's AI and fintech-security work. Naperville police have warned about grandparent and jewelry-swap scams. Gold-bar scams are a 2026 trend.
- **Differentiator:** combine rule-based red-flag detection (urgency, gift cards, crypto/gold, "don't tell anyone") with an LLM explanation. Show *which words* triggered the flag, so it's not a black box. Large font, senior-first UX. Test it with real seniors.
- **Technical challenge:** a hybrid classifier plus an explanation layer, and evaluating it on a labeled set of 50 real or fake scam messages (report precision and recall).
- **Risks:** scam detectors are a moderately crowded category, and false negatives are dangerous.

### #5. **Aviso Claro**: decode the government letter you got
**Pitch:** Take a photo of a confusing government letter (USCIS notice, IRS notice, SNAP recertification, the city water notice). The app explains in Spanish or English what it is, the deadline, and the next step. Nothing is stored.
- **Fit:** Foster's August 2026 letter on poor USCIS correspondence, plus 7.3% of households being limited-English.
- **MVP:** OCR (`pytesseract`) or vision LLM, then structured extraction (doc type, deadline, required action, phone number), then a plain-language card with a calendar reminder.
- **Technical challenge:** structured extraction with validation, plus privacy-by-design (in-memory only).
- **Risks:**
  - LLM errors on high-stakes documents: always show the original text, give a confidence level, and say "call this number."
  - It's close to the InsureLit-style "navigator" pattern that won IL-11 in 2025, which cuts both ways.

### #6. **BudgetClear 204/131**: ask your school district's budget anything
**Pitch:** Parents ask "Why are you cutting 20 positions?" and get answers sourced from the district's actual budget documents, in English or Spanish, with page citations.
- **Data:** the IPSD 204 ($5.8M gap) and D131 ($6.8M shortfall) budget PDFs.
- **Technical challenge:** RAG with real citations. PDF table extraction (`pdfplumber`) and chunking, retrieval, and an answer that must quote the page or it refuses. That's a strong coding-skill story.
- **Risks:**
  - Politically sensitive, so stay neutral and stick to facts.
  - Your angle is strong if you attend IPSD 204 or D131.

### #7. **SafeCross 59**: the walking-safety map for students
**Pitch:** A map of where crashes and pedestrian incidents actually happen near schools and along Route 59/Ogden, and the safest walking or biking route to your school.
- **Data:** Aurora Police Combined Traffic and Police Incidents layers; IDOT crash data. OSM routing via `osmnx`.
- **Technical challenge:** spatial hotspot detection (kernel density or DBSCAN) and weighted routing that avoids hotspots.
- **Hook:** the pedestrian killed near Fox Valley Mall in February 2025.
- **Risks:** more data cleaning, and routing takes time. Cut routing if you're behind.

### #8. **Fox Rising**: basement-flood early warning
**Pitch:** Live Fox River level against flood stages, rain-driven sewer-backup risk, and whether your address is in a FEMA flood zone. Shows an "act now" checklist when the river nears 13 ft.
- **Data:** USGS 05551540 real-time, NWS MNGI2 stages (action 13, minor 13.5, moderate 15, major 16 ft), FEMA NFHL. All verified live.
- **Fit:** FY27 flood funding for St. Charles; good science and data visuals.
- **Risks:**
  - **Overlaps PrepShield (IL-11 2024 winner)**, which hurts originality.
  - With no flood happening this week, the demo is less dramatic.

### #9. **Comida Cerca**: private, bilingual food help finder
**Pitch:** Find food pantries open *right now* near you. A 60-second SNAP/WIC eligibility screener with no account, no name, no location stored.
- **Fit:** about 61k SNAP recipients in Kane County; pantry surges in fall 2025; families afraid to go out during the enforcement surge.
- **Risks:**
  - **Weak data:** no NIFB API and a stale city layer, so you'd build the pantry list by hand.
  - Overlaps Bridge 2 Meal (IL-14 2025) and the general navigator pattern.

### #10. **WattWatch**: what are data centers doing to my electric bill?
**Pitch:** Enter your ComEd bill and see how data-center growth, capacity prices and your own usage shape it, with the physics explained.
- **Fit:** Foster's science and energy focus; Aurora's 5 data centers and its moratorium.
- **Risks:**
  - Little open data, so it ends up mostly explanation.
  - Hard to show a clear user need in 3 days.
  - The lowest-scoring idea on this list.

---

## 3. Recommendation: build **Unseen** (#1)

It's the only idea that has all of these:
- **verified, address-level, live government data** for exactly your ZIP
- a **current, documented crisis** (lead exceedances in 2025 and 2026)
- the **representative's own funding** behind the same problem
- a **physics hook** for a physicist congressman
- a **true personal angle** (your own home and neighbors)
- a **real technical challenge** for the scored short answer
- a scope one person can ship in Python by Sunday

If it's done well, it fits IL-11's winning pattern (practical safety and access tools: PrepShield, InsureLit) without copying it.

**Fallback:** if you'd rather do an immigrant-access project, #2 Ayuda Legítima has the best Foster alignment of any idea. Check the roster data first.

### Winning checklist
- [ ] Confirm your district by street address. Register on congressionalappchallenge.us **today**.
- [ ] Working core (search → result cards) by Fri night; deployed by Sat night.
- [ ] 3–5 real users tested; write down their reactions.
- [ ] Video under 3:00. Problem shown in the first 15 seconds, then a live demo on your real address. State your name, app name, one-sentence purpose, audience, languages/tools, and what you learned.
- [ ] Short answer on the technical challenge: address matching, coordinate projection, privacy aggregation.
- [ ] Disclose AI-tool use honestly.
- [ ] Clean, commented code and a README on GitHub.
- [ ] **Submit by 9 am CT Monday** (the cutoff is 11:00 am CT).
- [ ] Use the same project for the other hackathon.

---

## Open questions / caveats
- Foster's 2026 page: confirm the exact short-answer questions and the AI-disclosure wording.
- IL-11 entry counts and runner-up apps weren't found, so how strong the field is is inferred (IMSA and IPSD 204 schools).
- The DOJ EOIR roster URL needs re-finding (for idea #2).
- Aurora's lead inventory classification can change. Show the dataset's last-edit date in the app.
- A note on honesty: you don't need a made-up story. "I live here, I looked up my own house, here's what I found, here's who tested it" is stronger and can be checked. Offices and local press do follow up with winners.
