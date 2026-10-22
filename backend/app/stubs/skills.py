"""Stub skill detector: keyword matching. The ML lane replaces it with trained models.

Also used by the ML lane as the "keyword baseline" in its evaluation.
"""

from __future__ import annotations

from backend.app.contracts import Highlight, SkillLabel, SkillProbs

KEYWORDS: dict[SkillLabel, list[str]] = {
    SkillLabel.CHECKED_IN: [
        "are you ok",
        "are u ok",
        "you ok",
        "u ok",
        "you good",
        "how are you",
        "what's wrong",
        "whats wrong",
        "you seem",
        "you seemed",
    ],
    SkillLabel.VALIDATED: [
        "that sounds",
        "makes sense",
        "i hear you",
        "really hard",
        "i'm sorry",
        "im sorry",
        "that must",
        "glad you told me",
    ],
    SkillLabel.ASKED_DIRECTLY: [
        "kill yourself",
        "killing yourself",
        "suicide",
        "suicidal",
        "end your life",
        "hurt yourself",
        "not wanting to be alive",
        "want to die",
    ],
    SkillLabel.ENCOURAGED_HELP: [
        "talk to someone",
        "get help",
        "reach out",
        "don't have to deal with this alone",
        "dont have to deal with this alone",
    ],
    SkillLabel.REFERRED_ADULT: [
        "counselor",
        "counsellor",
        "teacher",
        "your mom",
        "your dad",
        "your parents",
        "trusted adult",
        "nurse",
    ],
    SkillLabel.REFERRED_988: ["988", "hotline", "crisis line", "lifeline"],
    SkillLabel.FOLLOW_UP: [
        "check on you",
        "text you tomorrow",
        "text you tonight",
        "i'll stay",
        "i'm here",
        "im here",
        "i'll go with you",
    ],
    SkillLabel.DISMISSED: [
        "you'll be fine",
        "youll be fine",
        "lol",
        "don't say that",
        "dont say that",
        "get over it",
        "drama",
        "not that bad",
    ],
    SkillLabel.ADVICE_DUMP: [
        "you should just",
        "just go",
        "just stop",
        "you need to",
        "have you tried",
    ],
    SkillLabel.PROMISED_SECRECY: [
        "won't tell",
        "wont tell",
        "our secret",
        "i won't tell anyone",
        "i promise i wont",
    ],
}

HIGH, LOW = 0.9, 0.05


class StubSkills:
    def predict(self, text: str, context: list[str]) -> SkillProbs:
        lowered = text.lower()
        return {
            label: (HIGH if any(k in lowered for k in words) else LOW)
            for label, words in KEYWORDS.items()
        }

    def explain(self, text: str, context: list[str]) -> list[Highlight]:
        lowered = text.lower()
        highlights: list[Highlight] = []
        for label, words in KEYWORDS.items():
            for word in words:
                start = lowered.find(word)
                if start >= 0:
                    end = start + len(word)
                    highlights.append(
                        Highlight(
                            start=start,
                            end=end,
                            text=text[start:end],
                            label=label,
                            delta=HIGH - LOW,
                        )
                    )
                    break
        return highlights


def get_service() -> StubSkills:
    return StubSkills()
