"""ML lane entry point for the end-of-conversation critic. Set IMPLEMENTED = True once tests pass."""

from __future__ import annotations

from backend.app.contracts import CriticReport, Node, Session

IMPLEMENTED = False


class Critic:
    def score_conversation(self, session: Session, path: list[Node]) -> CriticReport:
        raise NotImplementedError


def get_service() -> Critic:
    return Critic()
