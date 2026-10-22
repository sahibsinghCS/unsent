"""Stub critic: scores each helper message with whichever skill detector is active.

The ML lane replaces it with the calibrated two-model ensemble, verified rewrites and summaries.
"""

from __future__ import annotations

from backend.app import services
from backend.app.contracts import (
    CriticReport,
    MessageScore,
    Node,
    Session,
    SkillLabel,
    SkillProbs,
)
from backend.app.pipeline import friend_context


def rubric_summary(all_probs: list[SkillProbs]) -> dict[str, float]:
    """Map per-message label probabilities to the 7 rubric skills (see contracts.RUBRIC_SKILLS)."""

    def peak(label: SkillLabel) -> float:
        return max((p.get(label, 0.0) for p in all_probs), default=0.0)

    negative = max(peak(SkillLabel.DISMISSED), peak(SkillLabel.ADVICE_DUMP))
    return {
        "check_in": peak(SkillLabel.CHECKED_IN),
        "listen": peak(SkillLabel.VALIDATED) * (1.0 - negative),
        "ask_directly": peak(SkillLabel.ASKED_DIRECTLY),
        "no_secrecy": 1.0 - peak(SkillLabel.PROMISED_SECRECY),
        "persuade": peak(SkillLabel.ENCOURAGED_HELP),
        "refer": max(peak(SkillLabel.REFERRED_ADULT), peak(SkillLabel.REFERRED_988)),
        "follow_up": peak(SkillLabel.FOLLOW_UP),
    }


class StubCritic:
    def score_conversation(self, session: Session, path: list[Node]) -> CriticReport:
        detector = services.skills()
        scores: list[MessageScore] = []
        for index, node in enumerate(path):
            if node.role != "user" or not node.bubbles:
                continue
            context = friend_context(path[:index])
            probs = node.events or detector.predict(node.bubbles[0], context)
            scores.append(
                MessageScore(
                    node_id=node.id,
                    probs=probs,
                    highlights=detector.explain(node.bubbles[0], context),
                )
            )
        summary = rubric_summary([s.probs for s in scores])
        missed = [
            f"You never got to '{skill.replace('_', ' ')}'."
            for skill, value in summary.items()
            if value < 0.5
        ]
        return CriticReport(
            per_message=scores,
            skill_summary=summary,
            turning_point=services.engine().turning_point(path),
            missed_opportunities=missed,
            summary_text="Stub feedback: the trained critic will replace this summary.",
        )


def get_service() -> StubCritic:
    return StubCritic()
