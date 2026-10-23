# Whatif lane notes

## Done
- `whatif/candidates.py`: targets from the critic's `missing_skill` + conversation-missing skills; pool = session scenario + locale exemplars at level ±1 (widen to all levels if < 3 skills survive); filters: detector gain ≥ 0.2 on the skill taught (critic's bar), no negative label ≥ 0.5, Guardian `continue`; the critic's exemplar rewrite is candidate #1; MMR (λ 0.7, near-duplicate cosine ≥ 0.9 excluded, new skill required while one exists).
- `whatif/rollout.py`: `IMPLEMENTED = True`. Real `Engine` with `llm_attempts = 0` (bank voice only, zero OpenAI calls). Replaced message + up to 3 helper turns, each by one-step look-ahead (trust Δ + 10 × level Δ ± 25 ending), never repeating a text; "Seen" and endings mirror `pipeline._friend_reply`. `prev_active` passed explicitly (`labels_before`), so replays match the live engine exactly. Deterministic node ids (`<node>.w<i>.<step>u/f`), guardian latency zeroed in rollout nodes.
- `value = final trust + 10 × levels gained + 25 success − 25 fail − 10 per helper turn after the first`; `best_index` = argmax, earliest wins ties; `critic_score` = per-message rubric score of the candidate's target skill; `trust_series[0]` = trust before the replaced message.
- `whatif/cache.py`: per-text embedding cache active only during `simulate()` (never wraps the hash embedder). p95 2.6 s → 0.6 s, identical outputs.
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
- **deploy:** optional warm-up: `backend.app.whatif.cache.warm([ex.text for ex in content.load_exemplars(sid, loc)])` per scenario/locale at startup removes the first-click cost (a cold first call per scenario is ~1 s).

## Known issues
- Evaluation weak points are scripted with weak continuations, so "beats actual" is an easy bar (the textbook comparison is the harder one).
- Look-ahead is greedy (one step), not a full 3-step search.
- The embedding cache swaps the shared embedder during a simulation; concurrent chat turns in that window also get cached vectors (same values, just faster).

## Numbers (FR_EMBED=fastembed, trained detector, FR_LLM=0; split "scripted", n = 90 weak points)
- 3 diverse paths 100%; best beats actual (value) 100%, (final trust) 100%; mean trust gain +76.2.
- best ≥ textbook continuation 100%, mean value +57.5 over it; best path success 100%.
- latency p50 0.49 s, p95 0.64 s; deterministic 100%.
- unsafe candidates 0 / 885 helper messages; unsafe friend lines 0 / 2,183 bubbles; wrong-language bubbles 0 / 3,068.
- Spanish (split "scripted_es", Maya, n = 18): 3 diverse paths 100%, best beats actual 100%, trust gain +71.2, ≥ textbook 100% (+65.9), success 100%, p50/p95 0.55/0.68 s, deterministic 100%, unsafe 0/190 and 0/502, wrong language 0/692.
