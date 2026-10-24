"""Turn handling over HTTP: one turn at a time per session, refused messages change nothing, and the
helper's own crisis message is never replayed as a mistake."""

from __future__ import annotations

import threading
import time

from fastapi.testclient import TestClient

from backend.app import services
from backend.app.main import app
from backend.app.session import path_to, store

client = TestClient(app)


def _start() -> str:
    return client.post("/api/sessions", json={"scenario_id": "after-the-breakup"}).json()[
        "session_id"
    ]


def _say(session_id: str, text: str, parent: str | None = None) -> dict:
    body = {"text": text, **({"parent_node_id": parent} if parent else {})}
    return client.post(f"/api/sessions/{session_id}/messages", json=body)


def test_concurrent_messages_take_turns(stub_mode, monkeypatch):
    """A double-click sends two messages at once: they must chain, not both branch from one node."""
    skills = services.skills()
    predict = skills.predict

    def slow_predict(text, context):
        time.sleep(0.2)
        return predict(text, context)

    monkeypatch.setattr(skills, "predict", slow_predict)
    session_id = _start()
    threads = [
        threading.Thread(target=_say, args=(session_id, f"hey, you ok? ({i})")) for i in (1, 2)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(10)
    session = store.get(session_id)
    assert [n.role for n in path_to(session)] == ["friend", "user", "friend", "user", "friend"]
    assert len(session.nodes) == 5, "no orphan branch"


def test_refused_message_does_not_move_the_head(stub_mode):
    session_id = _start()
    root = store.get(session_id).root_id
    crisis = _say(session_id, "honestly i want to die too").json()
    assert crisis["crisis"]
    client.post(f"/api/sessions/{session_id}/rewind", json={"node_id": root})
    refused = _say(session_id, "hey", parent=crisis["system_node"]["id"])
    assert refused.status_code == 409
    assert store.get(session_id).head_id == root, "the conversation stays where the helper left it"
    assert _say(session_id, "hey", parent="nope").status_code == 404


def test_crisis_message_has_no_what_if(stub_mode):
    session_id = _start()
    _say(session_id, "hey are you ok? you seemed off")
    crisis = _say(session_id, "honestly i want to die too").json()
    for node_id in (crisis["user_node"]["id"], crisis["system_node"]["id"]):
        response = client.post(f"/api/sessions/{session_id}/whatif", json={"node_id": node_id})
        assert response.status_code == 409
    report = client.post(f"/api/sessions/{session_id}/finish").json()
    assert crisis["user_node"]["id"] not in [m["node_id"] for m in report["per_message"]]
