"""Write example API payloads to backend/app/stubs/fixtures/ (reference for the frontend and tests).

Runs a scripted conversation through the real API code with FR_STUB=1 (all stubs).
Run: make fixtures
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("FR_STUB", "1")
os.environ.setdefault("FR_EMBED", "hash")

from fastapi.testclient import TestClient  # noqa: E402

from backend.app.main import app  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "backend" / "app" / "stubs" / "fixtures"
SCRIPT = [
    "hey are you ok? you seemed really off at lunch",
    "lol you'll be fine",
    "sorry, that was a dumb thing to say. that sounds really hard",
    "are you thinking about killing yourself?",
    "i'm really glad you told me. can we talk to the counselor tomorrow? i'll go with you",
    "i'll text you tonight to check on you",
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    client = TestClient(app)
    session = client.post("/api/sessions", json={"scenario_id": "after-the-breakup"}).json()
    sid = session["session_id"]
    turns = [client.post(f"/api/sessions/{sid}/messages", json={"text": t}).json() for t in SCRIPT]
    payloads = {
        "scenarios.json": client.get("/api/scenarios").json(),
        "session_start.json": session,
        "turns.json": turns,
        "crisis_turn.json": client.post(
            f"/api/sessions/{client.post('/api/sessions', json={'scenario_id': 'after-the-breakup'}).json()['session_id']}/messages",
            json={"text": "honestly i want to die too"},
        ).json(),
        "tree.json": client.get(f"/api/sessions/{sid}/tree").json(),
        "critic_report.json": client.post(f"/api/sessions/{sid}/finish").json(),
        "whatif.json": client.post(f"/api/sessions/{sid}/whatif", json={}).json(),
        "realmode.json": client.get("/api/realmode").json(),
        "metrics.json": client.get("/api/metrics").json(),
    }
    for name, payload in payloads.items():
        (OUT / name).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {len(payloads)} fixtures to {OUT}")


if __name__ == "__main__":
    main()
