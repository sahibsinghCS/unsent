# Frontend lane notes

## Done
- Vite + React 18 + TS + Tailwind + react-router + Chart.js app in `frontend/`, built to `frontend/dist` (served by FastAPI at `/`).
- `npm run gen:api` → `src/api/types.ts` (committed), generated from the stub API's OpenAPI schema.
- App shell: sticky top bar, an always-visible **"I need help now"** button → `/real`, safety footer, EN/ES toggle (`src/i18n/*.json`, ES marked `needs_native_review`), dark mode (saved, no flash), design tokens in `src/index.css`.
- Screens: Landing, Scenario picker + content warning, Chat (typing delays, staggered bubbles, Seen, crisis card, blocked card, success/fail endings, trust graph, disclosure ladder, skill chips, rewind, branch tree drawer), **X-ray mode** (Guardian level/action/latency/evidence, probability bars, trust math; friend reaction/line id/level), Feedback (radar, summary, turning point, missed opportunities, highlights, uncertain tags, verified rewrite, Try again from here, What if?), What-if (side-by-side paths, mini chats, mini curves, overlay chart, Simulated label, "Try this in the chat"), Real mode (country picker, tel:/sms: buttons, emergency number, **offline fallback** from bundled `content/` copies), Transparency (inline SVG pipeline, live component status, metrics table with empty state, does/doesn't, privacy, **Try the Guardian** with presets), after-session check-in, Privacy, 404.
- Accessibility: keyboard everywhere, focus rings, focus-trapping dialogs, `aria-live="polite"` message list, chart text alternatives, WCAG AA token contrast (checked), reduced motion respected.
- Tests: 45 vitest tests (typingDelay, highlights, trust math, API errors, Real-mode fallback, i18n parity, crisis card, check-in, shell, tree/graph helpers).
- `scripts/screenshots.mjs`: full journey in Chromium (mobile 390×844 + desktop 1440×900) against `make dev-stub` → 50 screenshots in `frontend/screenshots/`. Fails on any broken step, a skippable crisis card, console errors or horizontal overflow.
- `dist/404.html` = copy of `index.html`, so deep links load when FastAPI serves the build (StaticFiles html mode serves 404.html).

## In progress
- Nothing. Lane is feature-complete against the stubs.

## Decisions
- The chat renders exactly the server's root → head path. Rewind, reload and crisis all reuse the same code path.
- Crisis acknowledgement rewinds to the parent of the crisis message, because a `paused_crisis` head returns 409 on the next message.
- "Rewind to here" on a helper message rewinds to the friend message *before* it and pre-fills the input with the old text, so the user tries a different reply.
- Trust math = published label weights + an "other"/"decay" remainder, so the shown equation always equals the engine's real `last_delta`.
- Real mode renders the bundled copy immediately, then upgrades from the API (instant, and works offline).
- Country "other" maps to the backend's `*` (international directory + "your local emergency number").
- The rewrite screenshot injects a rewrite into the real stub `/finish` response inside the Playwright script only (the stub critic never makes rewrites). Documented in `docs/how/frontend.md`.

## Requests
1. **API (integrator):** proper SPA fallback in `main.py` (serve `index.html` with 200 for non-`/api` paths). Today deep links work through `dist/404.html` but return HTTP 404.
2. **Contracts (integrator + ml):** optional `MessageScore.rewrite_skill: str | None` (the rubric skill the rewrite improves) so the badge can say "+0.41 ask directly". The frontend already reads it if present.
3. **Contracts (integrator + engine):** optional `State.trust_terms: dict[str, float] | None` (per-label contributions + decay) so X-ray mode can show the engine's exact breakdown instead of mirroring `engine/config.yaml` weights.
4. **Deploy lane:** build the frontend with `cd frontend && npm ci && npm run build`. The `prebuild` step copies `content/*.json` into `src/content/` if present (committed copies are used otherwise).

## Known issues
- Spanish strings need native review.
- With every component stubbed, the summary text is the stub's placeholder and metrics are empty (the page shows a friendly empty state).

## Numbers
- vitest: 45/45 passing (8 files).
- E2E journey: passes on mobile + desktop; 50 screenshots.
- Bundle: app 264 KB (86 KB gzip), charts 179 KB (63 KB gzip, separate chunk), CSS 36 KB (7 KB gzip).
- Lowest AA contrast pair: 4.98 (white on coral button, light mode).
