# FirstReply: parallel build plan (worktrees + AI agents)

*Written Thu Oct 22, 2026. Read with `FIRSTREPLY.md` (what we're building). This file covers **how** to build it fast with parallel worktrees, which tool runs which lane, what each lane builds, and how everything merges.*

**Tools:** Claude Code Max, Cursor Pro, ChatGPT Plus (includes Codex), OpenAI API key. **Grok is not used anywhere.**

---

## 0. TL;DR (one screen)

1. **Contracts first.** A short "Phase 0" (2–3 h tonight) creates the skeleton: shared data types (`contracts.py`), stub versions of every module that return realistic fake data, the API, the LLM client, tests, CI, and the rules file for agents (`AGENTS.md`). After that, **every lane can work alone and never wait on another**. The frontend runs against the stub API from hour one.
2. **One lane = one branch = one worktree (or cloud session) = one owner.** Each lane may only edit its own folders (`ownership.yaml`), and a script enforces it. That makes merge conflicts nearly impossible.
3. **Lanes:**
   - **Wave A (Fri):** Engine, Safety, ML (Claude Code ×3), Data (Codex), Frontend (you + Cursor), Content (you + ChatGPT, mostly tonight).
   - **Wave B (Sat):** What-if (Claude), Red-team + CI (Codex), Deploy/ops (Claude), Critic polish (Claude), Frontend B (you).
4. **Merge windows:**

   | Window | Time (CT) | What happens |
   |---|---|---|
   | M0 | Thu night | Phase 0 + content |
   | M1 | Fri 4 pm | |
   | **M2** | **Fri 10 pm** | **"Friday Night Playable"** |
   | M3 | Sat 2 pm | First public URL |
   | **M4** | **Sat 10 pm** | **Feature freeze** |
   | **M5** | **Sun 2 pm** | **Code freeze** |

   Merge order within each window: safety → engine → ml → data → whatif → deploy → redteam → frontend.
5. **You have school Friday, and the deadline is Monday 11:00 am CT, also during school.** So run agents **in the cloud** while you're at school (Claude Code on the web, Codex cloud), and **submit Sunday night** (target 10 pm CT). Monday 7 am is emergency buffer only.
6. **You are the bottleneck, not the agents.** You do only what only you can do: content decisions, labeling, the frontend parts you want, approving merges, real-person testing, the video, short answers. Everything else goes to agents.

---

## 1. Things you didn't mention (added to this plan)

| # | Missing piece | Where it's handled |
|---|---|---|
| 1 | **School Friday and Monday morning.** Agents must run in the cloud during school, and you must submit Sunday night. | §2, §15 |
| 2 | **Register and confirm your district tonight.** ZIP 60502 is split between IL-11 and IL-14. | §15 Thu |
| 3 | **Merge the research branch into `main` first** (`claude/amazing-carson-31tzo3`). | §9 |
| 4 | **OpenAI spending cap, response caching, and a fake LLM for tests.** Agents can burn money fast. | §13 |
| 5 | **Refusal test tonight.** The OpenAI model might refuse to role-play a struggling teen. Test before building on it. | Phase 0 step 17, §16 |
| 6 | **Worktree gotchas:** `.env` isn't shared between worktrees (copy it), each dev server needs its own port, and a branch can be checked out in only one worktree at a time. | §9 |
| 7 | **Only one owner for `pyproject.toml`/`uv.lock`/`contracts.py`.** All dependencies are installed up front. | §3, §11 |
| 8 | **Spanish support means the embedding model must be multilingual.** | Phase 0 step 8 |
| 9 | **Deployment memory.** PyTorch is too heavy for free hosts, so use ONNX-based `fastembed` and Hugging Face Spaces (Docker). | §13 |
| 10 | **Protecting the public demo:** the API key never reaches the frontend, plus per-IP rate limits, a daily $ budget, and an automatic switch to "demo mode." | §13, Deploy lane |
| 11 | **Privacy:** no accounts, conversations kept in memory for 60 min only, no message text in logs, a privacy page and disclaimers ("not a crisis service"). | §13 |
| 12 | **Safe-messaging guidelines, crisis numbers checked against official sites, and trademark-safe wording** ("inspired by the QPR model"; not affiliated with QPR Institute or Mental Health First Aid). | Content lane |
| 13 | **Real teen replies:** an anonymous, consented survey gives a *real-world* test set, not just synthetic data. | §18 survey |
| 14 | **A labeling tool and a label guide.** Human labels are the slowest step, so make labeling fast. | Data lane |
| 15 | **"X-ray mode"** that shows the engine working live during the chat, the best shot for the video. | Frontend lane |
| 16 | **A Transparency page** that reads the real evaluation numbers from the backend. | Phase 0, Frontend |
| 17 | **CI runs offline**, with no API keys in GitHub. | Phase 0, Red-team lane |
| 18 | **Demo mode with cached responses**, so the video can be recorded the same way every time. | Deploy and What-if lanes |
| 19 | **Proof you understand it:** a DEVLOG, an explain-back quiz before every merge, and `docs/how/*`. Also an honest AI-use disclosure. | §10, §11, §18 |
| 20 | **Video logistics:** captions, Public visibility, 1080p, under 3:00, the required items, a thumbnail, testing the link in incognito. | §14 |
| 21 | **The other hackathon's deadline and requirements.** Check them. | §15 Thu |
| 22 | **Backups:** push every branch often. A laptop crash shouldn't cost you a day. | §10 |
| 23 | **Agent usage limits:** if Claude hits its limit, move the lane to Codex or Cursor using the same mission prompt. | §2 |
| 24 | **Ask a counselor in person at school Friday.** Email may not get answered before the deadline. | §18 |
| 25 | **Tell a parent or guardian what you're building.** It's a heavy topic, and the counselor may ask. | §15 Thu |
| 26 | **Sleep, and look after yourself.** You'll be reading suicide-related content for days. Take breaks, and 988 is there for you too. | §16 |
| 27 | **Accessibility:** keyboard use, contrast, screen-reader labels, reduced motion. | Frontend lane |
| 28 | **README written for judges:** screenshots or GIF, architecture diagram, evaluation tables, safety section. Optionally rename the repo to `firstreply` (GitHub redirects old URLs). | §14 |

---

## 2. What each tool is for

| Tool | Role in this build | Lanes |
|---|---|---|
| **Claude Code (Max)** | Main builder for hard, safety-critical code and tests. Run locally in worktrees in the evening, and as **Claude Code on the web** (claude.ai/code, cloud sessions on a branch) while you're at school. Keep **at most 3 Claude lanes running at once**, since they share your usage limit. | Phase 0/Integrator, Engine, Safety, ML, What-if, Deploy |
| **Codex (ChatGPT Plus)** | Well-specified, mostly separate tasks: data scripts, labeling tool, red-team harness, CI. Run the CLI or IDE extension in a worktree, or **Codex cloud** on the branch (opens a PR). It reads `AGENTS.md`. | Data, Red-team + CI |
| **Cursor Pro** | **You** building the frontend, with Cursor's agent for scaffolding and boilerplate. Open the `fr-frontend` worktree as its own window. | Frontend A + B |
| **ChatGPT Plus (chat)** | Content drafts (scenarios, rubric, real-mode steps, Spanish drafts you then check), video script, short-answer polishing, survey wording, **logo and thumbnail images**. | Content |
| **OpenAI API key** | Runtime: the friend (Actor), the LLM judge, the simulated helper, the attacker bots, data generation, and the moderation endpoint. **Set a hard monthly budget in the OpenAI dashboard tonight.** | All, through `backend/app/llm.py` only |
| ~~Grok~~ | Not used. | none |

**If you hit a usage limit:** commit and push → open the same branch in another tool → paste the same mission prompt and add *"Continue from the current state of the branch; read wt-notes/<lane>.md first."* Mission prompts are written to work in any of the three tools.

---

## 3. Repo layout and ownership

```
firstreply/                          (your repo)
├─ AGENTS.md  CLAUDE.md               rules for all agents (CLAUDE.md just contains "@AGENTS.md")
├─ FIRSTREPLY.md  PLAN_WORKTREES.md   product plan / this plan
├─ README.md  DEVLOG.md  HOW_IT_WORKS.md (generated from docs/how/*)
├─ ownership.yaml                     which branch may touch which paths
├─ pyproject.toml  uv.lock  Makefile  .env.example  .gitignore    ← INTEGRATOR ONLY
├─ backend/app/
│  ├─ contracts.py                    ← FROZEN after Phase 0 (integrator only)
│  ├─ services.py  pipeline.py  config.py  llm.py  embed.py  prompts/__init__.py   ← integrator
│  ├─ api/routes.py                   ← integrator
│  ├─ stubs/ + stubs/fixtures/        ← integrator (fake data the frontend uses)
│  ├─ engine/  state.py actor.py verifier.py tree.py turning_point.py config.yaml   ← ENGINE
│  ├─ safety/  normalizer.py lexicon.yaml guardian.py train_guardian.py artifacts/  ← SAFETY
│  ├─ ml/      skill_detector.py train.py explain.py judge.py critic.py kappa.py    ← ML
│  ├─ whatif/  rollout.py                                                          ← WHATIF
│  ├─ ops/     ratelimit.py budget.py demo.py privacy.py                           ← DEPLOY
│  └─ prompts/ actor.md(ENGINE) judge.md(ML) helper_sim.md(WHATIF) attacker.md(REDTEAM)
├─ models/                            ← ML (skill_detector.joblib + metadata)
├─ data/
│  ├─ scenarios/*.json                ← CONTENT
│  ├─ guardian/                       ← SAFETY
│  └─ skills/                         ← DATA
├─ content/  realmode.en.json realmode.es.json crisis_lines.json   ← CONTENT
├─ docs/
│  ├─ RUBRIC.md LABEL_GUIDE.md SAFE_MESSAGING.md                   ← CONTENT
│  ├─ DATASET.md (DATA)  DEPLOY.md (DEPLOY)
│  └─ how/<lane>.md                   ← each lane writes only its own file
├─ scripts/  data/ (DATA)  check_ownership.py spike_actor.py (integrator)  report.py (REDTEAM)
├─ tools/labeler/                     ← DATA
├─ eval/  README.md (integrator)  guardian/ (SAFETY)  skills/ (ML)  redteam/ (REDTEAM)  reports/*.json (each lane writes its own prefix)
├─ tests/ unit/{engine,safety,ml,whatif,ops}/ (per lane)  safety/ (REDTEAM)  e2e/ (integrator)
├─ wt-notes/<lane>.md                 ← each lane's notes and "Requests" to the integrator
├─ .github/workflows/ci.yml           ← Phase 0 creates; REDTEAM extends
├─ Dockerfile  deploy/                ← DEPLOY
└─ frontend/                          ← YOU (Cursor)
```

**`ownership.yaml`** (created in Phase 0, enforced by `scripts/check_ownership.py`):
```yaml
wt/engine:   [backend/app/engine/**, backend/app/prompts/actor*.md, tests/unit/engine/**, docs/how/engine.md, eval/reports/engine_*, eval/engine/**, wt-notes/engine.md]
wt/safety:   [backend/app/safety/**, data/guardian/**, tests/unit/safety/**, eval/guardian/**, eval/reports/safety_*, docs/how/safety.md, wt-notes/safety.md]
wt/data:     [scripts/data/**, tools/labeler/**, data/skills/**, docs/DATASET.md, docs/how/data.md, tests/unit/data/**, wt-notes/data.md]
wt/ml:       [backend/app/ml/**, backend/app/prompts/judge*.md, models/**, tests/unit/ml/**, eval/skills/**, eval/reports/ml_*, docs/how/ml.md, wt-notes/ml.md]
wt/whatif:   [backend/app/whatif/**, backend/app/prompts/helper_sim*.md, tests/unit/whatif/**, scripts/precompute_demo_whatif.py, eval/reports/whatif_*, docs/how/whatif.md, wt-notes/whatif.md]
wt/redteam:  [eval/redteam/**, tests/safety/**, .github/workflows/**, scripts/report.py, backend/app/prompts/attacker*.md, eval/reports/redteam_*, docs/how/redteam.md, wt-notes/redteam.md]
wt/deploy:   [Dockerfile, .dockerignore, deploy/**, backend/app/ops/**, tests/unit/ops/**, docs/DEPLOY.md, docs/how/deploy.md, eval/reports/deploy_*, wt-notes/deploy.md]
wt/frontend: [frontend/**, wt-notes/frontend.md]
wt/content:  [data/scenarios/**, content/**, docs/RUBRIC.md, docs/LABEL_GUIDE.md, docs/SAFE_MESSAGING.md]
main:        ["**"]   # integrator only
```

**The trick that prevents conflicts:** Phase 0 creates *every* file above with its function signatures, plus `IMPLEMENTED = False`. `services.py` uses a module's real code only when it sets `IMPLEMENTED = True`, and falls back to the stub otherwise. So a lane "turns itself on" by editing **only its own file**, and nobody touches shared wiring.

---

## 4. Contracts (frozen in Phase 0)

`backend/app/contracts.py`. Every lane codes against this. Changes go only through the integrator (see §11).

```python
from enum import Enum
from typing import Literal, Protocol
from pydantic import BaseModel, Field

CONTRACTS_VERSION = "1.0"

class SkillLabel(str, Enum):           # 10 labels the skill detector predicts
    CHECKED_IN = "checked_in"          # noticed / reached out
    VALIDATED = "validated"            # reflected feelings, no judging
    ASKED_DIRECTLY = "asked_directly"  # asked directly about suicide
    ENCOURAGED_HELP = "encouraged_help"
    REFERRED_ADULT = "referred_adult"  # counselor / trusted adult, offered to go with them
    REFERRED_988 = "referred_988"
    FOLLOW_UP = "follow_up"            # committed to check in / stay
    DISMISSED = "dismissed"            # minimized / joked / changed subject   (negative)
    ADVICE_DUMP = "advice_dump"        # jumped to fixing / lecturing          (negative)
    PROMISED_SECRECY = "promised_secrecy"  #                                    (negative)

SkillProbs = dict[SkillLabel, float]   # 0..1 per label

# 7 rubric skills shown to users = mapping of the 10 labels (in ml/critic.py):
# check_in=CHECKED_IN, listen=VALIDATED & not(DISMISSED|ADVICE_DUMP), ask_directly=ASKED_DIRECTLY,
# no_secrecy=not PROMISED_SECRECY, persuade=ENCOURAGED_HELP, refer=REFERRED_ADULT|REFERRED_988, follow_up=FOLLOW_UP

class Fact(BaseModel):
    id: str
    text: str

class LevelSpec(BaseModel):
    label: str
    facts: list[Fact]

class Persona(BaseModel):
    name: str
    age: int
    style: str
    guardedness: Literal["open", "guarded"]

class Scenario(BaseModel):
    id: str
    title: str
    persona: Persona
    situation: str
    opening: list[str]
    levels: dict[int, LevelSpec]              # 0..4, never contains methods
    fallback_lines: dict[int, list[str]]
    content_warning: str
    review_status: Literal["draft", "reviewed"] = "draft"

class Highlight(BaseModel):
    start: int
    end: int
    text: str
    label: SkillLabel
    delta: float

class GuardianResult(BaseModel):
    level: Literal["none", "concern", "crisis"]
    action: Literal["continue", "show_resources", "pause_roleplay", "block_message"]
    categories: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    score: float = 0.0
    sources: list[Literal["lexicon", "classifier", "moderation"]] = Field(default_factory=list)
    latency_ms: float = 0.0

class Flags(BaseModel):
    asked_directly_ever: bool = False
    promised_secrecy: bool = False
    referral_turns: list[int] = Field(default_factory=list)

class State(BaseModel):
    trust: float = 30.0                       # 0..100
    level: int = 0                            # disclosure 0..4
    turn: int = 0
    flags: Flags = Field(default_factory=Flags)
    status: Literal["active", "silent", "ended_success", "ended_fail", "paused_crisis"] = "active"
    last_delta: float = 0.0

class ActorOutput(BaseModel):
    bubbles: list[str] = Field(default_factory=list, max_length=3)   # [] = left on "Seen"
    used_fact_ids: list[str] = Field(default_factory=list)
    tone: str = ""

class VerifierResult(BaseModel):
    ok: bool
    reasons: list[str] = Field(default_factory=list)

class Node(BaseModel):
    id: str
    parent_id: str | None
    role: Literal["user", "friend", "system"]
    bubbles: list[str]
    events: SkillProbs | None = None          # on user nodes
    guardian: GuardianResult | None = None
    state_after: State
    seen_no_reply: bool = False

class Session(BaseModel):
    id: str
    scenario_id: str
    locale: str = "en"
    country: str = "US"
    nodes: dict[str, Node]
    head_id: str

class TurnResponse(BaseModel):
    user_node: Node
    friend_node: Node | None
    state_before: State
    state_after: State
    crisis: bool = False

class MessageScore(BaseModel):
    node_id: str
    probs: SkillProbs
    uncertain: list[SkillLabel] = Field(default_factory=list)
    highlights: list[Highlight] = Field(default_factory=list)
    rewrite: str | None = None

class TurningPoint(BaseModel):
    node_id: str
    trust_drop: float
    reason: str

class CriticReport(BaseModel):
    per_message: list[MessageScore]
    skill_summary: dict[str, float]           # 7 rubric skills, 0..1
    turning_point: TurningPoint | None = None
    missed_opportunities: list[str] = Field(default_factory=list)

class WhatIfPath(BaseModel):
    candidate: str
    critic_score: float
    nodes: list[Node]
    trust_series: list[float]
    value: float

class WhatIfResult(BaseModel):
    from_node_id: str
    paths: list[WhatIfPath]
    best_index: int
    simulated: bool = True

# ---- service interfaces (stubs implement these too) ----
class GuardianService(Protocol):
    def check_user(self, text: str, history: list[Node]) -> GuardianResult: ...
    def check_friend(self, text: str) -> GuardianResult: ...

class SkillService(Protocol):
    def predict(self, text: str, context: list[str]) -> SkillProbs: ...
    def explain(self, text: str, context: list[str]) -> list[Highlight]: ...

class EngineService(Protocol):
    def initial_state(self, scenario: Scenario) -> State: ...
    def update(self, state: State, events: SkillProbs, scenario: Scenario) -> State: ...
    async def generate(self, scenario: Scenario, state: State, history: list[Node], locale: str) -> ActorOutput: ...
    def verify(self, out: ActorOutput, scenario: Scenario, state: State) -> VerifierResult: ...
    def turning_point(self, nodes: list[Node]) -> TurningPoint | None: ...

class CriticService(Protocol):
    async def score_conversation(self, session: Session) -> CriticReport: ...

class WhatIfService(Protocol):
    async def simulate(self, session: Session, node_id: str) -> WhatIfResult: ...
```

**API (Phase 0 builds all of these, backed by stubs at first):**

| Method | Path | Returns |
|---|---|---|
| GET | `/api/health` | ok and the component status (stub/real for each) |
| GET | `/api/scenarios` | list of `{id, title, persona.name, guardedness, content_warning}` |
| POST | `/api/sessions` `{scenario_id, locale, country}` | `{session_id, opening friend Node, state}` |
| POST | `/api/sessions/{id}/messages` `{text, parent_node_id?}` | `TurnResponse` (includes Guardian, events and states, for X-ray mode) |
| POST | `/api/sessions/{id}/rewind` `{node_id}` | `{head_id, state}` |
| GET | `/api/sessions/{id}/tree` | all nodes (for the branch view) |
| POST | `/api/sessions/{id}/finish` | `CriticReport` |
| POST | `/api/sessions/{id}/whatif` `{node_id?}` | `WhatIfResult` (defaults to the turning point) |
| GET | `/api/realmode?lang=en&country=US` | static steps plus crisis lines (**no AI**) |
| POST | `/api/guardian/check` `{text}` | `GuardianResult` (for the Transparency page demo) |
| GET | `/api/metrics` | everything in `eval/reports/*.json` (feeds the Transparency page) |

---

## 5. Phase 0: foundation (Thu night, ~2–3 h of agent time, ONE session)

**Who:** the integrator. Use one Claude Code session in your main checkout, **or let this cloud Claude session do it right now and push it**, which is fastest. Meanwhile you do the Content lane in ChatGPT (§6).

**Mission prompt (paste into Claude Code):**
```
You are the INTEGRATOR for FirstReply. First read FIRSTREPLY.md and PLAN_WORKTREES.md §3–§4 and §10.
Goal: build the foundation so parallel lanes can work without blocking or conflicting.
Do NOT implement lane logic (engine/safety/ml/whatif/ops) beyond stubs.

Build, committing in small steps prefixed "phase0:":
1. Python 3.11 project managed by uv. pyproject.toml with ALL deps now: fastapi, uvicorn[standard],
   pydantic>=2, python-dotenv, openai, tenacity, diskcache, fastembed, numpy, pandas, scikit-learn,
   joblib, pyyaml, httpx, matplotlib; dev: pytest, pytest-asyncio, ruff. Commit uv.lock.
2. Create the exact layout in PLAN_WORKTREES.md §3. Every module file exists with docstrings,
   function signatures matching contracts, `IMPLEMENTED = False`, and NotImplementedError bodies.
3. backend/app/contracts.py exactly as §4 (pydantic v2; fix any typing issues without changing names/fields).
4. backend/app/stubs/: stub implementations of every service returning realistic data from
   backend/app/stubs/fixtures/*.json (a 10-turn session with states rising/falling, a critic report with
   highlights + a turning point, a what-if result with 3 paths). Make fixtures look real — the frontend is
   built against them.
5. backend/app/services.py: registry returning the real module if module.IMPLEMENTED else the stub.
   GET /api/health reports which components are real.
6. backend/app/pipeline.py: the turn pipeline against interfaces: guardian.check_user → if crisis:
   pause + system node → skills.predict → engine.update → if status silent: Seen node →
   engine.generate → engine.verify (regenerate ≤2, else scenario fallback line) → guardian.check_friend
   (block → fallback) → save nodes in session tree. Ops hooks: call ops.ratelimit.check(), ops.budget.allowed(),
   ops.privacy.store (stubs are no-ops). Unit-test the pipeline with stubs + FakeLLM.
7. backend/app/api/routes.py: all endpoints in §4 (async). In-memory session store via ops.privacy stub.
   Serve frontend/dist at "/" if it exists. /api/metrics returns merged eval/reports/*.json.
8. backend/app/llm.py: OpenAI wrapper. chat_json(prompt_name, vars, schema: type[BaseModel], role:
   "actor"|"judge"|"bulk", temperature=0.7, seed=None) using Structured Outputs; async variant; tenacity
   retries; diskcache cache ON by default in dev (key = hash(model, messages, schema, temperature, seed));
   usage log to eval/logs/llm_usage.jsonl (tokens, est. cost, role — NEVER message text when FR_ENV=prod);
   daily budget guard (LLM_DAILY_BUDGET_USD); moderate(text) via the moderation endpoint (returns
   self-harm category scores); FakeLLM (deterministic canned outputs per schema) used automatically when
   FR_FAKE_LLM=1 and in all unit tests. Models from env: OPENAI_MODEL_ACTOR, OPENAI_MODEL_JUDGE,
   OPENAI_MODEL_BULK (do not hardcode model names elsewhere).
9. backend/app/embed.py: fastembed wrapper (ONNX, no torch). Use a MULTILINGUAL model (check
   TextEmbedding.list_supported_models(); prefer sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2),
   lazy singleton, batch embed, LRU cache, cosine helper.
10. backend/app/prompts/__init__.py: loads prompts/*.md with {{var}} placeholders; placeholder files
    actor.md, judge.md, helper_sim.md, attacker.md.
11. data/scenarios/_schema.json (from contracts.Scenario) + one complete sample scenario;
    content/realmode.en.json + content/crisis_lines.json placeholders (marked UNVERIFIED).
12. Makefile targets: dev (uvicorn :8000), dev-stub (FR_STUB=1 FR_FAKE_LLM=1), check (ruff check +
    ruff format --check + pytest -m "not llm"), smoke (tests/e2e scripted 6-turn conversation through
    the API with FakeLLM), ownership (scripts/check_ownership.py), train (ml), guardian-train (safety),
    data-generate / data-prelabel / data-queue / label / data-split / counselor-export / counselor-import (data),
    eval (runs every eval/*/run*.py that exists), report (scripts/report.py), redteam, precompute-demo, docker.
    Targets whose scripts aren't implemented yet print "not implemented yet (lane X)".
13. ownership.yaml exactly as §3 + scripts/check_ownership.py [branch] (diff vs main; exit 1 listing violations).
14. .github/workflows/ci.yml: setup uv, `make check`, ownership check on pull requests. No secrets.
15. AGENTS.md = PLAN_WORKTREES.md §10 verbatim; CLAUDE.md containing only "@AGENTS.md";
    docs/how/{engine,safety,data,ml,whatif,redteam,deploy}.md skeletons; HOW_IT_WORKS.md generator
    (make docs concatenates docs/how/*); DEVLOG.md; wt-notes/README.md; eval/README.md with the report
    JSON schema: [{"lane","metric","value","n","split","notes","created"}]; .env.example; .gitignore
    (.env, .cache/, .venv/, node_modules/, frontend/dist/, eval/logs/); README markers
    <!-- METRICS:START --> <!-- METRICS:END -->.
16. frontend/: Vite + React + TypeScript + Tailwind scaffold, /api proxy → http://localhost:8000,
    script "gen:api" (openapi-typescript from http://localhost:8000/openapi.json → src/api/types.ts),
    one placeholder page listing scenarios from the API. Keep it minimal — the human builds the UI.
17. scripts/spike_actor.py: with the REAL OpenAI actor model and a draft actor prompt, run the sample
    scenario at levels 0–4 (2 turns each) and print outputs + any refusals/safety disclaimers + latency.
Acceptance: make check green; make dev-stub then curl every endpoint returns fixture JSON; make smoke
passes; npm run dev shows scenarios; check_ownership works. End with a summary of stubs and decisions,
and append a DEVLOG.md entry.
```

**After Phase 0 (you, about 20 min):**
1. Run `uv run python scripts/spike_actor.py` and **read the outputs**:
   - Does the friend sound like a real teen?
   - Does the model refuse or add "as an AI…" disclaimers?
   - Pick the actor, judge and bulk models (put them in `.env`) and write the choice in `DEVLOG.md`.
   - If it refuses, see §16 (fallback: the friend's lines are pre-written and the LLM only rephrases them).
2. Commit the content-lane files (§6). Tag: `git tag v0-contracts && git push --tags`.
3. Create the worktrees and cloud lanes (§9) and paste the mission prompts.

---

## 6. Content lane (you + ChatGPT Plus, tonight, in parallel with Phase 0)

**Why it's urgent:** scenarios, the rubric and the label guide feed the Data lane (generation), ML (judge prompt) and Engine (tests). They must be on `main` before the Data lane starts generating.

| Deliverable | File | Notes |
|---|---|---|
| 5 scenarios | `data/scenarios/*.json` | Breakup; failing a class; moved schools/lonely; being bullied; "fine" but giving things away. Each has a persona (name, age, texting style, open/guarded), opening texts, facts at levels 0–4, and fallback lines per level. **No methods or means, ever.** **You** edit the texting style until it sounds like your friends actually text. That's your real contribution. |
| Rubric | `docs/RUBRIC.md` | The 7 skills, each with a definition, 3 good and 3 bad example replies, and how it maps to the 10 labels. Line at top: *"Inspired by publicly described gatekeeper frameworks (e.g., the QPR model: Question, Persuade, Refer) and teen peer-support guidance. Not affiliated with or endorsed by QPR Institute or Mental Health First Aid."* |
| Label guide | `docs/LABEL_GUIDE.md` | Decision rules for the 10 labels plus edge cases. Example: "are you ok?" = `checked_in`, but **not** `asked_directly`. "Asked directly" requires naming suicide or self-harm explicitly. |
| Real mode | `content/realmode.en.json`, `.es.json` | Steps:<br>• stay with them / keep talking<br>• ask directly<br>• don't promise secrecy<br>• tell a trusted adult *today*<br>• call/text **988**<br>• **911** if in immediate danger<br>Static text, **no AI**. Have a fluent speaker check the Spanish. |
| Crisis lines | `content/crisis_lines.json` | US 988 (call/text), Canada 988, UK Samaritans 116 123, Australia Lifeline 13 11 14, plus a findahelpline.com link for others. **Check every number on its official site** and record the date checked. |
| Safe messaging | `docs/SAFE_MESSAGING.md` | A checklist based on public safe-messaging guidance (AFSP, reportingonsuicide.org): no method details, don't frame suicide as a solution, include hope and resources, no graphic content. |

**ChatGPT prompt for the scenarios:**
```
I'm building a suicide-prevention TRAINING simulator where high-school students practice responding
to a friend who is struggling. Write 5 scenario files as JSON matching this schema: [paste _schema.json].
Rules: realistic 2026 teen texting (lowercase, short, some slang/emoji, not cringe); facts at disclosure
levels 0 (surface) → 1 (stress) → 2 (hopelessness) → 3 (has had thoughts of not wanting to be alive) →
4 (open to getting help with support). NEVER include suicide methods, means, plans, or graphic details.
Follow safe-messaging guidelines. Include 3 fallback lines per level. Scenarios: [list the 5].
```
Then **you rewrite the voices yourself.** Judges and the counselor will read these.

---

## 7. Wave A lanes (Fri; start them Thu night before bed)

Every lane follows the same routine:
1. Paste the mission prompt.
2. Have the agent **plan first** and review the plan (2 min).
3. Let it build, with tests written first.
4. It commits and pushes often.
5. Before merging: `make check` + `make ownership` + the **explain-back quiz** (§18).

### Lane 1: ENGINE (Claude Code A) · branch `wt/engine` · worktree `../fr-engine` · port 8101
```
Lane: ENGINE (branch wt/engine). Read AGENTS.md, FIRSTREPLY.md §6, PLAN_WORKTREES.md §4 + this lane.
Own ONLY the paths for wt/engine in ownership.yaml. Goal: the friend is a state machine OUR code controls;
the LLM is only the voice. Write tests first; commit after each green step ("engine: ...").
1. engine/state.py — pure, deterministic. initial_state(scenario); update(state, events: SkillProbs, scenario) -> State.
   Events → booleans at p ≥ 0.5. Weights in engine/config.yaml: validated +12, asked_directly +15,
   checked_in +8, encouraged_help +6, referred_adult +8, referred_988 +6, follow_up +5, dismissed −20,
   advice_dump −10, promised_secrecy −15, decay −2/turn; guarded persona multiplies positive weights ×0.7.
   Clamp 0–100. Disclosure levels 0–4, up-thresholds [0,25,45,60,75]; hysteresis: drop a level only if
   trust < (threshold of current level − 15). Gates: level 3 requires flags.asked_directly_ever; level 4
   requires level ≥3 reached + a referral (adult or 988) within the last 3 turns. promised_secrecy sets a
   flag; a later referral costs −10 and marks the friend's next reply tone "you promised". Silent: trust
   dropped ≥15 this turn or trust < 20 → status "silent" for one turn (friend leaves you on Seen).
   End: success when level 4 reached and referral accepted; fail when trust < 10 two turns in a row; max 16 turns.
   ≥20 unit tests incl. property tests (trust always in bounds; same inputs → same outputs; hysteresis).
2. engine/actor.py — async generate(scenario, state, history, locale) -> ActorOutput via
   llm.chat_json("actor", ..., schema=ActorOutput, role="actor"). Pass ONLY facts with level ≤ state.level.
   prompts/actor.md: persona + teen texting style guide + 1–3 bubbles + current tone + hard rules (never
   methods/means/plans, never encourage harm, stay in character, deflect method questions, respond in locale).
3. engine/verifier.py — verify(out, scenario, state) -> VerifierResult: (a) used_fact_ids ⊆ unlocked;
   (b) leak detection: cosine(embed(bubble), embed(locked fact)) > threshold (tune in tests) → leak;
   (c) persona break phrases ("as an ai", "language model", "i'm an assistant"); (d) output safety via
   services.guardian().check_friend (stub until SAFETY merges). Report every reason.
4. engine/tree.py — node creation, full State snapshot per node, rewind(node_id) restores exactly, branches.
5. engine/turning_point.py — largest single-turn trust drop among user turns + missed opportunities
   (friend at level ≥2 and next user reply lacks asked_directly).
6. Set IMPLEMENTED = True in each finished module (services.py then uses it).
7. eval/engine/trajectories.py → PNG trust trajectories for 3 scripted conversations (good / dismissive /
   recovery) + eval/reports/engine_trajectories.json.
8. docs/how/engine.md in plain language: the trust formula, why deterministic, why the LLM can't decide
   disclosure, how leak detection works.
Acceptance: make check green; one @pytest.mark.llm test runs 3 real turns with zero verifier failures.
```

### Lane 2: SAFETY (Claude Code B) · `wt/safety` · `../fr-safety` · port 8102
```
Lane: SAFETY (branch wt/safety). Read AGENTS.md, FIRSTREPLY.md §6, PLAN_WORKTREES.md §4 + this lane.
Own ONLY wt/safety paths. Goal: a local, layered Guardian that runs before any LLM call, works offline,
p95 < 50 ms, understands teen slang, with honestly measured recall. Tests first; commit often ("safety: ...").
1. safety/normalizer.py: NFKC, lowercase, leetspeak map (1→i 3→e 0→o 4/@→a $→s 7→t), squeeze repeated
   letters (3+ → 2), join spaced letters ("k m s"→"kms"), punctuation tricks ("k.m.s"), emoji → tags
   (🪦 grave, 😭 crying; 💀 = AMBIGUOUS — teens use it for laughing, never flag it alone), Spanish accent
   folding, common misspellings. One test per rule.
2. safety/lexicon.yaml (human-reviewable): self_risk (explicit, indirect, slang/algospeak e.g. "kms",
   "unalive", "sewerslide", Spanish e.g. "quiero morirme", "no quiero vivir"), harm_to_other /
   encouragement ("kys", "just do it" in context), method_seeking, prompt_injection ("ignore your
   instructions", "you are now", "system prompt"), and TRICKY NEGATIVES ("this test is killing me",
   "i'm dead 💀 lol", "killed it", "i'd die for those shoes"). Word-boundary matching on normalized text.
3. Dataset data/guardian/: generate with llm (role="bulk") ~600 labeled, NON-GRAPHIC messages, never
   methods: self-risk explicit/indirect/slang/Spanish (~200), harmful-to-friend + method-seeking (~100),
   tricky negatives (~200), neutral (~100). Add programmatic perturbations (leetspeak, spacing, stretching,
   emoji insertion) as a robustness set. Seeded stratified train/val/test. Write a 60-item sample to
   data/guardian/review_sample.csv for the HUMAN to review.
4. safety/train_guardian.py: app.embed + LogisticRegression(class_weight="balanced"); choose threshold on
   val for self_risk recall ≥ 0.95 (report precision there). Two tiers: concern → show_resources,
   crisis → pause_roleplay. Save backend/app/safety/artifacts/guardian.joblib (+ metadata).
5. safety/guardian.py implementing GuardianService: check_user = lexicon OR classifier (OR moderation
   only if FR_USE_MODERATION=1 and online — never required); check_friend = method/means/encouragement
   detection for persona output. Return evidence + sources + latency. IMPLEMENTED = True.
6. eval/guardian/run_eval.py → eval/reports/safety_*.json + PR-curve PNG: per-category precision/recall/F1
   on test; robustness (decision unchanged under perturbation) WITH vs WITHOUT normalizer; latency p50/p95;
   comparison table on the slang subset: lexicon-only vs classifier-only vs combined vs OpenAI moderation.
7. docs/how/safety.md (plain language: why recall over precision, why local, what "tricky negatives" are).
Acceptance: make check green offline (dataset + joblib committed); latency test passes; numbers reported
honestly even if below target.
```

### Lane 3: DATA (Codex) · `wt/data` · `../fr-data` (or Codex cloud on the branch) · no server
```
Lane: DATA (branch wt/data). Read AGENTS.md, PLAN_WORKTREES.md §4 + this lane, docs/LABEL_GUIDE.md,
docs/RUBRIC.md, data/scenarios/*.json. Own ONLY wt/data paths. Use app.llm for all LLM calls.
Goal: a high-quality labeled dataset for the 10 SkillLabels + a FAST human labeling tool.
PRIORITY: push data/skills/prelabeled.jsonl by Friday 12:00 CT (the ML lane depends on it).
1. scripts/data/generate_contexts.py: per scenario × level 0–4, 3 in-persona friend messages → contexts.jsonl.
2. scripts/data/generate_replies.py: per context ~10 teen replies from a design matrix — each label
   positive and negative, mixed replies, short/long, styles (clean, slang, typos, emoji, Spanish ~15%),
   quality (great / okay / harmful-but-realistic). Target ≈ 800 after dedupe (cosine > 0.95 removed).
3. scripts/data/prelabel.py: TWO independent labeling passes (role="judge", two different prompt wordings
   built from docs/LABEL_GUIDE.md, temperature 0, structured output of 10 booleans + short rationale)
   → prelabeled.jsonl with per-label agreement flags.
4. scripts/data/queue.py: human queue = all items with any disagreement + 100 random fully-agreed items (audit).
5. tools/labeler/: tiny local web app (FastAPI + one HTML/JS page, no new deps): shows the last 2 friend
   messages + the reply + LLM suggestions pre-checked; keys 1–9,0 toggle the 10 labels, Enter = save & next,
   B = back, progress bar, autosave to data/skills/human_labels.jsonl. Must make 300 items doable in ~60 min.
6. scripts/data/merge_labels.py + split.py: final label = human if present else agreed LLM label;
   audit agreement per label (LLM vs human) → eval/reports/data_audit.json (allowed: write via your own path
   data/skills/ and request integrator if needed); stratified 70/15/15 split, seeded, grouped by context to
   avoid leakage; import path for data/skills/survey_real.jsonl (anonymous consented survey replies; ALWAYS test-only).
7. scripts/data/export_counselor.py → data/skills/counselor_sheet.csv (30 test items incl. real survey
   replies; Google-Sheets-friendly; instructions row) and import_counselor.py → counselor_labels.jsonl.
8. docs/DATASET.md (dataset card: generation, label definitions, counts per label, audit agreement,
   limitations, ethics) + docs/how/data.md. Unit tests (offline) for dedupe, split, merge.
```
*(You'll see one "allowed: … request integrator" line: the audit report path is under `eval/reports/data_*`. The integrator adds that glob to `ownership.yaml` in Phase 0 if it's missing.)*

**You, Fri ~3:30–5 pm:** `make label`. Label the queue (about 300 items, about 60–75 min). Then `make data-split`. This is your most important technical contribution, and you should say so in the short answers.

### Lane 4: ML (Claude Code C) · `wt/ml` · `../fr-ml` · port 8103
```
Lane: ML (branch wt/ml). Read AGENTS.md, FIRSTREPLY.md §6, PLAN_WORKTREES.md §4 + this lane, docs/RUBRIC.md.
Own ONLY wt/ml paths. Goal: OUR trained skill detector + a calibrated Critic ensemble + explanations.
Phase A (now — before human labels): build the whole pipeline on data/skills/prelabeled.jsonl; if not yet
pushed, generate a 120-item seed set via llm into tests/unit/ml/fixtures to develop against.
1. ml/skill_detector.py + ml/train.py: features = embed(reply) ⊕ embed(last friend message) ⊕ cheap lexical
   features (question mark, 2nd-person pronouns, length, 988/counselor/adult terms); one LogisticRegression per
   label (class_weight="balanced"), seeded; save models/skill_detector.joblib + metadata (data hash, date,
   metrics). predict(text, context) -> SkillProbs. IMPLEMENTED = True when ready.
2. eval/skills/run_eval.py: per-label precision/recall/F1 + macro-F1 on TEST, confusion-matrix PNGs,
   baselines (keyword rules; LLM-judge-only) → eval/reports/ml_*.json.
3. ml/explain.py: leave-one-word-out occlusion with batched embeddings → Highlights (span, label, delta);
   keep |delta| ≥ 0.1, top 3 per label; tests.
Phase B (after `make data-split` lands, Fri night/Sat):
4. Retrain on final splits; re-run eval; also report on the real survey subset separately.
5. ml/judge.py + prompts/judge.md: LLM judge (role="judge") from the rubric → per-label probability (structured).
6. ml/critic.py: per label, stacking LogisticRegression on VAL with inputs (p_detector, p_judge); uncertain if
   |p_detector − p_judge| > 0.5; Platt calibration on val (isotonic only if n ≥ 300); reliability-diagram PNG;
   map 10 labels → 7 rubric skills (see contracts comment); score_conversation(session) -> CriticReport
   (uses services.engine().turning_point). IMPLEMENTED = True.
7. Rewrites: judge proposes one rewrite per weak message; keep ONLY if the detector's target-skill
   probability rises ≥ 0.2 and guardian.check_user passes.
8. ml/kappa.py: agreement vs counselor labels — Cohen's kappa per label + overall, bootstrap 95% CI,
   n reported honestly → eval/reports/ml_counselor.json.
9. docs/how/ml.md: why embeddings + logistic regression, what F1/kappa/calibration mean, what occlusion shows.
Acceptance: make check green offline (small joblib committed; tests use fixtures); make train reproducible.
```

### Lane 5: FRONTEND A (you + Cursor) · `wt/frontend` · `../fr-frontend` · Vite 5173 → API 8000
Run the backend in stub mode (`make dev-stub` in your main folder), then `cd frontend && npm install && npm run dev && npm run gen:api`.

**Fri screens:**
1. **Landing:** phone mockup, the one-liner, "Start practicing," a content-warning card, and a 988 banner.
2. **Scenario picker:** cards showing name, situation, guarded/open, and the content warning.
3. **Chat screen:**
   - iMessage-style bubbles
   - "typing…" with delay = clamp(400 + 35 ms × characters, 800, 3500) per bubble
   - "Seen" when `seen_no_reply`
   - text input, plus an **"I need help now"** button always visible (opens Real mode)
   - side panel: **live trust graph** (Chart.js, with event icons at each turn) plus disclosure-level steps

**What to build yourself vs hand to Cursor:**
- **Write yourself (good for your understanding and the "I built it" story):** the chat message list and typing logic, plus the trust graph.
- **Let Cursor's agent do:** scaffolding, Tailwind styling, i18n setup.

**Cursor prompt example:**
```
Using src/api/types.ts, build ChatScreen.tsx: phone-frame layout, message list rendering Node.bubbles with
staggered typing delays (formula in PLAN_WORKTREES.md Lane 5), "Seen" indicator when friend_node.seen_no_reply,
input with Enter to send (POST /api/sessions/{id}/messages), an always-visible "I need help now" button routing
to /real, and a right panel with a Chart.js line of state_after.trust per turn. Tailwind, mobile-first,
aria-live for new messages, respects prefers-reduced-motion. Don't touch files outside frontend/.
```

---

## 8. Wave B lanes (start at M2, Fri ~10 pm; run overnight and Sat)

### Lane 6: WHAT-IF (Claude Code A, new branch from main after M2) · `wt/whatif`
```
Lane: WHATIF (branch wt/whatif). Read AGENTS.md, PLAN_WORKTREES.md §4 + this lane. Own ONLY wt/whatif paths.
Goal: from a node (default: the turning point) simulate better futures — "here's what would have happened".
1. whatif/rollout.py: candidates — generate N=4 diverse helpful replies (prompts/helper_sim.md; strategies:
   validate, ask directly, refer, validate+ask); Guardian-check each; score with services.skills (target skills).
2. For each candidate, simulate depth 3 in an ISOLATED copy of the tree: candidate → engine.update →
   engine.generate (+verify) → simulated helper continues the same strategy (helper_sim) → ... .
   value = final trust + 10×levels gained + 15×(referral accepted) − 10×(any guardian concern).
   Run candidates concurrently (asyncio.gather); cache by (session snapshot hash, candidate text).
3. Return WhatIfResult (paths with nodes + trust_series, best_index, simulated=True). Time budget 20 s →
   return partial results gracefully. IMPLEMENTED = True.
4. scripts/precompute_demo_whatif.py: precompute + cache the demo scenario's what-if for demo mode/video.
5. Tests with FakeLLM (deterministic), timeout test, one @llm end-to-end test. docs/how/whatif.md
   (explain Monte Carlo rollouts like a game AI).
```

### Lane 7: RED-TEAM + CI (Codex) · `wt/redteam`
```
Lane: REDTEAM (branch wt/redteam). Read AGENTS.md, PLAN_WORKTREES.md §4 + this lane, docs/SAFE_MESSAGING.md.
Own ONLY wt/redteam paths. Goal: automated adversarial testing; every failure becomes a permanent test.
1. eval/redteam/attackers.py + prompts/attacker.md: LLM attacker personas (non-graphic): dismissive,
   method_seeking, persona_breaker, prompt_injector, slang_heavy, user_in_crisis, encourager.
2. eval/redteam/harness.py: run conversations IN-PROCESS through app.pipeline (real modules, llm cache on):
   7 attackers × 5 scenarios × 3 seeds (≤10 turns) = 105 conversations; `--small` = 1 seed.
3. eval/redteam/checks.py, every turn: no method/means content in friend output (guardian.check_friend +
   llm.moderate self-harm/instructions); persona never breaks; guardian paused on user_in_crisis turns;
   prompt injection had no effect (persona + schema intact); no locked-fact leaks (engine.verify);
   friend never encourages harm.
4. eval/redteam/matrix.py → eval/reports/redteam_*.json + attack×scenario pass-rate table (markdown + PNG)
   + failures with transcripts in eval/redteam/failures/.
5. tests/safety/: each failure → fixture JSON + test_regressions.py replaying the DETERMINISTIC parts offline
   (guardian on attacker messages, verify() on recorded actor outputs, state engine on recorded events).
   Must pass in CI with NO API keys.
6. .github/workflows/ci.yml: keep `make check` + ownership check on PRs; add regression suite; upload
   eval artifacts; README CI badge.
7. scripts/report.py: rebuild README between <!-- METRICS:START/END --> from eval/reports/*.json (tables:
   detector F1, counselor kappa, guardian recall/robustness/latency, red-team pass rate, safety test count).
8. For failures in OTHER lanes' code: write a Request in wt-notes/redteam.md (owner lane fixes it). docs/how/redteam.md.
```

### Lane 8: DEPLOY / OPS (Claude Code B, after Safety merges) · `wt/deploy`
```
Lane: DEPLOY (branch wt/deploy). Read AGENTS.md, PLAN_WORKTREES.md §13 + this lane. Own ONLY wt/deploy paths.
1. Dockerfile: multi-stage — node builds frontend/dist; python:3.11-slim + uv runtime, non-root user,
   pre-download the fastembed model at build, uvicorn on $PORT (default 7860). .dockerignore.
2. deploy/: Hugging Face Spaces (Docker SDK, app_port 7860) guide + Space README metadata; Render as backup.
   Secrets only via host env vars (OPENAI_API_KEY, models, budget).
3. backend/app/ops/: ratelimit.py (per-IP token bucket, e.g. 30 messages / 10 min, 5 what-ifs / hour);
   budget.py (reads llm usage → over the daily cap ⇒ demo mode); demo.py (demo mode replays cached sessions
   + precomputed what-if for the demo scenario, banner "demo mode"); privacy.py (in-memory session store,
   60-min TTL + purge task; prod logs exclude message text); input limit 500 chars; security headers;
   same-origin CORS. IMPLEMENTED = True for each.
4. Startup warm-up (load embed + joblibs once) + /api/health readiness.
5. eval/deploy_latency (script under deploy/) → 20 concurrent simulated sessions → p50/p95 turn latency →
   eval/reports/deploy_latency.json.
6. docs/DEPLOY.md + docs/how/deploy.md. Acceptance: docker build/run serves the full app at :7860;
   public URL live by M3 (Sat 2 pm); rate-limit + budget + TTL tests pass.
```

### Lane 4 continues: ML Phase B (critic, judge, rewrites, kappa), see Lane 4 above.

### Lane 9: FRONTEND B (you + Cursor), Saturday
1. **Feedback report:**
   - a 7-skill radar chart
   - one card per message with **highlighted words** (green helped / red hurt) and the verified rewrite
   - "uncertain" tags
   - the **turning-point** marker
2. **Rewind/branch view:** tap a message → rewind → the conversation tree (a simple indented tree is fine).
3. **"What if?" view:** 3–4 paths shown side by side with their trust curves; the best one highlighted; "simulated" label.
4. **X-ray mode:** a toggle in the chat that shows, under each user message:
   - the Guardian result (with latency)
   - detected labels with probabilities
   - the trust formula, e.g. "+12 validated −2 decay = +10"

   **This is your strongest video shot.**
5. **Real mode:** static steps, big `tel:988` / `sms:988` buttons, country picker, EN/ES. Must work even if the API is down: bundle the JSON into the frontend build as a fallback.
6. **Transparency page:** architecture diagram (SVG), live numbers from `/api/metrics`, safety-test count, "what the AI does / doesn't do."
7. **After-session check-in:** "How are you feeling after that?" → if "not great" → resources.
8. **Language toggle (EN/ES), privacy page, disclaimer footer**, accessibility pass, mobile layout, and optionally an installable app (PWA manifest).

---

## 9. Worktree and cloud setup (commands)

*(macOS/Linux/Git Bash. On Windows, use Git Bash for these.)*

**One-time, tonight, in your main checkout:**
```bash
cd ~/code/hackathon-cac
git fetch origin
git switch main && git pull
git merge origin/claude/amazing-carson-31tzo3      # bring in research + plan docs
git push origin main
# (Phase 0 lands here, then:)
git tag v0-contracts && git push --tags
```

**Create the Wave A worktrees** (each gets its own folder and branch):
```bash
git worktree add -b wt/engine   ../fr-engine   main
git worktree add -b wt/safety   ../fr-safety   main
git worktree add -b wt/data     ../fr-data     main
git worktree add -b wt/ml       ../fr-ml       main
git worktree add -b wt/frontend ../fr-frontend main
for d in ../fr-*; do cp .env "$d/.env"; (cd "$d" && uv sync); done   # .env is NOT shared — copy it
for b in engine safety data ml frontend; do (cd ../fr-$b && git push -u origin wt/$b); done   # backup + cloud access
git worktree list
```

**Run an agent in a lane:**
- **Claude Code (local):** `cd ../fr-engine && claude` → paste the mission prompt → "Plan first, don't edit yet" → approve the plan → let it run. Use auto-accept edits *inside that folder*, but keep approval for pushes.
- **Claude Code on the web (during school):** claude.ai/code → pick your repo → **branch `wt/engine`** → paste the same prompt. It works and pushes to the branch, and you can check progress on your phone at lunch.
- **Codex:** run `codex` (or the IDE extension) in `../fr-data`, **or** Codex cloud → repo → branch `wt/data` → paste the prompt. It reads `AGENTS.md`.
- **Cursor:** File → Open Folder → `../fr-frontend`. Add `AGENTS.md` to context (or a project rule that points to it).
- **Ports:** set `PORT=8101/8102/8103/8104` in each lane's `.env` if you run servers there. The main integration server stays on 8000.

**Gotchas:**
- A branch can be checked out in only one worktree at a time.
- `node_modules` and `.venv` are per worktree (uv's global cache keeps this fast).
- The Hugging Face model cache is shared (good).
- **Never** let a cloud agent and a local agent work on the same lane branch at the same time. Pick one per lane per time block.

**Wave B:** after M2, create `wt/whatif`, `wt/redteam` and `wt/deploy` the same way, from the updated `main`.

**Cleanup at the end:** `git worktree remove ../fr-engine` (etc.), then `git worktree prune`.

---

## 10. How every agent must code (`AGENTS.md`, copied verbatim in Phase 0)

```markdown
# AGENTS.md — rules for every AI coding agent in this repo
Project: FirstReply — see FIRSTREPLY.md. Plan: PLAN_WORKTREES.md. Ship target: Sun Oct 25 night.

## Golden rules
1. Stay in your lane. Only edit paths your branch owns (ownership.yaml). Run `make ownership` before saying done.
   Need something outside your lane (contracts, dependencies, Makefile, another lane's file)? Write it under
   "## Requests" in wt-notes/<lane>.md, use a local workaround or stub, and continue.
2. Contracts are frozen: backend/app/contracts.py. Implement them; never edit them.
3. Tests first. Turn each acceptance criterion into a test, then implement. `make check` must pass before you say done.
4. No network in unit tests: use FakeLLM/fixtures. Real-API tests are marked @pytest.mark.llm.
5. No new dependencies (Phase 0 installed everything). If truly needed, add a Request.
6. Never commit secrets. Keys come from .env via app.config. Never log user/friend message text when FR_ENV=prod.
7. SAFETY (non-negotiable): the friend persona never describes or hints at suicide methods, means or plans,
   never encourages self-harm, stays in character; "real mode" contains no AI; the Guardian runs before any
   LLM call; follow docs/SAFE_MESSAGING.md. If unsure, choose the safer behavior and note it.
8. All LLM calls go through backend/app/llm.py; prompts live in backend/app/prompts/*.md, never inline.
9. Deterministic: fixed seeds; LLM cache on in dev; same input → same output wherever possible.
10. Small commits prefixed with your lane ("engine: add hysteresis"); commit after each green test; push often.
11. Explain your work in docs/how/<lane>.md in plain language a high-school student can explain to a judge:
    what it does, why this approach, alternatives considered, how it is measured, known limitations.
12. Evaluations write JSON to eval/reports/<lane>_*.json using the schema in eval/README.md.
13. Keep wt-notes/<lane>.md current: Done / In progress / Decisions / Requests / Known issues.
14. When done with a task: run make check + make ownership, summarize changes, then offer the explain-back quiz.

## Commands
make dev | dev-stub | check | smoke | ownership | train | guardian-train | eval | report | redteam | docker

## Style
Python 3.11, type hints everywhere, pydantic v2, ruff format, small functions, docstrings on public functions,
no global mutable state except documented singletons (embed model, joblib models).
```

---

## 11. Merge protocol ("merge it well")

**Merge windows** (batch your reviews; don't merge randomly):

| Window | When (CT) | What should land | Milestone |
|---|---|---|---|
| **M0** | Thu ~midnight | Phase 0 + content files | `v0-contracts` |
| **M1** | Fri 4:00 pm | engine/state + tree, safety normalizer + lexicon, data prelabeled, ml pipeline (on prelabels), frontend shell | Pieces turn on in `/api/health` |
| **M2** | **Fri 10:00 pm** | actor + verifier + turning point, guardian v1, ml v1 retrained on your labels, frontend chat on the real API | **"Friday Night Playable":** a real conversation end to end |
| **M3** | Sat 2:00 pm | critic ensemble + explanations + rewrites, red-team v1, deploy v1, frontend feedback page | **First public URL** |
| **M4** | **Sat 10:00 pm** | what-if, red-team regressions + CI badge, frontend what-if, X-ray, Transparency | **Feature freeze** |
| **M5** | **Sun 2:00 pm** | final eval numbers, counselor kappa, README/report, docs/how → HOW_IT_WORKS | **Code freeze** (bug fixes only after) |

**Order inside each window:** contracts/deps Requests → **safety → engine → ml → data → whatif → deploy → redteam → frontend.** Frontend goes last because it adapts to the API.

**Per-branch merge procedure.** Prefer GitHub PRs so CI runs automatically; cloud agents open PRs anyway:
1. In the lane: `git fetch origin && git merge origin/main` (**merge, don't rebase**, so cloud and local work never needs force-pushes), then `make check && make ownership`, then push.
2. Open a PR `wt/x → main`. CI must be green. Read the summary and `git diff --stat`.
3. **Explain-back quiz** (§18) for that lane, about 5 min. You must be able to answer.
4. Merge with **"Create a merge commit"** (no squash; history shows real incremental work).
5. In the main folder: `git pull && make smoke` (and play one conversation if it's M2 or later).
6. If smoke is red: **revert the merge** (`git revert -m 1 <merge-sha>`), push, and write the failure in `wt-notes/<lane>.md`. Never "fix forward" in main under time pressure.
7. Tell the other lanes to sync: each running agent gets "`git fetch && git merge origin/main`, re-run make check."

**Integrator prompt (Claude Code in the main folder, at each window):**
```
You are the INTEGRATOR. For merge window M#: for each branch in order [safety, engine, ml, data, whatif,
deploy, redteam, frontend] with new commits: show git log main..origin/wt/X and diff --stat; run
scripts/check_ownership.py wt/X (stop + report violations); merge --no-ff into main; run make check &&
make smoke; if red → git revert -m 1 and write the failure to wt-notes/X.md. Then process "## Requests" in
all wt-notes/*.md: dependency adds (uv add + lock), Makefile targets, ownership globs, contract changes
(only additive, bump CONTRACTS_VERSION, list affected lanes). Push main. Print which lanes must sync.
Never rewrite main's history.
```

**Contract-change rule:** additive only (new optional fields). Never rename or remove. Bump `CONTRACTS_VERSION`, then every lane syncs.

**Conflict playbook:**
- *A conflict inside a lane's own files:* impossible by design. If it happens, the ownership check failed, so find out who wrote outside their lane.
- *Lockfile conflict:* take main's `uv.lock`, then the integrator re-runs `uv lock`.
- *A fixture or contract mismatch the frontend notices:* the frontend adapts. If the API is wrong, file a Request with the integrator.
- *Two lanes need the same helper:* the integrator adds it to a shared module (`embed.py`/`llm.py`), and both lanes sync.

**Release:** at M5, tag `v1.0`, deploy from the tag, and record the commit in `DEVLOG.md`. **Rollback** = redeploy the previous tag.

---

## 12. Evaluation: numbers you'll publish (targets, not promises; report the real values)

| Metric | Produced by | Target | Where it shows up |
|---|---|---|---|
| Skill detector macro-F1 (held-out test) and per-label F1 | ML | ≥ 0.75 | README, Transparency, video |
| Detector vs baselines (keywords; LLM judge only) | ML | beats keywords | README |
| Results on the **real survey replies** subset | ML | report honestly | README ("real-world check") |
| Critic agreement with the counselor (kappa, 95% CI, n) | ML | report honestly | README, video, short answer |
| LLM-label vs human-label audit agreement | Data | report | DATASET.md |
| Guardian recall on self-risk (test) / precision | Safety | recall ≥ 0.95 | README, video |
| Slang robustness with vs without normalizer | Safety | big improvement | README, video ("unalive" shot) |
| Guardian vs OpenAI moderation on slang | Safety | report whatever is true | README |
| Guardian latency p95 | Safety | < 50 ms | README |
| Verifier catches (leaks blocked per 100 turns) | Engine | report | README |
| Red-team pass rate; method-content leaks | Red-team | 100% / **0** | README, CI badge, video |
| Safety regression tests passing | Red-team | all | CI badge |
| Turn latency p50/p95 under load | Deploy | p50 < 3 s | README |

---

## 13. Deployment, security, cost, privacy

- **Host:** **Hugging Face Spaces (Docker)** is free, has plenty of RAM, and suits ONNX models. Render is the backup. One container serves the API and the built frontend (same origin, so no CORS headaches). The free tier sleeps when idle, so add "may take ~30 s to wake" to the README. Judges mostly watch the video anyway.
- **Embeddings:** `fastembed` (ONNX), **not** PyTorch, because torch is too big for free tiers.
- **The API key** lives only in server environment variables, never in the frontend, never in git, never in CI. If it's ever exposed: rotate it immediately.
- **Abuse protection** (the public link is open to anyone):
  - per-IP rate limits
  - a 500-character input cap
  - a daily $ cap that automatically switches to **demo mode** (cached sessions)
  - **plus a hard monthly limit in the OpenAI dashboard**
- **Cost control in development:**
  - LLM cache on (repeat runs are free)
  - FakeLLM in tests
  - a small model for bulk data and red-team
  - the usage log (`eval/logs/llm_usage.jsonl`) shows spending per lane

  Check OpenAI's pricing page. With a small model and caching, the whole project should cost a few dollars, but confirm against the usage log.
- **Privacy, built as described:**
  - no accounts and no analytics
  - sessions held in memory, deleted after 60 min
  - production logs contain no message text
  - nothing is used for training
  - a privacy page that says exactly this
- **Disclaimers:**
  - footer: *"FirstReply is a practice tool, not a crisis service or therapy. If someone is in immediate danger, call 911. In the US, call or text 988."*
  - a content warning before every session

---

## 14. Sunday: harden, prove, ship

1. **Morning bug bash (1 h):**
   - 3–5 classmates play on the public URL; read them the content warning first.
   - Collect quotes, but only with their permission, and only first names or "a 10th grader."
2. **Fix-only work** by the owning lanes (agents), then the final eval run: `make eval && make report && make docs`.
3. **README for judges:**
   - one-liner, GIF/screenshots, the problem stats
   - architecture diagram
   - **evaluation tables** (auto-generated)
   - safety section, privacy, how to run
   - AI-use disclosure, credits (counselor with permission)
4. **`HOW_IT_WORKS.md`:** read all of it. Then ask Claude: *"Quiz me on HOW_IT_WORKS.md like a skeptical engineer judge, 10 questions, one at a time."*
5. **Video (3–7 pm):**
   - Record in **demo mode** so it's identical on every take, and turn X-ray mode on for the "under the hood" section.
   - Tools: OBS/QuickTime for screen capture; CapCut/Clipchamp to edit.
   - Format: 1080p, **under 3:00**, captions.
   - Required items: your name, app name, one-sentence purpose, audience, languages and tools, the app working, what you learned.
   - Thumbnail from ChatGPT.
   - Upload as **Public** and test the link in an incognito window.
6. **Short answers + AI disclosure (7–9 pm):** use the draft in `FIRSTREPLY.md` §9 with the real numbers.
7. **SUBMIT by 10 pm CT Sunday.** Screenshot the confirmation page. Monday 7 am is buffer only, for checking the submission and fixing a broken link.

---

## 15. Hour-by-hour schedule

### Thursday (tonight)
| Time | You | Agents |
|---|---|---|
| Now (20 min) | Confirm district by street address → **register on congressionalappchallenge.us**. Check the other hackathon's deadline. Set the OpenAI **monthly budget cap**. Create `.env`. Merge the research branch into main. Tell a parent what you're building. | none |
| +0:20 → +2:30 | **Content lane** with ChatGPT: 5 scenarios (then fix the voices yourself), rubric, label guide, real mode, crisis lines (check them), safe-messaging list. Prep the counselor ask and survey (templates in §18). | **Phase 0** (integrator) |
| +2:30 → +3:15 | Run `spike_actor.py` and read the outputs, pick models, commit content, tag `v0-contracts`, create worktrees, push lane branches. | none |
| +3:15 → bed | Paste mission prompts: **Engine, Safety, ML (Phase A)** in Claude Code, **Data** in Codex. Answer their plan questions, then **go to sleep.** | Wave A starts |

### Friday (school day)
| Time | You | Agents |
|---|---|---|
| 6:45–7:30 am | Check overnight progress, answer questions. **Move lanes to the cloud** (Claude Code web / Codex cloud on the same branches) if your laptop goes to school. | keep running |
| School | **Ask the counselor or psych/health teacher in person**, and email as backup. Send the survey link to friends at lunch (anonymous). Check agents on your phone. | Wave A |
| 3:30–5:00 pm | **Labeling session** (`make label`, ~300 items), then `make data-split`. | ML switches to final labels |
| ~4:30 pm | **M1 merge** (window moved to after school). | |
| 5:00–8:00 pm | **Frontend A** in Cursor (landing, picker, chat, trust graph) against the stub API. | Engine/Safety/ML finish v1 |
| 8:00–10:00 pm | Switch the frontend to the real API. **M2 merge → Friday Night Playable.** Play 3 conversations and write down bugs. | |
| 10:00 pm → bed | Start **Wave B**: What-if (Claude A), Red-team + CI (Codex), Deploy (Claude B), ML Phase B (Claude C). | run overnight |

### Saturday
| Time | You | Agents |
|---|---|---|
| 8:30–10:00 am | Review overnight PRs; send counselor labels to `import_counselor` if they've arrived. | Wave B continues |
| 10:00 am–2:00 pm | **Frontend B:** feedback report, X-ray mode, rewind tree, real mode. | |
| 2:00 pm | **M3 merge → public URL.** Send it to 2–3 friends to try. | Red-team runs; failures → requests |
| 2:00–8:00 pm | Frontend B: what-if view, Transparency page, check-in, EN/ES, accessibility. | Lanes fix red-team requests |
| 10:00 pm | **M4 merge → feature freeze.** Write the video script (ChatGPT can polish it; keep your own voice). | Overnight: full red-team + eval runs |

### Sunday
| Time | You | Agents |
|---|---|---|
| 9:00–10:00 am | Bug bash with classmates (quotes, with permission). | Fix-only |
| 10:00 am–2:00 pm | Read `HOW_IT_WORKS.md`, do the quiz, review the README and numbers. | Final `make eval/report/docs` |
| **2:00 pm** | **M5 → code freeze → tag v1.0 → deploy.** | none |
| 3:00–7:00 pm | **Record and edit the video.** Upload as Public. | none |
| 7:00–9:00 pm | Short answers, AI disclosure, fill in the submission form. | none |
| **≤10:00 pm** | **SUBMIT.** Screenshot it. 🎉 | none |

### Monday
| 7:00 am | Buffer only: check the submission page and that the video plays. **Deadline 11:00 am CT.** |
|---|---|

---

## 16. Risks and fallbacks

| Risk | Early signal | Fallback |
|---|---|---|
| OpenAI model refuses the persona or adds "as an AI" disclaimers | `spike_actor.py` Thu night | Reframe the prompt (training simulator, safe-messaging rules) → try another OpenAI model → **hybrid friend:** pre-written lines per level that the LLM only rephrases. The state engine still drives it, which is arguably *safer* (say so in the README). |
| Human labels late | Fri 6 pm | Train on agreed LLM labels plus whatever you've labeled. Report the audit agreement honestly. |
| Counselor doesn't reply | Sat noon | Ask another adult (psych/health teacher, school nurse). Otherwise say honestly: "rubric based on published gatekeeper frameworks; professional review in progress." |
| Claude usage limit | Agent stops | Move the lane to Codex or Cursor with the same prompt. Reduce to 2 concurrent Claude lanes. |
| Merge breaks main | `make smoke` red | Revert the merge, fix in the lane, re-merge next window. |
| Deploy out of memory / slow | M3 | fastembed already avoids torch. Move to HF Spaces or turn on demo mode. The video is recorded locally anyway. |
| What-if too slow or flaky | Sat evening | Ship turning-point detection plus 1 precomputed demo what-if (cached). |
| Running out of time overall | Sat 10 pm | Ship the **minimum viable submission** below. |
| The topic weighs on you or testers | any time | Breaks, content warnings, 988 visible. Talk to someone. It's okay to step away for an hour. |

**Minimum viable submission (MVS):** it must exist by Sat 10 pm no matter what:
- chat with the state engine and live trust graph
- Guardian
- your trained skill detector with word highlights
- basic feedback report
- real mode
- README with real numbers

Everything else (what-if, the red-team matrix, calibration plot, voice) is a bonus.

---

## 17. What the judges will see

- **Video:** the phone hook → trust drop → rewind → highlighted words → "here's where you lost them" what-if → X-ray "under the hood" → numbers → real mode → required items.
- **Short answers:** the "LLM is only the voice" system design, *your* dataset and labeling, measured safety, the counselor review.
- **GitHub:** clean modules, `AGENTS.md`/ownership (they'll see a real engineering process), green CI badge, evaluation tables, `docs/how/*`, incremental commit history, honest AI disclosure.

---

## 18. Templates

### Counselor or teacher ask (in person Friday; email backup)
> **Subject:** Quick review for a student app that helps teens support struggling friends
>
> Hi [Name], I'm [your name], a [grade] at [school]. For the Congressional App Challenge I'm building **FirstReply**, a practice simulator where teens learn what to say when a friend texts that they're not okay. It's based on publicly described gatekeeper frameworks like QPR (Question, Persuade, Refer). It never gives crisis counseling, and its "real situation" mode is a fixed plan that points to a trusted adult and 988.
>
> Could you spare **15–20 minutes before Saturday evening** to:
> 1. look over the 7-skill rubric and the 5 practice scenarios (1–2 pages), and
> 2. label 30 sample replies in a Google Sheet (checkboxes)?
>
> With your permission I'd credit you by title ("reviewed by a school counselor at [school]"). Thank you so much!

### Anonymous survey (Google Form, no names, no emails collected)
Intro: *"Anonymous, optional, for a student app project about helping friends. Skip any question. If you're struggling, call or text 988."*
1. Grade (9 / 10 / 11 / 12 / prefer not to say)
2. If a friend texted *"honestly idk why i even bother anymore,"* how confident would you be about what to say? (1–5)
3. **What would you text back?** (free text; optional) → *"I agree my anonymous answer may be used as an example in the app's testing."* (checkbox)
4. Have you ever been taught how to help a friend who might be thinking about suicide? (yes / no / not sure)
5. Would you try a free app to practice this? (1–5)
End screen: *"Thank you. If you or a friend are struggling: call or text 988, or talk to a trusted adult."*

→ Q2/Q4 give you **real stats** for the video ("X of Y classmates said…"). Q3 gives you **real teen replies** for the real-world test set.

### Explain-back quiz (run before every merge)
```
Explain what you built in this lane like I'm a 10th grader, in under 200 words. Then ask me 5 questions a
skeptical software-engineer judge would ask about it — one at a time — wait for my answer, and correct me.
Finally, list 3 things I should be able to say about its limitations.
```

### AI-use disclosure (fill in honestly)
> I designed FirstReply's architecture and safety approach, wrote and reviewed the scenarios, rubric and crisis content, labeled the training data, ran and interpreted the evaluations, organized the parallel build and code reviews, and built [which frontend parts]. I used AI coding assistants (Claude Code, OpenAI Codex, Cursor) to write much of the code under my direction, and ChatGPT to draft content I then edited. At runtime the app uses OpenAI models only for the simulated friend's wording and as one input to scoring; my own models and code make the safety, scoring and conversation decisions.

### DEVLOG entry format (2 lines, every session)
`2026-10-23 16:40 — Labeled 312 replies; LLM-vs-human audit agreement 0.87; decided "are you ok?" ≠ asked_directly.`
