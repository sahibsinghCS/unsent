"""Custom friends' helper-written profile (ENGINE lane): read it back out of the scenario, and detect a
reply that copies it.

"Add your own friend" (backend/app/custom_friend.py) puts the helper's personality text and example
texts into `persona.style`. Those words are untrusted: the voice prompt labels them as data, and the
verifier rejects an LLM reply that repeats 4+ words in a row from them (an obedient model echoing an
injected instruction). The situation is exempt: echoing "got cut from the team" is natural.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from backend.app.content import is_custom
from backend.app.contracts import Scenario

# How custom_friend._build appends the example texts to the personality.
SAMPLES_MARKER = ". Texts they have sent ("
COPY_NGRAM = 4
SITUATION_RUN = 6
SITUATION_SHARE = 0.6
_WORD = re.compile(r"[\w']+")


def profile_parts(scenario: Scenario) -> tuple[str, list[str]]:
    """(personality, example texts) written by the helper; ("", []) for built-in friends."""
    if not is_custom(scenario.id):
        return "", []
    style = scenario.persona.style
    personality, _, rest = style.partition(SAMPLES_MARKER)
    samples = re.findall(r'"([^"]*)"', rest.split("):", 1)[1]) if "):" in rest else []
    return personality.strip(), samples


def _ngrams(text: str, n: int = COPY_NGRAM) -> set[tuple[str, ...]]:
    words = _WORD.findall(text.lower())
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


def copied_from_profile(bubbles: Sequence[str], scenario: Scenario) -> str | None:
    """Why a reply looks copied from the helper-written profile, or None:
    - a run of 4+ words from the personality or an example text (minus runs also in the situation),
      or a whole 3-word example text;
    - most of the situation replayed (a run of >= 6 words covering >= 60% of it): mentioning what
      happened ("got cut from the team") is natural, reciting the student's sentence is not."""
    if not is_custom(scenario.id):
        return None
    personality, samples = profile_parts(scenario)
    reply_text = " ".join(bubbles)
    reply_words = _WORD.findall(reply_text.lower())
    profile = set().union(*(_ngrams(text) for text in [personality, *samples]))
    profile -= _ngrams(scenario.situation)
    shared = sorted(set().union(*(_ngrams(b) for b in bubbles)) & profile) if bubbles else []
    if shared:
        return " ".join(shared[0])
    for text in [personality, *samples]:
        words = _WORD.findall(text.lower())
        if len(words) == COPY_NGRAM - 1 and _longest_run(words, reply_words) == len(words):
            return text
    situation = _WORD.findall(scenario.situation.lower())
    run = _longest_run(situation, reply_words)
    if run >= SITUATION_RUN and run >= SITUATION_SHARE * len(situation):
        return f"{run} words of the situation"
    return None
