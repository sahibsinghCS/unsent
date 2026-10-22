"""Normalises teen text (slang, leetspeak, spacing, emoji) before safety checks (SAFETY lane).

People who want to slip past a filter write "k1ll mys3lf", "k.m.s" or "kiiiill myself". Teens also
just text that way. Every rule below turns one of those spellings back into plain words so the
lexicon and the classifier see the same thing. Each rule that fires adds a note, so the Guardian
can show *why* it read a message the way it did.

The output is for matching only. It is lowercase, apostrophe-free and expanded ("dont" -> "do not",
"u" -> "you", "wanna" -> "want to"), so lexicon phrases are written in that same canonical form.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

ZERO_WIDTH = re.compile("[​-‏⁠-⁤﻿­͏︀-️]")
QUOTES = str.maketrans({"‘": "'", "’": "'", "‚": "'", "′": "'", "`": "'",
                        "“": '"', "”": '"', "„": '"', "″": '"'})  # fmt: skip

# Emoji that carry meaning in this context become word tags the lexicon can match.
EMOJI_TAGS = {
    "\U0001faa6": "emoji_grave",  # headstone
    "⚰": "emoji_coffin",
    "\U0001f62d": "emoji_crying",
    "\U0001f622": "emoji_crying",
    "\U0001f494": "emoji_heartbreak",
    "\U0001f52a": "emoji_knife",
    "\U0001f52b": "emoji_gun",
    "\U0001f48a": "emoji_pill",
    "\U0001fa78": "emoji_blood",
    "\U0001f602": "emoji_laughing",
    "\U0001f923": "emoji_laughing",
    "\U0001f480": "emoji_skull",  # teens use it for "i'm dying laughing": AMBIGUOUS, never enough alone
    "☠": "emoji_skull",
}
AMBIGUOUS_TAGS = {"emoji_skull"}

LEET = str.maketrans(
    {"0": "o", "1": "i", "3": "e", "4": "a", "@": "a", "5": "s", "$": "s", "7": "t"}
)
LEET_CHARS = set("013457@$")

# Word-level rewrites: misspellings, texting shorthand and contractions -> one canonical spelling.
WORD_MAP = {
    # misspellings of the words that matter most
    "suicde": "suicide", "suiside": "suicide", "sucide": "suicide", "suicid": "suicide",
    "suicdie": "suicide", "sucidal": "suicidal", "suicdal": "suicidal", "suisidal": "suicidal",
    "myslef": "myself", "mysef": "myself", "myslf": "myself", "meself": "myself",
    "urself": "yourself", "yourslef": "yourself", "yourelf": "yourself", "urslf": "yourself",
    "kil": "kill", "unalve": "unalive", "anymor": "anymore", "anymroe": "anymore",
    # texting shorthand
    "u": "you", "yu": "you", "ur": "your", "r": "are", "ppl": "people",
    "rn": "right now", "wanna": "want to", "wana": "want to", "gonna": "going to",
    "gotta": "got to", "tryna": "trying to", "ima": "i am going to", "imma": "i am going to",
    "pls": "please", "plz": "please", "bc": "because", "cuz": "because", "cause": "because",
    "nobody": "no one", "noone": "no one", "everyones": "everyone is",
    # contractions (apostrophes are removed first)
    "im": "i am", "ive": "i have", "id": "i would", "ill": "i will",
    "youre": "you are", "youve": "you have", "youd": "you would", "youll": "you will",
    "dont": "do not", "doesnt": "does not", "didnt": "did not", "cant": "can not",
    "cannot": "can not", "wont": "will not", "wouldnt": "would not", "shouldnt": "should not",
    "isnt": "is not", "arent": "are not", "wasnt": "was not", "aint": "am not",
    "havent": "have not", "hasnt": "has not", "whats": "what is", "thats": "that is",
    "its": "it is", "theyd": "they would", "theyre": "they are", "lets": "let us",
    # Spanish texting shorthand
    "q": "que", "xq": "porque", "pq": "porque", "tmb": "tambien", "tb": "tambien",
}  # fmt: skip

# Collapsed spaced letters that are worth recovering even when short ("k m s").
SPACED_TARGETS = {"kms", "kys", "die", "kill", "dead", "unalive", "suicide"}
SEPARATED_RUN = re.compile(r"(?<![\w])((?:[a-z0-9@$][.\-_*/|]){2,}[a-z0-9@$])(?![\w])")


@dataclass
class Normalized:
    """Result of normalize(): canonical text for matching plus notes on what changed."""

    text: str
    notes: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)  # emoji tags found, e.g. "emoji_grave"
    ambiguous: list[str] = field(default_factory=list)  # tags that never decide anything alone

    def __iter__(self):  # allows: text, notes = normalize(raw)
        return iter((self.text, self.notes))


def fold_accents(text: str) -> str:
    """Remove accents ("está" -> "esta", "mátate" -> "matate") so Spanish matches either spelling."""
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def _emoji_to_tags(text: str, out: Normalized) -> str:
    for emoji, tag in EMOJI_TAGS.items():
        if emoji in text:
            text = text.replace(emoji, f" {tag} ")
            if tag not in out.tags:
                out.tags.append(tag)
            if tag in AMBIGUOUS_TAGS and tag not in out.ambiguous:
                out.ambiguous.append(tag)
    if out.tags:
        out.notes.append("emoji->tags: " + ", ".join(out.tags))
    return text


def _deleet_token(token: str) -> str:
    if any(c.isalpha() for c in token) and any(c in LEET_CHARS for c in token):
        return token.translate(LEET)
    return token


def _collapse_separated(text: str, out: Normalized) -> str:
    """'k.m.s', 'k-m-s', 'k*m*s' -> 'kms'; also 'k m s' when the result is a known risk word."""

    def join(match: re.Match[str]) -> str:
        letters = re.sub(r"[.\-_*/|]", "", match.group(1))
        return letters.translate(LEET) if sum(c.isalpha() for c in letters) >= 2 else match.group(1)

    new = SEPARATED_RUN.sub(join, text)
    tokens, result, i = new.split(" "), [], 0
    while i < len(tokens):
        j = i
        while j < len(tokens) and len(tokens[j]) == 1 and tokens[j] not in "?!.,":
            j += 1
        run = "".join(tokens[i:j]).translate(LEET)
        if j - i >= 3 and (j - i >= 4 or run in SPACED_TARGETS):
            result.append(run)
            i = j
        else:
            result.append(tokens[i])
            i += 1
    new = " ".join(result)
    if new != text:
        out.notes.append("joined spaced/dotted letters")
    return new


def normalize(text: str) -> Normalized:
    """Turn raw teen text into canonical lowercase words for matching. Never raises."""
    out = Normalized(text="")
    if not text:
        return out
    t = unicodedata.normalize("NFKC", text)
    stripped = ZERO_WIDTH.sub("", t)
    if stripped != t:
        out.notes.append("removed zero-width characters")
    t = stripped.translate(QUOTES)
    t = _emoji_to_tags(t, out)
    t = t.lower()
    folded = fold_accents(t)
    if folded != t:
        out.notes.append("folded accents")
    t = folded.replace("'", "")
    t = re.sub(r"\s+", " ", t).strip()
    t = _collapse_separated(t, out)

    tokens = []
    for raw in t.split(" "):
        lead = re.match(r"^[^\w@$]*", raw).group(0)
        trail = re.search(r"[^\w@$]*$", raw).group(0)
        core = raw[len(lead) : len(raw) - len(trail)] if trail else raw[len(lead) :]
        tokens.append((lead, core, trail))

    deleeted = [(lead, _deleet_token(core), trail) for lead, core, trail in tokens]
    if deleeted != tokens:
        out.notes.append("leetspeak -> letters")

    squeezed = [(lead, re.sub(r"([a-z])\1{2,}", r"\1\1", core), tr) for lead, core, tr in deleeted]
    if squeezed != deleeted:
        out.notes.append("shortened stretched letters")

    words, mapped = [], False
    for lead, core, trail in squeezed:
        canon = WORD_MAP.get(core)
        if canon is None and re.fullmatch(r"[a-z]*([a-z])\1[a-z]*", core or "-"):
            canon = WORD_MAP.get(re.sub(r"([a-z])\1", r"\1", core))  # "suiciidde" -> "suicide"
        if canon is not None:
            mapped = True
            core = canon
        words.append(f"{lead}{core}{trail}")
    if mapped:
        out.notes.append("expanded slang/misspellings")

    t = " ".join(words)
    t = re.sub(r"([?!.,;¿¡])", r" \1 ", t)  # punctuation as its own token
    out.text = re.sub(r"\s+", " ", t).strip()
    return out


def squeeze(text: str) -> str:
    """Collapse every doubled letter ("kiill" -> "kil"). Used to match stretched words both ways."""
    return re.sub(r"([a-z])\1+", r"\1", text)
