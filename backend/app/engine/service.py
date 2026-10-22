"""ENGINE lane entry point. Composes state.py, actor.py, verifier.py and turning_point.py.

Set IMPLEMENTED = True once the lane's tests pass; services.py then uses this instead of the stub.
"""

from __future__ import annotations

from backend.app.contracts import (
    ActorOutput,
    Node,
    Scenario,
    SkillProbs,
    State,
    TurningPoint,
    VerifierResult,
)

IMPLEMENTED = False


class Engine:
    def initial_state(self, scenario: Scenario) -> State:
        raise NotImplementedError

    def update(self, state: State, events: SkillProbs, scenario: Scenario) -> State:
        raise NotImplementedError

    def generate(
        self,
        scenario: Scenario,
        state: State,
        history: list[Node],
        user_text: str,
        events: SkillProbs,
        locale: str,
    ) -> ActorOutput:
        raise NotImplementedError

    def verify(self, output: ActorOutput, scenario: Scenario, state: State) -> VerifierResult:
        raise NotImplementedError

    def turning_point(self, path: list[Node]) -> TurningPoint | None:
        raise NotImplementedError


def get_service() -> Engine:
    return Engine()
