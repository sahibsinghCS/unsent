"""Optional extra signal: OpenAI's free moderation endpoint (SAFETY lane).

The local Guardian decides. Moderation can only:
  - SUPPORT a local flag (adds "moderation" to sources and its score to the evidence);
  - raise "none" to "concern" (show resources, keep practicing) when it is very sure about self-harm
    AND our lexicon found nothing allowed in the message.
It can never pause the role-play or block a message on its own, and it can never overrule the speaker
rules. Moderation reads "are you thinking about killing yourself?" as self-harm content; for FirstReply
that question is the skill we teach, so our "asking the friend" match wins and the score is only noted.
Offline (no key, FR_LLM=0, budget spent, API error) it returns None and the Guardian behaves identically.
"""

from __future__ import annotations

from backend.app.safety.lexicon import LexiconResult
from backend.app.safety.model import Decision

SELF_HARM_KEYS = ("self-harm", "self-harm/intent", "self-harm/instructions")
HARM_KEYS = ("harassment", "harassment/threatening", "violence")
SUPPORT = 0.50  # score that counts as agreeing with a local flag
UPGRADE = 0.80  # self-harm score that may raise "none" to "concern"


def fetch(text: str) -> dict[str, float] | None:
    """Moderation scores, or None when unavailable. Never raises."""
    try:
        from backend.app import llm

        return llm.moderate(text)
    except Exception:  # noqa: BLE001 - LLMUnavailable or anything else: just no extra signal
        return None


def _max(scores: dict[str, float], keys: tuple[str, ...]) -> tuple[float, str]:
    best = max(keys, key=lambda k: scores.get(k, 0.0))
    return scores.get(best, 0.0), best


def combine(d: Decision, lex: LexiconResult | None, scores: dict[str, float] | None) -> Decision:
    """Fold moderation into a local decision (see module docstring for the rules)."""
    if not scores:
        return d
    sh, sh_key = _max(scores, SELF_HARM_KEYS)
    hm, hm_key = _max(scores, HARM_KEYS)

    if d.categories:
        agrees = (d.level in ("crisis", "concern") and sh >= SUPPORT) or (
            d.action == "block_message" and (hm >= SUPPORT or sh >= SUPPORT)
        )
        if agrees:
            key, value = (sh_key, sh) if sh >= hm else (hm_key, hm)
            d.sources.append("moderation")
            d.evidence.append(f"moderation {key}={value:.2f} agrees")
        return d

    allowed = lex is not None and bool(lex.allowed) and not lex.hits
    if allowed:
        if max(sh, hm) >= SUPPORT:
            reason = lex.allowed[0].reason
            key, value = (sh_key, sh) if sh >= hm else (hm_key, hm)
            d.evidence.append(f"moderation {key}={value:.2f} overruled by speaker rules ({reason})")
        return d

    if sh >= UPGRADE:
        d.level, d.action = "concern", "show_resources"
        d.categories = ["concern"]
        d.sources = ["moderation"]
        d.evidence = [f"moderation {sh_key}={sh:.2f} (no local rule matched)"]
        d.score = sh
    return d
