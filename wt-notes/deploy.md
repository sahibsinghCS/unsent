# Deploy lane notes

## Done
- `backend/app/ops` **IMPLEMENTED** (`install(app)` + `on_startup()`), 27 tests in `tests/unit/ops/`:
  - `ratelimit.py`: per-client token buckets. Defaults (env): `FR_RL_SESSIONS_PER_MIN=10`, `FR_RL_MESSAGES_PER_MIN=30`, `FR_RL_MESSAGES_PER_DAY=300`, `FR_RL_WHATIF_PER_MIN=6`, `FR_RL_GUARDIAN_PER_MIN=30`, `FR_RL_API_PER_MIN=240` (other `/api/*`); `/api/health` exempt. On by default only in prod (`FR_RATE_LIMIT=0/1` overrides) so dev/tests are unaffected. 429 → `{detail, retry_after}` + `Retry-After`. Refused requests take no token. Idle buckets are dropped.
  - Client = first `X-Forwarded-For` hop only when `FR_TRUST_PROXY=1`, else `request.client.host`.
  - `headers.py`: CSP (`default-src 'self'`, script-src `'self'` + SHA-256 of each inline script in the built `index.html`, `style-src 'self'`, `img-src 'self' data:`, `connect-src 'self'`, `object-src 'none'`, `base-uri`/`form-action 'self'`, `frame-ancestors 'self' https://huggingface.co https://*.hf.space`), nosniff, `Referrer-Policy: no-referrer`, Permissions-Policy, HSTS 30 days, COOP; no X-Frame-Options; `server` header stripped. `/docs` + `/redoc` get a looser CSP (CDN) so the API docs still work.
  - `middleware.py`: one pure-ASGI middleware: rate limit → body limit (`FR_MAX_BODY_BYTES`, 32 KB; Content-Length checked up front, chunked bodies read with a cap) → headers → one JSON log line `{evt, method, route template, status, ms, client}`; client = HMAC(per-process random salt, day|ip)[:12].
  - `purge.py`: daemon thread purges expired sessions every `FR_PURGE_INTERVAL_S` (60 s).
  - `on_startup()`: starts the purge, logs `{"evt":"ready", components, embedder, llm_enabled, llm_has_key, rate_limits, ...}` (no secrets).
- **CSP verified in headless Chromium** (`deploy/csp_check.mjs`) against the real build served by the prod-mode server: landing, practice, chat (+X-ray, branches), feedback, what-if, real mode, /how (+Guardian), light and dark: **0 violations, 0 console errors**. Negative control (edit the inline script) → the check fails as expected.
- `Dockerfile` (node:20-slim frontend stage → python:3.13-slim + uv 0.11.32, `uv sync --frozen --no-dev`, copies backend/data/content/models/eval/reports/frontend dist, bakes the fastembed model into `/app/.cache/fastembed`, uid 1000, `FR_ENV=prod FR_EMBED=fastembed FR_TRUST_PROXY=1 HF_HUB_OFFLINE=1 PORT=7860`, HEALTHCHECK, `uvicorn ... --workers 1 --proxy-headers --forwarded-allow-ips=* --no-access-log --no-server-header`) + `.dockerignore`.
- **Every build step reproduced locally** (no Docker daemon): frontend built from exactly the tracked files; fresh venv with `uv sync --frozen --no-dev` (626 MB); `python -m deploy.predownload` into the image cache path (241 MB); exact prod command with `HF_HUB_OFFLINE=1` and the network proxy pointed at a dead port (proves offline start). Every API route + SPA deep links checked (200s; 413 on 40 KB body; 429 + `Retry-After: 6` on the 11th session/min).
- `deploy/space-README.md` (HF front matter: `sdk: docker`, `app_port: 7860`), `deploy/push_space.sh` (temp worktree, README swap, `huggingface_hub.upload_folder` so binaries need no git-lfs, mirrors exactly one commit, `--dry-run`), `docs/DEPLOY.md` (click-by-click, costs, wake-up, logs, rollback, local Docker).
- `deploy/loadtest.py` → `eval/reports/deploy_load.json` (71 records).
- `docs/how/deploy.md`.

## In progress
- Nothing.

## Decisions
- Rate limits default **off outside prod**: e2e tests and `make dev` create many sessions from one address.
- Inline theme script allowed by **hash** (computed at startup from `frontend/dist/index.html`), not `'unsafe-inline'`; survives rebuilds.
- `--no-access-log`: uvicorn's access log prints raw paths (session IDs) and IPs; our own log line replaces it.
- Load test gives each conversation its own `X-Forwarded-For` address so the real limiter stays on.
- Upload via `huggingface_hub` instead of `git push` to the Space: the `.joblib` models are binary and the Hub requires Xet/LFS for binaries; the library handles it with no extra install.
- python:3.13-slim matches the interpreter the lock was verified with locally (3.13.16).

## Requests
1. **frontend:** optional: move the inline theme script in `frontend/index.html` to `public/theme.js` (`<script src="/theme.js"></script>`). The CSP then needs no hash. Not required; the hash works and is tested.
2. **ml (critic):** `POST /finish` costs ~1.2 s CPU per call (p50 1.17 s at 1 user, 18 s at 20 simultaneous). Worth profiling (repeated embeddings? per-message rewrites?). Messages are fine.
3. **platform (`.env.example`):** add the new knobs: `FR_RATE_LIMIT=` (empty = on in prod), `FR_TRUST_PROXY=0`, `FR_MAX_BODY_BYTES=32768`, `FR_RL_SESSIONS_PER_MIN=10`, `FR_RL_MESSAGES_PER_MIN=30`, `FR_RL_MESSAGES_PER_DAY=300`, `FR_RL_WHATIF_PER_MIN=6`, `FR_RL_GUARDIAN_PER_MIN=30`, `FR_RL_API_PER_MIN=240`.
4. **platform (Makefile):** `loadtest: ## load test a local prod-mode server (FR_LLM=0)` → `FR_LLM=0 $(UV) run python deploy/loadtest.py` and `csp-check:` → `node deploy/csp_check.mjs $${FR_URL:-http://127.0.0.1:7860}`.
5. **redteam (CI):** after `docker run`, wait for `/api/health`, then run `node deploy/csp_check.mjs http://127.0.0.1:7860` (needs `npm ci` in `frontend/` for playwright-core and Chromium on the runner) and check that `docker inspect` shows `User: user`.
6. **platform (`llm.py`):** in prod, `eval/logs/llm_usage.jsonl` is still appended on disk (role, prompt name, model, token counts, cost: no text). Not conversation content, but for "nothing on disk in prod" consider keeping it in memory when `is_prod()`.

## Known issues
- No Docker daemon in this sandbox: the real `docker build` is first run by the red-team CI job.
- Finish latency under simultaneous load (see Request 2).
- Rate limits key on the visitor address: a school NAT shares one bucket.

## Numbers (`eval/reports/deploy_load.json`, 4-CPU sandbox, prod mode, FR_LLM=0, fastembed, 1 worker)
- Cold start (process start → first healthy response, incl. warm-up): **5.8 s** (n=1).
- RSS: **796 MB** after warm-up, **1.58 GB** peak (n=1).
- Message p50/p99: 34/94 ms (c1), 161/283 ms (c5), 290/453 ms (c10), 583/887 ms (c20); n=120 each.
- Finish p50: 1.2 s / 4.7 s / 9.2 s / 18.1 s (c1/5/10/20; n=20). What-if p50: 130/558/840/1844 ms.
- Errors: **0 / 800** requests. Throughput ~6–8 req/s (CPU-bound).
- CSP: 0 violations across 7 pages × 2 color schemes.
