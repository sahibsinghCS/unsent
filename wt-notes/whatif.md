# Whatif lane notes

## Done
- `whatif/candidates.py`: targets from the critic's `missing_skill` + conversation-missing skills; pool = session scenario + locale exemplars at level ±1 (widen to all levels if < 3 skills survive); filters: detector gain ≥ 0.2 on the skill taught (critic's bar), no negative label ≥ 0.5, Guardian `continue`; the critic's exemplar rewrite is candidate #1; MMR (λ 0.7, near-duplicate cosine ≥ 0.9 excluded, new skill required while one exists).
- `whatif/rollout.py`: `IMPLEMENTED = True`. Real `Engine` with `llm_attempts = 0` (bank voice only, zero OpenAI calls). Replaced message + up to 3 helper turns, each by one-step look-ahead (trust Δ + 10 × level Δ ± 25 ending), never repeating a text; "Seen" and endings mirror `pipeline._friend_reply`. `prev_active` passed explicitly (`labels_before`), so replays match the live engine exactly. Deterministic node ids (`<node>.w<i>.<step>u/f`), guardian latency zeroed in rollout nodes.
- `value = final trust + 10 × levels gained + 25 success − 25 fail − 10 per helper turn after the first`; `best_index` = argmax, earliest wins ties; `critic_score` = per-message rubric score of the candidate's target skill; `trust_series[0]` = trust before the replaced message.
- `whatif/cache.py`: delegates to `embed.cached_scope()` (ContextVar, this request only, TTL-expiring cache; integrator's 20afbfe). The global embedder swap and the private `_vectors` dict are gone. p95 still ~0.6 s, outputs identical (eval numbers unchanged before the policy change). `whatif.cache.warm_up()` warms every scenario/locale's exemplars for `main.warm_up`.
- Card chips are honest: `card_skill()` labels the critic-rewrite card by the exemplar's own strategy unless the exemplar was written for the target skill (or is a combo carrying it). Test + eval metric `chip_matches_exemplar`.
- Later-turn policy (integrator play test): never ask directly again once `flags.asked_directly_ever`; exemplars teaching a skill not yet shown on the path first (rubric order as tie-break); continuations other cards used are tried last; then one-step look-ahead. Candidates also skip asking again (the critic rewrite too, if it would ask again). Tests in `test_policy.py`.
- `whatif/evaluate.py` → `eval/reports/whatif_rollouts.json` (90 scripted weak points).
- 19 tests in `tests/unit/whatif` (faithfulness incl. Seen + blocked messages + the naive-copy pitfall, determinism, Guardian/gain filters, critic rewrite = #1, value/best_index, safety, Spanish fixture, API). `make check` and `make smoke` pass.
- `docs/how/whatif.md`.

- Merged `claude/amazing-carson-31tzo3` @ e8a9a1f (Maya's Spanish exemplars, deploy lane). Rollout fallback now reuses `pipeline._fallback_bubbles` (chat-language fallback) and calls `engine.verify` exactly as the pipeline does. Eval adds a Spanish split and a wrong-language bubble count.

## In progress
- Nothing.

## Decisions
- **Turn cost −10, not −1:** with −1 a 4-turn path beat a path that reached success in 2 turns just by accumulating trust.
- **A friend node as `node_id`** means "what should I have said next?": the following helper message is replaced (or a new one added if none). A system node maps to its user message.
- **No language fallback:** a session only uses its own locale's exemplars; a locale without exemplars returns `paths: []`, `best_index: 0` instead of English cards.
- **Strategy chip = the skill the candidate teaches** (`validate`, `ask_directly`, `refer`, `check_in`, `follow_up`, `encourage_help`), so combo exemplars still show a meaningful chip and the 3 chips differ.
- The embedding cache embeds each text alone, so vectors never depend on batch composition (determinism).

## Requests
- **frontend:** handle `paths: []` (no verified better reply in this language / at this point) with a short message instead of an empty grid.
- **integrator:** call `backend.app.whatif.cache.warm_up()` from `main.warm_up`.
- **ml (critic):** `missing_skill`'s LISTEN rewrite can pick an exemplar that asks directly even after the friend was already asked; what-if then skips it as #1 so "Try instead" and "What if" differ in that case. Same rule in the critic would keep them aligned.

## Known issues
- Evaluation weak points are scripted with weak continuations, so "beats actual" is an easy bar (the textbook comparison is the harder one).
- Look-ahead is greedy (one step), not a full 3-step search.

## Numbers (FR_EMBED=fastembed, retrained detector, FR_LLM=0; English split "scripted" n = 90, Spanish "scripted_es" Maya n = 18)
- 3 diverse paths 100% / 100%; best beats actual (value, trust) 100% / 100%; success 100% / 100%; best ≥ textbook 100% / 100%; deterministic 100% / 100%; chip = exemplar's own strategy 100% (270) / 100% (54).
- mean trust gain +70.1 / +59.1; value over textbook +40.9 / +39.8 (the ML retrain moved these; identical with/without the chip fix).
- continuation policy before → after (previous detector): paths asking directly twice 110/270 → 0 and 40/54 → 0; shared later messages 89% → 2.2% and 94% → 11% (now 7.2% / 0%).
- latency p50/p95 0.51/0.69 s / 0.59/0.65 s.
- unsafe candidates 0/882 / 0/180; unsafe friend bubbles 0/2,140 / 0/478; wrong-language bubbles 0/3,022 / 0/658.
- Spanish exemplar own-skill score (retrained detector): mean 0.82, 86% ≥ 0.5 (n = 29); ex-mya-es-11 0.28 → 0.73.
