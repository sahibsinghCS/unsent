"""Phrase highlights for the skill detector by occlusion (ML lane).

For each label the detector is confident about (p ≥ 0.5) we delete a phrase (1–5 neighbouring words that
don't cross punctuation), re-score the message, and measure how far the label falls in log-odds.
Log-odds, not probability: a confident model sits at 0.9999, where deleting the key phrase may move the
probability only to 0.99 but the odds by 100×. The phrase with the biggest drop wins, then we trim it to
its shortest part that keeps ≥ 80% of that drop (the crisp core). A second, separate phrase is kept only
if it is nearly as important. Character offsets point exactly into the original message.

Highlight.delta is that log-odds drop (natural log): 1.0 means deleting the phrase cuts the odds about
2.7×, 2.3 means 10×, 4.6 means 100×. It is always > 0 and comparable across labels.
"""

from __future__ import annotations

import math
import re
from collections.abc import Callable

from backend.app.contracts import Highlight, SkillLabel

WORD = re.compile(r"[\w']+", re.UNICODE)
BOUNDARY = re.compile(r"[.!?,;:¿¡]")
MIN_PROB = 0.5
MIN_LOGIT_DROP = 1.0  # deleting the phrase must cut the odds by at least e (≈2.7×)
SECOND_SPAN_SHARE = 0.5  # a 2nd phrase must be at least half as important as the 1st
CORE_SHARE = 0.8  # trim a phrase to its shortest part keeping 80% of its drop
MAX_SPAN_WORDS = 5
TOP_SPANS = 2
MAX_EXTEND = 2  # words a phrase may grow on each side to reach its clause edge
EPS = 1e-9

# Scores a batch of texts -> one {label: probability} dict per text.
BatchScorer = Callable[[list[str]], list[dict[SkillLabel, float]]]


def words(text: str) -> list[tuple[int, int]]:
    """(start, end) character offsets of each word."""
    return [m.span() for m in WORD.finditer(text)]


def occlude(text: str, start: int, end: int) -> str:
    """The text with [start, end) removed and the gap closed to a single space."""
    return re.sub(r"\s{2,}", " ", (text[:start] + " " + text[end:])).strip()


def log_odds(p: float) -> float:
    p = min(max(p, EPS), 1 - EPS)
    return math.log(p / (1 - p))


def phrases(text: str, spans: list[tuple[int, int]], max_words: int) -> list[tuple[int, int]]:
    """(first_word, last_word) windows of 1..max_words words that don't cross punctuation."""
    out = []
    for a in range(len(spans)):
        for b in range(a, min(a + max_words, len(spans))):
            if b > a and BOUNDARY.search(text[spans[b - 1][1] : spans[b][0]]):
                break
            out.append((a, b))
    return out


def _core(window: tuple[int, int], drops: dict[tuple[int, int], float]) -> tuple[int, int]:
    """Shortest sub-phrase of `window` keeping CORE_SHARE of its drop (ties: bigger drop, earlier)."""
    a, b = window
    target = CORE_SHARE * drops[window]
    inside = [(x, y) for (x, y) in drops if a <= x <= y <= b and drops[(x, y)] >= target]
    return min(inside, key=lambda w: (w[1] - w[0], -drops[w], w[0]))


def clause_bounds(text: str, spans: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """For each word: (first, last) word index of its clause (punctuation or the message edge)."""
    starts = [0]
    for i in range(1, len(spans)):
        if BOUNDARY.search(text[spans[i - 1][1] : spans[i][0]]):
            starts.append(i)
    ends = [s - 1 for s in starts[1:]] + [len(spans) - 1]
    out = []
    for first, last in zip(starts, ends, strict=True):
        out.extend([(first, last)] * (last - first + 1))
    return out


def extend_to_clause(
    window: tuple[int, int], others: list[tuple[int, int]], bounds: list[tuple[int, int]]
) -> tuple[int, int]:
    """Grow a phrase to its clause edges when each side needs ≤ MAX_EXTEND words and hits no other span."""
    a, b = window
    first, last = bounds[a][0], bounds[b][1]
    new_a = first if 0 < a - first <= MAX_EXTEND else a
    new_b = last if 0 < last - b <= MAX_EXTEND else b
    if any(c[1] >= new_a and c[1] < a for c in others):
        new_a = a
    if any(c[0] <= new_b and c[0] > b for c in others):
        new_b = b
    return new_a, new_b


def occlusion_highlights(text: str, score: BatchScorer) -> list[Highlight]:
    """Up to 2 crisp phrase highlights for every label with p ≥ 0.5."""
    spans = words(text)
    if not spans:
        return []
    base = score([text])[0]
    targets = [label for label, p in base.items() if p >= MIN_PROB]
    if not targets:
        return []
    max_words = MAX_SPAN_WORDS if len(spans) <= 40 else 2  # keep long messages fast
    windows = phrases(text, spans, max_words)
    occluded = score([occlude(text, spans[a][0], spans[b][1]) for a, b in windows])

    by_window = dict(zip(windows, occluded, strict=True))
    chosen_by_label: dict[SkillLabel, list[tuple[int, int]]] = {}
    for label in targets:
        drops = {w: log_odds(base[label]) - log_odds(p[label]) for w, p in by_window.items()}
        chosen: list[tuple[int, int]] = []
        for window in sorted(drops, key=lambda w: (-drops[w], w[1] - w[0], w[0])):
            if len(chosen) == TOP_SPANS or drops[window] < MIN_LOGIT_DROP:
                break
            if chosen and drops[window] < SECOND_SPAN_SHARE * drops[chosen[0]]:
                break
            core = _core(window, drops)
            if any(not (core[1] < c[0] or core[0] > c[1]) for c in chosen):
                continue  # overlaps a phrase we already have
            touching = [c for c in chosen if core[0] == c[1] + 1 or c[0] == core[1] + 1]
            group = [core, *touching]
            merged = (min(w[0] for w in group), max(w[1] for w in group))
            if touching and merged in drops:  # neighbours form one phrase ("killing" + "yourself")
                chosen = [c for c in chosen if c not in touching] + [merged]
            else:
                chosen.append(core)
        chosen_by_label[label] = chosen

    # Round each phrase out to its clause ("hey are" -> "hey are you ok") when that adds ≤ 2 words a
    # side, so highlights read as natural phrases; the delta is re-measured for the final span.
    bounds = clause_bounds(text, spans)
    for label, chosen in chosen_by_label.items():
        chosen_by_label[label] = [
            extend_to_clause(w, [c for c in chosen if c != w], bounds) for w in chosen
        ]
    missing = sorted({w for ws in chosen_by_label.values() for w in ws if w not in by_window})
    if missing:
        rescored = score([occlude(text, spans[a][0], spans[b][1]) for a, b in missing])
        by_window.update(zip(missing, rescored, strict=True))

    highlights: list[Highlight] = []
    for label in targets:
        for a, b in sorted(chosen_by_label[label]):
            start, end = spans[a][0], spans[b][1]
            drop = log_odds(base[label]) - log_odds(by_window[(a, b)][label])
            highlights.append(
                Highlight(
                    start=start, end=end, text=text[start:end], label=label, delta=round(drop, 2)
                )
            )
    return highlights
