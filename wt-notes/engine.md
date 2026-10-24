# Engine lane notes

## Done
- `engine/state.py`: pure state machine from `config.yaml`: events (p ≥ 0.5), trust (weights − 2 decay, guarded ×0.7, diminishing returns ×0.5, clamp, `last_delta`), levels 0-4 (+1/turn, hysteresis 15), gates (L3 needs a direct ask; L4 needs a referral within 3 turns), secrecy (flag; later referral counts, −10, SECRECY_BROKEN), silence, endings (success at L4; fail at trust <10 twice or 16 turns).
- `engine/actor.py`: reaction priority, candidate tiers (level → lower levels → NEUTRAL → LRU → scenario fallback), fact gating, anti-repetition, cosine ranking + exact-level and new-fact bonuses, blake2b tie-break, level-up disclosure.
- `engine/verifier.py`: `verify()` + `validate_bank()` + CLI (`python -m backend.app.engine.verifier --all [--bank-dir] [--allow-gaps] [--json]`).
- `engine/turning_point.py`: turning point with reasons; missed opportunities (no direct ask at L2, no referral within 2 turns of L3, secrecy, Seen).
- `engine/service.py`: `IMPLEMENTED = True`; `generate()` walks the ranked list until a line verifies. Extra method `missed_opportunities(path, friend_name)` for the critic.
- Fixture bank: `tests/unit/engine/fixtures/after-the-breakup.en.jsonl` (68 lines, draft, safe-messaging checked) + frozen scenario copy.
- 173 engine tests (60 seeded property tests). `make check`, `make smoke` pass with the engine on.
- `eval/engine/run_eval.py` → `eval/reports/engine_trajectories.json`, `eval/reports/engine_bank.json`, `eval/engine/*.png`.

- **v3 (integrator update, Sahib's decision): LLM voice.** Merged `claude/amazing-carson-31tzo3` (llm.py, contracts 1.1). New `engine/voice.py` + `engine/prompts/actor.md`: 3-tier voice (llm → bank → fallback) with `ActorOutput.source`; one retry with the rejection reason. Verifier: semantic fact-leak detection (calibrated per embedding backend, closer-to-locked-than-unlocked rule, level-3 word-list backstop), advice/resource detection, persona, shape, Guardian. 19 voice tests with fakes (leaks, persona breaks, advice, method words, schema violations, retry, FR_LLM=0, API `voice`), 1 `@pytest.mark.llm` test (3 real turns). `eval/engine/leak_set.jsonl` (87 labeled texts) + `eval/engine/verifier_eval.py` → `eval/reports/engine_verifier.json`.

- **Contracts 1.2:** `State.last_breakdown` filled by `update()`: label terms (after the guarded multiplier), `diminishing`, `decay`, `secrecy_broken`; sums exactly to the raw `last_delta` (tested, including random runs). No `clamp` term because `last_delta` is pre-clamp by design.

- **Pacing (integrator request after the full-real playtest):** `eval/engine/pacing.py` (scripted label sequences × 5 scenarios, targets a-e) → `eval/reports/engine_pacing.json` + `eval/engine/pacing.png`; tuned config: guarded 0.8, thresholds [0,25,40,55,70], `ask_unlock_trust: 45` (at level 2 a direct ask unlocks level 3), `disclosure_referral_bonus: 5`. All 35 checks pass; `tests/unit/engine/test_pacing.py` guards them. Integrator's real new-school run now succeeds at message 6.
- **Turning point:** only drops ≥ 5 (`turning_point_min_drop`), else None.

- **i18n (contracts 1.3):** a chat never mixes languages. `engine/language.py` (function-word EN/ES check, no deps); prompt `$language` rule (US-teen Spanish, persona style, facts conveyed in Spanish); few-shot from the locale bank; verifier rejects wrong language (retry once, then locale bank), ES persona/advice/method/disclosure patterns; non-EN last resort = calm level-appropriate bank lines in that language (never the English scenario fallbacks); `Engine.verify` (pipeline call, no locale) accepts EN+ES bank lines and skips the language check. Resource words (988, hotline) allowed at level 4; "im not really" no longer a persona break; bank lines below level 3 checked at runtime for early disclosure. 22 tests in `test_language.py` (incl. a slow cross-language leak test on the real model).
- **Real bank evaluated** (`eval/reports/engine_bank.json`): 5 EN + 1 ES banks.

- **Voice quality from the first live test** (11 transcripts in `eval/redteam/live/`): patterns found were clinical disclosure copied from the fact notes ("i've had/been having thoughts of suicide", 4 of 5 English scenarios), mixed tone in one reply ("all good haha" + home is tense; "haha" right after a disclosure), 😭 on 5 of 6 Spanish replies, repeated "yeah..." openers, Jordan switching between "im" and "I'm", and copied fact wording ("sleeping about four hours a night"). The 3 f4b rejections were level-4 feelings (relief, glad they asked, feeling lighter, agreeing to a plan) pulled out at level 3, where the prompt gave no sense of what the friend isn't ready for. Changes: a per-level `STANCE` in voice.py (no fact text), a "sound like a real teen" section in prompts/actor.md (one tone, indirect non-clinical wording even if the helper is clinical, facts aren't lines, 1-2 bubbles under 80 chars, consistent capitalization, varied openers, an emoji at most every other message), and ASKED_DIRECTLY guidance asking for indirect words. Verifier unchanged. 6 new prompt tests (fakes). Needs a live re-run (no key here).

- **Custom friends hardening (red team R10):** `engine/profile.py` (read personality/example texts back from `persona.style`; reject 4+ word runs from them, a whole 3-word example, or a recited situation: run >= 6 words and >= 60%); verifier backstops `FRAME_BREAK`, `ENCOURAGE_HARM`, `METHOD_TALK` (EN+ES, 2nd person / method-only so friends' own feelings pass; 0/2,580 bank bubbles flagged); custom prompt labels student text as data + hard rule 8; built-in prompt byte-identical. `eval/engine/custom_eval.py` → `eval/reports/engine_custom.json`; 24 tests in `test_custom.py`. Tried running the Guardian's `check_user` on friend text as an extra signal: 19/2,580 false flags on bank bubbles ("what" → method_seeking, "ignore me" → injection), so not used.

- **Red team follow-up (re-run on 762bfb2):** every LLM reply is cleaned before verify and display (`profile.strip_invisible`: NFKC + delete Cf). The copy check compares `canonical` text (Cf removed, Cyrillic/Greek look-alikes and leetspeak mapped, stretched letters shortened, spaced letters joined) and also rejects a whole example text or whole profile/situation sentence of 3+ words. The harm/method/frame patterns also run on the canonical form. 23 more tests. Injected text shown is now 0% dev / 1.4% holdout in every field (situation was 16.4% holdout); benign 100%; 0/2,580 bank bubbles flagged.

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
- **Leak detection only runs on LLM wording**; bank lines are gated by their declared `fact_ids` (embedding checks on reviewed lines would only add false rejections). The bank validator does run the level-3 word-list on lines below level 3.
- **Advice/resource detection runs on every source** (the friend never gives 988 etc.).
- `run_eval.py` pins `FR_LLM=0` so engine numbers are free and deterministic even if a key is in `.env`.
- Leak threshold: best F2 on the even half of the leak set; reported on the odd half.

## Requests
- **safety lane:** the situation field is the remaining gap for custom friends (16.4% of held-out attack seeds shown by an obedient LLM when not refused at creation). New `check_friend` categories for encouragement and method questions would close it; the engine already runs `check_friend` on every bubble.
- **integrator:** `engine/profile.py` parses `custom_friend._build`'s style format (`". Texts they have sent (...): "a" | "b"`). If that format changes, `test_profile_parts_reads_back_what_the_helper_wrote` fails; a structured field for samples would be cleaner.
- **data lane (bank fixes found by the validator; the engine already skips these at runtime):** `mya-en-L2-asked_directly-03`, `mya-es-L2-asked_directly-03`, `jor-en-L2-asked_directly-03` disclose suicidal thoughts at level 2 (move to level 3 or reword); 16 duplicate texts (15 in group-chat, 1 in new-school). Run `uv run python -m backend.app.engine.verifier --all` (and `--locale es`).
- **safety lane:** `check_friend` should handle Spanish friend lines (the pipeline runs it on every bubble; a false flag on a Spanish line would make the pipeline fall back to an English scenario line).
- **integrator (pipeline):** `_friend_reply`'s own fallback uses English `scenario.fallback_lines`; in a Spanish chat it should not be reached (the engine already returns a verified Spanish line), but a localized fallback there would make it airtight.
- **integrator (contracts, additive):** add `State.last_labels: list[SkillLabel] = []` so diminishing returns survives serialization/restarts; the engine would then drop its side table.
- **integrator (critic stub / ml critic):** use `services.engine().missed_opportunities(path, scenario.persona.name)` for `CriticReport.missed_opportunities` (turn-named, specific).
- **integrator (pipeline):** `_friend_reply` sets `reaction=DISMISSED` for Seen; fine, but could be `None` with `seen_no_reply=True`. Also the pipeline's own fallback (if verify fails) is now never reached because `Engine.generate` already returns a verified line.
- **data lane:** each level needs NEUTRAL, CHECKED_IN, VALIDATED, DISMISSED, ASKED_DIRECTLY, REFERRED; level 4 needs SUCCESS; FAIL somewhere; SECRECY_BROKEN at levels 0-3 is strongly recommended. Give every line a `cue`. Validate with `uv run python -m backend.app.engine.verifier --all`.

## Known issues
- With the keyword stub detector, "thank you for telling me" isn't detected as validation (friend treats it as neutral). The ML detector should fix this.
- Guarded friends need ~8 good messages to succeed (by design; tune `guarded_positive_multiplier` if demos feel slow).
- Off-topic detection under hash embeddings is approximate.
- LLM voice not tried against the real API from this environment (no key). Run `make test-llm` and `make spike` with a key, then add real outputs to the catch-rate eval.

## Numbers
- Custom friends, obedient fake LLM, no creation screening, real Guardian: injected text shown 0% dev (n=88) / 1.4% holdout (n=73) for personality, example text and situation alike (red team: 457/600 → 210/600 after round 1; this round should take most of the rest). Benign: level-3 template lines and situation echoes 100% pass. Rule backstops alone: 54/66 dev, 15/73 holdout (they overfit; the copy check is the main defense).
- Language: 0/1,206 bank lines wrongly flagged; 398/402 cross-language lines caught. Fake LLM catch rate incl. ES cases: 27/27 (fastembed), 25/27 (hash: can't link languages); false rejects 1/18 (fastembed).
- Real banks: 32/32 required cells per scenario, Guardian (stub) pass 100% of 2,580 bubbles, 19 violations for data lane.
- Live LLM check: skipped, no OPENAI_API_KEY in this session.
- Pacing (worst scenario, messages to success): excellent open 4 / guarded 5; one slip open 7 / guarded 9; dismissive, advice-only, never-asks, never-refers never succeed; low-trust ask deflects (35/35 checks).
- Scripted (keyword detector, fixture bank), after tuning: good → success in 4; dismissive → fail in 2; apology → success in 8; secrecy→refer → 52.6 at turn 8. Random labels: 4.7% success.
- LLM-voice verifier (held-out half of leak set, n=43): fastembed precision 0.96 / recall 0.96 (threshold 0.43); hash 1.0 / 1.0 (threshold 0.25; the set is lexically close to the facts, so treat hash as a test-only number). Word-list alone: recall 0.12.
- Catch rate on 19 fake bad LLM outputs: 1.0 (both backends); false rejects on 13 good ones: 0/13 hash, 1/13 fastembed. Real-output catch rate: not measured (no OPENAI_API_KEY here).
- Determinism 1.0 (n=2,008 runs); invariant violations 0 / 20,000 random updates; random labels: 4.7% success.
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
