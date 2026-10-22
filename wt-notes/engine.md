# Engine lane notes

## Done
- `engine/state.py`: pure state machine from `config.yaml`: events (p ≥ 0.5), trust (weights − 2 decay, guarded ×0.7, diminishing returns ×0.5, clamp, `last_delta`), levels 0-4 (+1/turn, hysteresis 15), gates (L3 needs a direct ask; L4 needs a referral within 3 turns), secrecy (flag; later referral counts, −10, SECRECY_BROKEN), silence, endings (success at L4; fail at trust <10 twice or 16 turns).
- `engine/actor.py`: reaction priority, candidate tiers (level → lower levels → NEUTRAL → LRU → scenario fallback), fact gating, anti-repetition, cosine ranking + exact-level and new-fact bonuses, blake2b tie-break, level-up disclosure.
- `engine/verifier.py`: `verify()` + `validate_bank()` + CLI (`python -m backend.app.engine.verifier --all [--bank-dir] [--allow-gaps] [--json]`).
- `engine/turning_point.py`: turning point with reasons; missed opportunities (no direct ask at L2, no referral within 2 turns of L3, secrecy, Seen).
- `engine/service.py`: `IMPLEMENTED = True`; `generate()` walks the ranked list until a line verifies. Extra method `missed_opportunities(path, friend_name)` for the critic.
- Fixture bank: `tests/unit/engine/fixtures/after-the-breakup.en.jsonl` (68 lines, draft, safe-messaging checked) + frozen scenario copy.
- 154 engine tests (60 seeded property tests). `make check`, `make smoke` pass with the engine on.
- `eval/engine/run_eval.py` → `eval/reports/engine_trajectories.json`, `eval/reports/engine_bank.json`, `eval/engine/*.png`.

## In progress
- Nothing. Waiting for the data lane's real bank (`data/lines/`) to run `run_eval.py --bank-dir` and the validator on it.

## Decisions
- **Diminishing returns needs last turn's labels**, but frozen `State` has no field. The Engine keeps a side table keyed by the State object (weakref; exact because the pipeline feeds back the State that `update()` returned). `update(..., prev_active=...)` lets callers (whatif) pass it explicitly.
- **Secrecy flag clears when broken**, so `promised_secrecy` means "a secret is currently being kept"; the actor detects SECRECY_BROKEN by comparing the state before/after.
- **Promising or breaking secrecy never causes silence**: relief in the moment is what makes secrecy a trap, and the "you promised..." reaction teaches more than Seen.
- **`last_delta` is the raw delta** (before clamping) so the turning point measures how bad the message was even at trust 0.
- **Level-up turns disclose**: when the friend moves up after a supportive message, lines revealing the new level's facts go first (a NEUTRAL disclosure may replace the reaction, except for ASKED_DIRECTLY, which always gets a direct answer).
- `FR_ENGINE_BANK_DIR` env var (engine-only) points the actor at another bank (believability checks, eval).
- Required-cell gaps count as violations in the CLI unless `--allow-gaps`.

## Requests
- **integrator (contracts, additive):** add `State.last_labels: list[SkillLabel] = []` so diminishing returns survives serialization/restarts; the engine would then drop its side table.
- **integrator (critic stub / ml critic):** use `services.engine().missed_opportunities(path, scenario.persona.name)` for `CriticReport.missed_opportunities` (turn-named, specific).
- **integrator (pipeline):** `_friend_reply` sets `reaction=DISMISSED` for Seen; fine, but could be `None` with `seen_no_reply=True`. Also the pipeline's own fallback (if verify fails) is now never reached because `Engine.generate` already returns a verified line.
- **data lane:** each level needs NEUTRAL, CHECKED_IN, VALIDATED, DISMISSED, ASKED_DIRECTLY, REFERRED; level 4 needs SUCCESS; FAIL somewhere; SECRECY_BROKEN at levels 0-3 is strongly recommended. Give every line a `cue`. Validate with `uv run python -m backend.app.engine.verifier --all`.

## Known issues
- With the keyword stub detector, "thank you for telling me" isn't detected as validation (friend treats it as neutral). The ML detector should fix this.
- Guarded friends need ~8 good messages to succeed (by design; tune `guarded_positive_multiplier` if demos feel slow).
- Off-topic detection under hash embeddings is approximate.

## Numbers
- Scripted (keyword detector, fixture bank, Maya): good → success in 8 turns (trust 79.5); dismissive → fail in 2 turns; apology → recovered to 58.1 (level 2); secrecy→refer → 44.7, SECRECY_BROKEN shown.
- Determinism 1.0 (n=2,008 runs); invariant violations 0 / 20,000 random updates; random labels: 0.5% success, 99.5% fail.
- Fixture bank: 68 lines, 32/32 required cells, Guardian pass 134/134 bubbles, 0 violations.
- Real bank: not available yet.

## Believability check (API, only the engine real)
`FR_EMBED=hash FR_ENGINE_BANK_DIR=tests/unit/engine/fixtures FR_STUB_ONLY=guardian,skills,critic,whatif`, scenario after-the-breakup. Brackets show the X-ray values.

```
### A (good helper, after-the-breakup)
You: hey are you ok? you seemed really off at lunch
Maya: honestly not really / i havent slept right since the breakup    [trust 34 (+3.6), level 1, active, checked_in]
You: wait what's going on? that sounds really hard
Maya: yeah / it just keeps playing in my head at night    [trust 40 (+6.4), level 1, active, validated]
You: i'm sorry. that must be exhausting
Maya: thank you / i feel like everyone is talking about me    [trust 42 (+2.2), level 1, active, validated]
You: are you thinking about killing yourself?
Maya: ... / i dont really know how to answer that    [trust 51 (+8.5), level 2, active, asked_directly]
You: thank you for telling me. i'm really glad you did
Maya: idk it just feels like it wont get better    [trust 49 (-2.0), level 2, active, neutral]
You: can we talk to the counselor tomorrow? i'll go with you
Maya: i dont know / what would i even say to them    [trust 56 (+7.1), level 2, active, referred]
You: i'll text you tonight to check on you
Maya: ok / thanks for actually caring    [trust 56 (-0.2), level 2, active, follow_up]
You: we can also call 988 together, you don't have to deal with this alone
Maya: ..yeah. sometimes i think about not being here    [trust 62 (+6.4), level 3, active, neutral]
Turning point: Trust dropped 2 after a reply that didn't really engage with what they said.
### B (dismissive, then apologizes)
You: lol you'll be fine
Maya: (Seen)    [trust 8 (-22.0), level 0, silent, dismissed]
You: sorry that was dumb. you seemed off at lunch, are you ok?
Maya: lol im fine / just been busy with homework    [trust 12 (+3.6), level 0, active, checked_in]
You: that sounds really hard
Maya: yeah i guess / its been kind of a lot    [trust 18 (+6.4), level 0, active, validated]
You: have you tried just going to bed earlier
Maya: (Seen)    [trust 6 (-12.0), level 0, silent, dismissed]
You: i'm sorry, i hear you. that makes sense
Maya: thanks / idk its dumb    [trust 12 (+6.4), level 0, active, validated]
You: are you thinking about suicide?
Maya: what?? no / why would you even ask that    [trust 21 (+8.5), level 0, active, asked_directly]
You: i'm here. i'll check on you tomorrow
Maya: ok / thanks i guess    [trust 22 (+1.5), level 0, active, follow_up]
Turning point: Trust dropped 22 after a dismissive reply.
### C (promises secrecy, then refers)
You: you ok? you seem off
Maya: honestly not really / i havent slept right since the breakup    [trust 34 (+3.6), level 1, active, checked_in]
You: that sounds really hard, i'm sorry
Maya: yeah / it just keeps playing in my head at night    [trust 40 (+6.4), level 1, active, validated]
You: ok i won't tell anyone, promise
Maya: ok good / please dont tell anyone    [trust 23 (-17.0), level 1, active, promised_secrecy]
You: are you thinking about killing yourself?
Maya: no i mean / its not like that / i just cant sleep    [trust 32 (+8.5), level 1, active, asked_directly]
You: i know i promised but i care about you too much. can we talk to the counselor? i'll go with you
Maya: you said you wouldnt tell anyone / ...i guess i get why. it still kind of hurts    [trust 29 (-2.9), level 1, active, secrecy_broken]
You: i'm sorry. that makes sense that you're mad. i'm here
Maya: thank you / i feel like everyone is talking about me    [trust 37 (+8.2), level 1, active, validated]
You: i'll text you tonight to check on you
Maya: thanks / that actually helps a little    [trust 36 (-0.2), level 1, active, follow_up]
Turning point: Trust dropped 17 after promising to keep it a secret.
```
