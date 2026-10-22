# FirstReply: shared context for every lane (authoritative)

*Last updated Thu Oct 22, 2026 (night). If `PLAN_WORKTREES.md` or `FIRSTREPLY.md` conflicts with this file, **this file wins**.*

## 1. Mission
**FirstReply** is a web app for the **2026 Congressional App Challenge** (district IL-11, Rep. Bill Foster).

> *FirstReply lets teens practice the text that could save a friend's life: they chat with a realistic simulated friend who's struggling while models we trained score every reply, keep it safe, and show exactly where they lost the friend and what would have worked.*

- **Developer:** Sahib, a high-school student, solo. Several cloud agents build lanes in parallel. Sahib reviews, labels data, integrates and presents.
- **Ship target:** Sun Oct 25, 10 pm CT (code freeze Sun 2 pm). Hard deadline: Mon Oct 26, 11:00 am CT.
- **Judging:** a district panel of engineers, educators and professionals scores (1) originality and quality of the idea, (2) implementation, UX and design, (3) coding skill. Judges see a ≤3-minute demo video, short written answers (including *"What technical challenge did you face and how did you solve it?"*) and **this GitHub repo**. Usually there's no live interview, so **the code, tests, README and docs must explain themselves.**
- **Why it can win:** mental health keeps winning, but past winners help the person who is struggling. **No CAC winner trains the friend.** CDC YRBS 2023 found that 20.4% of US high schoolers seriously considered suicide, and teens usually tell a peer first.

## 2. Non-negotiable constraints
1. **$0 to run. No paid APIs, no API keys, no LLM calls in the app, tests or scripts.** No OpenAI, Anthropic, Gemini or Grok SDKs. All text data (friend lines, practice replies, safety examples) is **written into files in the repo** by agents or humans. All models are trained locally (scikit-learn on local embeddings).
2. **Safety first.**
   - The friend never describes or hints at suicide methods, means or plans, never encourages harm, and never claims to be a real person in crisis.
   - "Real mode" is fixed text with no AI.
   - The Guardian runs before anything else on every message.
   - Follow `docs/SAFE_MESSAGING.md`.
3. **Speaker awareness.** The user plays the **helper**. *"Are you thinking about killing yourself?"* from the helper is the **best** thing they can say (label `asked_directly`) and must **never** trigger the Guardian. The Guardian has three tiers:
   - **crisis:** the helper themself seems at risk ("honestly i want to die too").
   - **block:** harmful messages toward the friend ("kys", "just do it"), method-seeking, and prompt injection.
   - **concern:** ambiguous distress from the helper.
4. **Deterministic and offline.** The same input gives the same output. Unit tests run offline with `FR_EMBED=hash`.
5. **Explainable by Sahib.** Every lane keeps `docs/how/<lane>.md` in plain language, so a high-school student can answer a skeptical engineer's questions about it.

## 3. Architecture (v2, zero cost)
```
Helper message
  → GUARDIAN (safety lane)      normalizer + human-reviewable lexicon + trained classifier, speaker-aware, <50 ms
       crisis → pause role-play + resources     block → teaching message, nothing else runs
  → SKILL DETECTOR (ml lane)    two local models (embeddings+LR, char-n-gram TF-IDF+LR) → stacked + calibrated
                                → probabilities for 10 labels (contracts.SkillLabel)
  → STATE ENGINE (engine lane)  deterministic rules: trust 0–100, disclosure level 0–4, gates, hysteresis,
                                silence ("Seen"), secrecy flag, endings
  → FRIEND VOICE (engine lane)  picks a line from the reviewed LINE BANK (data/lines, written by the data lane)
                                by (level, reaction) + semantic similarity to the helper's message
                                + anti-repetition; only facts unlocked at the current level may appear
  → VERIFIER (engine lane)      fact gating, Guardian.check_friend, no repeats → else scenario fallback line
  → Phone UI + live trust graph + X-ray mode (frontend lane)
End of chat → CRITIC (ml lane)  per-message calibrated scores + word highlights (occlusion) + "uncertain" flags
                                + verified rewrites (exemplar bank) + 7-skill summary + turning point
"What if"  → ROLLOUTS (whatif lane, Wave B)  exemplar-bank candidates simulated through the real engine + line bank
```
**Why a line bank and not a live chatbot:** every word the friend can say is written in advance, checked by code (100% of lines pass the Guardian) and reviewable by a school counselor. There's no live AI improvising in a suicide-prevention context. It's also free, instant and works offline. "Not an AI wrapper": the intelligence is **our** trained models, rules and algorithms.

## 4. Repo map (integrator-owned unless a lane is named)
| Path | What |
|---|---|
| `backend/app/contracts.py` | **Frozen shared types. Read first.** |
| `backend/app/services.py` | Registry: real module if `IMPLEMENTED = True`, else the stub |
| `backend/app/pipeline.py` | One turn: Guardian → detector → engine → line → verifier |
| `backend/app/session.py` | Conversation tree (rewind/branches), in-memory store with a 60-min TTL |
| `backend/app/content.py` | Loaders for scenarios, line bank, exemplars, real mode, crisis lines, metrics |
| `backend/app/embed.py` | Local embeddings: `fastembed` multilingual model (`paraphrase-multilingual-MiniLM-L12-v2`, 384-d) or `HashEmbedder` for tests |
| `backend/app/api/routes.py`, `main.py` | FastAPI under `/api`; serves `frontend/dist` at `/` |
| `backend/app/stubs/` | Working placeholders. **The app is playable now:** `make dev-stub`. Example payloads are in `stubs/fixtures/` |
| `data/scenarios/*.json` | 5 scenario drafts (Sahib edits the voices) |
| `docs/RUBRIC.md`, `docs/LABEL_GUIDE.md`, `docs/SAFE_MESSAGING.md` | The 7 skills, the 10 labels, the content rules |
| `content/realmode.*.json`, `content/crisis_lines.json` | Fixed crisis steps (EN/ES) and helplines (to be verified by a human) |
| `ownership.yaml` + `scripts/check_ownership.py` | Which lane may touch which paths |
| `Makefile` | `make check`, `make smoke`, `make dev-stub`, `make fixtures`, `make eval`, `make docs` ... |

### API (all JSON; OpenAPI at `/docs`)
| Method | Path | Returns |
|---|---|---|
| GET | `/api/health` | `{ok, contracts_version, components: {guardian, skills, engine, critic, whatif: "real" or "stub"}}` |
| GET | `/api/scenarios` | list of `ScenarioSummary` |
| POST | `/api/sessions` `{scenario_id, locale, country}` | `SessionView {session_id, root_id, head_id, state, nodes}` |
| GET | `/api/sessions/{id}` | `SessionView` |
| POST | `/api/sessions/{id}/messages` `{text, parent_node_id?}` | `TurnResponse` (Guardian, events and states included, for X-ray mode). 409 if ended, 422 if >500 chars |
| POST | `/api/sessions/{id}/rewind` `{node_id}` | `SessionView` |
| GET | `/api/sessions/{id}/tree` | all nodes (for the branch view) |
| POST | `/api/sessions/{id}/finish` | `CriticReport` |
| POST | `/api/sessions/{id}/whatif` `{node_id?}` | `WhatIfResult` (defaults to the turning point; 409 if none) |
| GET | `/api/realmode?lang=en&country=US` | fixed steps plus `crisis {lines, emergency}` |
| POST | `/api/guardian/check` `{text}` | `GuardianResult` (Transparency-page demo) |
| GET | `/api/metrics` | `{components, records}` from `eval/reports/*.json` |

### Data file formats (DATA lane writes; others read)
- `data/lines/<scenario_id>.<locale>.jsonl`: one `contracts.Line` per row.
- `data/exemplars/<scenario_id>.<locale>.jsonl`: one `contracts.Exemplar` per row.
- `data/skills/`:
  - `contexts.jsonl`: `{context_id, scenario_id, level, friend_messages: [..]}`
  - `replies.jsonl`: `{id, context_id, text, style, lang, intended: {label: bool}}`
  - `blind_labels.jsonl`, `queue.jsonl`, `human_labels.jsonl`
  - `final.jsonl`: `{id, context_id, scenario_id, level, context: [..], text, lang, labels: {label: bool}, label_source}`
  - `splits/{train,val,test}.jsonl` (same rows as `final.jsonl`)
  - `survey_real.jsonl`: real anonymous replies, test set only
- `data/guardian/messages.jsonl`: `{id, text, category, lang, style}` with category one of `self_risk | concern | harm_to_other | method_seeking | prompt_injection | asking_friend | tricky_negative | neutral`, plus `data/guardian/splits/`.
- `data/redteam/attacks.jsonl`: `{id, strategy, text, expected_action}`.

### Evaluation reports
`eval/reports/<lane>_<name>.json` holds a list of `{"lane", "metric", "value", "n", "split", "notes", "created"}`. They feed the README tables and the Transparency page.

## 5. Lanes
| Lane | Branch | Model | Wave | Builds |
|---|---|---|---|---|
| **engine** | `wt/engine` | Opus 5.5 | A (now) | State machine, line-bank actor, verifier and bank validator, turning points |
| **safety** | `wt/safety` | Opus 5.5 | A (now) | Guardian: normalizer, lexicon, speaker-aware rules, trained classifier, evaluation |
| **data** | `wt/data` | Sonnet 5.5 | A (now) | All text datasets (practice replies, Guardian examples, ~1,000 friend lines, exemplars, attacks) plus the labeling tool and dataset tooling |
| **ml** | `wt/ml` | Opus 5.5 | A (now) | Skill detector (2-model ensemble, calibration), explanations, critic, rewrites, kappa |
| **frontend** | `wt/frontend` | Opus 5.5 | A (now) | The entire UI (React + TS + Tailwind) against the stub API |
| whatif | `wt/whatif` | Opus 5.5 | B (after M2) | Deterministic multi-turn rollouts of better replies |
| redteam | `wt/redteam` | Opus 5.5 | B | Adversarial runs, fuzzing, regression tests, CI, README metrics |
| deploy | `wt/deploy` | Opus 5.5 | B | Dockerfile, Hugging Face Spaces, rate limits, security headers, warm-up, load test |
| *integrator* | `claude/amazing-carson-31tzo3` | Opus 5.5 | all | Contracts, services, pipeline, API, content drafts, merges lanes at merge windows |

**Cross-lane dependencies (never wait; never commit another lane's files):**
- **engine** needs friend lines from **data**. Build and test with a small fixture bank under `tests/unit/engine/fixtures/`. When data has pushed, read the real bank **read-only**: `git fetch origin wt/data && git show origin/wt/data:data/lines/<file>`, or `git archive origin/wt/data data/lines | tar -x -C /tmp/wtdata`.
- **ml** needs labeled replies from **data**. Use the same read-only approach into a temp dir, and commit only `models/` artifacts and reports.
- **safety** needs Guardian examples from **data**. Same approach, plus its own `data/guardian_extra/`.
- **frontend** uses the stub API (`make dev-stub`) and depends on no other lane.
- If something you need isn't there yet: finish everything else, document the gap in `wt-notes/<lane>.md`, push and end your session. **Don't wait in a loop.** The integrator will restart you when the data lands.

## 6. Integration
- Lanes push **only** to their own `wt/<lane>` branch. No PRs, no merges of other lanes, never touch `main`.
- At merge windows the integrator merges lanes into `claude/amazing-carson-31tzo3` in this order: **safety → engine → data → ml → frontend** (Wave B: whatif → deploy → redteam), running `make check && make smoke` after each. Sahib merges that into `main`.
- Merge windows (CT): M1 Fri ~4:30 pm, **M2 Fri 10 pm ("Friday Night Playable")**, M3 Sat 2 pm (public URL), **M4 Sat 10 pm (feature freeze)**, **M5 Sun 2 pm (code freeze)**.

## 7. Quality bar ("good enough to win")
- **It works:** `make check` and `make smoke` pass with your component turned on, and a 6-turn conversation feels believable.
- **It's real engineering:** your own logic and models, tested, with measured numbers in `eval/reports/`. Judges will open the code.
- **It's honest:** report real numbers, even if they're below target, with `n` and the split. Never fake or hard-code results.
- **It's safe:** see §2. When in doubt, choose the safer behavior and note it.
- **It's explainable:** `docs/how/<lane>.md` covers what it does, how it works, why this approach, how it was measured, its limits, and 5 questions a judge might ask (with answers).
- **It's demo-ready:** the video shows the trust graph moving, highlighted words, "here's where you lost them," X-ray mode and the numbers. Build with that shot list in mind.
