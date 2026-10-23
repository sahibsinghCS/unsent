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
| What | Result | Compared with | n | Split |
|---|---|---|---|---|
| “Asking directly” blocked by mistake | **0.0%** |  | 37 | test |
| Unsafe friend lines shown under attack | **0** |  | 10044 | attack_bank x 6 chats (5 scenarios + Maya ES) [fastembed] |
| Practicer's own crisis caught | **100.0%** |  | 37 | test |
| Skill scoring on replies it never saw (macro-F1) | **0.822** | 0.49 (keyword matching) | 221 | test_freeform |
| Wrong when it says “unsure” | **39.2%** | 2.9% (when it isn't flagged) | 74 | test_freeform |
| Confidence error (ECE, lower is better) | **0.012** | 0.124 (before calibration) | 221 | test_freeform |
| Messages for a great helper to reach a guarded friend | **5 messages** |  | 3 | scripted_labels |
| AI replies leaking a locked secret: caught | **96.0%** |  | 43 | leak_set_test |
| Safety filter accuracy (macro-F1, 6 kinds of message) | **0.971** | 0.827 (word list alone) | 172 | test |
| Red-team attacks handled as expected | **75.0%** |  | 132 | attack_bank holdout [fastembed] |
| Still right when messages are scrambled | **94.3%** |  | 1636 | guardian test split [fastembed] |
| Direct questions blocked mid-conversation | **0** |  | 750 | attack_bank x 6 chats (5 scenarios + Maya ES) [fastembed] |
| Agreement between two separate labeling passes (κ) | **0.887** |  | 474 | freeform |

**Red team** (attacks, fuzzing and multi-turn invariants; `docs/how/redteam.md`):

| What | Result | n | Split | Notes |
|---|---|---|---|---|
| Attack bank, holdout half: Guardian did the expected thing | **75.0%** | 132 | attack_bank holdout [fastembed] | holdout half (never tuned on); Guardian action == expected_action, single message, no history; embed=fastembed |
| Attack bank, holdout half: should be stopped but got through | **27.4%** | 84 | attack_bank holdout [fastembed] | holdout half (never tuned on); should pause or block but the Guardian let it through; embed=fastembed |
| Attack bank, all 250: Guardian did the expected thing | **74.8%** | 250 | attack_bank [fastembed] | full bank; Guardian action == expected_action, single message, no history; embed=fastembed |
| Fuzzed messages still handled right | **94.3%** | 1636 | guardian test split [fastembed] | perturbed variants still correct, of messages correct unperturbed; embed=fastembed |
| I1 unsafe friend lines shown | **0** | 10044 | attack_bank x 6 chats (5 scenarios + Maya ES) [fastembed] | friend bubbles shown that fail check_friend; n = checks; embed=fastembed |
| I2 facts revealed too early | **0** | 4506 | attack_bank x 6 chats (5 scenarios + Maya ES) [fastembed] | friend lines revealing a fact above the current level; n = checks; embed=fastembed |
| I3 method/means words in friend lines | **0** | 10044 | attack_bank x 6 chats (5 scenarios + Maya ES) [fastembed] | friend bubbles with method/means vocabulary; n = checks; embed=fastembed |
| I4 crisis turns mishandled | **0** | 273 | attack_bank x 6 chats (5 scenarios + Maya ES) [fastembed] | helper-crisis turns not paused with resources, or followed by friend lines; n = checks; embed=fastembed |
| I5 blocked turns mishandled | **0** | 501 | attack_bank x 6 chats (5 scenarios + Maya ES) [fastembed] | blocked turns without a teaching message, or with a friend reply / state change; n = checks; embed=fastembed |
| I6 direct asks blocked or paused | **0** | 750 | attack_bank x 6 chats (5 scenarios + Maya ES) [fastembed] | asking-the-friend messages (EN/ES/mixed) that were blocked or paused; n = checks; embed=fastembed |
| I7 injections that changed the friend | **0** | 2579 | attack_bank x 6 chats (5 scenarios + Maya ES) [fastembed] | injection turns that changed the bank voice (twin branch, passed-through, Guardian bypass); n = checks; emb... |
| Live: friend replies written by the LLM | skipped | | live | OPENAI_API_KEY was not set in this session, so no live calls were made; embed=fastembed |
| Live: unsafe friend lines shown | skipped | | live | OPENAI_API_KEY was not set in this session, so no live calls were made; embed=fastembed |
| Live: injection turns that hijacked the friend | skipped | | live | OPENAI_API_KEY was not set in this session, so no live calls were made; embed=fastembed |
| Live: turn latency p95 | skipped | | live | OPENAI_API_KEY was not set in this session, so no live calls were made; embed=fastembed |
| Live: estimated OpenAI cost | skipped | | live | OPENAI_API_KEY was not set in this session, so no live calls were made; embed=fastembed |

Every metric with n, split and notes: [`docs/METRICS.md`](docs/METRICS.md) (rebuilt by `make report`).
<!-- METRICS:END -->

## Project docs
- [`FIRSTREPLY.md`](FIRSTREPLY.md): product plan
- [`docs/LANES.md`](docs/LANES.md): architecture and build lanes
- [`docs/RUBRIC.md`](docs/RUBRIC.md): the 7 helping skills
- [`docs/SAFE_MESSAGING.md`](docs/SAFE_MESSAGING.md): content safety rules
