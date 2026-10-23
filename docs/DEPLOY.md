# Deploying FirstReply (about 10 minutes)

FirstReply runs as one Docker container: FastAPI serves the API under `/api` and the built React app
at `/`. The original plan was a **Hugging Face Docker Space** (CPU basic: 2 vCPU, 16 GB RAM). You click
through the Hugging Face and OpenAI websites; one script does the upload.

> **Update (Oct 2026):** Hugging Face now requires a paid PRO subscription to host a Docker Space,
> even on CPU basic (`402 Payment Required: ... requires a PRO subscription`). The free route we use is
> **Google Cloud Run** (§9). Render's free plan does not fit: the app needs about **810 MB** of memory
> at startup (mostly the multilingual embedding model), and Render free gives 512 MB.

**What it costs**

| Item | Cost |
|---|---|
| Hugging Face Space (CPU basic) | **Free.** It sleeps after about 48 hours with no visitors. |
| OpenAI (friend's wording only) | Capped twice: the app stops calling OpenAI once its own daily estimate passes `LLM_DAILY_BUDGET_USD` (we use **$1/day**) and falls back to the reviewed line bank; your OpenAI spending limit (step 5) is the hard stop. With no key at all the app still works, fully offline. |

Before you start, on your computer: this repo cloned, `uv` installed and `make install` run once.

---

## 1. Create a Hugging Face account and a Docker Space

1. Go to **https://huggingface.co/join**, sign up and confirm your email.
2. Open **https://huggingface.co/new-space**.
3. Fill in:
   - **Owner:** your username. **Space name:** `firstreply`.
   - **Short description:** `Practice the text that could help a struggling friend`.
   - **Select the Space SDK:** click **Docker**, then the **Blank** template.
   - **Space hardware:** **CPU basic · 2 vCPU · 16 GB · FREE**.
   - **Public** (judges must be able to open it).
4. Click **Create Space**. Ignore the "add a Dockerfile" instructions; our script uploads everything.

Your Space lives at `https://huggingface.co/spaces/<user>/firstreply`, and the app itself at
`https://<user>-firstreply.hf.space` (that direct link is the one to give judges).

## 2. Add the secret and the variables

In the Space, click **Settings**, scroll to **Variables and secrets**.

1. **New secret** → Name `OPENAI_API_KEY`, Value: your OpenAI key → **Save**.
   (Secrets are hidden, even from you, after saving. Never put the key in a file in the repo.)
2. **New variable**, one at a time:

| Name | Value | Why |
|---|---|---|
| `LLM_DAILY_BUDGET_USD` | `1` | App-side daily cap on OpenAI spend |
| `OPENAI_MODEL` | `gpt-6-luna` | The model for the friend's wording (`make models` lists what your key can use) |
| `FR_ENV` | `prod` | Already set in the image; set here too so it is visible |

Optional: `OPENAI_PRICE_INPUT_PER_M` / `OPENAI_PRICE_OUTPUT_PER_M` (your model's real prices, used by
the budget estimate), `FR_RL_MESSAGES_PER_DAY` (default 300 per visitor).

## 3. Create a write token and push

1. Open **https://huggingface.co/settings/tokens** → **Create new token**.
2. **Token type: Write**, name `firstreply-deploy` → **Create token** → copy it (starts with `hf_`).
3. In a terminal at the repo root, on the commit you want to deploy:

```bash
export HF_TOKEN=hf_xxxxxxxx            # pasted, not saved anywhere
deploy/push_space.sh <user>/firstreply --dry-run   # optional: see the file list first
deploy/push_space.sh <user>/firstreply
```

The script checks out the current commit into a temporary folder, swaps in
`deploy/space-README.md` as the Space's `README.md`, and uploads only what the Docker build needs.
Nothing in your repo changes. The Space starts building right away (about 5–10 minutes the first
time: the frontend build, Python packages and the embedding model are all baked into the image).

## 4. Check it is healthy

1. On the Space page the status badge goes **Building → Running**.
2. Open `https://<user>-firstreply.hf.space/api/health`. You should see `"ok": true`,
   every component `"real"` (what-if may say `"stub"` until that lane ships) and
   `"llm": {"enabled": true, "has_key": true, ...}`.
3. Open `https://<user>-firstreply.hf.space/`, start a practice chat and send one message.

If `has_key` is `false`, the secret name is wrong (it must be exactly `OPENAI_API_KEY`); fix it and
the Space restarts by itself.

## 5. Set an OpenAI spending limit (the hard stop)

1. Go to **https://platform.openai.com** → **Settings** → your project → **Limits**
   (or **Organization → Limits**).
2. Set a **monthly budget** (for example **$5**) and an email alert at 80%.
3. Best practice: make a separate project called `firstreply-demo`, create the key there, and use
   that key in step 2. If it ever leaks, you revoke just that key.

## 6. Wake the Space before judging

Free Spaces sleep after about 48 hours without visitors, and the first visit then waits for a
restart (about 1 minute). The day before and an hour before judging:

1. Open the Space page; if it says **Sleeping**, click **Restart this Space**.
2. When it shows **Running**, open `/api/health` once. Inside the container the server is ready
   about 5–6 seconds after it starts (models load at startup), so judges never wait on the first message.

## 7. Logs and rollback

- **Logs:** on the Space page click **Logs** (top right). **Build** shows the Docker build;
  **Container** shows the app. Every request is one JSON line with method, route template,
  status, latency and an anonymous daily-rotating client hash: never message text, session IDs
  or IP addresses. The `"evt": "ready"` line lists each component's status at startup.
- **Restart:** Settings → **Restart this Space** (or **Factory rebuild** to rebuild from scratch).
- **Roll back** to an earlier good commit:

```bash
git checkout <good-commit>
deploy/push_space.sh <user>/firstreply
git checkout -          # back to your branch
```

  The Space mirrors exactly the commit you push, so this fully replaces the bad version.
  (The Space's own **Files → History** also shows every deploy commit.)
- **Emergency off switch for OpenAI:** add the variable `FR_LLM` = `0`. The friend then uses only
  the reviewed line bank; everything else keeps working.

## 8. Alternative: run the same container yourself

Any machine with Docker:

```bash
docker build -t firstreply .
docker run --rm -p 7860:7860 -e OPENAI_API_KEY="$OPENAI_API_KEY" -e LLM_DAILY_BUDGET_USD=1 firstreply
# open http://localhost:7860   (leave out OPENAI_API_KEY to run fully offline)
```

Without Docker (same steps the image runs):

```bash
uv sync --frozen --no-dev
(cd frontend && npm ci && npm run build)
FASTEMBED_CACHE_PATH=.cache/fastembed uv run python -m deploy.predownload
FR_ENV=prod FR_EMBED=fastembed FASTEMBED_CACHE_PATH=.cache/fastembed \
  uv run uvicorn backend.app.main:app --host 0.0.0.0 --port 7860 --workers 1 --no-access-log
```

**Always exactly one worker:** practice sessions live in that one process's memory (and are deleted
after an hour of inactivity), so a second worker would not find them.

## 9. Free hosting: Google Cloud Run (about 20 minutes, first time)

Cloud Run builds the same `Dockerfile` straight from GitHub, so your OpenAI key never leaves Google's
console. It scales to zero when nobody is using it: the first visit after a quiet spell takes about
30-60 seconds to wake up (wake it before judging, see §6).

**What it costs:** the always-free tier (2 million requests, 180,000 vCPU-seconds and 360,000
GiB-seconds a month) covers judging traffic many times over. Google asks for a card to open a billing
account; with the budget alert below nothing should be charged. The only thing that can cost a few cents a
month is storing the built image (about 1-2 GB in Artifact Registry, 0.5 GB free); delete it after judging.

1. **Account and project:** go to **https://console.cloud.google.com**, sign in, accept the free trial /
   create a billing account, then **Select a project → New project** named `firstreply`.
2. **Budget alert (safety net):** **Billing → Budgets & alerts → Create budget**, amount **$1**, alerts
   at 50% / 100%, email to you.
3. **Store the OpenAI key as a secret:** search **Secret Manager** → enable the API → **Create secret**,
   name `OPENAI_API_KEY`, paste your key → **Create**.
4. **Create the service:** search **Cloud Run** → **Create service** (also called **Deploy container** →
   **Service**) → **Continuously deploy from a repository (source or function)** → **Set up with Cloud
   Build** → connect GitHub → repository `sahibsinghcs/hackathon-cac`, branch `^wt/live$` (or `^main$` once
   merged) → Build type **Dockerfile**, path `/Dockerfile` → **Save**.
5. **Service settings** (same page):
   - Service name `firstreply`, region `us-central1`.
   - Authentication: **Allow unauthenticated invocations** (judges must open it without a login).
   - Billing: **Request-based**. Minimum instances **0**. **Maximum instances 1** (required: practice
     sessions live in one process's memory, so a second instance would not find them; this also caps cost).
   - **Containers → Settings:** container port **7860**; memory **2 GiB**; CPU **1**; request timeout 60 s.
   - **Variables & secrets → Add variable:** `FR_ENV=prod`, `LLM_DAILY_BUDGET_USD=1`,
     `OPENAI_MODEL=gpt-6-luna`, `OPENAI_PRICE_INPUT_PER_M=0.10`, `OPENAI_PRICE_OUTPUT_PER_M=0.50`.
   - **Reference a secret:** `OPENAI_API_KEY` → exposed as environment variable `OPENAI_API_KEY`, version
     `latest` (if asked, grant the service account *Secret Manager Secret Accessor*).
   - **Create.** The first build takes about 5-10 minutes; the URL looks like
     `https://firstreply-xxxxxxxx-uc.a.run.app`.
6. **Check it:** open `<URL>/api/health`. All five components must say `"real"`, and `llm.has_key` and
   `llm.enabled` must be `true`, with `model_actor` `gpt-6-luna`.

**Redeploy:** push to the connected branch; Cloud Build rebuilds and Cloud Run switches over with no
downtime. **Roll back:** Cloud Run → `firstreply` → **Revisions** → pick the previous one → **Manage
traffic** → 100%. **Off switch for OpenAI:** **Edit & deploy new revision** → add `FR_LLM=0`.
**After judging:** delete the service and the image in Artifact Registry.

## What the container does for safety

- **Rate limits per visitor:** 10 new sessions/min, 30 messages/min and 300/day, 6 what-ifs/min,
  30 Guardian checks/min, 240 other API calls/min (`/api/health` exempt). Over the limit: HTTP 429
  with `Retry-After`. All are environment variables (`FR_RL_*`), see `backend/app/ops/ratelimit.py`.
- **Security headers:** a strict Content-Security-Policy (same-origin only, no inline scripts
  except the one hashed theme script, framing allowed only by Hugging Face), `nosniff`,
  `Referrer-Policy: no-referrer`, a Permissions-Policy that turns off camera/mic/location, HSTS.
- **Request bodies over 32 KB** are refused with 413.
- **Privacy:** nothing from a conversation is written to disk; sessions are purged from memory
  every minute once expired; logs contain no text.
