"""End-to-end smoke test through the HTTP API: stub mode and live registry (whatever lanes are on)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

SCRIPT = [
    "hey are you ok? you seemed really off at lunch",
    "that sounds really hard. i'm glad you told me",
    "are you thinking about killing yourself?",
    "i'm really glad you told me. can we talk to the counselor tomorrow? i'll go with you",
    "i'll text you tonight to check on you",
]


@pytest.mark.parametrize("stubbed", [True, False], ids=["stubs", "live-registry"])
def test_full_flow(monkeypatch, stubbed):
    if stubbed:
        monkeypatch.setenv("FR_STUB", "1")
    client = TestClient(app)
    assert client.get("/api/health").json()["ok"]
    scenarios = client.get("/api/scenarios").json()
    assert len(scenarios) >= 5

    session = client.post("/api/sessions", json={"scenario_id": scenarios[0]["id"]}).json()
    sid = session["session_id"]
    first_node = None
    for text in SCRIPT:
        response = client.post(f"/api/sessions/{sid}/messages", json={"text": text})
        if response.status_code == 409:  # conversation already ended
            break
        assert response.status_code == 200, response.text
        first_node = first_node or response.json()["user_node"]["id"]

    tree = client.get(f"/api/sessions/{sid}/tree").json()
    assert len(tree["nodes"]) >= 3
    assert (
        client.post(f"/api/sessions/{sid}/rewind", json={"node_id": session["root_id"]}).status_code
        == 200
    )
    branch = client.post(f"/api/sessions/{sid}/messages", json={"text": "lol you'll be fine"})
    assert branch.status_code == 200

    report = client.post(f"/api/sessions/{sid}/finish").json()
    assert set(report["skill_summary"]) == {
        "check_in",
        "listen",
        "ask_directly",
        "no_secrecy",
        "persuade",
        "refer",
        "follow_up",
    }
    whatif = client.post(f"/api/sessions/{sid}/whatif", json={})
    assert whatif.status_code in (200, 409)

    assert client.get("/api/realmode?lang=es").json()["steps"]
    assert (
        client.post("/api/guardian/check", json={"text": "are you thinking about suicide?"}).json()[
            "level"
        ]
        == "none"
    )
    assert "records" in client.get("/api/metrics").json()


def test_rejects_long_messages():
    client = TestClient(app)
    sid = client.post("/api/sessions", json={"scenario_id": "after-the-breakup"}).json()[
        "session_id"
    ]
    response = client.post(f"/api/sessions/{sid}/messages", json={"text": "a" * 501})
    assert response.status_code == 422
