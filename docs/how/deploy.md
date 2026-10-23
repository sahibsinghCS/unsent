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
  1. Works out who the visitor is. On Hugging Face every request comes through their proxy, so we
     use the first address in the `X-Forwarded-For` header, but *only* when `FR_TRUST_PROXY=1`
     (set in the image). Otherwise anyone could fake that header to dodge the limits.
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
Full results: `eval/reports/deploy_load.json`.

| Concurrent users | Message p50 / p99 (n=120) | Finish p50 (n=20) | What-if p50 (n=20) | Errors (n=200) |
|---|---|---|---|---|
| 1 | 34 ms / 94 ms | 1.2 s | 130 ms | 0 |
| 5 | 161 ms / 283 ms | 4.7 s | 558 ms | 0 |
| 10 | 290 ms / 453 ms | 9.2 s | 840 ms | 0 |
| 20 | 583 ms / 887 ms | 18.1 s | 1.8 s | 0 |

- **Cold start:** 5.8 s from process start to the first healthy response, including loading every
  model (n=1).
- **Memory:** 796 MB after warm-up, 1.58 GB peak during the test (n=1). The Space has 16 GB.
- **Throughput:** about 6–8 requests per second, flat from 5 to 20 users: the CPU is the limit.
- **CSP:** `deploy/csp_check.mjs` drives headless Chromium through every page (landing, practice,
  chat with X-ray and branches, feedback, what-if, real mode, transparency + Guardian) in light
  and dark mode: **0 violations, 0 console errors**. As a control, changing one character of the
  inline script makes the check fail, so it really does catch violations.

## Limitations
- **"Finish" (the feedback report) is the slow step:** about 1.2 s of CPU each, and requests share
  2 CPUs, so 20 people pressing Finish *at the same instant* wait up to ~20 s. Real visitors are
  spread out; messages stay under 1 s even at 20 at once.
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
4. **"How many people can use it at once?"** We measured: at 20 simultaneous users every request
   succeeded and messages took under 0.9 s at the 99th percentile. The feedback report is the slow
   part (about 1.2 s of CPU each), so a whole class pressing Finish at once would queue.
5. **"Why only one server process?"** Sessions are kept in memory for privacy (nothing on disk), and
   memory isn't shared between processes; a second process wouldn't find your conversation. One
   process handles our measured load with zero errors.
