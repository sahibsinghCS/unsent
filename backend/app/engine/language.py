"""Cheap, deterministic language check (ENGINE lane): is this friend reply English or Spanish?

A chat never mixes languages, so the verifier rejects LLM wording in the wrong language. No model and no
new dependency: we count very common function words (and Spanish-only characters) for each language.
Short or ambiguous texts ("ok", "😭") count as matching any language.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

# Frequent words that are (almost) never used in the other language. Words shared by both ("no", "me",
# "a") are left out on purpose.
EN_WORDS = frozenset(
    "the and is you i to it that of in my just so but im i'm dont don't what like lol be not have "
    "know this with its it's are was for do on about really feel yeah idk honestly kinda gonna "
    "wanna sorry thanks thank why they would could should been can't cant didnt didn't whatever "
    "youre you're weird forget gotta bye helps go um nvm talk later see okay right".split()
)
ES_WORDS = frozenset(
    "que de la el y es en lo por un una con para pero mi te se como qué estoy eso esto ya jaja jajaja "
    "pues muy sé nada porque ando tú yo bien también mucho algo cuando todo más hay está estás "
    "gracias perdón neta oye sí siento creo quiero tengo puedo eres soy las los del al sin adiós "
    "luego hablamos solo unas malas vi ayuda olvídalo ni dime nos vemos onda vale".split()
)
ES_CHARS = re.compile(r"[áéíóúñ¿¡]")
TOKEN = re.compile(r"[a-záéíóúñü']+")


def language_scores(text: str) -> tuple[int, int]:
    """(English evidence, Spanish evidence) for a text."""
    tokens = TOKEN.findall(text.lower())
    en = sum(token in EN_WORDS for token in tokens)
    es = sum(token in ES_WORDS for token in tokens) + len(ES_CHARS.findall(text.lower()))
    return en, es


def detect(bubbles: Sequence[str]) -> str | None:
    """'en', 'es', or None on a tie (e.g. "ok", "...", an emoji: no signal words at all).

    The language with more signal words wins, so Spanglish ("jaja ok, sorry") stays Spanish.
    """
    en, es = language_scores(" ".join(bubbles))
    if en == es:
        return None
    return "en" if en > es else "es"


def wrong_language(bubbles: Sequence[str], locale: str) -> str | None:
    """The language the reply is clearly written in, if it isn't `locale` (else None).

    Only English and Spanish are told apart; other locales are not checked.
    """
    if locale not in ("en", "es"):
        return None
    found = detect(bubbles)
    return found if found is not None and found != locale else None
