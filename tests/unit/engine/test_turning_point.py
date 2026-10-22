"""Turning point and missed opportunities, played through the real engine."""

from __future__ import annotations

from backend.app.contracts import Flags, Node, State
from backend.app.contracts import SkillLabel as L
from backend.app.engine.turning_point import missed_opportunities, turning_point

from .conftest import probs


def user(id_: str, delta: float, turn: int, *labels: L, level: int = 1, **flags) -> Node:
    state = State(trust=40, level=level, turn=turn, last_delta=delta, flags=Flags(**flags))
    return Node(
        id=id_, parent_id=None, role="user", bubbles=["x"], events=probs(*labels), state_after=state
    )


def test_no_drop_no_turning_point():
    assert turning_point([user("a", 5, 1, L.VALIDATED), user("b", 3, 2, L.CHECKED_IN)]) is None


def test_most_negative_wins_and_reason_names_it():
    path = [user("a", -2, 1), user("b", -22, 2, L.DISMISSED), user("c", -12, 3, L.ADVICE_DUMP)]
    tp = turning_point(path)
    assert tp.node_id == "b" and tp.trust_drop == 22
    assert tp.reason == "Trust dropped 22 after a dismissive reply."


def test_ties_go_to_earliest():
    path = [user("a", -12, 1, L.ADVICE_DUMP), user("b", -12, 2, L.ADVICE_DUMP)]
    assert turning_point(path).node_id == "a"


def test_skips_unscored_nodes():
    blocked = Node(
        id="blk", parent_id=None, role="user", bubbles=["kys"], state_after=State(last_delta=-50)
    )
    assert turning_point([blocked, user("a", -12, 1, L.ADVICE_DUMP)]).node_id == "a"


def test_tiny_drops_are_not_turning_points():
    # A good conversation where trust only dipped by decay or diminishing returns: nothing to fix.
    path = [user("a", 5, 1, L.VALIDATED), user("b", -0.25, 2, L.FOLLOW_UP), user("c", -4.9, 3)]
    assert turning_point(path) is None
    assert turning_point([*path, user("d", -5, 4, L.ADVICE_DUMP)]).node_id == "d"


def test_secrecy_broken_reason():
    path = [
        user("a", -17, 1, L.PROMISED_SECRECY, promised_secrecy=True),
        user("b", -4, 2, L.REFERRED_ADULT),
    ]
    path[1].state_after.last_delta = -30  # make the referral the biggest drop for the test
    assert "broke a promise" in turning_point(path).reason


def test_missed_direct_ask_and_referral(convo):
    convo.say("are you ok? you seem off", probs(L.CHECKED_IN))
    convo.say("that sounds really hard", probs(L.VALIDATED, L.CHECKED_IN))
    convo.say("i hear you, that makes sense", probs(L.VALIDATED, L.FOLLOW_UP))
    convo.say("that sounds heavy, i'm sorry", probs(L.VALIDATED, L.ENCOURAGED_HELP))
    assert convo.state.level >= 2
    convo.say("ok", probs())
    missed = missed_opportunities(convo.path, "Maya")
    assert any("ask directly" in m and m.startswith("Turn ") for m in missed), missed


def test_no_missed_ask_if_already_asked(convo):
    convo.say("are you thinking about suicide?", probs(L.ASKED_DIRECTLY))
    for _ in range(4):
        convo.say("that sounds hard", probs(L.VALIDATED, L.CHECKED_IN))
    assert not any("ask directly" in m for m in missed_opportunities(convo.path))


def test_missed_referral_after_disclosure():
    path = [
        user("a", 10, 1, L.ASKED_DIRECTLY, level=3),
        user("b", 5, 2, L.VALIDATED, level=3),
        user("c", 5, 3, L.VALIDATED, level=3),
    ]
    missed = missed_opportunities(path)
    assert any(m.startswith("Turn 1") and "988" in m for m in missed)
    path[2] = user("c", 5, 3, L.REFERRED_988, level=3)
    assert not any("988" in m for m in missed_opportunities(path))


def test_secrecy_and_seen_are_reported(convo):
    convo.say("ok i won't tell anyone", probs(L.PROMISED_SECRECY))
    convo.say("lol you'll be fine", probs(L.DISMISSED))
    missed = missed_opportunities(convo.path, "Maya")
    assert any("promised to keep it secret" in m for m in missed)
    assert any("left you on Seen" in m and m.startswith("Turn 2") for m in missed)
    assert missed == sorted(missed, key=lambda m: int(m.split()[1].rstrip(":")))
