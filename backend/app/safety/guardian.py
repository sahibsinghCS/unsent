"""SAFETY lane entry point: the real Guardian. Set IMPLEMENTED = True once tests pass."""

from __future__ import annotations

from backend.app.contracts import GuardianResult, Node

IMPLEMENTED = False


class Guardian:
    def check_user(self, text: str, history: list[Node]) -> GuardianResult:
        raise NotImplementedError

    def check_friend(self, text: str) -> GuardianResult:
        raise NotImplementedError


def get_service() -> Guardian:
    return Guardian()
