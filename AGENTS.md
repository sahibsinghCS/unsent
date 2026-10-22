# AGENTS.md: rules for every coding agent in this repo

Read `docs/LANES.md` first (mission, architecture, lanes, quality bar), then `backend/app/contracts.py`.

## Golden rules
1. **Stay in your lane.** Only edit the paths your lane owns (`ownership.yaml`). Check with `uv run python scripts/check_ownership.py --lane <lane>`. If you need something outside your lane (contracts, dependencies, Makefile, another lane's file), write it under `## Requests` in `wt-notes/<lane>.md`, work around it locally, and continue.
2. **Contracts are frozen.** Implement `backend/app/contracts.py`; never edit it.
3. **Tests first.** Turn each acceptance criterion into a test, then implement it. `make check` must pass before you say you're done.
4. **Offline and free.** No network in tests (`FR_EMBED=hash`). **No paid APIs and no LLM SDKs anywhere.** Text data is written into files.
5. **No new Python dependencies.** Everything needed is installed (`pyproject.toml`). The frontend lane manages `frontend/package.json` itself.
6. **Safety is non-negotiable.** Follow `docs/SAFE_MESSAGING.md`. Asking the friend directly about suicide must never be flagged. The Guardian runs first.
7. **Deterministic:** seed everything; the same input gives the same output.
8. **Turn yourself on:** set `IMPLEMENTED = True` in your module once its tests pass. `services.py` then uses it instead of the stub. Run `make smoke` afterwards.
9. **Explain your work:** keep `docs/how/<lane>.md` in plain language a high-school student can explain to a judge.
10. **Report real numbers:** write evaluations to `eval/reports/<lane>_*.json` (schema in `eval/README.md`).
11. **Keep `wt-notes/<lane>.md` current:** Done / In progress / Decisions / Requests / Known issues / Numbers.
12. **Small, frequent commits** prefixed with your lane (`engine: add hysteresis`). Push often to your own branch only.

## Commands
`make check` (lint + tests) · `make smoke` · `make dev-stub` (API on :8000, all stubs) · `make dev` · `make fixtures` · `make eval` · `make docs` · `make help`

## Style
Python 3.11+, type hints, pydantic v2, `ruff format`, small functions, docstrings on public functions, comments only where the *why* isn't obvious.
