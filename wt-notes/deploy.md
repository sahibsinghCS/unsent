# Deploy lane notes

## Done
- `backend/app/ops` **IMPLEMENTED** (`install(app)` + `on_startup()`), 27 tests in `tests/unit/ops/`:
  - `ratelimit.py`: per-client token buckets. Defaults (env): `FR_RL_SESSIONS_PER_MIN=10`, `FR_RL_MESSAGES_PER_MIN=30`, `FR_RL_MESSAGES_PER_DAY=300`, `FR_RL_WHATIF_PER_MIN=6`, `FR_RL_GUARDIAN_PER_MIN=30`, `FR_RL_API_PER_MIN=240` (other `/api/*`); `/api/health` exempt. On by default only in prod (`FR_RATE_LIMIT=0/1` overrides) so dev/tests are unaffected. 429 → `{detail, retry_after}` + `Retry-After`. Refused requests take no token. Idle buckets are dropped.
  - Client = the `FR_PROXY_HOPS`-th `X-Forwarded-For` entry from the right (default 1: the hop our proxy appended; entries further left are client-written and forgeable) only when `FR_TRUST_PROXY=1`, else `request.client.host`.
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
2. ~~ml: /finish 1.2 s CPU~~ **done** (a9f1cb9 background explanations): finish p50 57 ms at 1 user with think time.
3. ~~platform: .env.example knobs~~, 4. ~~Makefile loadtest/csp-check~~, 6. ~~usage log in memory in prod~~: **done** in 836baaa.
5. **redteam (CI):** after `docker run`, wait for `/api/health`, then run `node deploy/csp_check.mjs http://127.0.0.1:7860` and check that `docker inspect` shows `User: user`.
7. **whatif:** `POST /whatif` is now the heaviest endpoint: ~0.7 s CPU per call (p50 0.72 s at 1 user; 9.7 s p50 at 20 users with think time, 13.5 s in burst). Worth profiling or caching rollouts per turning point; the 6/min per-visitor limit already bounds abuse.

## Known issues
- No Docker daemon in this sandbox: the real `docker build` is first run by the red-team CI job.
- What-if latency under simultaneous load (Request 7).
- Rate limits key on the visitor address: a school NAT shares one bucket.

## Numbers (a9f1cb9 merged; 4-CPU sandbox, prod mode, FR_LLM=0, fastembed, 1 worker; 20 conversations per level)
Think time (`eval/reports/deploy_load.json`: 2-4 s before each message, 1.5-2.5 s before finish, seed 20261025):
- Message p50/p99 (n=120): 27/192 ms (c1), 25/75 (c5), 24/125 (c10), 25/345 (c20).
- Finish p50/p99 (n=20): 57/92 ms (c1), 117/319 (c5), 215/790 (c10), 1169/1683 (c20).
- What-if p50/p99 (n=20): 0.72/1.38 s (c1), 1.34/2.43 (c5), 3.06/5.14 (c10), 9.69/11.26 (c20).
- Errors 0/800. Cold start 7.0 s. RSS 791 MB idle, 845 MB peak.
Burst (`eval/reports/deploy_load_burst.json`, `--no-think`):
- Message p50/p99: 22/217 ms (c1), 100/175 (c5), 208/356 (c10), 382/605 (c20).
- Finish p50/p99: 50/1840 ms (c1, first call before background explanations catch up), 272/349 (c5), 718/988 (c10), 1297/1969 (c20).
- What-if p50: 0.71 / 3.2 / 6.4 / 13.5 s. Errors 0/800. Cold start 6.2 s. RSS peak 854 MB. ~11 req/s.
- CSP: 0 violations across 7 pages × 2 color schemes.
