# Frontend lane notes

## Done
- Vite + React 18 + TS + Tailwind + react-router + Chart.js app in `frontend/`, built to `frontend/dist` (served by FastAPI at `/`).
- `npm run gen:api` → `src/api/types.ts` (committed), generated from the stub API's OpenAPI schema.
- App shell: sticky top bar, an always-visible **"I need help now"** button → `/real`, safety footer, EN/ES toggle (`src/i18n/*.json`, ES marked `needs_native_review`), dark mode (saved, no flash), design tokens in `src/index.css`.
- Screens: Landing, Scenario picker + content warning, Chat (typing delays, staggered bubbles, Seen, crisis card, blocked card, success/fail endings, trust graph, disclosure ladder, skill chips, rewind, branch tree drawer), **X-ray mode** (Guardian level/action/latency/evidence, probability bars, trust math; friend reaction/line id/level), Feedback (radar, summary, turning point, missed opportunities, highlights, uncertain tags, verified rewrite, Try again from here, What if?), What-if (side-by-side paths, mini chats, mini curves, overlay chart, Simulated label, "Try this in the chat"), Real mode (country picker, tel:/sms: buttons, emergency number, **offline fallback** from bundled `content/` copies), Transparency (inline SVG pipeline, live component status, metrics table with empty state, does/doesn't, privacy, **Try the Guardian** with presets), after-session check-in, Privacy, 404.
- Accessibility: keyboard everywhere, focus rings, focus-trapping dialogs, `aria-live="polite"` message list, chart text alternatives, WCAG AA token contrast (checked), reduced motion respected.
- Tests: 61 vitest tests (typingDelay, highlights, trust math, API errors, Real-mode fallback, i18n parity, crisis card, check-in, shell, tree/graph helpers).
- `scripts/screenshots.mjs`: full journey in Chromium (mobile 390×844 + desktop 1440×900) against `make dev-stub` → 50 screenshots in `frontend/screenshots/`. Fails on any broken step, a skippable crisis card, console errors or horizontal overflow.
- **Contracts 1.2** (integrator d4e2b2b, merged): X-ray trust math uses the engine's real `State.last_breakdown` and shows only the total when it's empty. The rewrite badge shows `rewrite_skill` when present. The Privacy page (EN/ES) states the integrator's exact facts; the OpenAI-policy sentence is flagged for verification in `privacy._meta.verify`. Breakdown terms are shown to one decimal with friendly names (diminishing → "repeated", decay → "time"), plus a clamp note when trust hit 0 or 100 ("trust can't go below 0, actual change −5"). The 404.html workaround was removed now that `main.py` serves the SPA (deep links → 200, unknown /api → 404).

- **v3 / contracts 1.1** (integrator update): merged `claude/amazing-carson-31tzo3`, regenerated types. X-ray shows who wrote each friend reply (`voice`: AI verified ✓ / Reviewed line / Fallback). Transparency has "The AI is only the voice" plus live LLM status from `/api/health`. Feedback labels rewrites by `rewrite_source`. The typing indicator stays on for the whole request (AI replies take 1–3 s). Privacy, does/doesn't and pipeline copy now say OpenAI words the friend's replies (EN + ES).

- **All-real integration** (c60cc2f, fast-forward): tested against `FR_EMBED=fastembed FR_LLM=0 make dev`. Highlight `delta` (now log-odds) is shown only as relative strength (solid = strong, dotted = some, never the number). The null turning point shows "You never lost their trust". `referral_after_disclosure` → "referred after they opened up". Rewrite gain is shown as percentage points. Screenshots re-taken from the real backend, plus `26-feedback-success` (new-school played to success).

- **Localized scenarios** (48263a9): Practice fetches `/scenarios?lang=` and shows "Solo en inglés por ahora" on friends without the UI language. Chat shows a neutral "Práctica en inglés" / "Practice in Spanish" chip when `SessionView.locale` differs from the UI language. 22/23 were re-shot with a real Spanish Maya session, plus `27-practice-es`. The journey also asserts the chip on an English-only friend started in ES.

- **Headline metrics** (cc5cedb): /how shows curated headline cards (EN/ES label + explanation, baseline comparison, n · split · better) and hides `found=false`. The ~300 raw records sit in a collapsed, lane-grouped, searchable `<details>`. Desktop /how went from ~13,000 px to ~3,200 px. Re-shot 18/19 plus `28-how-es` against the real backend.

- **Real what-if** (20afbfe): "Skill match N%" instead of "Critic score", localized strategy names, a friendly empty state when `paths` is `[]` (EN/ES, with a test). Re-shot 14 against the real backend, plus `29-whatif-es` (real Spanish Maya rollouts).

- **Final quality pass** (51e87a9): full journey on the real backend in EN + ES, light + dark, mobile + desktop (new ES shots: blocked, crisis, feedback, real mode). axe-core on 9 pages × 2 themes reports 0 violations after fixing 4 serious contrast issues. A keyboard-only chat test passes. The slow-backend harness (4.5 s latency, slow 503) checks the typing dots, disabled Send, a single request, kept drafts, the error state and retry. Added a synchronous double-send guard in Chat. X-ray voice now reads "AI wording · checked by our verifier" / "Reviewed line" (EN + ES). Screenshots all re-shot; feedback shows real verified rewrites and what-if the real rollouts.

- **Redesign (Sahib: "looks generic")**: first, a critical fix for the blank page after clicking nav links. `App.tsx`'s effect returned `window.scrollTo`'s value as its cleanup; every effect now has a block body, a vitest scans the source for the pattern, and `npm run test:nav` clicks through every link/CTA in EN + ES, including a run with a patched `scrollTo` (it fails on the old code). Then the bold redesign: "dusk" tokens (violet signature, ember care, paper/night), self-hosted Fraunces + Plus Jakarta Sans, film grain, a live chat demo hero, three-step "how it works", story-style friend cards with initials art, night-glass X-ray with a scan banner, an animated trust meter, "Delivered" receipts, feedback as a story (pull quote, timeline, you said vs. what would have worked), branching futures on What-if, editorial headline numbers. All routes, test ids and behavior are unchanged. axe: 0 violations; CSP check: passes (asset inlining off for fonts); JS +3 KB gzip. Before/after pairs in `frontend/screenshots/redesign/`.

- **Redesign polish** (integrator review of 8462a97):
  - The X-ray banner is now a solid strip under the contact bar, outside the scroll area, so nothing bleeds under it.
  - What-if branch cards stack below sm (a vertical rail instead of curves); labels wrap and trust stays on one line.
  - The rewrite chip reads "✓ adds: listening" (ES "suma: escuchar"); the exact gain is in a tooltip, never a bare "+100%".
  - The chat drops the drawn phone bezel below sm (the landing demo keeps it).
  - Re-shot only the affected screenshots.

- **Messages-style chat + Add your own friend** (f00da33…7bd8934):
  - **Chat:** iOS-like bubbles with tails, a centered-avatar header with a back chevron, "Today …" timestamp, Delivered/Read receipts ("Read 9:42 PM" when left on read; the `seen` testid is kept), a gray typing bubble, and a "+" + pill composer. The landing demo and What-if transcripts use the same bubbles. AA-safe blues: #0071EB / #0A6EF0.
  - **Custom friend:** /practice/new form with live preview, counters, privacy and safety notices, field-level 422s, a real_help card first, `GET /api/friends/{id}` lookups, an expired → "Create again" flow, and "Your friend" with a not-reviewed chip. React state only.
  - **Tests:** 7 new vitest tests; `npm run test:friends` E2E (EN/ES × mobile/desktop, axe 0); click-nav now covers /practice/new and the chat's back chevron.

## In progress
- Nothing. Lane is feature-complete against the stubs.

## Decisions
- The chat renders exactly the server's root → head path. Rewind, reload and crisis all reuse the same code path.
- Crisis acknowledgement rewinds to the parent of the crisis message, because a `paused_crisis` head returns 409 on the next message.
- "Rewind to here" on a helper message rewinds to the friend message *before* it and pre-fills the input with the old text, so the user tries a different reply.
- Trust math shows only the engine's own breakdown (`last_breakdown`) and never estimates one.
- Real mode renders the bundled copy immediately, then upgrades from the API (instant, and works offline).
- Country "other" maps to the backend's `*` (international directory + "your local emergency number").
- The rewrite screenshot injects a rewrite into the real stub `/finish` response inside the Playwright script only (the stub critic never makes rewrites). Documented in `docs/how/frontend.md`.

## Requests
- Resolved by the integrator (d4e2b2b): SPA deep links, `rewrite_skill`, `last_breakdown`, and the privacy facts.
- **Engine lane:** fill `State.last_breakdown` so the X-ray equation appears (until then it shows the total only).
- **ML lane:** fill `MessageScore.rewrite_skill` and `rewrite_source`.
- **Sahib:** verify the OpenAI data-policy sentence on the Privacy page (`privacy._meta.verify` in `src/i18n/en.json`) before release.
- **Deploy lane:** build with `cd frontend && npm ci && npm run build`. The `prebuild` step copies `content/*.json` into `src/content/` if present; otherwise the committed copies are used.

## Known issues
- Spanish strings need native review.
- With every component stubbed, the summary text is the stub's placeholder and metrics are empty (the page shows a friendly empty state).

## Numbers
- vitest: 61/61 passing (10 files).
- E2E journey: passes on mobile + desktop; 50 screenshots.
- Bundle: app 291 KB (94 KB gzip), charts 179 KB (63 KB gzip, separate chunk), CSS 51 KB (10 KB gzip); fonts are self-hosted woff2 (Latin subsets downloaded on demand).
- Lowest AA contrast pair: 4.98 (white on coral button, light mode).
