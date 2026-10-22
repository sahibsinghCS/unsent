# Platform (contracts, pipeline, API, sessions)

*Owner: integrator.*

## What it does
It connects the parts. Every message goes through one pipeline (`backend/app/pipeline.py`):
1. **Guardian** first, for safety. A crisis pauses the practice, and harmful messages are blocked with a teaching note.
2. **Skill detector**, which gives the probability of each of the 10 helping and hurting behaviours.
3. **State engine**, which updates trust and the disclosure level using deterministic rules.
4. **Friend voice**, which picks a pre-written, safety-checked line from the line bank.
5. **Verifier**, which double-checks the line. If it fails, a safe fallback line is used instead.

## How it works
- **Contracts** (`contracts.py`) are shared data types, so the parts built in parallel fit together.
- **Registry** (`services.py`): each part has a working *stub* and a *real* version. The real one switches on when its lane marks it `IMPLEMENTED = True`. That's how 5+ parts were built in parallel without breaking each other.
- **Conversation tree** (`session.py`): every message is a node with a saved copy of the conversation state. Rewinding moves the "head" back. Typing again creates a branch.
- **Privacy:** sessions exist only in server memory and are deleted after 60 minutes of inactivity. There are no accounts, no database and no analytics.

## Why this approach
Parallel development needs fixed interfaces. Stubs let the frontend and every lane run on day 1.

## How we measured it
`tests/e2e/test_smoke.py` runs a full conversation through the HTTP API with stubs and with the real parts. `tests/unit/test_pipeline.py` checks that crises pause, harmful messages are blocked, dismissive messages get "Seen," and that asking directly is **not** treated as a crisis.

## Limitations
Sessions are in memory, so they don't survive a server restart. That's intended, for privacy.

## Questions a judge might ask (with answers)
- *Why not store conversations?* Privacy: this is a mental-health topic and users are minors. Nothing is stored.
- *What happens if a part breaks?* The verifier and fallback lines mean the friend always says something safe.
