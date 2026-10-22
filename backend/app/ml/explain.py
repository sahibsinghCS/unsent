"""Leave-one-word-out explanations for the skill detector (ML lane).

For each label the detector is confident about (p ≥ 0.5) we delete one word at a time, re-score the
message, and see how much that label's calibrated probability falls. Words whose removal drops it by
at least 0.1 are "the words that made the model say so". Neighbouring important words are merged into
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

# Scores a batch of texts -> one {label: probability} dict per text.
BatchScorer = Callable[[list[str]], list[dict[SkillLabel, float]]]


def words(text: str) -> list[tuple[int, int]]:
    """(start, end) character offsets of each word."""
    return [m.span() for m in WORD.finditer(text)]


def occlude(text: str, start: int, end: int) -> str:
    """The text with [start, end) removed and the gap closed to a single space."""
    return re.sub(r"\s{2,}", " ", (text[:start] + " " + text[end:])).strip()


def _merge_runs(indices: list[int]) -> list[tuple[int, int]]:
    """[1, 2, 4] -> [(1, 2), (4, 4)]: runs of adjacent word indices (inclusive)."""
    runs: list[tuple[int, int]] = []
    for i in sorted(indices):
        if runs and i == runs[-1][1] + 1:
            runs[-1] = (runs[-1][0], i)
        else:
            runs.append((i, i))
    return runs


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

    runs_by_label: dict[SkillLabel, list[tuple[int, int]]] = {}
    for label in targets:
        important = [i for i, probs in enumerate(single) if base[label] - probs[label] >= MIN_DELTA]
        runs_by_label[label] = _merge_runs(important)

    # Re-score each merged span with all its words removed together (one batch for all labels).
    unique_runs = sorted({run for runs in runs_by_label.values() for run in runs})
    run_texts = [occlude(text, spans[a][0], spans[b][1]) for a, b in unique_runs]
    run_probs = dict(zip(unique_runs, score(run_texts), strict=True)) if run_texts else {}

    highlights: list[Highlight] = []
    for label in targets:
        scored = []
        for a, b in runs_by_label[label]:
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
