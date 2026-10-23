"""Load test for a prod-mode FirstReply server (run with FR_LLM=0: no OpenAI calls, ever).

    uv run python deploy/loadtest.py                 # spawns its own prod-mode server on :7861
    uv run python deploy/loadtest.py --url http://127.0.0.1:7860   # test a server you started

Each simulated user opens the scenario list, starts a session, sends a 6-message conversation,
finishes (feedback) and asks for the what-if. Every user gets its own client address (via
X-Forwarded-For, which the server trusts with FR_TRUST_PROXY=1), so the real per-visitor rate
limits stay on, exactly as in production. The same 20 conversations run at 1, 5, 10 and 20
concurrent users. When it spawns the server it also measures cold start (process start -> first
healthy response, including model warm-up) and peak memory (RSS).

Writes eval/reports/deploy_load.json in the shared schema (eval/README.md).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import httpx
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "eval" / "reports" / "deploy_load.json"

CONVERSATION = [
    "hey are you ok? you seemed really off at lunch",
    "lol you'll be fine",  # a weak reply, so the feedback has a turning point for the what-if
    "sorry, that was a dumb thing to say. that sounds really hard",
    "are you thinking about killing yourself?",
    "i'm really glad you told me. can we talk to the counselor tomorrow? i'll go with you",
    "i'm here. we can call 988 together and i'll check on you tonight",
]


class Recorder:
    def __init__(self) -> None:
        self.latency: dict[str, list[float]] = defaultdict(list)
        self.errors: dict[str, int] = defaultdict(int)
        self.statuses: dict[str, dict[int, int]] = defaultdict(lambda: defaultdict(int))

    async def call(self, client: httpx.AsyncClient, name: str, method: str, url: str, **kw):
        started = time.perf_counter()
        try:
            response = await client.request(method, url, **kw)
            status = response.status_code
        except httpx.HTTPError:
            response, status = None, 0
        self.latency[name].append((time.perf_counter() - started) * 1000)
        self.statuses[name][status] += 1
        if not (200 <= status < 300):
            self.errors[name] += 1
        return response


async def one_user(base: str, index: int, level: int, rec: Recorder) -> None:
    ip = f"10.{level}.{index // 250}.{index % 250 + 1}"  # a distinct visitor per conversation
    async with httpx.AsyncClient(
        base_url=base, headers={"x-forwarded-for": ip}, timeout=60.0
    ) as client:
        scenarios = await rec.call(client, "scenarios", "GET", "/api/scenarios")
        if scenarios is None or scenarios.status_code != 200:
            return
        items = scenarios.json()
        scenario = items[index % len(items)]["id"]
        created = await rec.call(
            client,
            "session_create",
            "POST",
            "/api/sessions",
            json={"scenario_id": scenario, "locale": "en", "country": "US"},
        )
        if created is None or created.status_code != 200:
            return
        sid = created.json()["session_id"]
        for text in CONVERSATION:
            await rec.call(
                client, "message", "POST", f"/api/sessions/{sid}/messages", json={"text": text}
            )
        await rec.call(client, "finish", "POST", f"/api/sessions/{sid}/finish")
        await rec.call(client, "whatif", "POST", f"/api/sessions/{sid}/whatif", json={})


async def run_level(base: str, users: int, conversations: int) -> tuple[Recorder, float]:
    rec = Recorder()
    queue = list(range(conversations))
    sem = asyncio.Semaphore(users)

    async def guarded(i: int) -> None:
        async with sem:
            await one_user(base, i, users, rec)

    started = time.perf_counter()
    await asyncio.gather(*(guarded(i) for i in queue))
    return rec, time.perf_counter() - started


def rss_kb(pid: int, field: str = "VmRSS") -> int | None:
    try:
        for line in Path(f"/proc/{pid}/status").read_text().splitlines():
            if line.startswith(field + ":"):
                return int(line.split()[1])
    except OSError:
        return None
    return None


def spawn_server(port: int, cwd: Path) -> tuple[subprocess.Popen, float]:
    """Start the exact production command (one worker) and return (process, cold start seconds)."""
    env = {
        **os.environ,
        "FR_ENV": "prod",
        "FR_EMBED": "fastembed",
        "FR_TRUST_PROXY": "1",
        "FR_LLM": "0",
        "PYTHONUNBUFFERED": "1",
    }
    env.pop("OPENAI_API_KEY", None)  # belt and braces: this lane never calls OpenAI
    cmd = [
        sys.executable, "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1",
        "--port", str(port), "--workers", "1", "--proxy-headers", "--forwarded-allow-ips=*",
        "--no-access-log", "--no-server-header",
    ]  # fmt: skip
    started = time.perf_counter()
    proc = subprocess.Popen(
        cmd, cwd=cwd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    deadline = started + 180
    while time.perf_counter() < deadline:
        if proc.poll() is not None:
            raise SystemExit(f"server exited early with code {proc.returncode}")
        try:
            if httpx.get(f"http://127.0.0.1:{port}/api/health", timeout=1).status_code == 200:
                return proc, time.perf_counter() - started
        except httpx.HTTPError:
            pass
        time.sleep(0.05)
    proc.kill()
    raise SystemExit("server never became healthy")


def record(metric: str, value: float, n: int, split: str, notes: str) -> dict:
    return {
        "lane": "deploy",
        "metric": metric,
        "value": round(float(value), 2),
        "n": int(n),
        "split": split,
        "notes": notes,
        "created": datetime.now().astimezone().isoformat(timespec="seconds"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--url", help="test an already-running server instead of spawning one")
    parser.add_argument("--port", type=int, default=7861)
    parser.add_argument(
        "--cwd", type=Path, default=ROOT, help="app directory for the spawned server"
    )
    parser.add_argument("--levels", default="1,5,10,20")
    parser.add_argument("--conversations", type=int, default=20, help="per concurrency level")
    parser.add_argument("--out", type=Path, default=REPORT)
    args = parser.parse_args()
    if os.getenv("FR_LLM", "0") != "0":
        print(
            "refusing to run: set FR_LLM=0 (the load test must never call OpenAI)", file=sys.stderr
        )
        return 2

    records: list[dict] = []
    proc = None
    base = args.url
    host = f"{os.cpu_count()} CPU sandbox, prod mode, FR_LLM=0, fastembed, 1 uvicorn worker"
    if base is None:
        proc, cold = spawn_server(args.port, args.cwd)
        base = f"http://127.0.0.1:{args.port}"
        records.append(
            record("cold_start_s", cold, 1, "local", "process start -> first healthy /api/health, "
                   "incl. warm-up of every model; " + host)
        )  # fmt: skip
        idle = rss_kb(proc.pid)
        if idle:
            records.append(record("rss_idle_mb", idle / 1024, 1, "local", "after warm-up; " + host))

    summary = []
    for users in [int(x) for x in args.levels.split(",")]:
        rec, wall = asyncio.run(run_level(base, users, args.conversations))
        total = sum(len(v) for v in rec.latency.values())
        errors = sum(rec.errors.values())
        split = f"c{users}"
        line = {"users": users, "requests": total, "errors": errors, "rps": round(total / wall, 1)}
        for name, values in sorted(rec.latency.items()):
            arr = np.array(values)
            for q in (50, 95, 99):
                records.append(
                    record(f"latency_p{q}_ms/{name}", np.percentile(arr, q), len(arr), split,
                           f"{users} concurrent users; " + host)
                )  # fmt: skip
            line[f"{name}_p95_ms"] = round(float(np.percentile(arr, 95)), 1)
        records.append(record("error_rate", errors / max(total, 1), total, split,
                              f"non-2xx or failed; statuses {_statuses(rec)}"))  # fmt: skip
        records.append(record("throughput_rps", total / wall, total, split,
                              f"{args.conversations} conversations, {users} at a time"))  # fmt: skip
        summary.append(line)
        print(json.dumps(line))

    if proc is not None:
        peak = rss_kb(proc.pid, "VmHWM")
        if peak:
            records.append(record("rss_peak_mb", peak / 1024, 1, "local",
                                  "peak resident memory over the whole run (VmHWM); " + host))  # fmt: skip
        proc.terminate()
        proc.wait(timeout=10)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(records)} records to {args.out}")
    return 0


def _statuses(rec: Recorder) -> str:
    return ", ".join(
        f"{name}: " + "/".join(f"{code}x{count}" for code, count in sorted(codes.items()))
        for name, codes in sorted(rec.statuses.items())
    )


if __name__ == "__main__":
    raise SystemExit(main())
