"""ENGINE lane entry point. Composes state.py, actor.py, verifier.py and turning_point.py.

Set IMPLEMENTED = True once the lane's tests pass; services.py then uses this instead of the stub.
"""

from __future__ import annotations

import threading
import weakref
from collections.abc import Sequence
from pathlib import Path

from backend.app.contracts import (
    ActorOutput,
    Line,
    Node,
    Scenario,
    SkillLabel,
    SkillProbs,
    State,
    TurningPoint,
    VerifierResult,
)
from backend.app.engine import actor, verifier
from backend.app.engine import state as engine_state
from backend.app.engine import turning_point as tp
from backend.app.engine.state import EngineConfig, default_config

IMPLEMENTED = True


class Engine:
    """The friend: deterministic state machine + line-bank actor + verifier + turning points."""

    def __init__(self, cfg: EngineConfig | None = None, bank_dir: Path | None = None) -> None:
        self.cfg = cfg or default_config()
        self.bank_dir = bank_dir
        # Labels active on the message that produced each State, keyed by the State object itself.
        # The frozen contract's State has no field for this, and diminishing returns needs it; the
        # pipeline always feeds back the exact State object update() returned, so this is exact.
        self._labels: dict[int, tuple[weakref.ref, frozenset[SkillLabel]]] = {}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ state
    def initial_state(self, scenario: Scenario) -> State:
        return engine_state.initial_state(scenario, self.cfg)

    def update(
        self,
        state: State,
        events: SkillProbs,
        scenario: Scenario,
        prev_active: frozenset[SkillLabel] | None = None,
    ) -> State:
        """One helper message -> the friend's new state. `prev_active` overrides the remembered
        labels of the previous message (for callers that replay a path themselves)."""
        if prev_active is None:
            prev_active = self._previous_labels(state)
        new = engine_state.update(state, events, scenario, self.cfg, prev_active)
        self._remember(new, engine_state.active_labels(events, self.cfg.event_threshold))
        return new

    def _previous_labels(self, state: State) -> frozenset[SkillLabel]:
        with self._lock:
            entry = self._labels.get(id(state))
        if entry is None or entry[0]() is not state:
            return frozenset()
        return entry[1]

    def _remember(self, state: State, labels: frozenset[SkillLabel]) -> None:
        key = id(state)

        def forget(_ref: weakref.ref, key: int = key) -> None:
            with self._lock:
                if key in self._labels and self._labels[key][0]() is None:
                    del self._labels[key]

        with self._lock:
            self._labels[key] = (weakref.ref(state, forget), labels)

    # ------------------------------------------------------------------ voice
    def bank(self, scenario_id: str, locale: str = "en") -> tuple[Line, ...]:
        return actor.load_bank(scenario_id, locale, self.bank_dir)

    def generate(
        self,
        scenario: Scenario,
        state: State,
        history: list[Node],
        user_text: str,
        events: SkillProbs,
        locale: str,
    ) -> ActorOutput:
        """The best-ranked reply that passes the verifier (scenario fallback lines as a last resort)."""
        bank = self.bank(scenario.id, locale)
        ranked = actor.ranked_candidates(
            scenario, state, history, user_text, events, locale, bank, self.cfg
        )
        for candidate in ranked:
            output = actor.to_output(candidate)
            if verifier.verify(output, scenario, state, bank).ok:
                return output
        return actor.to_output(ranked[-1])

    def verify(
        self,
        output: ActorOutput,
        scenario: Scenario,
        state: State,
        bank: Sequence[Line] | None = None,
    ) -> VerifierResult:
        if bank is None:
            bank = self.bank(scenario.id)
        return verifier.verify(output, scenario, state, bank)

    # ------------------------------------------------------------------ feedback
    def turning_point(self, path: list[Node]) -> TurningPoint | None:
        return tp.turning_point(path)

    def missed_opportunities(self, path: list[Node], friend_name: str = "your friend") -> list[str]:
        return tp.missed_opportunities(path, friend_name)


def get_service() -> Engine:
    return Engine()
