"""State machine: trust math, levels, gates, hysteresis, secrecy, silence, endings, properties."""

from __future__ import annotations

import random

import pytest

from backend.app.contracts import Flags, State
from backend.app.contracts import SkillLabel as L
from backend.app.engine.state import (
    active_labels,
    initial_state,
    load_config,
    secrecy_broken,
    trust_delta,
    update,
)

from .conftest import probs


def at(trust: float, level: int = 0, turn: int = 3, **flags) -> State:
    return State(trust=trust, level=level, turn=turn, flags=Flags(**flags))


def test_config_matches_yaml(cfg):
    assert cfg.weights[L.VALIDATED] == 12 and cfg.weights[L.DISMISSED] == -20
    assert cfg.level_up_thresholds == (0, 25, 45, 60, 75)
    assert cfg.max_turns == 16 and cfg.event_threshold == 0.5
    assert load_config().weights == cfg.weights


def test_initial_state(scenario, cfg):
    state = initial_state(scenario, cfg)
    assert (state.trust, state.level, state.turn, state.status) == (30, 0, 0, "active")


def test_event_threshold_is_inclusive():
    on = active_labels({L.VALIDATED: 0.5, L.DISMISSED: 0.49})
    assert on == {L.VALIDATED}


def test_open_persona_full_weight(open_scenario, cfg):
    new = update(at(30), probs(L.VALIDATED), open_scenario, cfg)
    assert new.last_delta == 10 and new.trust == 40


def test_guarded_persona_scales_positive_only(scenario, cfg):
    assert update(at(30), probs(L.VALIDATED), scenario, cfg).last_delta == pytest.approx(6.4)
    assert update(at(50), probs(L.DISMISSED), scenario, cfg).last_delta == -22


def test_decay_when_nothing_detected(open_scenario, cfg):
    assert update(at(30), probs(), open_scenario, cfg).last_delta == -2


def test_diminishing_returns_for_repeated_positive(cfg):
    on = frozenset({L.VALIDATED})
    assert trust_delta(on, frozenset(), False, cfg) == 10
    assert trust_delta(on, on, False, cfg) == 4  # 12 * 0.5 - 2


def test_negative_labels_never_diminish(cfg):
    on = frozenset({L.DISMISSED})
    assert trust_delta(on, on, False, cfg) == trust_delta(on, frozenset(), False, cfg) == -22


def test_multiple_labels_add_up(cfg):
    on = frozenset({L.VALIDATED, L.ASKED_DIRECTLY})
    assert trust_delta(on, frozenset(), False, cfg) == 25


def test_breakdown_terms(open_scenario, scenario, cfg):
    new = update(at(30), probs(L.VALIDATED, L.ASKED_DIRECTLY), open_scenario, cfg)
    assert new.last_breakdown == {"asked_directly": 15, "validated": 12, "decay": -2}
    guarded = update(at(30), probs(L.VALIDATED), scenario, cfg, frozenset({L.VALIDATED}))
    assert guarded.last_breakdown == {"validated": 8.4, "diminishing": -4.2, "decay": -2}
    promised = update(at(50), probs(L.PROMISED_SECRECY), open_scenario, cfg)
    broke = update(promised, probs(L.REFERRED_ADULT), open_scenario, cfg)
    assert broke.last_breakdown == {"referred_adult": 8, "decay": -2, "secrecy_broken": -10}


def test_breakdown_sums_to_last_delta_even_when_clamped(open_scenario, cfg):
    low = update(at(5), probs(L.DISMISSED, L.ADVICE_DUMP), open_scenario, cfg)
    assert low.trust == 0 and low.last_delta == -32
    assert round(sum(low.last_breakdown.values()), 4) == low.last_delta


def test_trust_clamped(open_scenario, cfg):
    assert update(at(5), probs(L.DISMISSED), open_scenario, cfg).trust == 0
    big = probs(*[label for label in L if cfg.weights[label] > 0])
    assert update(at(95, level=1), big, open_scenario, cfg).trust == 100


def test_level_rises_at_most_one_per_turn(open_scenario, cfg):
    big = probs(*[label for label in L if cfg.weights[label] > 0])
    new = update(at(30), big, open_scenario, cfg)
    assert new.trust > 75 and new.level == 1


def test_level_3_gate_needs_direct_ask(open_scenario, cfg):
    state = at(70, level=2)
    assert update(state, probs(L.VALIDATED), open_scenario, cfg).level == 2
    asked = update(state, probs(L.ASKED_DIRECTLY), open_scenario, cfg)
    assert asked.level == 3 and asked.flags.asked_directly_ever


def test_level_3_gate_remembers_earlier_ask(open_scenario, cfg):
    state = at(70, level=2, asked_directly_ever=True)
    assert update(state, probs(L.VALIDATED), open_scenario, cfg).level == 3


def test_level_4_gate_needs_recent_referral(open_scenario, cfg):
    state = at(80, level=3, turn=5, asked_directly_ever=True)
    assert update(state, probs(L.VALIDATED), open_scenario, cfg).level == 3
    referred = update(state, probs(L.REFERRED_988), open_scenario, cfg)
    assert referred.level == 4 and referred.status == "ended_success"
    assert referred.flags.referral_turns == [6]


@pytest.mark.parametrize(("ref_turn", "reaches_4"), [(4, True), (3, False)])
def test_referral_window(open_scenario, cfg, ref_turn, reaches_4):
    state = at(80, level=3, turn=5, asked_directly_ever=True, referral_turns=[ref_turn])
    new = update(state, probs(L.VALIDATED), open_scenario, cfg)  # this is turn 6
    assert (new.level == 4) is reaches_4


def test_hysteresis_holds_level_near_threshold(open_scenario, cfg):
    # Level 2 starts at 45; the friend only steps down below 45 - 15 = 30.
    assert update(at(33, level=2), probs(), open_scenario, cfg).level == 2  # 31
    assert update(at(31, level=2), probs(), open_scenario, cfg).level == 1  # 29


def test_level_drops_at_most_one_per_turn(open_scenario, cfg):
    state = at(62, level=3, asked_directly_ever=True)
    assert update(state, probs(L.DISMISSED, L.ADVICE_DUMP), open_scenario, cfg).level == 2


def test_secrecy_promise_then_referral(open_scenario, cfg):
    promised = update(at(50, level=2), probs(L.PROMISED_SECRECY), open_scenario, cfg)
    assert promised.flags.promised_secrecy and promised.last_delta == -17
    referred = update(promised, probs(L.REFERRED_ADULT), open_scenario, cfg)
    assert referred.last_delta == 8 - 2 - 10
    assert referred.flags.referral_turns == [referred.turn]  # it still counts
    assert not referred.flags.promised_secrecy
    assert secrecy_broken(promised, referred)


def test_promise_and_referral_same_message_is_not_broken(open_scenario, cfg):
    new = update(at(50), probs(L.PROMISED_SECRECY, L.REFERRED_ADULT), open_scenario, cfg)
    assert new.last_delta == -15 + 8 - 2
    assert new.flags.promised_secrecy and not secrecy_broken(at(50), new)


def test_doing_right_after_secrecy_can_still_succeed(open_scenario, cfg):
    state = at(80, level=3, asked_directly_ever=True, promised_secrecy=True)
    new = update(state, probs(L.REFERRED_ADULT, L.VALIDATED, L.FOLLOW_UP), open_scenario, cfg)
    assert new.status == "ended_success"


def test_secrecy_promise_is_answered_not_silent(open_scenario, cfg):
    new = update(at(40, level=1), probs(L.PROMISED_SECRECY), open_scenario, cfg)
    assert new.last_delta == -17 and new.status == "active"
    both = update(at(40, level=1), probs(L.PROMISED_SECRECY, L.DISMISSED), open_scenario, cfg)
    assert both.status == "silent"


def test_big_drop_goes_silent(open_scenario, cfg):
    assert update(at(60, level=2), probs(L.DISMISSED), open_scenario, cfg).status == "silent"


def test_decay_alone_never_goes_silent(open_scenario, scenario, cfg):
    # Real case: trust 22, "you've seemed really down lately. what's been going on?" with no labels.
    for persona in (open_scenario, scenario):
        new = update(at(22), probs(), persona, cfg)
        assert new.last_delta == -2 and new.trust == 20 and new.status == "active"
    assert update(at(12), probs(), open_scenario, cfg).status == "active"  # 10, still answered


def test_low_trust_and_negative_label_goes_silent(open_scenario, cfg):
    assert update(at(25), probs(L.ADVICE_DUMP), open_scenario, cfg).status == "silent"  # 13
    assert update(at(25), probs(L.ADVICE_DUMP), open_scenario, cfg).last_delta == -12
    assert update(at(40), probs(L.ADVICE_DUMP), open_scenario, cfg).status == "active"  # 28


def test_neutral_low_trust_gets_guarded_neutral_reply(engine, scenario):
    from .conftest import Convo

    convo = Convo(engine, scenario)
    convo.path[-1].state_after = at(22, turn=2)
    friend = convo.say("you've seemed really down lately. what's been going on?", probs())
    assert not friend.seen_no_reply and friend.bubbles
    assert friend.reaction.value in ("neutral", "off_topic")


def test_validation_recovers_from_silence(open_scenario, cfg):
    silent = update(at(25), probs(L.ADVICE_DUMP), open_scenario, cfg)
    assert silent.status == "silent"
    assert update(silent, probs(L.VALIDATED), open_scenario, cfg).status == "active"


def test_fail_after_two_low_turns(open_scenario, cfg):
    once = update(at(14), probs(L.ADVICE_DUMP), open_scenario, cfg)  # 2
    assert once.trust < 10 and once.status != "ended_fail"
    twice = update(once, probs(), open_scenario, cfg)
    assert twice.status == "ended_fail"


def test_max_turns_ends_in_fail(open_scenario, cfg):
    state = at(50, level=2, turn=cfg.max_turns - 1)
    assert update(state, probs(L.VALIDATED), open_scenario, cfg).status == "ended_fail"


def test_success_wins_on_last_turn(open_scenario, cfg):
    state = at(80, level=3, turn=cfg.max_turns - 1, asked_directly_ever=True)
    assert update(state, probs(L.REFERRED_988), open_scenario, cfg).status == "ended_success"


def test_ended_conversation_never_changes(open_scenario, cfg):
    done = at(80, level=4).model_copy(update={"status": "ended_success"})
    assert update(done, probs(L.DISMISSED), open_scenario, cfg) == done


def test_update_does_not_mutate_input(open_scenario, cfg):
    state = at(50, level=2)
    before = state.model_dump()
    update(state, probs(L.ASKED_DIRECTLY, L.REFERRED_ADULT), open_scenario, cfg)
    assert state.model_dump() == before


# ---------------------------------------------------------------- seeded property tests


def random_run(seed: int, scenario, cfg, turns: int = 30) -> list[State]:
    rng = random.Random(seed)
    state, prev = initial_state(scenario, cfg), frozenset()
    states = [state]
    for _ in range(turns):
        events = {label: round(rng.random(), 3) for label in L}
        state = update(state, events, scenario, cfg, prev)
        prev = active_labels(events)
        states.append(state)
    return states


@pytest.mark.parametrize("seed", range(40))
def test_property_bounds_and_steps(seed, scenario, cfg):
    states = random_run(seed, scenario, cfg)
    for before, after in zip(states, states[1:], strict=False):
        assert 0 <= after.trust <= 100
        assert 0 <= after.level <= 4
        assert abs(after.level - before.level) <= 1
        if before.status not in ("ended_success", "ended_fail"):
            assert after.turn == before.turn + 1
        if after.level >= 3:
            assert after.flags.asked_directly_ever
        if after.status == "ended_success":
            assert after.flags.referral_turns
        if after.turn != before.turn:
            assert round(sum(after.last_breakdown.values()), 4) == after.last_delta


@pytest.mark.parametrize("seed", range(10))
def test_property_deterministic(seed, scenario, cfg):
    assert random_run(seed, scenario, cfg) == random_run(seed, scenario, cfg)


@pytest.mark.parametrize("seed", range(10))
def test_property_ended_is_absorbing(seed, scenario, cfg):
    states = random_run(seed, scenario, cfg, turns=40)
    ended = [i for i, s in enumerate(states) if s.status.startswith("ended")]
    assert ended, "every run must end by max_turns"
    assert all(s == states[ended[0]] for s in states[ended[0] :])
    assert states[ended[0]].turn <= cfg.max_turns
