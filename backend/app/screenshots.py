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
    # names, numbers, handles, addresses or schools were found in the draft and removed
    removed_identifying: bool = False


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
    draft, removed = _screened_draft(read)
    return AnalyzeResponse(
        draft=draft, signs=signs, urgency=level, imminent=imminent, removed_identifying=removed
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
        or _classifier_hears_self_risk(read.friend_lines)
    )
    imminent = read.mentions_plan_or_means or risk.imminent
    if urgent or imminent:
        return "tell_an_adult_now", imminent, signs
    return ("check_in_soon" if signs or risk.urgency == "check_in_soon" else "none"), False, signs


def _classifier_hears_self_risk(lines: list[str]) -> bool:
    """A second opinion from the Guardian's trained classifier: the friend speaks in the first person,
    so its "self_risk" call fits their lines (it catches slang the word lists miss). Only self_risk
    counts; a pasted "ignore your rules" is the helper's kind of problem, not a sign about the friend."""
    guardian = services.guardian()
    for line in lines[:12]:
        if not line.strip():
            continue
        result = guardian.check_user(line, [])
        if result.action == "pause_roleplay" and "self_risk" in result.categories:
            return True
    return False


# Identifying details the AI was told to leave out; removed again here in case it didn't.
_PII = [
    re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),  # email
    re.compile(r"https?://\S+|www\.\S+"),  # link
    re.compile(r"(?<![\w@])@\s?[A-Za-z0-9_.]{2,}"),  # social handle (also "@ jess_m")
    re.compile(r"\+?\d[\d\s().-]{5,}\d"),  # phone number
    re.compile(
        r"\b\d{1,5}\s+(?:[A-Z][a-z]+\s){0,3}"
        r"(?:St|Street|Ave|Avenue|Rd|Road|Dr|Drive|Ln|Lane|Blvd|Ct|Way)\b\.?"
    ),
    re.compile(r"\b(?:calle|avenida|av\.)\s+[\wáéíóúñ]+(?:\s+\d+)?", re.IGNORECASE),
    re.compile(r"\b(?:[A-Z][a-z]+\s){1,3}(?:High|Middle|Elementary|Academy|School|College)\b"),
    re.compile(
        r"\b(?i:(?:her|his|their|my)\s+name\s+is|named|called|se\s+llama|llamad[oa])\s+"
        r"[A-ZÁÉÍÓÚÑ][\wáéíóúñ'-]+(?:\s+[A-ZÁÉÍÓÚÑ][\wáéíóúñ'-]+)?"
    ),
]


_SPACED = re.compile(r"(?<!\w)(?:\w ){2,}\w(?!\w)")


def strip_identifying(text: str) -> tuple[str, bool]:
    """Remove emails, links, handles, phone numbers, street addresses, school names and "her name is
    X" phrases. Returns (text, whether anything was removed)."""
    # Letter-spaced words ("J e s s i c a") are joined first so a disguised name is still a name.
    text = _SPACED.sub(lambda m: m.group(0).replace(" ", ""), text)
    found = False
    for pattern in _PII:
        text, n = pattern.subn("", text)
        found = found or n > 0
    text = re.sub(r"\s+([,.!?])", r"\1", re.sub(r"\s{2,}", " ", text)).strip(" ,;:-")
    return text, found


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


def _screened_draft(read: ScreenshotRead) -> tuple[FriendDraft, bool]:
    """The same rules as a hand-written friend: anything the Guardian refuses is left blank for the
    helper to write, so a screenshot can never smuggle instructions or harmful details into a friend."""
    guardian = services.guardian()
    screen = getattr(guardian, "screen_profile", None) or (
        lambda text: guardian.check_user(text, [])
    )

    removed = False

    def refused(original: str, redacted: str) -> bool:
        # Screen the text as the AI wrote it AND after redaction: tidying the spacing can break up
        # a disguised spelling ("p a i n f u l ?") that the Guardian would otherwise put back together.
        return any(screen(t).action == "block_message" for t in {original, redacted} if t)

    def keep(text: str, field: str) -> str:
        nonlocal removed
        original = clean(text)
        redacted, identifying = strip_identifying(original)
        removed = removed or identifying
        redacted = redacted[: LIMITS[field][1]]
        return "" if not redacted or refused(original, redacted) else redacted

    samples = []
    for text in read.sample_texts[: MAX_SAMPLES * 2]:
        original = clean(text)
        text, identifying = strip_identifying(original)
        text = text[: LIMITS["sample"][1]]
        if identifying:
            removed = True
            continue  # a sample that named someone is dropped, not patched
        if refused(original, text):
            continue
        if text and all(guardian.check_friend(t).level == "none" for t in {original, text}):
            samples.append(text)
    draft = FriendDraft(
        personality=keep(read.style, "personality"),
        situation=keep(read.situation, "situation"),
        sample_texts=samples[:MAX_SAMPLES],
        guardedness=read.guardedness,
    )
    return draft, removed
