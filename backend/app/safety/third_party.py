"""Warning signs in a REAL friend's own messages (SAFETY lane).

Used by "Practice for a real friend": the helper uploads screenshots and we decide how urgently
they should get real help before any practice. This is different from check_user, where the
person typing is the helper. Here the FRIEND is speaking, so "i want to die" means the friend:

  - talking about suicide or wanting to die (any first-person phrasing, slang or Spanish, even as a
    joke like "kms lol"), saying goodbye, or giving things away  -> tell_an_adult_now
  - those plus a plan, a means or a time ("tonight")             -> tell_an_adult_now + imminent
  - hopelessness, feeling like a burden, feeling trapped, withdrawing or sudden calm
                                                                  -> check_in_soon
  - everyday venting ("this test is killing me lol", "im dead 😭") -> none

Lexicon only, so every decision has a readable reason. Never raises (an error escalates).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

from backend.app.safety.lexicon import STRIP, _Phrases, drop_fillers, get_lexicon
from backend.app.safety.normalizer import normalize, squeeze

PATH = Path(__file__).with_name("third_party.yaml")
URGENT_SIGNS = ("talks_about_dying", "saying_goodbye", "giving_things_away")
AMBIGUOUS_PLANS = {
    squeeze(p)
    for p in ("i have a plan", "i made a plan", "i have it planned", "tonight is the night")
}
WATCH_SIGNS = (
    "feels_like_a_burden",
    "feels_hopeless",
    "feels_trapped_or_in_pain",
    "withdrawing",
    "sudden_calm",
)


class FriendLineRisk(BaseModel):
    """How urgently the helper should get real help, from the friend's own words."""

    urgency: Literal["none", "check_in_soon", "tell_an_adult_now"] = "none"
    imminent: bool = False  # a plan, a means or a time together with a risk sign
    signs: list[str] = Field(default_factory=list)  # sign ids, same names as screenshots.Sign
    evidence: list[str] = Field(default_factory=list)  # matched phrases (never shown to others)


@lru_cache(maxsize=1)
def _lists() -> dict[str, _Phrases]:
    data = yaml.safe_load(PATH.read_text(encoding="utf-8"))
    return {key: _Phrases(values or []) for key, values in data.items()}


def _find(key: str, raw: list[str]) -> list[str]:
    sq = [squeeze(w.strip(STRIP)) for w in raw]
    return [" ".join(raw[a:b]) for a, b in _lists()[key].find(sq)]


def assess_friend_lines(lines: list[str]) -> FriendLineRisk:
    """Warning signs in the friend's messages -> urgency. Never raises (errors escalate)."""
    try:
        return _assess([line for line in (lines or []) if line and line.strip()][:20])
    except Exception:  # noqa: BLE001 - fail safe: real help first
        return FriendLineRisk(
            urgency="tell_an_adult_now", evidence=["check failed: real help first"]
        )


def _assess(lines: list[str]) -> FriendLineRisk:
    lexicon = get_lexicon()
    signs: dict[str, None] = {}
    evidence: list[str] = []
    means = plan = timing = False
    for line in lines:
        norm = normalize(line)
        raw = drop_fillers(norm.text.split())
        # The friend's "i" is first person here, so the Guardian's self_risk rules = the friend at risk.
        for hit in lexicon.scan(norm).hits:
            if hit.category == "self_risk":
                signs["talks_about_dying"] = None
            elif hit.reason == "means + first person":
                means = True
            elif hit.category == "concern":
                signs.setdefault("feels_hopeless", None)
            else:
                continue
            evidence.append(hit.phrase)
        for hit in lexicon.scan_friend(norm).hits:
            if hit.reason == "method_seeking":  # a means word or a how/when question
                means = True
            elif hit.reason in ("unsafe_friend_line", "friend_method"):
                # "i know how i'd do it", a goodbye note: suicide-specific, as strong as a means.
                # "i have a plan" alone is ambiguous (a party?) and needs a warning sign next to it.
                if squeeze(hit.phrase.strip(STRIP)) in AMBIGUOUS_PLANS:
                    plan = True
                else:
                    means = True
            else:
                continue
            evidence.append(hit.phrase)
        for key in (*URGENT_SIGNS[1:], *WATCH_SIGNS):
            found = _find(key, raw)
            if found:
                signs[key] = None
                evidence += found
        found = _find("plan_or_timing", raw)
        if found:
            evidence += found
            plan = plan or any(len(f.split()) > 2 for f in found)  # "i have a plan", not "tonight"
            timing = True
    urgent = bool(signs.keys() & set(URGENT_SIGNS)) or means
    # A plan or a time only matters next to a warning sign ("i have a plan for the party" is fine).
    imminent = means or ((plan or timing) and bool(signs.keys() & set(URGENT_SIGNS)))
    urgency = "tell_an_adult_now" if urgent else "check_in_soon" if signs else "none"
    return FriendLineRisk(
        urgency=urgency,
        imminent=imminent,
        signs=list(signs),
        evidence=list(dict.fromkeys(evidence))[:8],
    )
