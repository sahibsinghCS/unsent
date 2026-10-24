# Deployment and operations

*Owner: deploy lane. Plain language, so Sahib can explain every part to a judge.*

## What it does
It puts FirstReply on the public internet so anyone (including judges) can open a link and try it,
and it protects that public server:
- **One container** holds everything: the Python API, our trained models, the embedding model and
  the built website. It runs on a free Hugging Face Space (2 CPUs, 16 GB of memory).
- **Rate limits** stop one visitor (or a bot) from flooding the server or running up the OpenAI bill.
- **Security headers** tell the browser to run only our own code, from our own site.
- **Privacy-safe logs** let us see whether the server is healthy without ever recording what anyone typed.

## How it works
- **Docker image, built in two stages** (`Dockerfile`). Stage 1 uses Node to build the React app
  into plain files. Stage 2 is a small Python image: it installs the exact package versions from
  `uv.lock`, copies only what the server reads (backend code, data, content, models, eval reports
  and the built site), and **downloads the embedding model during the build**. So the container
  starts in about 6 seconds and never needs the internet for embeddings. It runs as a normal user
  (uid 1000), not as root, with exactly **one worker process**, because practice sessions live only
  in that process's memory.
- **One middleware** (`backend/app/ops/middleware.py`) wraps every request:
  1. Works out who the visitor is. When the app runs behind a hosting proxy, every request comes
     through it, and the proxy adds the visitor's address to the *end* of the `X-Forwarded-For`
     header. So we use the last address (or the 2nd-to-last with `FR_PROXY_HOPS=2`, for two
     proxies), and *only* when `FR_TRUST_PROXY=1` (set in the image). Anything earlier in that
     header was written by the visitor, so anyone could fake it to dodge the limits.
  2. **Rate limit** with *token buckets* (`ratelimit.py`). Picture a bucket of 30 tokens per visitor
     for messages: each message takes one, and the bucket refills at 30 per minute. Empty bucket →
     HTTP 429 "slow down" with a `Retry-After` time. Limits: 10 new sessions/min, 30 messages/min
     and 300/day, 6 what-ifs/min, 30 Guardian checks/min. The health check is never limited. Old
     buckets are thrown away so memory doesn't grow.
  3. **Body limit:** any request over 32 KB is refused (413) before the app reads it.
  4. **Security headers** on every response (`headers.py`), most importantly the
     *Content-Security-Policy*: the browser may only load scripts, styles and data from our own
     site. Our page has one tiny inline script (it turns on dark mode before the page paints); we
     allow exactly that script by its SHA-256 fingerprint, computed from the built file at startup,
     instead of allowing all inline scripts. Framing is allowed only by Hugging Face, because
     Spaces show apps inside an iframe.
  5. **One log line** per request: method, route *template* (`/api/sessions/{session_id}/messages`,
     never the real ID), status, time taken, and a client pseudonym (a keyed hash of the address
     that changes every day and can't be turned back into the address). No message text, ever.
- **Session purge** (`purge.py`): every minute a background thread deletes sessions that have been
  inactive for an hour. Without it, a quiet server would keep old conversations in memory.
- **Startup hook** (`on_startup`): after every model is loaded, one "ready" log line lists each
  component's status (no secrets).
- **Deploy script** (`deploy/push_space.sh`): checks out the current commit into a temporary
  folder, swaps in the Space's own README, and uploads only the files the build needs. The repo on
  your computer never changes, and rolling back is just pushing an older commit.

## Why this approach (and what we considered instead)
- **Hugging Face Space vs. a paid host (Render, Fly, a VPS):** free, 16 GB of memory (our models need
  about 1.6 GB at peak), and a public URL. The cost is that it sleeps after ~48 h idle, so we wake
  it before judging.
- **Token buckets vs. "N requests per fixed minute":** buckets allow a natural burst (typing a few
  quick messages) but still cap the average, and they have no "reset at :00" edge to exploit.
- **In-memory limits vs. Redis:** one process means one memory, so a database would add cost and
  a moving part for nothing. If we ever ran several servers, we would need a shared store.
- **Hash-allowed inline script vs. `'unsafe-inline'`:** `'unsafe-inline'` would let an injected
  script run too, which is exactly what CSP is meant to stop. A fingerprint allows only our script.
- **Baking the model into the image vs. downloading at startup:** a cold start would otherwise
  depend on a third-party download (slow, and it can fail right when a judge opens the link).
- **Our own log line vs. the web server's access log:** the standard access log prints full URLs,
  which contain session IDs. Ours prints the route template only, so it is turned off.

## How we measured it (real numbers, with n and the split)
`deploy/loadtest.py` starts the exact production command (prod mode, real fastembed embeddings,
one worker, **no OpenAI calls**: `FR_LLM=0`) on a 4-CPU sandbox, then runs the same 20 simulated
conversations at 1, 5, 10 and 20 users at a time. Each user: scenario list → new session → 6
messages → finish (feedback) → what-if, each from its own address so the real rate limits stay on.
By default each user **thinks like a person**: 2–4 s before each message and about 2 s before
Finish (seeded random pauses, so every run is identical). That matters because the server
explains each message in the background while you chat, so Finish is ready almost instantly.
`--no-think` removes every pause (a burst: the worst case).
Results: `eval/reports/deploy_load.json` (think time) and `deploy_load_burst.json` (burst).

**With think time (realistic):**

| Users at once | Message p50 / p99 (n=120) | Finish p50 / p99 (n=20) | What-if p50 / p99 (n=20) | Errors (n=200) |
|---|---|---|---|---|
| 1 | 27 / 192 ms | 57 / 92 ms | 0.72 / 1.4 s | 0 |
| 5 | 25 / 75 ms | 117 / 319 ms | 1.3 / 2.4 s | 0 |
| 10 | 24 / 125 ms | 215 / 790 ms | 3.1 / 5.1 s | 0 |
| 20 | 25 / 345 ms | 1.2 / 1.7 s | 9.7 / 11.3 s | 0 |

**Burst (no pauses, worst case):** message p50 22 / 100 / 208 / 382 ms and finish p50
50 / 272 / 718 / 1297 ms at 1 / 5 / 10 / 20 users; what-if p50 0.7 / 3.2 / 6.4 / 13.5 s; 0 errors.

- **Cold start:** 6–7 s from process start to the first healthy response, including loading every
  model (n=1 per run).
- **Memory:** 791 MB after warm-up, 854 MB peak (n=1). The Space has 16 GB.
- **CSP:** `deploy/csp_check.mjs` drives headless Chromium through every page (landing, practice,
  chat with X-ray and branches, feedback, what-if, real mode, transparency + Guardian) in light
  and dark mode: **0 violations, 0 console errors**. As a control, changing one character of the
  inline script makes the check fail, so it really does catch violations.

## Limitations
- **What-if is now the slow step:** it simulates several alternative conversations, about 0.7 s of
  CPU each, and requests share the CPUs, so with 20 people asking for a what-if at about the same
  time the last ones wait ~10 s. Messages stay well under 0.5 s and Finish under 2 s even at 20 users.
- With OpenAI turned on, each message also waits for OpenAI (typically 1–3 s); the load test
  deliberately measured our own server without it.
- Rate limits use the visitor's address, so a whole school on one network shares a bucket
  (300 messages/day each is generous for a demo, and it is one environment variable to raise).
- Sessions vanish on restart or after an hour idle (privacy by design, but a judge who leaves for
  two hours starts over).
- The free Space sleeps after ~48 h with no visitors.
- The real `docker build` runs in CI (red-team lane); here we reproduced every step by hand.

## Questions a judge might ask (with answers)
1. **"What stops someone from spamming your app and running up an OpenAI bill?"** Three layers:
   per-visitor rate limits (30 messages/min, 300/day), an app-side daily budget
   (`LLM_DAILY_BUDGET_USD=1`) after which the friend switches to our reviewed line bank, and a
   hard monthly spending limit on the OpenAI account.
2. **"Do you store what teens type?"** No. Conversations live only in server memory, are deleted
   after an hour of inactivity (a background job checks every minute), and the logs record only
   the route, status and timing, with an anonymous daily-changing visitor code. No accounts, no database.
3. **"What is a Content-Security-Policy and why do you need one?"** It's a rule the server sends
   the browser: "only run scripts from this site." Even if someone found a way to inject code into
   the page, the browser would refuse to run it. We tested it in a real headless browser on every
   page: zero violations.
4. **"How many people can use it at once?"** We measured: with 20 simultaneous users (pausing like
   real people), every request succeeded, messages took under 0.35 s at the 99th percentile and the
   feedback report under 1.7 s. The what-if is the heavy part (it simulates alternative
   conversations), so a whole class asking at once would wait about 10 s.
5. **"Why only one server process?"** Sessions are kept in memory for privacy (nothing on disk), and
   memory isn't shared between processes; a second process wouldn't find your conversation. One
   process handles our measured load with zero errors.
