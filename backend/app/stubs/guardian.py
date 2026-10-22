"""Stub Guardian: a few regexes. The SAFETY lane replaces this with the real layered Guardian.

Speaker-aware on purpose: the helper asking "are you thinking about killing yourself?" is GOOD and
must not be flagged; only first-person risk ("i want to kill myself") pauses the role-play.
"""

from __future__ import annotations

import re
import time

from backend.app.contracts import GuardianResult, Node

SELF_RISK = [
    r"\bi\s*(?:want|wanna)\s+(?:to\s+)?(?:die|kill myself|end it)\b",
    r"\bkms\b",
    r"\bi(?:'m| am)\s+(?:going|gonna)\s+(?:to\s+)?kill myself\b",
    r"\bi\s+(?:don'?t|do not)\s+want\s+to\s+(?:live|be alive)\b",
    r"\bend my life\b",
    r"\bunalive myself\b",
]
HARM_TO_OTHER = [
    r"\bkys\b",
    r"^\s*(?:just\s+|go\s+)?kill yourself\b",
    r"\byou should (?:just )?(?:die|kill yourself)\b",
    r"\bjust do it\b",
]
METHOD_SEEKING = [
    r"\bhow (?:would|will|are) you (?:do|go through with) it\b",
    r"\bwhat would you use\b",
]
INJECTION = [
    r"ignore (?:all |your )?(?:previous )?instructions",
    r"\byou are now\b",
    r"system prompt",
]
UNSAFE_FRIEND = [r"\bpills?\b", r"\boverdose\b", r"\bgun\b", r"\brope\b", r"\bjust do it\b"]


def _first_match(patterns: list[str], text: str) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return None


class StubGuardian:
    def check_user(self, text: str, history: list[Node]) -> GuardianResult:
        start = time.perf_counter()
        lowered = text.lower()
        checks = [
            ("self_risk", SELF_RISK, "crisis", "pause_roleplay"),
            ("harm_to_other", HARM_TO_OTHER, "none", "block_message"),
            ("method_seeking", METHOD_SEEKING, "none", "block_message"),
            ("prompt_injection", INJECTION, "none", "block_message"),
        ]
        for category, patterns, level, action in checks:
            hit = _first_match(patterns, lowered)
            if hit:
                return GuardianResult(
                    level=level,
                    action=action,
                    categories=[category],
                    evidence=[hit],
                    score=0.99,
                    sources=["lexicon"],
                    latency_ms=(time.perf_counter() - start) * 1000,
                )
        return GuardianResult(
            level="none", action="continue", latency_ms=(time.perf_counter() - start) * 1000
        )

    def check_friend(self, text: str) -> GuardianResult:
        hit = _first_match(UNSAFE_FRIEND, text.lower())
        if hit:
            return GuardianResult(
                level="concern",
                action="block_message",
                categories=["unsafe_friend_line"],
                evidence=[hit],
                score=0.99,
                sources=["lexicon"],
            )
        return GuardianResult(level="none", action="continue")


def get_service() -> StubGuardian:
    return StubGuardian()
