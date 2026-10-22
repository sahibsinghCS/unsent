"""The turn pipeline, exercised with stubs (FR_STUB=1)."""

from __future__ import annotations

from backend.app.content import get_scenario
from backend.app.contracts import Node, Reaction
from backend.app.pipeline import run_turn
from backend.app.session import create_session, path_to


def _session():
    scenario = get_scenario("after-the-breakup")
    opening = Node(
        id="root",
        parent_id=None,
        role="friend",
        bubbles=scenario.opening,
        state_after=__import__("backend.app.services", fromlist=["x"])
        .engine()
        .initial_state(scenario),
        reaction=Reaction.OPENING,
    )
    return create_session(scenario.id, "en", "US", opening)


def test_normal_turn_gets_a_friend_reply(stub_mode):
    session = _session()
    response = run_turn(session, "hey are you ok? you seemed off")
    assert response.friend_node is not None and response.friend_node.bubbles
    assert response.state_after.trust > response.state_before.trust
    assert [n.role for n in path_to(session)] == ["friend", "user", "friend"]


def test_asking_directly_is_not_a_crisis(stub_mode):
    response = run_turn(_session(), "are you thinking about killing yourself?")
    assert not response.crisis and not response.blocked
    assert response.user_node.guardian.level == "none"


def test_first_person_risk_pauses_the_roleplay(stub_mode):
    response = run_turn(_session(), "honestly i want to die too")
    assert response.crisis
    assert response.friend_node is None and response.system_node is not None
    assert response.state_after.status == "paused_crisis"


def test_harmful_message_is_blocked(stub_mode):
    response = run_turn(_session(), "kys")
    assert response.blocked and response.system_node is not None
    assert response.state_after == response.state_before


def test_dismissive_message_leaves_friend_on_seen(stub_mode):
    response = run_turn(_session(), "lol you'll be fine")
    assert response.friend_node is not None and response.friend_node.seen_no_reply
    assert response.friend_node.bubbles == []
