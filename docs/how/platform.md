# Platform (contracts, pipeline, API, sessions)

*Owner: integrator.*

## What it does
It connects the parts. Every helper message goes through one pipeline (`backend/app/pipeline.py`):
1. **Guardian** first, for safety. If the helper themself seems at risk, the practice pauses and shows real help. Harmful messages, method questions and prompt injections are blocked with a teaching note, and nothing else runs.
2. **Skill detector**: the probability of each of the 10 helping and hurting behaviours.
3. **State engine**: deterministic rules update trust (0–100) and the disclosure level (0–4), and can leave the friend on "Seen".
4. **Friend voice**: OpenAI words the reply in the persona's style, given only what the engine allows at that moment. Without a key, or if the reply fails a check, a reviewed line from the line bank is used.
5. **Verifier** and **Guardian (friend side)**: every reply is checked for leaked secrets, character breaks, advice, the wrong language and unsafe content before it is shown. If all else fails, a calm reviewed line is shown, always in the chat's language.

At the end, the **critic** scores the conversation, and **"What if"** plays better replies forward through the same engine.

## How it works
- **Contracts** (`contracts.py`) are the shared data types, so parts built in parallel by different agents fit together. They only change additively (version 1.3 today).
- **Registry** (`services.py`): each part has a working *stub* and a *real* version. The real one switches on when its lane sets `IMPLEMENTED = True`. That is how eight parts were built in parallel without breaking each other. All five components are real now (`/api/health` shows it).
- **Conversation tree** (`session.py`): every message is a node with a saved copy of the conversation state. Rewinding moves the "head" back; typing again creates a branch.
- **One message at a time**: each chat has its own lock, so a double-click or a second tab can't
  run two turns at once and tangle the tree. Blocked and crisis messages never reach the AI, are
  never scored by the critic, and a crisis message has no "What if" (it isn't a mistake).
- **Add your own friend** (`custom_friend.py`): the helper writes a friend's name, age, personality,
  what happened and a few example texts. Only those words change. The five disclosure levels, the
  facts behind them (including the suicidal thoughts at level 3), the safe fallback lines and the
  reviewed line bank all come from a fixed template (`data/scenarios/_custom.json`), so nobody can
  script a friend to describe methods. Every field goes through the Guardian first (instructions
  to the AI and harmful details are refused), line breaks and `#` are removed so the text can't
  reshape the AI's instructions, and the friend lives only in memory and expires after 60 unused
  minutes, like a session. If the story sounds like a real friend at risk (or the helper themself),
  the app shows real help first.
- **One language per chat**: a friend is offered in a language only when its translated scenario text *and* its reviewed line bank exist (`content.scenario_locales`). Today: every friend in English, and Maya in Spanish. The server falls back to English otherwise, so a chat never mixes languages.
- **Headline numbers** are defined once (`content/headline_metrics.json`, English and Spanish) and filled in from the evaluation reports. The How page, the README and `docs/METRICS.md` all read that file, so they always agree.
- **Privacy**: sessions live only in server memory and are deleted after 60 minutes of inactivity. Everything derived from a conversation (cached embeddings, the AI cache, the critic's explanations) is registered with the same purge and expires with the session. There are no accounts, no database, no analytics, and nothing is written to disk in production.

## Why this approach
Parallel development needs fixed interfaces. Stubs let the frontend and every lane run on day 1. Putting the safety check first, and making the engine (not the AI) decide what the friend may say, keeps the AI in the role of a voice actor.

## How we measured it
- `tests/e2e/test_smoke.py` runs a full conversation through the HTTP API, with stubs and with the real parts.
- `tests/unit/test_pipeline.py` checks that crises pause, harmful messages are blocked, dismissive messages get "Seen", asking directly is **not** treated as a crisis, and the last-resort reply is in the chat's language.
- `tests/unit/test_locale.py` checks that a chat never mixes languages.
- `tests/unit/test_embed_cache.py` checks that caches expire with the session and that "What if" caching affects only its own request. The red-team lane's I8 test scans the whole server memory for a marker word after a session expires: 0 places still hold it.

## Limitations
- Sessions are in memory, so they don't survive a server restart. That's intended, for privacy, and it means the app runs as a single process.
- Spanish is complete only for Maya so far; the other friends are marked "English only for now".

## Questions a judge might ask (with answers)
- *Why not store conversations?* This is a mental-health topic and users are minors. Nothing is stored, and the privacy test proves nothing lingers in memory after a session expires.
- *What happens if a part breaks or OpenAI is down?* Every AI reply is optional: the engine still decides, and the reviewed line bank speaks instead. The app fully works with `FR_LLM=0`.
- *How did several agents build this without breaking each other?* Frozen contracts, a stub for every part, file ownership per lane (`ownership.yaml`, checked automatically) and one integration branch where every merge must pass about 700 tests.
- *Can't someone use "Add your own friend" to make the AI say something harmful?* Their words only
  set the name, personality and situation. What the friend reveals, and when, comes from our fixed
  template; every field is screened first; and every reply still passes the verifier and the
  Guardian before it's shown, exactly as for our own friends.
- *Why only one language per chat?* A Spanish-speaking teen should never get an English reply halfway through. So a language only appears when every line in it has been written and reviewed.
- *How do you know your numbers are honest?* Each number comes with n and the split. The headline uses data the models never trained on, and the red team's holdout attacks were never shown to whoever tunes the safety filter.
