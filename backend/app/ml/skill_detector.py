"""ML lane entry point for the skill detector. Set IMPLEMENTED = True once a trained artifact exists
and tests pass (services.py then stops using the keyword stub).
"""

from __future__ import annotations

from backend.app.contracts import Highlight, SkillProbs

IMPLEMENTED = False


class SkillDetector:
    def predict(self, text: str, context: list[str]) -> SkillProbs:
        raise NotImplementedError

    def explain(self, text: str, context: list[str]) -> list[Highlight]:
        raise NotImplementedError


def get_service() -> SkillDetector:
    return SkillDetector()
