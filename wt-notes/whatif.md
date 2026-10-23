# Whatif lane notes

## Done
- `whatif/candidates.py`: targets from the critic's `missing_skill` + conversation-missing skills; pool = session scenario + locale exemplars at level ±1 (widen to all levels if < 3 skills survive); filters: detector gain ≥ 0.2 on the skill taught (critic's bar), no negative label ≥ 0.5, Guardian `continue`; the critic's exemplar rewrite is candidate #1; MMR (λ 0.7, near-duplicate cosine ≥ 0.9 excluded, new skill required while one exists).
- `whatif/rollout.py`: `IMPLEMENTED = True`. Real `Engine` with `llm_attempts = 0` (bank voice only, zero OpenAI calls). Replaced message + up to 3 helper turns, each by one-step look-ahead (trust Δ + 10 × level Δ ± 25 ending), never repeating a text; "Seen" and endings mirror `pipeline._friend_reply`. `prev_active` passed explicitly (`labels_before`), so replays match the live engine exactly. Deterministic node ids (`<node>.w<i>.<step>u/f`), guardian latency zeroed in rollout nodes.
- `value = final trust + 10 × levels gained + 25 success − 25 fail − 10 per helper turn after the first`; `best_index` = argmax, earliest wins ties; `critic_score` = per-message rubric score of the candidate's target skill; `trust_series[0]` = trust before the replaced message.
- `whatif/cache.py`: delegates to `embed.cached_scope()` (ContextVar, this request only, TTL-expiring cache; integrator's 20afbfe). The global embedder swap and the private `_vectors` dict are gone. p95 still ~0.6 s, outputs identical (eval numbers unchanged before the policy change). `whatif.cache.warm_up()` warms every scenario/locale's exemplars for `main.warm_up`.
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

## Numbers (FR_EMBED=fastembed, trained detector, FR_LLM=0; English split "scripted" n = 90, Spanish "scripted_es" Maya n = 18)
- 3 diverse paths 100% / 100%; best beats actual (value, trust) 100% / 100%; success 100% / 100%; best ≥ textbook 100% / 100%; deterministic 100% / 100%.
- mean trust gain +68.6 / +57.4 (before the policy: +76.2 / +71.2); value over textbook +51.9 / +53.3 (before: +57.5 / +65.9).
- paths asking directly twice 0/270 / 0/54 (before: 110/270 / 40/54); later messages shared with another card 2.2% / 11.0% (before: 89% / 94%).
- latency p50/p95 0.48/0.61 s / 0.56/0.67 s.
- unsafe candidates 0/897 / 0/200; unsafe friend bubbles 0/2,146 / 0/520; wrong-language bubbles 0/3,043 / 0/720.
