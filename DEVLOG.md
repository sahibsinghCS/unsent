# Dev log

Format: `YYYY-MM-DD HH:MM CT — what happened / decision and why`

- 2026-10-22 — Picked FirstReply after three research rounds (see research/). Mental health keeps winning CAC, but no winner trains the *friend*.
- 2026-10-22 — Decided on a **zero-cost architecture**: no paid AI at runtime. The friend speaks from a pre-written, safety-checked line bank chosen by our own state engine and models. Every friend line can be reviewed by a counselor.
- 2026-10-22 — Phase 0: contracts, stubs, pipeline, API, content drafts, ownership rules, CI. Launched 5 parallel lanes (engine, safety, data, ml, frontend).
- 2026-10-22 — **Changed to architecture v3:** OpenAI writes only the friend's *wording*. Our engine still decides what the friend may reveal, the verifier and Guardian check every reply, and the reviewed line bank is the fallback (the app fully works with `FR_LLM=0`). Training data is still written into files, never generated with the API.
- 2026-10-22 — First-message latency was 25 s (models loading on the first request). Added a startup warm-up; the first message now takes ~0.1 s.
- 2026-10-22 — Found that our test replies reused phrases from training (32 of 140 fully covered by training 5-grams), so the scores were inflated. Added ~440 hand-written "free-form" replies and a `test_freeform` split that is never trained on (0% leakage). That is now the honest headline number.
- 2026-10-22 — The two labelers disagreed most on whether suggesting the counselor or 988 also counts as "encouraged help". Wrote explicit rules into `docs/LABEL_GUIDE.md` (a referral is `referred_*`; persuading is separate, as in QPR) and applied them; the rest wait for human review.
- 2026-10-22 — Spanish: a chat must never mix languages. A friend is offered in a language only when its translated text *and* its reviewed line bank exist (today: Maya in Spanish; the others in English).
- 2026-10-22 — Wave B: launched the what-if, red-team and deploy lanes.
