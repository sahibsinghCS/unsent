"""Shared helpers for the what-if tests: real engine + Guardian, keyword detector (FR_EMBED=hash), no LLM."""

from __future__ import annotations

import pytest

from backend.app import services
from backend.app.content import get_scenario
from backend.app.contracts import Node, Reaction, Session
from backend.app.pipeline import run_turn
from backend.app.session import create_session, path_to


@pytest.fixture(autouse=True)
def _no_llm(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("FR_LLM", "0")
    services.reset()


def new_session(scenario_id: str = "after-the-breakup", locale: str = "en") -> Session:
    scenario = get_scenario(scenario_id)
    opening = Node(
        id="root",
        parent_id=None,
        role="friend",
        bubbles=scenario.opening,
        state_after=services.engine().initial_state(scenario),
        reaction=Reaction.OPENING,
    )
    return create_session(scenario.id, locale, "US", opening)


def play(session: Session, texts: list[str]) -> list[Node]:
    """Send helper messages through the live pipeline; returns the root-to-head path."""
    for text in texts:
        run_turn(session, text)
    return path_to(session)


def user_ids(path: list[Node]) -> list[str]:
    return [n.id for n in path if n.role == "user"]


WEAK_CHAT = [
    "hey are you ok? you seemed off",
    "that sounds really hard, i'm sorry",
    "lol you'll be fine, just get over it",
    "ok",
]
