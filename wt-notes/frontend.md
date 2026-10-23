# Frontend lane notes

## Done
- Vite + React 18 + TS + Tailwind + react-router + Chart.js app in `frontend/`, built to `frontend/dist` (served by FastAPI at `/`).
- `npm run gen:api` → `src/api/types.ts` (committed), generated from the stub API's OpenAPI schema.
- App shell: sticky top bar, an always-visible **"I need help now"** button → `/real`, safety footer, EN/ES toggle (`src/i18n/*.json`, ES marked `needs_native_review`), dark mode (saved, no flash), design tokens in `src/index.css`.
- Screens: Landing, Scenario picker + content warning, Chat (typing delays, staggered bubbles, Seen, crisis card, blocked card, success/fail endings, trust graph, disclosure ladder, skill chips, rewind, branch tree drawer), **X-ray mode** (Guardian level/action/latency/evidence, probability bars, trust math; friend reaction/line id/level), Feedback (radar, summary, turning point, missed opportunities, highlights, uncertain tags, verified rewrite, Try again from here, What if?), What-if (side-by-side paths, mini chats, mini curves, overlay chart, Simulated label, "Try this in the chat"), Real mode (country picker, tel:/sms: buttons, emergency number, **offline fallback** from bundled `content/` copies), Transparency (inline SVG pipeline, live component status, metrics table with empty state, does/doesn't, privacy, **Try the Guardian** with presets), after-session check-in, Privacy, 404.
- Accessibility: keyboard everywhere, focus rings, focus-trapping dialogs, `aria-live="polite"` message list, chart text alternatives, WCAG AA token contrast (checked), reduced motion respected.
- Tests: 53 vitest tests (typingDelay, highlights, trust math, API errors, Real-mode fallback, i18n parity, crisis card, check-in, shell, tree/graph helpers).
- `scripts/screenshots.mjs`: full journey in Chromium (mobile 390×844 + desktop 1440×900) against `make dev-stub` → 50 screenshots in `frontend/screenshots/`. Fails on any broken step, a skippable crisis card, console errors or horizontal overflow.
- **Contracts 1.2** (integrator d4e2b2b, merged): X-ray trust math uses the engine's real `State.last_breakdown` and shows only the total when it's empty. The rewrite badge shows `rewrite_skill` when present. The Privacy page (EN/ES) states the integrator's exact facts; the OpenAI-policy sentence is flagged for verification in `privacy._meta.verify`. Breakdown terms are shown to one decimal with friendly names (diminishing → "repeated", decay → "time"), plus a clamp note when trust hit 0 or 100 ("trust can't go below 0, actual change −5"). The 404.html workaround was removed now that `main.py` serves the SPA (deep links → 200, unknown /api → 404).

- **v3 / contracts 1.1** (integrator update): merged `claude/amazing-carson-31tzo3`, regenerated types. X-ray shows who wrote each friend reply (`voice`: AI verified ✓ / Reviewed line / Fallback). Transparency has "The AI is only the voice" plus live LLM status from `/api/health`. Feedback labels rewrites by `rewrite_source`. The typing indicator stays on for the whole request (AI replies take 1–3 s). Privacy, does/doesn't and pipeline copy now say OpenAI words the friend's replies (EN + ES).

- **All-real integration** (c60cc2f, fast-forward): tested against `FR_EMBED=fastembed FR_LLM=0 make dev`. Highlight `delta` (now log-odds) is shown only as relative strength (solid = strong, dotted = some, never the number). The null turning point shows "You never lost their trust". `referral_after_disclosure` → "referred after they opened up". Rewrite gain is shown as percentage points. Screenshots re-taken from the real backend, plus `26-feedback-success` (new-school played to success).

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
- vitest: 53/53 passing (8 files).
- E2E journey: passes on mobile + desktop; 50 screenshots.
- Bundle: app 264 KB (86 KB gzip), charts 179 KB (63 KB gzip, separate chunk), CSS 36 KB (7 KB gzip).
- Lowest AA contrast pair: 4.98 (white on coral button, light mode).
