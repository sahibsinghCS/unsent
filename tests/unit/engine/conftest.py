"""Shared fixtures for the engine tests: a frozen copy of one scenario and a small line bank."""

from __future__ import annotations

from pathlib import Path

import pytest

from backend.app.content import read_jsonl
from backend.app.contracts import Line, Node, Scenario, SkillLabel, SkillProbs, State
from backend.app.engine.service import Engine
from backend.app.engine.state import default_config

FIXTURES = Path(__file__).with_name("fixtures")


def probs(*labels: SkillLabel, high: float = 0.9, low: float = 0.05) -> SkillProbs:
    """Detector output with the given labels on and everything else off."""
    return {label: (high if label in labels else low) for label in SkillLabel}


@pytest.fixture
def cfg():
    return default_config()


@pytest.fixture
def scenario() -> Scenario:
    path = FIXTURES / "scenario.after-the-breakup.json"
    return Scenario.model_validate_json(path.read_text(encoding="utf-8"))


@pytest.fixture
def open_scenario(scenario: Scenario) -> Scenario:
    persona = scenario.persona.model_copy(update={"guardedness": "open"})
    return scenario.model_copy(update={"persona": persona})


@pytest.fixture
def bank() -> tuple[Line, ...]:
    rows = read_jsonl(FIXTURES / "after-the-breakup.en.jsonl")
    return tuple(Line.model_validate(row) for row in rows)


@pytest.fixture
def engine() -> Engine:
    return Engine(bank_dir=FIXTURES)


class Convo:
    """Plays helper messages through an Engine and keeps the node path like the pipeline does."""

    def __init__(self, engine: Engine, scenario: Scenario, locale: str = "en") -> None:
        self.engine, self.scenario, self.locale = engine, scenario, locale
        state = engine.initial_state(scenario)
        self.path: list[Node] = [
            Node(
                id="root",
                parent_id=None,
                role="friend",
                bubbles=scenario.opening,
                state_after=state,
            )
        ]

    @property
    def state(self) -> State:
        return self.path[-1].state_after

    def say(self, text: str, events: SkillProbs) -> Node:
        new = self.engine.update(self.state, events, self.scenario)
        n = len(self.path)
        user = Node(
            id=f"u{n}",
            parent_id=self.path[-1].id,
            role="user",
            bubbles=[text],
            events=events,
            state_after=new,
        )
        self.path.append(user)
        if new.status == "silent":
            friend = Node(
                id=f"f{n}",
                parent_id=user.id,
                role="friend",
                bubbles=[],
                state_after=new,
                seen_no_reply=True,
            )
        else:
            out = self.engine.generate(self.scenario, new, self.path, text, events, self.locale)
            friend = Node(
                id=f"f{n}",
                parent_id=user.id,
                role="friend",
                bubbles=out.bubbles,
                state_after=new,
                line_id=out.line_id,
                reaction=out.reaction,
            )
        self.path.append(friend)
        return friend


@pytest.fixture
def convo(engine: Engine, scenario: Scenario) -> Convo:
    return Convo(engine, scenario)
