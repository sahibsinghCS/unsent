"""Leave-one-word-out explanations for the skill detector (ML lane).

For each label the detector is confident about (p ≥ 0.5) we delete one word at a time, re-score the
message, and see how much that label's calibrated probability falls. Words whose removal drops it by
at least 0.1 are "the words that made the model say so". If no single word matters on its own (the
message makes its point twice), we delete the most important word, then the next most important, until
the probability drops, and highlight that set with its joint drop. Neighbouring important words are merged into
one span, re-scored as a unit, and the top 3 spans per label become Highlights with exact character
offsets into the original message.
"""

from __future__ import annotations

import re
from collections.abc import Callable

from backend.app.contracts import Highlight, SkillLabel

WORD = re.compile(r"[\w']+", re.UNICODE)
MIN_PROB = 0.5
MIN_DELTA = 0.1
TOP_SPANS = 3
MAX_GREEDY_WORDS = 6  # fallback: delete at most this many words to find redundant evidence

# Scores a batch of texts -> one {label: probability} dict per text.
BatchScorer = Callable[[list[str]], list[dict[SkillLabel, float]]]


def words(text: str) -> list[tuple[int, int]]:
    """(start, end) character offsets of each word."""
    return [m.span() for m in WORD.finditer(text)]


def occlude(text: str, start: int, end: int) -> str:
    """The text with [start, end) removed and the gap closed to a single space."""
    return re.sub(r"\s{2,}", " ", (text[:start] + " " + text[end:])).strip()


def _merge_windows(windows: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Merge overlapping or touching word-index windows: [(1, 2), (3, 3), (6, 7)] -> [(1, 3), (6, 7)]."""
    runs: list[tuple[int, int]] = []
    for a, b in sorted(windows):
        if runs and a <= runs[-1][1] + 1:
            runs[-1] = (runs[-1][0], max(b, runs[-1][1]))
        else:
            runs.append((a, b))
    return runs


def occlude_all(text: str, spans: list[tuple[int, int]], removed: set[int]) -> str:
    """The text with every word index in `removed` deleted."""
    for i in sorted(removed, reverse=True):
        text = occlude(text, *spans[i])
    return text


def _greedy_set(
    text: str, spans: list[tuple[int, int]], label: SkillLabel, base: float, score: BatchScorer
) -> tuple[set[int], float]:
    """Delete the most important word, then the next, ... until the label drops by MIN_DELTA.

    Used when no single word matters on its own because the message repeats its point
    ("lol ur fine dont be dramatic"). Returns the deleted word indices and their joint drop.
    """
    removed: set[int] = set()
    for _ in range(min(MAX_GREEDY_WORDS, len(spans))):
        candidates = [i for i in range(len(spans)) if i not in removed]
        probs = score([occlude_all(text, spans, removed | {i}) for i in candidates])
        best = min(range(len(candidates)), key=lambda k: (probs[k][label], k))
        removed.add(candidates[best])
        drop = base - probs[best][label]
        if drop >= MIN_DELTA:
            return removed, drop
    return set(), 0.0


def occlusion_highlights(text: str, score: BatchScorer) -> list[Highlight]:
    """Highlights for every label with p ≥ 0.5 (top 3 spans per label with delta ≥ 0.1)."""
    spans = words(text)
    if not spans:
        return []
    base = score([text])[0]
    targets = [label for label, p in base.items() if p >= MIN_PROB]
    if not targets:
        return []
    single = score([occlude(text, s, e) for s, e in spans])

    # (start_word, end_word, delta) candidates per label.
    found: dict[SkillLabel, list[tuple[int, int, float]]] = {}
    to_rescore: set[tuple[int, int]] = set()
    for label in targets:
        hits = [i for i, probs in enumerate(single) if base[label] - probs[label] >= MIN_DELTA]
        if hits:
            runs = _merge_windows([(i, i) for i in hits])
            to_rescore.update(runs)
            found[label] = [(a, b, float("nan")) for a, b in runs]
        else:
            removed, drop = _greedy_set(text, spans, label, base[label], score)
            found[label] = [(a, b, drop) for a, b in _merge_windows([(i, i) for i in removed])]

    # Re-score each merged run of individually important words with the whole run removed.
    ordered = sorted(to_rescore)
    rescored = (
        score([occlude(text, spans[a][0], spans[b][1]) for a, b in ordered]) if ordered else []
    )
    run_probs = dict(zip(ordered, rescored, strict=True))

    highlights: list[Highlight] = []
    for label in targets:
        scored = []
        for a, b, delta in found[label]:
            if (a, b) in run_probs and delta != delta:  # NaN: delta comes from the re-score
                delta = base[label] - run_probs[(a, b)][label]
            if delta >= MIN_DELTA:
                scored.append((delta, spans[a][0], spans[b][1]))
        for delta, start, end in sorted(scored, key=lambda t: (-t[0], t[1]))[:TOP_SPANS]:
            highlights.append(
                Highlight(
                    start=start, end=end, text=text[start:end], label=label, delta=round(delta, 4)
                )
            )
    return highlights
