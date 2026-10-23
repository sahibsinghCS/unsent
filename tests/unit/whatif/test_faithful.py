"""Replay faithfulness: rollouts must reproduce the live engine exactly.

The live engine remembers each State's active labels keyed by the State *object* (diminishing returns).
Rollouts pass those labels explicitly instead, so replaying what the user actually said from any message
must give the same states, the same "Seen" and the same bank lines as the live conversation.
"""

from __future__ import annotations

from backend.app import services
from backend.app.content import get_scenario
from backend.app.engine.state import active_labels
from backend.app.whatif.rollout import WhatIf, labels_before, split_at

from .conftest import WEAK_CHAT, new_session, play, user_ids

REPEATS = [
    "hey are you ok? you seemed off",
    "that sounds really hard, i'm sorry",
    "that sounds really hard. i'm sorry it's like this",
    "lol you'll be fine, just get over it",
    "ok",
    "i'm sorry. that sounds really hard",
]


def _replay_matches(texts: list[str], start: int) -> None:
    session = new_session()
    path = play(session, texts)
    node_id = user_ids(path)[start]
    base, _, _ = split_at(path, node_id)
    sim = WhatIf().simulator(session)
    run = sim.replay(base, texts[start:], "t")
    live = path[len(base) :]
    assert len(run.nodes) == len(live)
    for mine, theirs in zip(run.nodes, live, strict=True):
        assert mine.role == theirs.role
        assert mine.state_after.model_dump() == theirs.state_after.model_dump()
        assert mine.bubbles == theirs.bubbles
        assert mine.seen_no_reply == theirs.seen_no_reply
        assert mine.line_id == theirs.line_id


def test_replay_reproduces_the_live_conversation_from_every_message():
    for start in range(len(REPEATS)):
        _replay_matches(REPEATS, start)


def test_replay_includes_seen_exactly_like_the_live_engine():
    session = new_session()
    path = play(session, WEAK_CHAT)
    assert any(n.seen_no_reply for n in path)
    _replay_matches(WEAK_CHAT, 1)


def test_a_blocked_message_keeps_the_remembered_labels():
    texts = ["that sounds really hard, i'm sorry", "kys", "that sounds really hard, i'm sorry"]
    _replay_matches(texts, 2)


def test_forgetting_the_previous_labels_would_change_the_result():
    """The pitfall itself: a naive rebuild (no previous labels) gives a different, wrong state."""
    session = new_session()
    path = play(session, REPEATS[:3])
    scenario = get_scenario(session.scenario_id)
    base, original, _ = split_at(path, user_ids(path)[2])
    prev = labels_before(base, 0.5)
    assert prev == active_labels(base[-2].events, 0.5) and prev
    state = base[-1].state_after
    engine = services.engine()
    naive = engine.update(state.model_copy(deep=True), original.events, scenario)
    faithful = engine.update(state, original.events, scenario, prev_active=prev)
    assert faithful.model_dump() == original.state_after.model_dump()
    assert naive.trust != faithful.trust
