# FirstReply

> Practice the text that could save a friend.

FirstReply lets teens practice the text that could save a friend's life: they chat with a realistic simulated friend who's struggling while models we trained score every reply, keep it safe, and show exactly where they lost the friend and what would have worked.

Built for the 2026 Congressional App Challenge.

**The AI is only the voice.** OpenAI writes the practice friend's wording. Our own deterministic engine decides what the friend may reveal, our verifier and Guardian check every reply, and our trained models score the helper. With no API key, the friend falls back to a reviewed line bank and everything still works.

> FirstReply is a practice tool, not a crisis service. If someone is in immediate danger, call 911. In the US, call or text **988**.

## Quick start
```bash
uv sync                 # install Python dependencies
make dev-stub           # API on http://localhost:8000 with every component stubbed
make check              # lint + tests
make help               # all commands
```
API docs: http://localhost:8000/docs

## How it works
See [`docs/LANES.md`](docs/LANES.md) (architecture) and `HOW_IT_WORKS.md` (built with `make docs`).

## Results
<!-- METRICS:START -->
*Evaluation tables are generated here by `make report`.*
<!-- METRICS:END -->

## Project docs
- [`FIRSTREPLY.md`](FIRSTREPLY.md): product plan
- [`docs/LANES.md`](docs/LANES.md): architecture and build lanes
- [`docs/RUBRIC.md`](docs/RUBRIC.md): the 7 helping skills
- [`docs/SAFE_MESSAGING.md`](docs/SAFE_MESSAGING.md): content safety rules
