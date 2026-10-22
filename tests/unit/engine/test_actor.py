"""Line-bank actor: reaction choice, candidate tiers, fact gating, anti-repetition, ranking."""

from __future__ import annotations

import pytest

from backend.app.contracts import Flags, Line, Node, State
from backend.app.contracts import Reaction as R
from backend.app.contracts import SkillLabel as L
from backend.app.engine import actor
from backend.app.engine.actor import choose_reaction, generate, load_bank

from .conftest import FIXTURES, probs


def st(level: int = 1, trust: float = 40, status: str = "active", turn: int = 2, **flags) -> State:
    return State(trust=trust, level=level, turn=turn, status=status, flags=Flags(**flags))


def hist(state: State, *friend_lines: str, text: str = "hi") -> list[Node]:
    """A short path: root, past friend lines, then the latest user node carrying `state`."""
    nodes = [Node(id="root", parent_id=None, role="friend", bubbles=["hey"], state_after=state)]
    for i, line_id in enumerate(friend_lines):
        nodes.append(
            Node(
                id=f"f{i}",
                parent_id=nodes[-1].id,
                role="friend",
                bubbles=["x"],
                state_after=state,
                line_id=line_id,
            )
        )
    nodes.append(
        Node(id="u", parent_id=nodes[-1].id, role="user", bubbles=[text], state_after=state)
    )
    return nodes


def line(id_: str, level: int, reaction: R, cue: str = "", facts=()) -> Line:
    return Line(
        id=id_,
        scenario_id="after-the-breakup",
        level=level,
        reaction=reaction,
        bubbles=[f"line {id_}"],
        fact_ids=list(facts),
        cue=cue or None,
    )


@pytest.mark.parametrize(
    ("labels", "expected"),
    [
        ((L.DISMISSED, L.VALIDATED), R.DISMISSED),
        ((L.PROMISED_SECRECY, L.ASKED_DIRECTLY), R.PROMISED_SECRECY),
        ((L.ASKED_DIRECTLY, L.REFERRED_ADULT), R.ASKED_DIRECTLY),
        ((L.REFERRED_988, L.VALIDATED), R.REFERRED),
        ((L.VALIDATED, L.ADVICE_DUMP), R.VALIDATED),
        ((L.ADVICE_DUMP, L.CHECKED_IN), R.ADVICE_DUMP),
        ((L.CHECKED_IN, L.ENCOURAGED_HELP), R.CHECKED_IN),
        ((L.ENCOURAGED_HELP, L.FOLLOW_UP), R.ENCOURAGED_HELP),
        ((L.FOLLOW_UP,), R.FOLLOW_UP),
    ],
)
def test_reaction_priority(cfg, labels, expected):
    state = st()
    reaction = choose_reaction(state, frozenset(labels), "hi", hist(state), cfg, state)
    assert reaction == expected


@pytest.mark.parametrize(
    ("status", "expected"), [("ended_success", R.SUCCESS), ("ended_fail", R.FAIL)]
)
def test_endings_beat_everything(cfg, status, expected):
    state = st(status=status)
    assert choose_reaction(state, frozenset({L.DISMISSED}), "x", hist(state), cfg) == expected


def test_secrecy_broken_beats_dismissed(cfg):
    before, after = st(promised_secrecy=True), st(promised_secrecy=False, referral_turns=[2])
    reaction = choose_reaction(after, frozenset({L.DISMISSED}), "x", hist(after), cfg, before)
    assert reaction == R.SECRECY_BROKEN


def test_off_topic_vs_neutral(cfg):
    state = st()
    path = hist(state, text="")
    path[0].bubbles = ["i cant sleep, i keep replaying the breakup"]
    assert choose_reaction(state, frozenset(), "zxq vbnm wert yuio", path, cfg) == R.OFF_TOPIC
    assert choose_reaction(state, frozenset(), "ok", path, cfg) == R.NEUTRAL
    related = "you keep replaying the breakup and cant sleep?"
    assert choose_reaction(state, frozenset(), related, path, cfg) == R.NEUTRAL


def test_picks_reaction_at_current_level(scenario, bank, cfg):
    state = st(level=2)
    out = generate(
        scenario, state, hist(state), "that sounds heavy", probs(L.VALIDATED), bank=bank, cfg=cfg
    )
    assert out.reaction == R.VALIDATED and out.line_id.startswith("atb-2-validated")


def test_widens_to_lower_level(scenario, cfg):
    bank = [line("low", 1, R.FOLLOW_UP), line("n2", 2, R.NEUTRAL)]
    state = st(level=2)
    out = generate(
        scenario, state, hist(state), "i'll check on you", probs(L.FOLLOW_UP), bank=bank, cfg=cfg
    )
    assert out.line_id == "low" and out.reaction == R.FOLLOW_UP


def test_falls_back_to_neutral_then_scenario_lines(scenario, cfg):
    state = st(level=1)
    bank = [line("n1", 1, R.NEUTRAL)]
    out = generate(scenario, state, hist(state), "x", probs(L.FOLLOW_UP), bank=bank, cfg=cfg)
    assert out.line_id == "n1" and out.reaction == R.NEUTRAL
    empty = generate(scenario, state, hist(state), "x", probs(L.FOLLOW_UP), bank=[], cfg=cfg)
    assert empty.line_id is None
    assert empty.bubbles[0] in scenario.fallback_lines[1] + scenario.fallback_lines[0]


def test_drops_lines_with_facts_above_level(scenario, cfg):
    bank = [line("leak", 1, R.VALIDATED, facts=["f3a"]), line("ok", 1, R.VALIDATED, facts=["f1a"])]
    state = st(level=1)
    out = generate(scenario, state, hist(state), "x", probs(L.VALIDATED), bank=bank, cfg=cfg)
    assert out.line_id == "ok"


def test_never_uses_line_above_level(scenario, cfg):
    bank = [line("high", 3, R.VALIDATED), line("low", 0, R.VALIDATED)]
    state = st(level=1)
    out = generate(scenario, state, hist(state), "x", probs(L.VALIDATED), bank=bank, cfg=cfg)
    assert out.line_id == "low"


def test_anti_repetition_and_least_recently_used(scenario, cfg):
    bank = [line("a", 1, R.VALIDATED), line("b", 1, R.VALIDATED)]
    state = st(level=1)
    out = generate(scenario, state, hist(state, "a"), "x", probs(L.VALIDATED), bank=bank, cfg=cfg)
    assert out.line_id == "b"
    out = generate(
        scenario, state, hist(state, "b", "a"), "x", probs(L.VALIDATED), bank=bank, cfg=cfg
    )
    assert out.line_id == "b"  # both used: b was used longest ago


def test_unused_neutral_preferred_over_repeating(scenario, cfg):
    bank = [line("v", 1, R.VALIDATED), line("n", 1, R.NEUTRAL)]
    state = st(level=1)
    out = generate(scenario, state, hist(state, "v"), "x", probs(L.VALIDATED), bank=bank, cfg=cfg)
    assert out.line_id == "n"


def test_ranks_by_similarity_to_cue(scenario, cfg):
    bank = [
        line("sleep", 1, R.VALIDATED, cue="that sounds exhausting, not sleeping is so hard"),
        line("school", 1, R.VALIDATED, cue="ugh everyone at school gossiping must feel awful"),
    ]
    state = st(level=1)
    text = "not sleeping sounds exhausting"
    out = generate(
        scenario, state, hist(state, text=text), text, probs(L.VALIDATED), bank=bank, cfg=cfg
    )
    assert out.line_id == "sleep"


def test_exact_level_bonus_breaks_close_calls(scenario, cfg):
    bank = [line("l0", 0, R.VALIDATED, cue="same cue"), line("l1", 1, R.VALIDATED, cue="same cue")]
    state = st(level=1)
    out = generate(scenario, state, hist(state), "same cue", probs(L.VALIDATED), bank=bank, cfg=cfg)
    assert out.line_id == "l1"


def test_deterministic(scenario, bank, cfg):
    state = st(level=2)
    runs = {
        generate(
            scenario, state, hist(state), "are you ok?", probs(L.CHECKED_IN), bank=bank, cfg=cfg
        ).line_id
        for _ in range(5)
    }
    assert len(runs) == 1


def test_silent_returns_no_bubbles(scenario, bank, cfg):
    state = st(status="silent")
    assert generate(scenario, state, hist(state), "x", probs(), bank=bank, cfg=cfg).bubbles == []


def test_success_line_at_level_4(scenario, bank, cfg):
    state = st(level=4, status="ended_success", trust=80)
    out = generate(
        scenario,
        state,
        hist(state),
        "i'll go with you",
        probs(L.REFERRED_ADULT),
        bank=bank,
        cfg=cfg,
    )
    assert out.reaction == R.SUCCESS and out.line_id.startswith("atb-4-success")


def test_load_bank_locale_fallback_and_env(monkeypatch):
    assert load_bank("after-the-breakup", "es", FIXTURES)[0].locale == "en"
    monkeypatch.setenv(actor.BANK_DIR_ENV, str(FIXTURES))
    assert len(load_bank("after-the-breakup")) >= 50
    assert load_bank("no-such-scenario") == ()


def test_level_up_turn_discloses_new_fact(scenario, cfg):
    bank = [
        line("ref", 3, R.REFERRED, cue="talk to the counselor"),
        line("tell", 3, R.NEUTRAL, facts=["f3a"]),
    ]
    before, after = st(level=2), st(level=3, asked_directly_ever=True)
    path = hist(before)
    path[-1].state_after = after
    text = "talk to the counselor"
    out = generate(scenario, after, path, text, probs(L.REFERRED_ADULT), bank=bank, cfg=cfg)
    assert out.line_id == "tell" and out.reaction == R.NEUTRAL
    steady = hist(after)
    out = generate(scenario, after, steady, text, probs(L.REFERRED_ADULT), bank=bank, cfg=cfg)
    assert out.line_id == "ref"
