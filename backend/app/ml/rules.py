"""A rule taken straight from the label definition, applied on top of the trained models.

docs/LABEL_GUIDE.md: `asked_directly` needs an EXPLICIT mention of suicide, killing oneself, ending one's
life, not wanting to be alive / be here, or self-harm. A model trained on our data can learn shortcuts
("thinking about" appears in most direct asks), so "have you tried just not thinking about him" scored
0.98. If none of the explicit terms is present, the probability is capped at 0.2: the ML decides how
likely it is, the rule makes sure it is never a direct ask without the words a direct ask needs.
Matching runs on the safety lane's normalizer output (lowercase, accents folded, slang/leetspeak fixed).
"""

from __future__ import annotations

import re

from backend.app.safety.normalizer import normalize

ASKED_DIRECTLY_CAP = 0.2

_SELF = r"(?:your ?self|yourselves|themselves|themself|urself)"
EXPLICIT_TERMS = [
    # English
    r"\bsuicid\w*",
    rf"\bkill(?:ing|ed)? {_SELF}",
    r"\bkms\b",
    r"\bunalive\w*",
    r"\b(?:end|ending|ended|take|taking|took) (?:your|ur|their) (?:own )?li(?:fe|ves)\b",
    r"\bend(?:ing)? it all\b",
    r"\b(?:want|wanna|wanting|wish|wished) (?:to )?(?:be )?(?:die|dead)\b",
    r"\bbetter off dead\b",
    r"\b(?:die|dying)\b",
    r"\bstay(?:ing)? alive\b",
    r"\b(?:done|over|finished)\b[^.?!]{0,30}\bwith (?:life|living|it all)\b",
    r"\b(?:not|dont|no longer|never|stop) (?:\w+ ){0,3}(?:(?:be|being) (?:alive|here|around)|live|living|"
    r"exist|existing|wake up|waking up)\b",
    r"\bself ?-?harm\w*",
    rf"\b(?:hurt|hurting|harm|harming|cut|cutting) {_SELF}",
    # Spanish (accents folded by the normalizer)
    r"\bmatar(?:te|se|me)\b",
    r"\bquitar(?:te|se) la vida\b",
    r"\b(?:acabar|terminar) con (?:tu|su) vida\b",
    r"\bhacer(?:te|se) dano\b",
    r"\blastimar(?:te|se)\b",
    r"\bcortar(?:te|se)\b",
    r"\bmorir(?:te|se)?\b",
    r"\b(?:te|se) (?:\w+ ){0,2}(?:hacer dano|lastimar|matar|cortar|quitar la vida)\b",
    r"\bno (?:\w+ ){0,2}(?:vivir|estar aqui|seguir viv\w+|existir)\b",
]
_EXPLICIT = re.compile("|".join(f"(?:{p})" for p in EXPLICIT_TERMS))


def has_explicit_term(text: str) -> bool:
    """True if the message contains a term the label guide requires for `asked_directly`."""
    return bool(_EXPLICIT.search(normalize(text).text))


# Hint phrases teens use instead of the explicit words ("ending it", "disappear"); quoted in the
# "almost asked" note. Matched on the normalizer's output.
HINT_PHRASES = re.compile(
    r"\b(?:end(?:ing)? it(?: all)?|disappear(?:ing)?(?: for good)?|not (?:be|being) (?:around|here)"
    r"|do something (?:stupid|dumb|bad)|give up on (?:everything|it all)|be gone"
    r"|acabar con todo|desaparecer|hacer(?:te)? algo|ya no estar)\b"
)


def almost_asked(text: str, pa: float, pb: float) -> bool:
    """Both models read a direct ask but the explicit-term rule capped it ("are you having thoughts of
    ending it?"). Probabilities stay capped; the critic only uses this to coach saying it plainly.

    Three conditions, because the coaching note must never be false: no explicit term (else it IS a
    direct ask), BOTH models read an ask (the stacked score alone fires on "are you thinking about
    quitting the team?": Model B 0.97, Model A 0.47), and a recognised hint phrase such as "ending it"
    (both models also fire on "are you thinking about moving back?"). An unknown euphemism stays silent.
    """
    return not has_explicit_term(text) and pa >= 0.5 and pb >= 0.5 and hint_phrase(text) is not None


def hint_phrase(text: str) -> str | None:
    """The euphemism the helper used, if we recognise one ("ending it")."""
    match = HINT_PHRASES.search(normalize(text).text)
    return match.group(0) if match else None


def gate_asked_directly(texts: list[str], probs: list[float]) -> list[float]:
    """Cap asked_directly at 0.2 for every message without an explicit term."""
    return [
        p if has_explicit_term(t) else min(p, ASKED_DIRECTLY_CAP)
        for t, p in zip(texts, probs, strict=True)
    ]
