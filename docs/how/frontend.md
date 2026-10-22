# The app (frontend)

*Owner: frontend lane. Plain language, so Sahib can explain every part to a judge.*

## What it does

The frontend is everything you see and tap. It's a website that works like a phone app:

| Screen | Address | What happens there |
|---|---|---|
| Landing | `/` | A phone mockup, the one-line pitch, three feature cards, the CDC "1 in 5" stat |
| Scenario picker | `/practice` | Five friends to text (name, age, situation, "open" or "guarded"). Picking one shows a **content warning** first |
| Chat | `/chat/:id` | iMessage-style texting with typing dots, several bubbles in a row, **"Seen"** when trust falls too far, a live **trust graph**, the **disclosure ladder** (0 surface → 4 open to help) and **skill chips** |
| X-ray mode | toggle in the chat | Under each of your messages: the Guardian's decision and **latency in ms**, the skill detector's probabilities as bars, and **the trust math** (`+12 validated · −2 decay = +10`). Under the friend's: **who wrote the words** ("AI, verified ✓", "Reviewed line" or "Fallback"), the reaction and the line id |
| Feedback | `/feedback/:id` | 7-skill **radar chart**, summary, **"This is where you lost them"**, missed opportunities, every message with **green/red word highlights**, "uncertain" tags and a **verified rewrite** |
| Rewind + branches | in the chat | Tap one of your messages → **Rewind to here**. The branch drawer shows every attempt as a tree with trust at each step |
| What-if | `/whatif/:id` | Better replies simulated forward, side by side, with an overlay chart and a clear **Simulated** label |
| Real mode | `/real` | **No AI.** Fixed steps, big **Call 988 / Text 988** buttons, the emergency number, a country picker. **Works with the server down** |
| Transparency | `/how` | Pipeline diagram, **"The AI is only the voice"** (what OpenAI does vs what our code decides, plus the live LLM status), component status, measured numbers, what the AI does and doesn't do, privacy, and a **Try the Guardian** box |
| Privacy, 404 | `/privacy`, anything else | Plain-language privacy promises; a friendly not-found page |

On every screen: an **"I need help now"** button (top right), and a footer that says "practice tool, not a crisis service · 911 · 988". After each session the app asks **"How are you feeling after that?"**, and 😔 shows resources.

## How it works

**Stack:** React 18 + TypeScript, built with Vite, styled with Tailwind CSS, routing with react-router, charts with Chart.js, tests with vitest + Testing Library, screenshots with Playwright. No CDNs, fonts or trackers are loaded at runtime. The build is plain files that the FastAPI server hosts.

**Folder map (`frontend/src/`):**
```
api/         client.ts (the only code that calls the server), types.ts (generated from the API's OpenAPI schema), models.ts (friendly names)
i18n/        en.json, es.json (every UI string) + index.tsx (language, theme, country, t())
lib/         small pure functions with tests: typingDelay, trustMath, highlight, realmode, conversation, labels
components/  Layout (top bar + footer), Phone (frame + bubbles), Xray, TrustChart, SkillRadar, Safety (crisis, content warning, check-in), TreeDrawer, ...
pages/       one file per screen (Landing, Practice, Chat, Feedback, WhatIf, RealMode, How, Privacy, NotFound)
content/     copies of content/realmode.*.json and crisis_lines.json, bundled in for offline Real mode
test/        vitest tests
```

**A turn in the chat, step by step:**
1. You press Enter. Your bubble appears right away (faded) and the typing dots start.
2. The app sends `POST /api/sessions/{id}/messages`. The server runs Guardian → skill detector → state engine → friend voice (OpenAI wording, or a reviewed bank line) → verifier and returns a `TurnResponse`. An AI-worded reply can take 1–3 seconds, so the typing dots stay on for the whole request.
3. The app adds your message and the friend's reply to the conversation. The friend's bubbles appear **one at a time**, each after a typing delay of `clamp(400 + 35 × characters, 800, 3500)` ms. That's long enough to feel like a person, but never slow. If your device asks for reduced motion, the delay is 0.
4. If the friend left you on read (`seen_no_reply`), "Seen" appears under your message instead.
5. The trust graph adds a point (`state_after.trust`), colored by the strongest skill detected. The ladder and the skill chips update.
6. If the Guardian said **crisis**, a resources card pops up that **can't be closed** until you tick "I've seen these resources." Then the app rewinds to just before that message so you can keep practicing. If it said **block**, a teaching card explains why the message wasn't sent.

**The trust math in X-ray mode.** The engine sends its own breakdown of every trust change (`state_after.last_breakdown`): one term per detected skill plus engine terms such as `decay`, `diminishing` or `secrecy_broken`, and these add up to the real change (`last_delta`). X-ray shows exactly those numbers: `+12 validated · +15 asked directly · −2 decay = +25`. If an engine doesn't send a breakdown (the stub doesn't), X-ray shows only the total. We never guess how a change splits.

**Word highlights.** The critic sends character positions (`start`, `end`) for the words that pushed each skill's score up. `lib/highlight.ts` cuts the message into plain and highlighted pieces: green for helping skills, red for `dismissed`, `advice_dump` and `promised_secrecy`. It's tested so that overlapping or out-of-range spans never drop or duplicate a letter.

**Real mode offline.** At build time a script copies the fixed crisis text into the app. Real mode shows that copy instantly, then tries the server. If the server is down, it keeps the bundled copy and says so.

**Rewind.** The server keeps the whole conversation as a tree. "Rewind to here" moves the head back to the friend's message before yours and puts your old text in the input box so you can edit it. The branch drawer draws the tree: straight runs stay in one column, and only real forks are indented, so it stays readable on a phone.

## Why this approach (and what we considered instead)

- **One source of truth.** The chat always draws exactly the path the server returns (root → head). We never keep a separate copy that could drift, so rewinding, reloading and crisis pauses all just work.
- **Types generated from the API** (`npm run gen:api`). If the backend changes a field, TypeScript points to every screen that breaks. The alternative was hand-written types, which go stale silently.
- **Tailwind + CSS variables** for the design system. Every color is a token in `src/index.css` with a light and a dark value, so dark mode is one class on `<html>`, and restyling the app means editing one block. We considered a component library, but it would look generic and add weight.
- **Chart.js** for the trust graph and radar: small, accessible and well known. Charts get their own chunk so the landing page loads fast.
- **A calm, warm palette** (teal for trust, coral for care, cream paper instead of clinical white): not clinical, not childish. System fonts only, so nothing loads from outside and text looks native on every phone.
- **Safety UX is structural, not optional.** The help button lives in the layout, so no page can forget it. The crisis card is a non-dismissible dialog with a required checkbox. Real mode doesn't depend on the server.

## How we measured it (real numbers, with n and the split)

- **Unit tests:** 47 vitest tests in 8 files (`npm run test`), covering the typing delay formula and its edges, highlight span rendering, trust-math formatting, API error handling (404/422/network down/non-JSON), the Real-mode offline fallback, EN/ES key parity, the crisis card not being skippable, the check-in, the X-ray voice chip, and the tree/graph helpers.
- **End-to-end:** `npm run screenshots` drives the whole journey in real Chromium against `make dev-stub`, on a phone (390×844) and a desktop (1440×900). It fails if any step breaks, if the crisis card can be skipped, if the X-ray trust math is missing, if there's any console error, or if the page scrolls sideways. Result: 25 screens × 2 sizes = 50 screenshots in `frontend/screenshots/`.
- **Accessibility:** every text/background token pair was checked against WCAG AA (4.5:1). The lowest pairs after tuning: white on the coral button 4.98, green on green-soft 5.36, white on the dark-mode bubble 5.93.
- **Size:** about 86 KB gzipped app code + 63 KB gzipped charts (loaded as a separate cached chunk) + 7 KB CSS.

## Limitations

- In stub mode the critic never writes rewrites, so the rewrite screenshot (`13-feedback-rewrite`) adds one to the real stub response inside the Playwright script. The UI is real; that one piece of data is a test fixture. With the ML lane's critic on, rewrites come from the server.
- The rewrite badge names the skill it improves (`rewrite_skill`, e.g. "+0.41 Ask directly") once the ML lane fills it. Until then it shows only the gain.
- In stub mode the engine sends no trust breakdown, so X-ray shows only the total change. The full equation appears once the engine lane fills `last_breakdown`.
- Feedback rewrites are labeled by source (`rewrite_source`): "Suggested by AI, verified by our model" or "From our exemplar bank".
- Spanish UI text was drafted by an agent and needs a native speaker's review (`es.json` → `_meta.needs_native_review`).

## Questions a judge might ask (with answers)

1. **"Is the friend just ChatGPT?"** No. The AI is only the voice. Our state engine decides what the friend is ready to reveal, our Guardian and verifier decide whether a reply is safe, and our trained models do all the scoring. OpenAI only words the reply inside those limits, and every AI reply is checked before it's shown. Without the AI, the friend uses pre-written, reviewed lines. X-ray mode labels every friend reply ("AI, verified ✓", "Reviewed line" or "Fallback") and shows every number behind it. The Transparency page shows the AI's live status and today's spending.
2. **"What happens if a student types something that suggests *they're* not okay?"** The Guardian checks every message before anything else runs. If it detects risk, the practice pauses and a card shows 988 and "talk to a trusted adult." It can't be closed until the student confirms they've seen the resources. On the Transparency page you can watch "kms" get caught while "are you thinking about killing yourself?" (the *right* question to ask a friend) is allowed.
3. **"Does it work for someone in a real crisis if your server is down?"** Yes. Real mode's text and helplines are bundled into the app at build time. If the server doesn't answer, it shows that saved copy and says so. The 988 call and text buttons are plain phone links.
4. **"How do you know the trust graph isn't faked?"** Every point is the engine's real `trust` value after that message, straight from the API. The X-ray equation always adds up to the engine's real change, and any part we can't attribute to a skill is labeled "other" instead of being hidden.
5. **"What happens to what I type?"** It lives only in the server's memory and is deleted after 60 minutes of inactivity. There are no accounts and no database. When the AI voice is on, recent practice messages go to OpenAI only to word the friend's reply, and on the live site nothing from a conversation is written to disk. With the AI off, nothing leaves our server. The Privacy page lists the exact facts.
6. **"Is it accessible?"** Every button is reachable by keyboard, with a visible focus ring. Dialogs trap focus and return it when closed. New messages are announced to screen readers (`aria-live="polite"`). Charts have text descriptions. Colors pass WCAG AA in light and dark mode. Animations turn off when the device asks for reduced motion. The layout works from a 360 px phone to a desktop, in English and Spanish.

## How to run

```bash
uv sync && make dev-stub            # API on :8000 (repo root)
cd frontend && npm install
npm run dev                         # http://localhost:5173, proxies /api to :8000
npm run test                        # vitest
npm run build                       # → frontend/dist (FastAPI serves it at /)
npm run preview & npm run screenshots   # full journey + screenshots (needs the API running)
npm run gen:api                     # refresh src/api/types.ts from the running API
```
