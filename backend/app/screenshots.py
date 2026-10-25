"""Read screenshots of a real conversation with a friend and draft a practice version of that friend.

The helper uploads 1-3 screenshots (names and numbers blacked out in the browser first). One AI call
reads them and returns a *draft*: how the friend texts, what seems to be going on, a few new example
texts and the warning signs it can see. Nothing is created automatically: the draft fills in the
"Add your own friend" form for the helper to review, and creating the friend then goes through the
same Guardian screening as a hand-written one.

Safety comes first: if the friend's own messages mention suicide, a plan, or goodbye-type warning
signs (our rules, not only the AI's), the answer says "tell an adult now" and the app shows real help
before any practice. Privacy: images and the friend's real messages are never stored, cached, logged
or returned; only the reviewed draft goes back to the browser.
"""

from __future__ import annotations

import base64
import binascii
import re
from pathlib import Path
from string import Template
from typing import Literal, get_args

from pydantic import BaseModel, Field

from backend.app import llm, services
from backend.app.custom_friend import LIMITS, MAX_SAMPLES, clean
from backend.app.safety.third_party import assess_friend_lines

PROMPT = Path(__file__).with_name("prompts") / "screenshot_reader.md"
PROMPT_NAME = "screenshot_reader"
MAX_IMAGES = 3
MAX_IMAGE_BYTES = 1_500_000  # per image, after decoding (the browser downsizes to about 1280 px)
_DATA_URL = re.compile(r"^data:image/(png|jpeg|webp);base64,([A-Za-z0-9+/=\s]+)$")
_MAGIC = {"png": b"\x89PNG", "jpeg": b"\xff\xd8\xff", "webp": b"RIFF"}

Sign = Literal[
    "talks_about_dying",
    "feels_hopeless",
    "feels_like_a_burden",
    "feels_trapped_or_in_pain",
    "withdrawing",
    "saying_goodbye",
    "giving_things_away",
    "sleep_changes",
    "mood_swings",
    "substance_use",
    "reckless_behavior",
    "sudden_calm",
]
SIGN_IDS = set(get_args(Sign))
URGENT_SIGNS = {"talks_about_dying", "saying_goodbye", "giving_things_away"}
Urgency = Literal["none", "check_in_soon", "tell_an_adult_now"]


class ScreenshotRead(BaseModel):
    """What the AI returns (friend_lines never leave the server)."""

    readable: bool = True
    friend_lines: list[str] = Field(default_factory=list)
    style: str = ""
    situation: str = ""
    sample_texts: list[str] = Field(default_factory=list)
    guardedness: Literal["open", "guarded"] = "guarded"
    signs: list[Sign] = Field(default_factory=list)
    mentions_suicide_or_self_harm: bool = False
    mentions_plan_or_means: bool = False


class AnalyzeRequest(BaseModel):
    images: list[str]
    locale: Literal["en", "es"] = "en"


class FriendDraft(BaseModel):
    personality: str = ""
    situation: str = ""
    sample_texts: list[str] = Field(default_factory=list)
    guardedness: Literal["open", "guarded"] = "guarded"


class AnalyzeResponse(BaseModel):
    draft: FriendDraft
    signs: list[Sign]
    urgency: Urgency
    # a plan, a means or a time next to a warning sign: "call your emergency number or 988 now"
    imminent: bool = False


class ScreenshotProblem(Exception):
    def __init__(self, status: int, reason: str, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.detail = {"reason": reason, "message": message}


TEXT = {
    "en": {
        "too_many": f"Add 1 to {MAX_IMAGES} screenshots.",
        "bad_image": "One of the files isn't a PNG, JPEG or WebP screenshot (or it's too big).",
        "unreadable": "We couldn't read a text conversation in these screenshots. Try clearer ones, or fill in the form yourself.",
        "needs_ai": "Reading screenshots needs the AI, which isn't available right now. You can fill in the form yourself.",
    },
    "es": {
        "too_many": f"Agrega de 1 a {MAX_IMAGES} capturas.",
        "bad_image": "Uno de los archivos no es una captura PNG, JPEG o WebP (o es demasiado grande).",
        "unreadable": "No pudimos leer una conversación en estas capturas. Prueba con otras más claras o llena el formulario tú.",
        "needs_ai": "Leer capturas necesita la IA, que no está disponible ahora. Puedes llenar el formulario tú.",
    },
}


def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    """Validate the images, read them with one AI call, and return a screened draft."""
    words = TEXT[request.locale]
    if not 1 <= len(request.images) <= MAX_IMAGES:
        raise ScreenshotProblem(422, "too_many", words["too_many"])
    images = [_checked(url, words) for url in request.images]
    try:
        read = llm.chat_json(
            PROMPT_NAME,
            _messages(images, request.locale),
            ScreenshotRead,
            role="vision",
            temperature=0.2,
            max_tokens=900,
            use_cache=False,  # nothing from a real conversation is kept, not even in memory
        )
    except llm.LLMUnavailable as exc:
        raise ScreenshotProblem(503, "needs_ai", words["needs_ai"]) from exc
    if not read.readable:
        raise ScreenshotProblem(422, "unreadable", words["unreadable"])
    level, imminent, signs = assess(read)
    return AnalyzeResponse(
        draft=_screened_draft(read), signs=signs, urgency=level, imminent=imminent
    )


def assess(read: ScreenshotRead) -> tuple[Urgency, bool, list[str]]:
    """(urgency, imminent, signs). Our own rules decide, on top of the AI's flags: the friend's own
    words go through the safety lane's warning-sign rules (jokes count, venting doesn't), and real
    help comes first whenever they mention suicide, a plan or a goodbye-type sign."""
    risk = assess_friend_lines(read.friend_lines)
    signs = list(dict.fromkeys([*read.signs, *(s for s in risk.signs if s in SIGN_IDS)]))
    urgent = (
        read.mentions_suicide_or_self_harm
        or read.mentions_plan_or_means
        or risk.urgency == "tell_an_adult_now"
        or bool(URGENT_SIGNS & set(signs))
    )
    imminent = read.mentions_plan_or_means or risk.imminent
    if urgent or imminent:
        return "tell_an_adult_now", imminent, signs
    return ("check_in_soon" if signs or risk.urgency == "check_in_soon" else "none"), False, signs


def _checked(url: str, words: dict) -> tuple[str, str]:
    match = _DATA_URL.match(url.strip())
    if not match:
        raise ScreenshotProblem(422, "bad_image", words["bad_image"])
    kind, payload = match.groups()
    try:
        raw = base64.b64decode(payload, validate=False)
    except (binascii.Error, ValueError) as exc:
        raise ScreenshotProblem(422, "bad_image", words["bad_image"]) from exc
    if len(raw) > MAX_IMAGE_BYTES or not raw.startswith(_MAGIC[kind]):
        raise ScreenshotProblem(422, "bad_image", words["bad_image"])
    return kind, base64.b64encode(raw).decode("ascii")


def _messages(images: list[tuple[str, str]], locale: str) -> list[dict]:
    language = "Spanish" if locale == "es" else "English"
    system = Template(PROMPT.read_text(encoding="utf-8")).safe_substitute(language=language)
    parts: list[dict] = [{"type": "text", "text": "Screenshots of the conversation:"}]
    parts += [
        {"type": "image_url", "image_url": {"url": f"data:image/{kind};base64,{data}"}}
        for kind, data in images
    ]
    return [{"role": "system", "content": system}, {"role": "user", "content": parts}]


def _screened_draft(read: ScreenshotRead) -> FriendDraft:
    """The same rules as a hand-written friend: anything the Guardian refuses is left blank for the
    helper to write, so a screenshot can never smuggle instructions or harmful details into a friend."""
    guardian = services.guardian()
    screen = getattr(guardian, "screen_profile", None) or (
        lambda text: guardian.check_user(text, [])
    )

    def keep(text: str, field: str) -> str:
        text = clean(text)[: LIMITS[field][1]]
        return text if text and screen(text).action != "block_message" else ""

    samples = []
    for text in read.sample_texts[: MAX_SAMPLES * 2]:
        text = clean(text)[: LIMITS["sample"][1]]
        if (
            text
            and screen(text).action != "block_message"
            and guardian.check_friend(text).level == "none"
        ):
            samples.append(text)
    return FriendDraft(
        personality=keep(read.style, "personality"),
        situation=keep(read.situation, "situation"),
        sample_texts=samples[:MAX_SAMPLES],
        guardedness=read.guardedness,
    )
