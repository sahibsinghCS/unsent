"""Stub engine: a simplified trust/level machine and fallback lines.

The ENGINE lane replaces it with the full deterministic state machine (gates, hysteresis, secrecy,
endings) and the line-bank actor.
"""

from __future__ import annotations

from backend.app.content import load_lines
from backend.app.contracts import (
    ActorOutput,
    Node,
    Reaction,
    Scenario,
    SkillLabel,
    SkillProbs,
    State,
    TurningPoint,
    VerifierResult,
)

WEIGHTS: dict[SkillLabel, float] = {
    SkillLabel.CHECKED_IN: 8,
    SkillLabel.VALIDATED: 12,
    SkillLabel.ASKED_DIRECTLY: 15,
    SkillLabel.ENCOURAGED_HELP: 6,
    SkillLabel.REFERRED_ADULT: 8,
    SkillLabel.REFERRED_988: 6,
    SkillLabel.FOLLOW_UP: 5,
    SkillLabel.DISMISSED: -20,
    SkillLabel.ADVICE_DUMP: -10,
    SkillLabel.PROMISED_SECRECY: -15,
}
THRESHOLDS = [0, 25, 45, 60, 75]
REACTION_PRIORITY: list[tuple[SkillLabel, Reaction]] = [
    (SkillLabel.DISMISSED, Reaction.DISMISSED),
    (SkillLabel.PROMISED_SECRECY, Reaction.PROMISED_SECRECY),
    (SkillLabel.ASKED_DIRECTLY, Reaction.ASKED_DIRECTLY),
    (SkillLabel.REFERRED_ADULT, Reaction.REFERRED),
    (SkillLabel.REFERRED_988, Reaction.REFERRED),
    (SkillLabel.VALIDATED, Reaction.VALIDATED),
    (SkillLabel.ADVICE_DUMP, Reaction.ADVICE_DUMP),
    (SkillLabel.CHECKED_IN, Reaction.CHECKED_IN),
    (SkillLabel.ENCOURAGED_HELP, Reaction.ENCOURAGED_HELP),
    (SkillLabel.FOLLOW_UP, Reaction.FOLLOW_UP),
]


def active(events: SkillProbs) -> set[SkillLabel]:
    return {label for label, p in events.items() if p >= 0.5}


class StubEngine:
    def initial_state(self, scenario: Scenario) -> State:
        return State(trust=30.0)

    def update(self, state: State, events: SkillProbs, scenario: Scenario) -> State:
        on = active(events)
        delta = sum(WEIGHTS[label] for label in on) - 2
        trust = max(0.0, min(100.0, state.trust + delta))
        flags = state.flags.model_copy(deep=True)
        flags.asked_directly_ever |= SkillLabel.ASKED_DIRECTLY in on
        flags.promised_secrecy |= SkillLabel.PROMISED_SECRECY in on
        turn = state.turn + 1
        if on & {SkillLabel.REFERRED_ADULT, SkillLabel.REFERRED_988}:
            flags.referral_turns.append(turn)
        level = state.level
        if level < 4 and trust >= THRESHOLDS[level + 1]:
            gated = (level + 1 == 3 and not flags.asked_directly_ever) or (
                level + 1 == 4 and not flags.referral_turns
            )
            if not gated:
                level += 1
        status = "silent" if delta <= -15 else "active"
        if trust < 10 and state.trust < 10:  # two low-trust turns in a row
            status = "ended_fail"
        elif level == 4 and flags.referral_turns:
            status = "ended_success"
        return State(
            trust=trust, level=level, turn=turn, flags=flags, status=status, last_delta=delta
        )

    def generate(
        self,
        scenario: Scenario,
        state: State,
        history: list[Node],
        user_text: str,
        events: SkillProbs,
        locale: str,
    ) -> ActorOutput:
        on = active(events)
        reaction = Reaction.NEUTRAL
        for label, candidate in REACTION_PRIORITY:
            if label in on:
                reaction = candidate
                break
        if state.status == "ended_success":
            reaction = Reaction.SUCCESS
        elif state.status == "ended_fail":
            reaction = Reaction.FAIL
        used = {node.line_id for node in history if node.line_id}
        bank = [
            line
            for line in load_lines(scenario.id, locale)
            if line.level == state.level and line.reaction == reaction and line.id not in used
        ]
        if bank:
            line = bank[0]
            return ActorOutput(
                bubbles=line.bubbles,
                line_id=line.id,
                reaction=reaction,
                fact_ids=line.fact_ids,
                source="bank",
            )
        fallback = scenario.fallback_lines.get(state.level) or ["..."]
        return ActorOutput(
            bubbles=[fallback[state.turn % len(fallback)]], reaction=reaction, source="fallback"
        )

    def verify(self, output: ActorOutput, scenario: Scenario, state: State) -> VerifierResult:
        return VerifierResult(ok=True)

    def turning_point(self, path: list[Node]) -> TurningPoint | None:
        worst: TurningPoint | None = None
        for node in path:
            if node.role != "user":
                continue
            drop = node.state_after.last_delta
            if drop < 0 and (worst is None or drop < -worst.trust_drop):
                worst = TurningPoint(
                    node_id=node.id,
                    trust_drop=-drop,
                    reason="Trust dropped the most after this message.",
                )
        return worst


def get_service() -> StubEngine:
    return StubEngine()
