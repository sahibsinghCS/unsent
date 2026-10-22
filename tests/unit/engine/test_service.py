"""The engine as the app uses it: service wiring, verifier fallback, pipeline + API integration."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.app import services
from backend.app.contracts import ActorOutput
from backend.app.contracts import Reaction as R
from backend.app.contracts import SkillLabel as L
from backend.app.engine import actor, service
from backend.app.engine.service import Engine

from .conftest import FIXTURES, Convo, probs

GOOD = [
    ("hey are you ok? you seemed really off at lunch", (L.CHECKED_IN,)),
    ("that sounds really hard. i'm glad you told me", (L.VALIDATED,)),
    ("are you thinking about killing yourself?", (L.ASKED_DIRECTLY,)),
    (
        "thank you for telling me. can we talk to the counselor? i'll go with you",
        (L.VALIDATED, L.REFERRED_ADULT, L.FOLLOW_UP),
    ),
    ("that sounds really scary, i'm glad you told me", (L.VALIDATED,)),
    (
        "we can call 988 together or go to the counselor tomorrow",
        (L.REFERRED_988, L.REFERRED_ADULT),
    ),
    ("i'm not going anywhere. i'll text you tonight", (L.FOLLOW_UP,)),
    (
        "i'll go with you to the counselor tomorrow, you don't have to do this alone",
        (L.REFERRED_ADULT, L.ENCOURAGED_HELP, L.FOLLOW_UP),
    ),
]


def test_registry_uses_real_engine():
    assert service.IMPLEMENTED
    assert isinstance(services.engine(), Engine)
    assert services.status()["engine"] == "real"


def test_good_conversation_succeeds(convo):
    for text, labels in GOOD:
        friend = convo.say(text, probs(*labels))
        if convo.state.status.startswith("ended"):
            break
    assert convo.state.status == "ended_success"
    assert friend.reaction == R.SUCCESS
    friend_lines = [n.line_id for n in convo.path if n.role == "friend" and n.line_id]
    assert len(friend_lines) == len(set(friend_lines)), "no line repeated"


def test_dismissive_conversation_goes_silent_then_fails(convo):
    seen = 0
    for _ in range(6):
        friend = convo.say("lol you'll be fine", probs(L.DISMISSED))
        seen += friend.seen_no_reply
        if convo.state.status.startswith("ended"):
            break
    assert seen >= 1 and convo.state.status == "ended_fail"


def test_diminishing_returns_through_service(engine, scenario):
    convo = Convo(engine, scenario)
    convo.say("that sounds hard", probs(L.VALIDATED))
    first = convo.state.last_delta
    convo.say("that sounds hard", probs(L.VALIDATED))
    assert convo.state.last_delta < first
    explicit = engine.update(convo.state, probs(L.VALIDATED), scenario, prev_active=frozenset())
    assert explicit.last_delta == pytest.approx(first)


def test_secrecy_then_referral_gives_secrecy_broken(convo):
    convo.say("are you ok?", probs(L.CHECKED_IN))
    convo.say("ok i won't tell anyone", probs(L.PROMISED_SECRECY))
    friend = convo.say(
        "i care about you too much, we need to tell the counselor", probs(L.REFERRED_ADULT)
    )
    assert friend.reaction == R.SECRECY_BROKEN and friend.bubbles
    assert convo.state.flags.referral_turns == [3]


def test_generate_skips_lines_that_fail_verification(engine, scenario, monkeypatch):
    real = engine.bank(scenario.id)
    poisoned = tuple(
        ln.model_copy(update={"bubbles": ["as an ai, i understand"]})
        if ln.level == 0 and ln.reaction == R.CHECKED_IN
        else ln
        for ln in real
    )
    monkeypatch.setattr(engine, "bank", lambda *_: poisoned)
    convo = Convo(engine, scenario)
    friend = convo.say("you ok?", probs(L.CHECKED_IN))
    assert "as an ai" not in " ".join(friend.bubbles)
    assert friend.bubbles


def test_verify_via_service(engine, scenario):
    assert not engine.verify(
        ActorOutput(bubbles=["made up text"]), scenario, Convo(engine, scenario).state
    ).ok


def test_api_flow_with_real_engine(monkeypatch):
    monkeypatch.setenv(actor.BANK_DIR_ENV, str(FIXTURES))
    monkeypatch.setenv("FR_STUB_ONLY", "guardian,skills,critic,whatif")
    services.reset()
    client = TestClient(__import__("backend.app.main", fromlist=["app"]).app)
    assert client.get("/api/health").json()["components"]["engine"] == "real"
    sid = client.post("/api/sessions", json={"scenario_id": "after-the-breakup"}).json()[
        "session_id"
    ]
    replies = []
    for text, _ in GOOD:
        response = client.post(f"/api/sessions/{sid}/messages", json={"text": text})
        if response.status_code == 409:
            break
        assert response.status_code == 200, response.text
        friend = response.json()["friend_node"]
        replies.append(friend["line_id"])
    assert all(r and r.startswith("atb-") for r in replies), replies
    report = client.post(f"/api/sessions/{sid}/finish").json()
    assert "skill_summary" in report
