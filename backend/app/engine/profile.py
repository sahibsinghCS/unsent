"""Custom friends' helper-written profile (ENGINE lane): read it back out of the scenario, and detect a
reply that copies it.

"Add your own friend" (backend/app/custom_friend.py) puts the helper's personality text and example
texts into `persona.style`. Those words are untrusted: the voice prompt labels them as data, and the
verifier rejects an LLM reply that repeats 4+ words in a row from them (an obedient model echoing an
injected instruction). The situation is exempt: echoing "got cut from the team" is natural.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence

from backend.app.content import is_custom
from backend.app.contracts import Scenario

# How custom_friend._build appends the example texts to the personality.
SAMPLES_MARKER = ". Texts they have sent ("
COPY_NGRAM = 4
SITUATION_RUN = 6
SITUATION_SHARE = 0.6
_WORD = re.compile(r"[\w']+")
# Look-alike letters (Cyrillic/Greek) and leetspeak, mapped back to plain letters for matching only.
_LOOKALIKE = str.maketrans("аеорсхуіοαԁ0134578@$", "aeopcxyioadoieastbas")
_SENTENCE = re.compile(r"[.!?;|\n]+")


def strip_invisible(text: str) -> str:
    """NFKC, then delete invisible format characters (zero-width spaces, joiners, direction marks).
    Applied to every LLM reply before it is checked or shown; the words themselves stay as they are."""
    text = unicodedata.normalize("NFKC", text)
    return "".join(ch for ch in text if unicodedata.category(ch) != "Cf")


def canonical(text: str) -> str:
    """Text reduced to plain lowercase words for comparing: invisible characters removed, look-alike
    letters and leetspeak mapped back, stretched letters ("sooo") shortened, and spaced-out letters
    ("l e v e l") joined back into a word."""
    text = strip_invisible(text).lower().translate(_LOOKALIKE)
    text = re.sub(r"(\w)\1{2,}", r"\1", text)
    return re.sub(
        r"\b\w(?: \w){2,}\b", lambda m: m.group(0).replace(" ", ""), " ".join(text.split())
    )


def _words(text: str) -> list[str]:
    return _WORD.findall(canonical(text))


def profile_parts(scenario: Scenario) -> tuple[str, list[str]]:
    """(personality, example texts) written by the helper; ("", []) for built-in friends."""
    if not is_custom(scenario.id):
        return "", []
    style = scenario.persona.style
    personality, _, rest = style.partition(SAMPLES_MARKER)
    samples = re.findall(r'"([^"]*)"', rest.split("):", 1)[1]) if "):" in rest else []
    return personality.strip(), samples


def _ngrams(text: str, n: int = COPY_NGRAM) -> set[tuple[str, ...]]:
    words = _words(text)
    return {tuple(words[i : i + n]) for i in range(len(words) - n + 1)}


def _longest_run(a: list[str], b: list[str]) -> int:
    """Length of the longest run of consecutive words shared by two word lists."""
    best, prev = 0, [0] * (len(b) + 1)
    for x in a:
        cur = [0] * (len(b) + 1)
        for j, y in enumerate(b, start=1):
            if x == y:
                cur[j] = prev[j - 1] + 1
                best = max(best, cur[j])
        prev = cur
    return best


def _units(text: str) -> list[list[str]]:
    """Sentences (or example texts) of 3+ words, as canonical word lists."""
    return [w for part in _SENTENCE.split(text) if len(w := _words(part)) >= COPY_NGRAM - 1]


def copied_from_profile(bubbles: Sequence[str], scenario: Scenario) -> str | None:
    """Why a reply looks copied from the helper-written profile, or None. Compared after `canonical`
    (so zero-width characters, look-alike letters, leetspeak and spaced letters don't hide a copy):
    - a run of 4+ words from the personality or an example text (minus runs also in the situation);
    - a whole example text, or a whole sentence of the personality or situation, of 3+ words
      ("are you a real person?");
    - most of the situation replayed (a run of >= 6 words covering >= 60% of it).
    Mentioning what happened in your own words ("i got cut from the team") still passes."""
    if not is_custom(scenario.id):
        return None
    personality, samples = profile_parts(scenario)
    reply_words = _words(" ".join(bubbles))
    profile = set().union(*(_ngrams(text) for text in [personality, *samples]))
    profile -= _ngrams(scenario.situation)
    reply_grams = {tuple(reply_words[i : i + COPY_NGRAM]) for i in range(len(reply_words))}
    shared = sorted(reply_grams & profile)
    if shared:
        return " ".join(shared[0])
    for text in [personality, *samples, scenario.situation]:
        for unit in _units(text):
            if _longest_run(unit, reply_words) == len(unit):
                return " ".join(unit)
    situation = _words(scenario.situation)
    run = _longest_run(situation, reply_words)
    if run >= SITUATION_RUN and run >= SITUATION_SHARE * len(situation):
        return f"{run} words of the situation"
    return None
