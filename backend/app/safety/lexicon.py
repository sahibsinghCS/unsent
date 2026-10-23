"""Speaker-aware phrase matching over lexicon.yaml (SAFETY lane).

The lexicon says WHAT to look for; this module decides WHO it is about. "i want to die" is the
helper at risk; "do you want to die?" is the helper asking the friend directly, which is the
skill we teach and must never be flagged.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml

from backend.app.safety.normalizer import Normalized, normalize, squeeze

LEXICON_PATH = Path(__file__).with_name("lexicon.yaml")
BOUNDARIES = {".", "!", "?", ";", "¿", "¡"}
STRIP = "\"'()[]*:~"
WEAK_FIRST = {"me", "my", "mi"}  # count only right before the phrase ("makes me want to die")
# Commands that need a cue word ("just kms", "go end it"); alone they mean something else.
CUE_ONLY = {("end", "it"), ("disappear",), ("desaparece",)}
RISK_CATEGORIES = ("self_risk", "concern", "harm_to_other", "method_seeking", "prompt_injection")


@dataclass
class Hit:
    """One phrase that matched, and why it counted (or why it was allowed)."""

    category: str
    phrase: str  # the matched words from the normalized message
    reason: str  # e.g. "first person", "command", "asking the friend", "reflection"


@dataclass
class LexiconResult:
    hits: list[Hit] = field(default_factory=list)  # risky matches
    allowed: list[Hit] = field(default_factory=list)  # asking_friend / tricky_negative / reflection

    @property
    def categories(self) -> list[str]:
        return list(dict.fromkeys(h.category for h in self.hits))

    def has(self, category: str) -> bool:
        return any(h.category == category for h in self.hits)


@dataclass
class _Sentence:
    start: int
    end: int  # exclusive
    question: bool


class _Phrases:
    """Phrases normalised and indexed by their first (squeezed) word for fast lookup.

    A phrase may start with "^" (must start its sentence) or end with "$" (must end its sentence):
    "^does it hurt$" is a method question on its own, but not inside "does it hurt when you see him".
    """

    def __init__(self, phrases: list[str]) -> None:
        self.by_first: dict[str, list[tuple[tuple[str, ...], bool, bool]]] = {}
        for phrase in phrases or []:
            raw = str(phrase).strip()
            start, end = raw.startswith("^"), raw.endswith("$")
            raw = raw.strip("^$")
            words = tuple(squeeze(w.strip(STRIP)) for w in normalize(raw).text.split())
            if words:
                self.by_first.setdefault(words[0], []).append((words, start, end))
        for bucket in self.by_first.values():
            bucket.sort(key=lambda item: len(item[0]), reverse=True)

    def find(self, sq: list[str]) -> list[tuple[int, int]]:
        """All (start, end) word spans that match a phrase, longest first at each position."""
        spans = []
        for i, word in enumerate(sq):
            for phrase, start, end in self.by_first.get(word, ()):
                j = i + len(phrase)
                if (start and i != 0) or (end and j != len(sq)):
                    continue
                if tuple(sq[i:j]) == phrase:
                    spans.append((i, j))
                    break
        return spans


class Lexicon:
    """Loads lexicon.yaml once and scans normalized messages with the speaker rules."""

    def __init__(self, path: Path = LEXICON_PATH) -> None:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        self.raw = data
        sec = {k: v or {} for k, v in data.items()}
        self.p = {
            f"{cat}.{kind}": _Phrases(sec.get(cat, {}).get(kind, []))
            for cat in (
                *RISK_CATEGORIES,
                "asking_friend",
                "tricky_negative",
                "dismissive",
                "unsafe_friend_line",
            )
            for kind in (
                "explicit",
                "framed",
                "framed_second",
                "imperative",
                "means",
                "topics",
                "do_it",
                "help_words",
            )
        }
        sp = sec["speaker"]
        self.first = {squeeze(w) for w in sp["first_person"]}
        self.second = {squeeze(w) for w in sp["second_person"]}
        self.third = {squeeze(w) for w in sp["third_person"]}
        self.second_verbs = set(sec["asking_friend"].get("second_person_verbs", []))
        self.negators = set(sp["negators"])
        self.breakers = set(sp["negation_breakers"])
        self.cues = set(sec["harm_to_other"].get("imperative_cues", []))
        self.reflection = _Phrases(sp["reflection_markers"])
        self.agreement = {normalize(a).text for a in sp["agreement"]}
        self.substrings = [
            normalize(x).text for x in sec["prompt_injection"].get("substrings", []) if x
        ]

    # ------------------------------------------------------------------ speaker rules
    def _speaker(self, sq: list[str], sent: _Sentence, i: int) -> str | None:
        """Nearest pronoun before word i in the same sentence: first / second / third / None."""
        for j in range(i - 1, sent.start - 1, -1):
            w = sq[j]
            if w in WEAK_FIRST and j < i - 1:
                continue  # "my friend told ME about ..." is not the helper's own feeling
            if w in self.first:
                return "first"
            if w in self.second or w in self.second_verbs:
                return "second"
            if w in self.third:
                return "third"
        return None

    def _negated(self, sq: list[str], sent: _Sentence, i: int) -> bool:
        for j in range(max(sent.start, i - 3), i):
            if "," in sq[j:i]:
                continue  # negation does not cross a comma ("i do not care, kill yourself")
            if sq[max(0, j - 2) : j + 2] == ["why", "do", "not", "you"]:
                continue  # "why don't you just ..." is a rhetorical command, not a negation
            if sq[j] in self.negators and not any(w in self.breakers for w in sq[j + 1 : i]):
                return True
        return False

    def _reflected(self, raw: list[str], sq: list[str], sent: _Sentence, i: int) -> bool:
        """True if the helper is repeating the friend's words back ("you said ...")."""
        markers = self.reflection.find(sq[sent.start : i])
        if not markers:
            return False
        end = sent.start + markers[-1][1]
        between = range(end, i)
        if any(raw[j].startswith('"') for j in between):
            return True  # quoting the friend
        return not any(sq[j] in {"i", "yo"} for j in between)

    @staticmethod
    def _sentences(raw: list[str]) -> list[_Sentence]:
        out, start = [], 0
        for i, tok in enumerate(raw + ["."]):
            if tok in BOUNDARIES or i == len(raw):
                if i > start:
                    question = tok == "?" or (i + 1 < len(raw) and raw[i + 1] == "?")
                    out.append(_Sentence(start, i, question))
                start = i + 1
        return out

    # ------------------------------------------------------------------ scanning
    def scan(self, norm: Normalized | str) -> LexiconResult:
        """Scan a HELPER message: risk hits plus allowed (asking / tricky / reflection) matches."""
        norm = normalize(norm) if isinstance(norm, str) else norm
        raw = norm.text.split()
        sq = [squeeze(w.strip(STRIP)) for w in raw]
        res = LexiconResult()
        helping = bool(self.p["harm_to_other.help_words"].find(sq))
        for sent in self._sentences(raw):
            words = sq[sent.start : sent.end]
            self._scan_sentence(raw, sq, words, sent, res)
            for a, b in self._spans("harm_to_other.do_it", words, sent):
                if helping:  # "just do it, text the counselor" is encouragement to get help
                    res.allowed.append(Hit("helping", " ".join(raw[a:b]), "points to help"))
                elif not self._negated(sq, sent, a) and not self._reflected(raw, sq, sent, a):
                    res.hits.append(Hit("harm_to_other", " ".join(raw[a:b]), "urges the friend on"))
        for marker in self.substrings:
            if marker in norm.text:
                res.hits.append(Hit("prompt_injection", marker, "code / control string"))
        return res

    def _spans(self, key: str, words: list[str], sent: _Sentence):
        for a, b in self.p[key].find(words):
            yield sent.start + a, sent.start + b

    def _scan_sentence(self, raw, sq, words, sent: _Sentence, res: LexiconResult) -> None:
        text = lambda a, b: " ".join(raw[a:b]).strip(STRIP)  # noqa: E731

        method = list(self._spans("method_seeking.explicit", words, sent))
        in_method = lambda a, b: any(a < mb and ma < b for ma, mb in method)  # noqa: E731

        for cat in ("self_risk", "concern"):
            for a, b in self._spans(f"{cat}.explicit", words, sent):
                if in_method(a, b):
                    continue
                if self._negated(sq, sent, a):
                    res.allowed.append(Hit("negated", text(a, b), "negated"))
                    continue
                if a > sent.start and sq[a - 1] in {"go", "should"}:
                    continue  # "go kms" is aimed at the friend (harm), not the helper's own risk
                if self._reflected(raw, sq, sent, a):
                    res.allowed.append(Hit("asking_friend", text(a, b), "reflection"))
                elif sent.question and self._speaker(sq, sent, a) == "second":
                    res.allowed.append(Hit("asking_friend", text(a, b), "asking the friend"))
                else:
                    res.hits.append(Hit(cat, text(a, b), "first person"))
            for a, b in self._spans(f"{cat}.framed", words, sent):
                if in_method(a, b):
                    continue
                if self._negated(sq, sent, a):
                    res.allowed.append(Hit("negated", text(a, b), "negated"))
                    continue
                if self._reflected(raw, sq, sent, a):
                    res.allowed.append(Hit("asking_friend", text(a, b), "reflection"))
                    continue
                who = self._speaker(sq, sent, a)
                if b < sent.end and sq[b] in self.second:
                    continue  # "unalive yourself" is about the friend, handled as harm/asking
                if sq[b - 1] == "it" and b < sent.end and sq[b] == "with":
                    res.allowed.append(Hit("tricky_negative", text(a, b + 1), "breakup"))
                    continue  # "i'm ending it with him" is a breakup
                if (
                    who is None
                    and cat == "self_risk"
                    and any(w in self.second for w in sq[b : sent.end])
                ):  # "end it, you deserve peace" is aimed at the friend
                    res.hits.append(Hit("harm_to_other", text(a, b), "command"))
                    continue
                if who is None and cat == "self_risk" and a > sent.start:
                    if sq[a - 1] in {
                        "and",
                        "go",
                        "should",
                        "then",
                    }:  # "...a favor and disappear forever"
                        res.hits.append(Hit("harm_to_other", text(a, b), "command"))
                        continue
                if who == "first" or (who is None and not sent.question):
                    res.hits.append(Hit(cat, text(a, b), "first person"))
                elif who == "second" or (who is None and sent.question):
                    res.allowed.append(Hit("asking_friend", text(a, b), "asking the friend"))

        for a, b in self._spans("harm_to_other.explicit", words, sent):
            if self._speaker(sq, sent, a) == "first" and sq[a] not in self.first:
                continue  # "i wish i could just die" is the helper's own pain, scanned above
            if self._reflected(raw, sq, sent, a):
                res.allowed.append(Hit("asking_friend", text(a, b), "reflection"))
            elif self._negated(sq, sent, a):
                res.allowed.append(Hit("negated", text(a, b), "negated"))
            else:
                res.hits.append(Hit("harm_to_other", text(a, b), "aimed at the friend"))
        for a, b in self._spans("harm_to_other.imperative", words, sent):
            if self._negated(sq, sent, a) or self._reflected(raw, sq, sent, a):
                continue
            before = sq[max(sent.start, a - 2) : a]
            if sq[a:b] == ["end", "it"] and b < sent.end and sq[b] == "with":
                continue  # "just end it with him" is breakup advice
            clause_start = (a == sent.start or raw[a - 1] == ",") and tuple(sq[a:b]) not in CUE_ONLY
            if clause_start or any(w in self.cues for w in before):
                res.hits.append(Hit("harm_to_other", text(a, b), "command"))
        for a, b in self._spans("harm_to_other.framed", words, sent):
            if self._reflected(raw, sq, sent, a):
                res.allowed.append(Hit("asking_friend", text(a, b), "reflection"))
                continue
            if self._negated(sq, sent, a):
                continue
            if "i" in sq[b : b + 3]:  # "no one would care if i ..." is about the helper
                res.hits.append(Hit("concern", text(a, b), "first person"))
            elif self._speaker(sq, sent, a) != "first":
                res.hits.append(Hit("harm_to_other", text(a, b), "aimed at the friend"))
            else:
                res.hits.append(Hit("concern", text(a, b), "first person"))

        for a, b in self._spans("harm_to_other.framed_second", words, sent):
            if sent.question or self._negated(sq, sent, a) or self._reflected(raw, sq, sent, a):
                continue
            if self._speaker(sq, sent, a) == "second":
                res.hits.append(Hit("harm_to_other", text(a, b), "insult aimed at the friend"))

        for a, b in method:
            res.hits.append(Hit("method_seeking", text(a, b), "asks how/when/with what"))
        for a, b in self._spans("method_seeking.means", words, sent):
            if self._speaker(sq, sent, a) == "first" or "myself" in sq[a:b]:
                res.hits.append(Hit("concern", text(a, b), "means + first person"))
            else:
                res.hits.append(Hit("method_seeking", text(a, b), "names a means"))

        for a, b in self._spans("prompt_injection.explicit", words, sent):
            res.hits.append(Hit("prompt_injection", text(a, b), "tries to break the practice"))

        for a, b in self._spans("asking_friend.explicit", words, sent):
            res.allowed.append(Hit("asking_friend", text(a, b), "asking the friend"))
        for a, b in self._spans("asking_friend.topics", words, sent):
            topic = sq[a:b]
            if (
                any(w in self.second for w in topic)
                or self._speaker(sq, sent, a) == "second"
                or any(w in self.second_verbs for w in words)
                or any(w in {"suicidarte", "matarte", "quitarte", "morirte"} for w in topic)
            ):
                res.allowed.append(Hit("asking_friend", text(a, b), "asking the friend"))
        for a, b in self._spans("tricky_negative.explicit", words, sent):
            res.allowed.append(Hit("tricky_negative", text(a, b), "everyday expression"))
        for a, b in self._spans("dismissive.explicit", words, sent):
            res.allowed.append(
                Hit("dismissive", text(a, b), "brush-off: the friend reacts, not us")
            )

    def scan_friend(self, norm: Normalized | str) -> LexiconResult:
        """Scan a FRIEND line: plans, encouragement, graphic detail, means, persona breaks, harm."""
        norm = normalize(norm) if isinstance(norm, str) else norm
        raw = norm.text.split()
        sq = [squeeze(w.strip(STRIP)) for w in raw]
        res = LexiconResult()
        for sent in self._sentences(raw):
            words = sq[sent.start : sent.end]
            for key in (
                "unsafe_friend_line.explicit",
                "method_seeking.means",
                "method_seeking.explicit",
                "harm_to_other.explicit",
                "prompt_injection.explicit",
            ):
                for a, b in self._spans(key, words, sent):
                    if key == "harm_to_other.explicit" and self._negated(sq, sent, a):
                        continue
                    phrase = " ".join(raw[a:b]).strip(STRIP)
                    res.hits.append(Hit("unsafe_friend_line", phrase, key.split(".")[0]))
            sub = LexiconResult()
            for a, b in self._spans("harm_to_other.imperative", words, sent):
                before = sq[max(sent.start, a - 2) : a]
                if not self._negated(sq, sent, a) and any(w in self.cues for w in before):
                    sub.hits.append(Hit("unsafe_friend_line", " ".join(raw[a:b]), "harm_to_other"))
            res.hits.extend(sub.hits)
        return res

    def is_agreement(self, norm: Normalized) -> bool:
        """A short "me too" / "same" / "yo tambien" message."""
        text = " ".join(w for w in norm.text.split() if w not in BOUNDARIES and w != ",")
        if len(text.split()) > 8:
            return False
        return any(text == a or text.startswith(a + " ") for a in self.agreement)


@lru_cache(maxsize=1)
def get_lexicon() -> Lexicon:
    """Process-wide lexicon (parsed once)."""
    return Lexicon()
