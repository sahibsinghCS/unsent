"""'Add your own friend': turn what a helper writes about a friend into a practice scenario.

The helper writes the friend's name, age, personality, texting style, what happened and a few example
texts. Only those words change. The disclosure levels, the facts behind them (including the suicidal
thoughts at level 3), the safe fallback lines and the reviewed line bank all come from the fixed
template `data/scenarios/_custom.json`, so a custom friend can never be scripted to describe methods
or to say anything our bank and verifier don't already allow. Every field is checked by the Guardian
first, and the friend lives only in memory, expiring like a session.
"""

from __future__ import annotations

import re
import secrets
from typing import Literal

from pydantic import BaseModel, Field

from backend.app import services
from backend.app.content import CUSTOM_PREFIX, custom_template, purge_custom, register_custom
from backend.app.contracts import Persona, Scenario, ScenarioText
from backend.app.session import register_sweeper

register_sweeper(purge_custom)  # custom friends expire together with sessions

LIMITS = {"name": (1, 24), "personality": (0, 300), "situation": (10, 400), "sample": (1, 160)}
MAX_SAMPLES = 5
AGES = (13, 19)

# Words that suggest the story may be about a real friend at risk: the form then shows real help first.
_REAL_RISK = re.compile(
    r"suicid|kill (?:him|her|them|my)sel|want(?:s|ed)? to die|end (?:it all|(?:his|her|their) life)"
    r"|not (?:want(?:s|ed)? to )?be(?:ing)? (?:here|alive)|self[- ]?harm|cutting|hurt (?:him|her|them)sel"
    r"|matar(?:se|me)|quitarse la vida|quiere morir|no quiere (?:estar|vivir)|hacerse daño|cortarse",
    re.IGNORECASE,
)

MESSAGES = {
    "en": {
        "too_short": "Please write a bit more here.",
        "too_long": "That's too long. Please shorten it.",
        "invalid": "Please check this field.",
        "prompt_injection": "This looks like instructions to the app. Describe your friend instead.",
        "harm": "Leave out anything about how someone could hurt themselves, or that encourages harm.",
        "unsafe_sample": "Leave out texts about how someone could hurt themselves. Feelings are fine.",
    },
    "es": {
        "too_short": "Escribe un poco más aquí.",
        "too_long": "Es demasiado largo. Acórtalo, por favor.",
        "invalid": "Revisa este campo.",
        "prompt_injection": "Esto parece una instrucción para la app. Mejor describe a tu amigo.",
        "harm": "No incluyas cómo alguien podría hacerse daño ni nada que lo anime.",
        "unsafe_sample": "No incluyas mensajes sobre cómo alguien podría hacerse daño. Los sentimientos sí.",
    },
}


class FriendRequest(BaseModel):
    name: str
    age: int = 16
    guardedness: Literal["open", "guarded"] = "guarded"
    personality: str = ""
    situation: str
    sample_texts: list[str] = Field(default_factory=list)
    locale: Literal["en", "es"] = "en"


class FriendProblem(Exception):
    """A field the helper needs to fix (shown next to that field)."""

    def __init__(self, field: str, reason: str, message: str) -> None:
        super().__init__(message)
        self.detail = {"field": field, "reason": reason, "message": message}


def clean(text: str) -> str:
    """One line of plain text: no control characters or line breaks that could reshape the AI prompt."""
    text = "".join(ch if ch.isprintable() else " " for ch in text)
    text = text.replace("#", "")  # no markdown headings inside the prompt's sections
    return re.sub(r"\s+", " ", text).strip()


def create_friend(request: FriendRequest) -> tuple[Scenario, bool]:
    """Validate, screen and register a custom friend. Returns (scenario, show_real_help_first).
    Raises FriendProblem for anything the helper should change."""
    words = MESSAGES[request.locale]
    name = clean(request.name)
    personality = clean(request.personality)
    situation = clean(request.situation)
    samples = [clean(t) for t in request.sample_texts if clean(t)]

    _check_length("name", name, *LIMITS["name"], words)
    _check_length("personality", personality, *LIMITS["personality"], words)
    _check_length("situation", situation, *LIMITS["situation"], words)
    if len(samples) > MAX_SAMPLES:
        raise FriendProblem("sample_texts", "too_long", words["too_long"])
    for index, sample in enumerate(samples):
        _check_length(f"sample_texts.{index}", sample, *LIMITS["sample"], words)
    if not AGES[0] <= request.age <= AGES[1]:
        raise FriendProblem("age", "invalid", words["invalid"])

    real_help = _screen(name, personality, situation, samples, words)
    scenario = _build(request, name, personality, situation, samples)
    register_custom(scenario)
    return scenario, real_help


def _check_length(field: str, text: str, low: int, high: int, words: dict) -> None:
    if len(text) < low:
        raise FriendProblem(field, "too_short", words["too_short"])
    if len(text) > high:
        raise FriendProblem(field, "too_long", words["too_long"])


def _screen(name: str, personality: str, situation: str, samples: list[str], words: dict) -> bool:
    """The Guardian checks every field before anything reaches the AI. Returns whether to show real
    help first: the helper may be writing about a real friend at risk, or about themself."""
    guardian = services.guardian()
    real_help = False
    fields = [("name", name), ("personality", personality), ("situation", situation)]
    fields += [(f"sample_texts.{i}", text) for i, text in enumerate(samples)]
    for field, text in fields:
        if not text:
            continue
        result = guardian.check_user(text, [])
        if result.action == "block_message":
            injection = "prompt_injection" in result.categories
            raise FriendProblem(
                field, "blocked", words["prompt_injection" if injection else "harm"]
            )
        if field.startswith("sample_texts"):
            # The friend's own words: sadness is realistic, but never method details or encouragement.
            if guardian.check_friend(text).level != "none":
                raise FriendProblem(field, "blocked", words["unsafe_sample"])
        elif result.action == "pause_roleplay":
            real_help = True
    return real_help or any(_REAL_RISK.search(text) for _, text in fields)


def _build(
    request: FriendRequest, name: str, personality: str, situation: str, samples: list[str]
) -> Scenario:
    template = custom_template()
    style = personality or template.persona.style
    if samples:
        quoted = " | ".join(f'"{text}"' for text in samples)
        style += (
            f". Texts they have sent (match this voice; never repeat them word for word): {quoted}"
        )
    scenario = template.model_copy(
        deep=True,
        update={
            "id": f"{CUSTOM_PREFIX}{secrets.token_hex(8)}",
            "persona": Persona(
                name=name, age=request.age, style=style, guardedness=request.guardedness
            ),
            "situation": situation,
            "review_status": "draft",
            "i18n": {},
        },
    )
    if request.locale != "en":
        text = template.i18n[request.locale]
        scenario.i18n = {
            request.locale: ScenarioText(
                title=text.title,
                situation=situation,
                opening=text.opening,
                content_warning=text.content_warning,
            )
        }
    return scenario
