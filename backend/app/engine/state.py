"""Deterministic trust / disclosure-level state machine (ENGINE lane). See docs/how/engine.md.

Every function here is pure: the same state + events + config always gives the same new state.
Numbers (weights, thresholds) live in engine/config.yaml so they can be tuned without code changes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml

from backend.app.contracts import Flags, Scenario, SkillLabel, SkillProbs, State

CONFIG_PATH = Path(__file__).with_name("config.yaml")
REFERRAL_LABELS = frozenset({SkillLabel.REFERRED_ADULT, SkillLabel.REFERRED_988})
ENDED = ("ended_success", "ended_fail")


@dataclass(frozen=True)
class EngineConfig:
    """Tunable numbers for the state machine (mirrors config.yaml)."""

    weights: dict[SkillLabel, float]
    decay_per_turn: float = 2
    guarded_positive_multiplier: float = 0.7
    repeat_multiplier: float = 0.5
    initial_trust: float = 30
    level_up_thresholds: tuple[float, ...] = (0, 25, 45, 60, 75)
    hysteresis: float = 15
    silence_drop: float = 15
    silence_floor: float = 20
    fail_floor: float = 10
    fail_turns: int = 2
    secrecy_broken_penalty: float = 10
    referral_window: int = 3
    max_turns: int = 16
    event_threshold: float = 0.5
    off_topic_max_similarity: float = 0.2
    off_topic_min_words: int = 3
    exact_level_bonus: float = 0.05
    new_fact_bonus: float = 0.05
    extra: dict = field(default_factory=dict)


def load_config(path: Path = CONFIG_PATH) -> EngineConfig:
    """Read config.yaml into an EngineConfig (unknown keys are kept in `extra`)."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    weights = {SkillLabel(k): float(v) for k, v in raw.pop("weights").items()}
    known = set(EngineConfig.__dataclass_fields__) - {"weights", "extra"}
    kwargs = {k: raw.pop(k) for k in list(raw) if k in known}
    if "level_up_thresholds" in kwargs:
        kwargs["level_up_thresholds"] = tuple(kwargs["level_up_thresholds"])
    return EngineConfig(weights=weights, extra=raw, **kwargs)


@lru_cache(maxsize=1)
def default_config() -> EngineConfig:
    return load_config()


def active_labels(events: SkillProbs, threshold: float = 0.5) -> frozenset[SkillLabel]:
    """Labels whose probability is at least the event threshold."""
    return frozenset(SkillLabel(label) for label, p in events.items() if p >= threshold)


def initial_state(scenario: Scenario | None = None, cfg: EngineConfig | None = None) -> State:
    """Starting state: initial trust, level 0, nothing flagged."""
    cfg = cfg or default_config()
    return State(trust=float(cfg.initial_trust), level=0, turn=0)


def trust_delta(
    active: frozenset[SkillLabel],
    prev_active: frozenset[SkillLabel],
    guarded: bool,
    cfg: EngineConfig,
) -> float:
    """Sum of active label weights minus decay.

    Positive labels are scaled down for guarded personas, and a positive label that was also active on
    the previous turn counts half (diminishing returns: repeating "that sounds hard" can't farm trust).
    Negative labels always count fully.
    """
    delta = -float(cfg.decay_per_turn)
    for label in sorted(active):
        weight = cfg.weights.get(label, 0.0)
        if weight > 0:
            if guarded:
                weight *= cfg.guarded_positive_multiplier
            if label in prev_active:
                weight *= cfg.repeat_multiplier
        delta += weight
    return round(delta, 4)


def next_level(level: int, trust: float, flags: Flags, turn: int, cfg: EngineConfig) -> int:
    """Move at most one level per turn.

    Up: trust reaches the next threshold AND the gate is open
      - level 3 (disclosing suicidal thoughts) needs the helper to have asked directly at least once;
      - level 4 (open to help) needs a referral (adult or 988) within the last `referral_window` turns.
    Down (hysteresis): only if trust falls below threshold(current) - hysteresis, so the friend doesn't
    flicker between levels when trust wobbles around a threshold.
    """
    thresholds = cfg.level_up_thresholds
    if level < 4 and trust >= thresholds[level + 1] and gate_open(level + 1, flags, turn, cfg):
        return level + 1
    if level > 0 and trust < thresholds[level] - cfg.hysteresis:
        return level - 1
    return level


def gate_open(target: int, flags: Flags, turn: int, cfg: EngineConfig) -> bool:
    """Whether the friend may move up to `target` given what the helper has done."""
    if target == 3:
        return flags.asked_directly_ever
    if target == 4:
        return recent_referral(flags, turn, cfg)
    return True


def recent_referral(flags: Flags, turn: int, cfg: EngineConfig) -> bool:
    """A referral happened in this turn or the previous `referral_window - 1` turns."""
    return any(turn - t < cfg.referral_window for t in flags.referral_turns)


def update(
    state: State,
    events: SkillProbs,
    scenario: Scenario,
    cfg: EngineConfig | None = None,
    prev_active: frozenset[SkillLabel] = frozenset(),
) -> State:
    """Apply one helper message (its detected label probabilities) to the friend's state.

    `prev_active` is the set of labels active on the previous helper message (for diminishing returns).
    An ended conversation never changes.
    """
    cfg = cfg or default_config()
    if state.status in ENDED:
        return state.model_copy(deep=True)

    active = active_labels(events, cfg.event_threshold)
    turn = state.turn + 1
    guarded = scenario.persona.guardedness == "guarded"
    delta = trust_delta(active, prev_active, guarded, cfg)

    flags = state.flags.model_copy(deep=True)
    flags.asked_directly_ever |= SkillLabel.ASKED_DIRECTLY in active
    broke_secret = False
    if active & REFERRAL_LABELS:
        flags.referral_turns.append(turn)
        if state.flags.promised_secrecy:
            broke_secret = True
            # Referring after promising secrecy is still the right call: it counts, but it stings.
            delta -= cfg.secrecy_broken_penalty
            flags.promised_secrecy = False
    if SkillLabel.PROMISED_SECRECY in active:
        flags.promised_secrecy = True

    trust = min(100.0, max(0.0, state.trust + delta))
    level = next_level(state.level, trust, flags, turn, cfg)
    status = _status(state, trust, delta, level, turn, cfg, broke_secret)
    return State(
        trust=round(trust, 4),
        level=level,
        turn=turn,
        flags=flags,
        status=status,
        last_delta=round(delta, 4),
    )


def _status(
    prev: State,
    trust: float,
    delta: float,
    level: int,
    turn: int,
    cfg: EngineConfig,
    broke_secret: bool = False,
):
    """Priority: success > fail (trust < fail_floor on 2 turns in a row, or out of turns) > silent > active.

    The turn a secret is broken is never silent: the friend reacts ("you promised..."), because that
    moment teaches more than being left on Seen.
    """
    if level == 4:
        return "ended_success"
    if trust < cfg.fail_floor and prev.trust < cfg.fail_floor:
        return "ended_fail"
    if turn >= cfg.max_turns:
        return "ended_fail"
    if broke_secret:
        return "active"
    if delta <= -cfg.silence_drop or (trust < cfg.silence_floor and delta <= 0):
        return "silent"
    return "active"


def secrecy_broken(before: State, after: State) -> bool:
    """True on the turn the helper referred after promising secrecy (the flag was cleared)."""
    return before.flags.promised_secrecy and not after.flags.promised_secrecy
