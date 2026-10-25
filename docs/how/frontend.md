# The app (frontend)

*Owner: frontend lane. Plain language, so Sahib can explain every part to a judge.*

## What it does

The frontend is everything you see and tap. It's a website that works like a phone app:

| Screen | Address | What happens there |
|---|---|---|
| Landing | `/` | A phone mockup, the one-line pitch, three feature cards, the CDC "1 in 5" stat |
| Scenario picker | `/practice` | Five friends to text (name, age, situation, "open" or "guarded"). Picking one shows a **content warning** first |
| Chat | `/chat/:id` | iMessage-style texting with typing dots, several bubbles in a row, **"Seen"** when trust falls too far, a live **trust graph**, the **disclosure ladder** (0 surface → 4 open to help) and **skill chips** |
| X-ray mode | toggle in the chat | Under each of your messages: the Guardian's decision and **latency in ms**, the skill detector's probabilities as bars, and **the trust math** (`+12 validated · −2 decay = +10`). Under the friend's: **who wrote the words** ("AI wording · checked by our verifier" or "Reviewed line"), the reaction and the line id |
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
2. The app sends `POST /api/sessions/{id}/messages`. The server runs Guardian → skill detector → state engine → friend voice (OpenAI wording, or a reviewed bank line) → verifier and returns a `TurnResponse`. An AI-worded reply takes about 2–5 seconds (p95 4.9 s), so the typing dots stay on and Send stays disabled for the whole request (checked by `npm run test:slow`).
3. The app adds your message and the friend's reply to the conversation. The friend's bubbles appear **one at a time**, each after a typing delay of `clamp(400 + 35 × characters, 800, 3500)` ms. That's long enough to feel like a person, but never slow. If your device asks for reduced motion, the delay is 0.
4. If the friend left you on read (`seen_no_reply`), "Seen" appears under your message instead.
5. The trust graph adds a point (`state_after.trust`), colored by the strongest skill detected. The ladder and the skill chips update.
6. If the Guardian said **crisis**, a resources card pops up that **can't be closed** until you tick "I've seen these resources." Then the app rewinds to just before that message so you can keep practicing. If it said **block**, a teaching card explains why the message wasn't sent.

**The trust math in X-ray mode.** The engine sends its own breakdown of every trust change (`state_after.last_breakdown`): one term per detected skill plus engine terms such as `decay`, `diminishing` or `secrecy_broken`, and these add up to the real change (`last_delta`). X-ray shows exactly those numbers, rounded to one decimal, with friendly names (diminishing → "repeated", decay → "time", referral_after_disclosure → "referred after they opened up"): `+8.4 validated · −4.2 repeated · −2 time = +2.2`. `last_delta` is the raw change *before* trust is clamped to 0–100, so when the real change is different X-ray adds a note, e.g. "(trust can't go below 0, actual change −5)". If an engine doesn't send a breakdown (the stub doesn't), X-ray shows only the total. We never guess how a change splits.

**Word highlights.** The critic sends character positions (`start`, `end`) for the words that pushed each skill's score up. `lib/highlight.ts` cuts the message into plain and highlighted pieces: green for helping skills, red for `dismissed`, `advice_dump` and `promised_secrecy`. It's tested so that overlapping or out-of-range spans never drop or duplicate a letter. The critic's `delta` is a log-odds drop (roughly 1–15), which only means something compared with the other spans in the same message. So the app computes intensity = delta ÷ the strongest delta in that message and shows only words: a solid underline for a **strong** signal (≥ 60% of the strongest) and a dotted one for **some** signal. The raw number is never shown. Rewrite gains are a probability gain on the missing skill. The chip names what the rewrite adds ("✓ adds: listening"), and the exact number of points is in its tooltip. When the critic finds no turning point, the red card becomes a green "You never lost their trust".

**Real mode offline.** At build time a script copies the fixed crisis text into the app. Real mode shows that copy instantly, then tries the server. If the server is down, it keeps the bundled copy and says so.

**One language per chat.** The scenario list is fetched in the UI language (`/api/scenarios?lang=es`), so titles, situations and content warnings are localized. Each friend lists the languages it supports (`locales`). In Spanish mode, English-only friends get a "Solo en inglés por ahora" chip, and starting one gives an English chat. The server decides the chat's language (`SessionView.locale`) and the friend never mixes languages. When the chat language differs from the UI, the chat header shows a small chip ("Práctica en inglés" / "Practice in Spanish"), but the UI language itself never changes. API text (feedback, what-if) is shown as the server sends it; the frontend never translates it.

**What-if.** The real rollouts play scenario-specific exemplar replies up to three more turns through the real engine. Each card shows the reply's strategy (localized), its "Skill match" (our detector's 0–1 score for the skill the card teaches, as a percentage), a mini chat and a mini trust curve. The best path is the one with the highest value (trust, plus levels gained, a success bonus or fail penalty, and a small cost per extra turn). If no verified better reply exists, the page says so kindly instead of showing empty cards.

**Messages-style chat.** The chat (and the landing demo and What-if transcripts) looks like a phone's messaging app:
- **Bubbles:** blue sent bubbles and gray received ones with an 18 px radius. Bubbles from the same sender stack tightly, and only the last bubble of a run gets the curved tail (two CSS pseudo-elements, no images).
- **Type:** the system font at 17 px.
- **Header:** a back chevron, a centered avatar with the name in a small pill, and round controls for branches and X-ray.
- **Receipts:** "Today 9:41 PM" at the top. Under your latest message it says "Delivered" while they type, then "Read", or "Read 9:42 PM" if you were left on read.
- **Composer:** a round "+" (decorative) and a "Text {name}" pill with the blue send arrow.
- **Colors:** dark mode is pure black with #262629 received bubbles. Two colors are nudged just enough to pass WCAG AA: the exact iOS blues (#007AFF, #0A84FF) are only 4.0 and 3.7:1 with white text, so we use #0071EB (light) and #0A6EF0 (dark), which look the same. The meta gray is #6E6E73 in light mode. There are no Apple names or logos anywhere.

**Add your own friend.** On /practice, a last card opens /practice/new:
- **Fields:** name (1–24), age (13–19), open/guarded, "What are they like and how do they text?" (≤300), "What happened recently?" (10–400, required), and up to 5 sample texts (≤160) that preview as gray bubbles in a live phone as you type. Every field has a live counter.
- **Notices:** the form says plainly what happens to the description (server memory only, deleted after 60 minutes, sent to OpenAI to write replies; use a nickname). It also has a calm link to "If it's real."
- **Server answer:** `POST /api/friends` checks everything. A 422 `{field, reason, message}` appears next to that field. When the server answers `notice: "real_help"`, a help card comes first and practice is still allowed after it.
- **Starting:** the chat starts like any other friend's. Custom friends are looked up with `GET /api/friends/{id}`, because they aren't in the scenario list.
- **Storage:** the friend and the form values live only in React state (never browser storage). If the server has already deleted the friend, the app says so and offers "Create again" with the values still filled in.

**Measured numbers on /how.** The API sends a short curated list (`headline`, defined in `content/headline_metrics.json`) next to the ~300 raw evaluation records. Each headline becomes a card with a big number (percent, 2-decimal score, or a count of messages), a plain-language label and explanation in the UI language, an optional baseline ("0.82 vs 0.48 for keyword matching"), and a small "n = 171 · test_freeform · higher is better". Headlines that aren't measured yet (`found: false`) are hidden, and new ones appear without frontend changes. The raw records sit in a collapsed `<details>` ("All 298 measured numbers"), grouped by lane, with a search box and a scrollable area, so the page stays short.

**Rewind.** The server keeps the whole conversation as a tree. "Rewind to here" moves the head back to the friend's message before yours and puts your old text in the input box so you can edit it. The branch drawer draws the tree: straight runs stay in one column, and only real forks are indented, so it stays readable on a phone.

### Practice for a real friend (from screenshots) and deleting friends

- **Why:** a teen who is worried about a real friend can practice for *that* conversation. They upload 1 to 3 screenshots of their chat, and the app sets up a practice version of the friend.
- **Privacy first, in the browser:** before anything is sent, you draw black boxes over names and numbers (drag with a mouse or finger; or "Add box" and the arrow keys; or one tap on "Cover the top bar", where phones show the contact's name). The boxes are burned into the pixels on a canvas, the image is shrunk to at most 1280 px and saved again as a JPEG (which also removes hidden photo data like location), and only that copy is sent. The original file never leaves the device. Nothing is stored: the images are dropped from memory as soon as the reading is done.
- **Safety first:** the server says how urgent it looks. If the friend might act soon (a plan, a way, a time), an even stronger card comes above everything: call the local emergency number (from our crisis-lines file, so it's right for each country) or 988 now, stay with them if it's safe, and don't keep it a secret. All of this wording was reviewed by our safety lane. If the friend's own words can be a sign of suicide, a steady red card comes first: "Practice can wait. Today, tell a trusted adult… call or text 988 together", with Call/Text 988. Warning signs are shown as plain chips ("pulling away from people") with "These are warning signs to check in about, not a diagnosis."
- **You stay in charge:** the AI's draft only fills in the normal "Add your own friend" form. The name stays empty ("Use a nickname"), you edit everything, and the same safety checks run when you create the friend. The chat is labelled "Practicing for a real friend". If the AI isn't available, the app says so and you fill in the form yourself.
- **Deleting:** your friend's card and the chat both have "Delete". It asks first ("This ends your practice chats with them. Nothing is kept."), then the server deletes the friend and every chat with it. Only the page that created the friend can delete it: the server hands back a secret token when the friend is made, the page keeps it in memory, and sends it with the delete. If the AI removed names or other identifying details from its draft, the form says so, so you can check the text still makes sense.
- **Checked:** unit tests check that pixels under a box really are black in the exported image, the 1280 px and 1.5 MB limits, the consent gate, that real help comes before the form, the error messages and the delete flow. `npm run test:real-friend` runs the whole flow in a browser: each urgency level (with a stand-in for the AI), keyboard-only redaction, a finger drag on mobile, both themes, axe with 0 problems, and one pass against the real backend with the AI off.

## Design: why it looks like this

**In one sentence for a judge: it uses the same type and dark style as my personal site, so my work looks like one person made it; the chat looks like iMessage because that's where this moment happens.** The full rules are in `frontend/DESIGN.md`.

- **Sahib's type system.** Big, bold Syne for headlines, names and numbers; IBM Plex Sans for reading; IBM Plex Mono only for data (X-ray numbers, trust math, sources). The fonts are stored inside the app, so nothing loads from another website.
- **Late night, but calm.** A near-black background with thin hairline borders, like sahibs.dev. Light mode works too. There is only one accent color (the iMessage blue), plus green/red for "helped/hurt" and a separate red only for "I need help now" and 988. No neon, glow or glass: the topic is a crisis, so the page stays quiet.
- **Calm motion, like a breath.** When the page opens, a few stars drift (or, in light mode, a soft dawn sky), a blue light behind the phone slowly "breathes" every 5.5 seconds, the headline rises line by line, and Maya starts typing. Things move slowly and only once, because this topic needs calm. If your device asks for reduced motion, nothing moves at all, and the help buttons never animate.
- **Real content instead of decoration.** The three "how it works" cards show real pieces of the app (chat bubbles, an X-ray row, the reply that lost her next to the one that won her back), not icons.
- **The landing page shows a real conversation, not feature cards, and nothing in it is made up.** Next to the headline, the phone replays a conversation with Maya. Below it, the same conversation with a short note on every message saying what the app did: "Safety check: fine, 26 ms. The skill detector hears 'dismissed'. Trust drops from 34 to 12. She left you on Read." That's X-ray mode as a picture. The conversation was recorded by `scripts/demo_transcript.py` (`make demo-transcript`): it sends fixed messages to the real app with no AI wording (`FR_LLM=0`) and saves exactly what came back (Maya's reviewed lines, the skills detected, trust before and after, the Guardian's time, Read receipts) to `content/demo_transcript.json`, in English and Spanish. The frontend copies that file into its bundle and only reads it, so every number on the page is one the engine computed. A backend test checks that each of Maya's lines is the real bank line and that trust chains from one message to the next.
- **Facts come with their source.** "1 in 5 US high schoolers seriously considered suicide in the past year (CDC Youth Risk Behavior Survey, 2023, 20.4%)" and "When teens tell someone about suicidal thoughts, it's most often a friend (Fox et al., 2021)". They're sentences, not giant stat banners.
- **Story cards, chat like Messages.** Each friend is a card with their initial, their name in big type and their situation; "Add your own friend" is the last card. The chat has bubbles with tails, "Delivered" and "Read", exactly like a phone. Cards lift slightly when you point at them, instead of having shadows.
- **Feedback reads like a story.** A short summary in big text, a numbered timeline of your messages with trust after each one, then "This is where you lost them": what you said next to what would have worked. Below that, your whole conversation marked up like a teacher's notes (green and red underlines, a note beside each message, a better reply right under the one it improves).
- **What-if shows branching futures.** Your message branches into the replies you could have sent, each ending at the trust it reached. The best one has a solid blue border and the word "Best", not a glow. "Best" means the most trust and openness in the fewest messages, so each path also says how many messages it took: a path can reach higher trust and still lose because it needed an extra message.
- **Only motion that means something.** The opening sky and breathing light (landing only), the demo phone, typing dots, a bubble sliding in, the trust gauge moving, a card lifting under your pointer, one of five figures lighting up for "1 in 5". Nothing fades in just to look fancy, and it all switches off with the phone's reduced-motion setting.
- **Checked, not guessed.** Every color pair passes the WCAG AA contrast test; axe reports 0 problems on every page in light and dark mode. (iPhone's exact blue and green are slightly too light for small text, so we use a hair darker shade of each.)

## Why this approach (and what we considered instead)

- **One source of truth.** The chat always draws exactly the path the server returns (root → head). We never keep a separate copy that could drift, so rewinding, reloading and crisis pauses all just work.
- **Types generated from the API** (`npm run gen:api`). If the backend changes a field, TypeScript points to every screen that breaks. The alternative was hand-written types, which go stale silently.
- **Tailwind + CSS variables** for the design system. Every color is a token in `src/index.css` with a light and a dark value, so dark mode is one class on `<html>`, and restyling the app means editing one block. We considered a component library, but it would look generic and add weight.
- **Chart.js** for the trust graphs: small, accessible and well known. Charts get their own chunk so the landing page loads fast.
- **Sahib's own design identity** (the type and dark style of sahibs.dev) instead of a generic template: see *Design: why it looks like this* above.
- **Safety UX is structural, not optional.** The help button lives in the layout, so no page can forget it. The crisis card is a non-dismissible dialog with a required checkbox. Real mode doesn't depend on the server.

## How we measured it (real numbers, with n and the split)

- **Unit tests:** 61 vitest tests in 10 files (`npm run test`), covering the typing delay formula and its edges, highlight span rendering, trust-math formatting, API error handling (404/422/network down/non-JSON), the Real-mode offline fallback, EN/ES key parity, the crisis card not being skippable, the check-in, the X-ray voice chip, and the tree/graph helpers.
- **End-to-end:** `npm run screenshots` drives the whole journey in real Chromium against `make dev-stub`, on a phone (390×844) and a desktop (1440×900). It fails if any step breaks, if the crisis card can be skipped, if the X-ray trust math is missing, if there's any console error, or if the page scrolls sideways. Result: 33 screens × 2 sizes, plus a slow-error shot = 67 screenshots, in English and Spanish, light and dark in `frontend/screenshots/`. The current set was taken against the **real** backend (`FR_EMBED=fastembed FR_LLM=0`: real Guardian, trained skill detector, tuned engine and critic; what-if real since 20afbfe). The same script also passes against `make dev-stub`.
- **Accessibility (axe-core):** `npm run test:a11y` runs axe with the WCAG 2.0/2.1 A + AA rules on 9 pages (landing, practice, chat with X-ray on, feedback, what-if, real mode, how, privacy, 404) in light and dark mode: **0 violations of any impact on all 18 runs**. The final pass fixed 4 serious contrast issues: muted text on the teal stat band, label-colored numbers in the X-ray trust math (now a colored dot next to high-contrast text), faded status-chip text, and the faded "sending" bubble. The same script drives the chat by keyboard only: Tab to the message box, Enter to send, focus returns to the box, Shift+Tab to your message, Enter opens it, Tab to "Rewind to here", and Space toggles X-ray.
- **Slow AI replies:** `npm run test:slow` adds 4.5 s of latency in the test harness (Playwright routing; app code untouched). It checks that the typing dots show for the whole wait, Send is disabled, a second Enter or click never sends twice (exactly one request), a draft typed during the wait is kept, a slow 503 shows the error, restores the draft and re-enables Send, and a retry clears the error. The app also guards sending with a synchronous flag, so a fast double-click can't slip through either.
- **Contrast tokens:** every text/background token pair was checked against WCAG AA (4.5:1). The lowest pairs after tuning: white on the coral button 4.98, green on green-soft 5.36, white on the dark-mode bubble 5.93.
- **Size:** about 94 KB gzipped app code + 63 KB gzipped charts (a separate cached chunk) + 10 KB CSS. The redesign added only ~3 KB of JS (no animation library; all motion is CSS or a few lines of React). The fonts are self-hosted woff2 files, and the browser only downloads the Latin subsets it needs.
- **Custom friend end to end:** `npm run test:friends` creates a friend through the form, chats 3 turns, finishes, opens What-if, and checks the friend appears on /practice with the "Made by you, not reviewed by us" chip. It runs in English and Spanish on phone and desktop, with axe (0 violations) on the form and the custom chat, and checks that nothing about the friend reaches browser storage.
- **Navigation by clicking:** `npm run test:nav` moves between every page by clicking header/footer links, the logo, the help button and the CTAs, in English and Spanish, plus a run where `window.scrollTo` is patched to return a value (as some browser extensions do). This guards the fixed "blank page until refresh" bug: an effect returned `scrollTo`'s value as its cleanup. A vitest (`effects.test.ts`) scans the source so no effect can return a non-function again, and it failed on the old code.
- **Production CSP:** `node deploy/csp_check.mjs` passes with zero violations. Vite's asset inlining is turned off, because it had turned small font files into `data:` URIs that `font-src 'self'` blocks.

## Limitations

- In stub mode the critic never writes rewrites, so the journey script adds one to the stub's `/finish` response for the rewrite screenshot. Against the real backend it leaves real rewrites untouched (the current screenshots show a real one).
- The rewrite badge names the skill it improves (`rewrite_skill`, e.g. "+0.41 Ask directly") once the ML lane fills it. Until then it shows only the gain.
- In stub mode the engine sends no trust breakdown, so X-ray shows only the total change. The full equation appears once the engine lane fills `last_breakdown`.
- Feedback rewrites are labeled by source (`rewrite_source`): "Suggested by AI, verified by our model" or "From our exemplar bank".
- Spanish UI text was drafted by an agent and needs a native speaker's review (`es.json` → `_meta.needs_native_review`).

## Questions a judge might ask (with answers)

1. **"Is the friend just ChatGPT?"** No. The AI is only the voice. Our state engine decides what the friend is ready to reveal, our Guardian and verifier decide whether a reply is safe, and our trained models do all the scoring. OpenAI only words the reply inside those limits, and every AI reply is checked before it's shown. Without the AI, the friend uses pre-written, reviewed lines. X-ray mode labels every friend reply ("AI wording · checked by our verifier" or "Reviewed line") and shows every number behind it. The Transparency page shows the AI's live status and today's spending.
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
