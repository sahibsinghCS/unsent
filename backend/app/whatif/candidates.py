"""Candidate replies for "what if": better versions of one helper message, from the reviewed exemplar bank.

Steps (see docs/how/whatif.md):
  1. targets: the rubric skills this message (and the whole conversation) was missing, using the critic's
     own rules, so "what if" and the feedback report agree on what went wrong;
  2. pool: the session's scenario + locale exemplars near the friend's disclosure level (widening to every
     level if that leaves fewer than 3);
  3. filters: our detector must score the candidate at least MIN_GAIN higher than the original on the skill
     it teaches, it must not trip a negative label, and the Guardian must let it through ("continue");
  4. pick 3: the critic's verified rewrite first (so "Try instead" and "What if" match), then maximal
     marginal relevance (MMR) on embeddings: relevant, but different skills and no near-duplicates.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from backend.app.contracts import (
    NEGATIVE_LABELS,
    RUBRIC_SKILLS,
    Exemplar,
    Node,
    SkillLabel,
    SkillProbs,
    State,
)
from backend.app.embed import embed_one
from backend.app.ml import critic

ON = critic.ON  # a label counts as "done" at calibrated probability >= 0.5
MIN_GAIN = critic.MIN_REWRITE_GAIN  # the same bar the critic uses for "Try instead"
MAX_PATHS = 3
LEVEL_WINDOW = 1  # exemplars written for level L +/- 1 first
MMR_LAMBDA = 0.7  # relevance vs. diversity
NEAR_DUPLICATE = 0.9  # cosine above this counts as the same reply

# Which rubric skill each exemplar strategy teaches, and the chip name shown for each skill.
STRATEGY_SKILL = {
    "check_in": "check_in",
    "validate": "listen",
    "ask_directly": "ask_directly",
    "refer": "refer",
    "follow_up": "follow_up",
}
SKILL_STRATEGY = {
    "check_in": "check_in",
    "listen": "validate",
    "ask_directly": "ask_directly",
    "refer": "refer",
    "follow_up": "follow_up",
    "persuade": "encourage_help",
}
LABEL_SKILL = {
    SkillLabel.CHECKED_IN: "check_in",
    SkillLabel.VALIDATED: "listen",
    SkillLabel.ASKED_DIRECTLY: "ask_directly",
    SkillLabel.ENCOURAGED_HELP: "persuade",
    SkillLabel.REFERRED_ADULT: "refer",
    SkillLabel.REFERRED_988: "refer",
    SkillLabel.FOLLOW_UP: "follow_up",
}


@dataclass(frozen=True)
class Candidate:
    """One verified better reply for the chosen message."""

    text: str
    skill: str  # rubric skill it teaches (what critic_score measures)
    strategy: str  # chip shown in the UI
    score: float  # our detector's calibrated score for `skill` on this reply (0..1)
    gain: float  # score minus the original message's score on the same skill
    relevance: float
    source: str  # "rewrite" (the critic's own suggestion) or "exemplar"
    exemplar_id: str


@dataclass(frozen=True)
class Targets:
    """What the chosen message should have done."""

    primary: str | None  # the critic's missing skill for this message (None if it was fine)
    missing: tuple[str, ...]  # rubric skills the whole conversation never reached, in tip order

    def rank(self, skill: str) -> int:
        if skill == self.primary:
            return 0
        if skill in self.missing:
            return 1 + self.missing.index(skill)
        return 1 + len(self.missing) + critic.TIP_ORDER.index(skill)


def skill_score(probs: SkillProbs, skill: str) -> float:
    """The per-message rubric score for one skill (the same mapping the critic's summary uses)."""
    return critic.rubric_summary([probs])[skill]


def has_negative(probs: SkillProbs) -> bool:
    return any(probs.get(label, 0.0) >= ON for label in NEGATIVE_LABELS)


def exemplar_skills(exemplar: Exemplar) -> list[str]:
    """Rubric skills an exemplar teaches: its strategy's skill, or for combos, its labels' skills."""
    if exemplar.strategy in STRATEGY_SKILL:
        return [STRATEGY_SKILL[exemplar.strategy]]
    skills = [LABEL_SKILL[label] for label in exemplar.labels if label in LABEL_SKILL]
    return list(dict.fromkeys(skills)) or ["listen"]


def find_targets(
    original: SkillProbs, before: State, first: bool, scored: list[SkillProbs]
) -> Targets:
    """The critic's missing skill for this message plus the skills the conversation never reached."""
    target = critic.missing_skill(original, before, first)
    summary = critic.rubric_summary(scored) if scored else dict.fromkeys(RUBRIC_SKILLS, 0.0)
    missing = tuple(s for s in critic.TIP_ORDER if s != "no_secrecy" and summary[s] < ON)
    primary = target.improves if target is not None else None
    return Targets(primary=primary, missing=missing)


def critic_rewrite(
    exemplars: Sequence[Exemplar],
    original: SkillProbs,
    before: State,
    first: bool,
    context: list[str],
    predict,
    guardian_ok,
) -> tuple[Exemplar, str] | None:
    """The exemplar the critic would show as "Try instead" for this message (exemplar rewrites only;
    this lane never calls the LLM), with the rubric skill it improves."""
    target = critic.missing_skill(original, before, first)
    if target is None:
        return None
    friend_last = context[-1] if context else ""
    base = critic.target_score(original, target)
    ranked = critic.rank_exemplars(tuple(exemplars), target, before.level, friend_last)
    for exemplar in ranked[: critic.MAX_CANDIDATES]:
        gain = critic.target_score(predict([exemplar.text])[0], target) - base
        if gain >= MIN_GAIN and guardian_ok(exemplar.text):
            return exemplar, target.improves
    return None


def select(
    exemplars: Sequence[Exemplar],
    original_text: str,
    original: SkillProbs,
    before: State,
    first: bool,
    scored: list[SkillProbs],
    context: list[str],
    history: list[Node],
    predict,
    guardian,
) -> list[Candidate]:
    """Up to 3 diverse, verified candidates for the chosen message, best first."""
    verdicts: dict[str, bool] = {}

    def guardian_ok(text: str) -> bool:
        if text not in verdicts:
            verdicts[text] = guardian.check_user(text, history).action == "continue"
        return verdicts[text]

    pool = [ex for ex in exemplars if ex.text.strip() != original_text.strip()]
    pool = [ex for ex in pool if not set(ex.labels) & set(NEGATIVE_LABELS)]
    targets = find_targets(original, before, first, scored)
    rewrite = critic_rewrite(pool, original, before, first, context, predict, guardian_ok)

    near = [ex for ex in pool if abs(ex.level - before.level) <= LEVEL_WINDOW]
    found = _verified(near, original, before.level, targets, predict, guardian_ok)
    if len({c.skill for c in found}) < MAX_PATHS:
        found = _verified(pool, original, before.level, targets, predict, guardian_ok)

    chosen: list[Candidate] = []
    if rewrite is not None:
        exemplar, skill = rewrite
        probs = predict([exemplar.text])[0]
        score = skill_score(probs, skill)
        chosen.append(
            Candidate(
                text=exemplar.text,
                skill=skill,
                strategy=SKILL_STRATEGY[skill],
                score=round(score, 4),
                gain=round(score - skill_score(original, skill), 4),
                relevance=float("inf"),
                source="rewrite",
                exemplar_id=exemplar.id,
            )
        )
    return mmr(chosen, [c for c in found if c.text != (rewrite[0].text if rewrite else None)])


def _verified(
    pool: Sequence[Exemplar],
    original: SkillProbs,
    level: int,
    targets: Targets,
    predict,
    guardian_ok,
) -> list[Candidate]:
    """Every exemplar that beats the original on a skill it teaches and passes the Guardian."""
    if not pool:
        return []
    probs_list = predict([ex.text for ex in pool])
    out: list[Candidate] = []
    for exemplar, probs in zip(pool, probs_list, strict=True):
        if has_negative(probs):
            continue
        best: Candidate | None = None
        for skill in exemplar_skills(exemplar):
            score = skill_score(probs, skill)
            gain = score - skill_score(original, skill)
            if gain < MIN_GAIN:
                continue
            rank = targets.rank(skill)
            relevance = gain + score + 1.0 / (1 + rank) - 0.15 * abs(exemplar.level - level)
            candidate = Candidate(
                text=exemplar.text,
                skill=skill,
                strategy=SKILL_STRATEGY[skill],
                score=round(score, 4),
                gain=round(gain, 4),
                relevance=round(relevance, 6),
                source="exemplar",
                exemplar_id=exemplar.id,
            )
            if best is None or candidate.relevance > best.relevance:
                best = candidate
        if best is not None:
            out.append(best)
    out.sort(key=lambda c: (-c.relevance, c.exemplar_id))
    return [c for c in out if guardian_ok(c.text)]


def mmr(chosen: list[Candidate], pool: list[Candidate], k: int = MAX_PATHS) -> list[Candidate]:
    """Greedy maximal marginal relevance: each pick trades relevance against similarity to the picks
    so far. A new skill is required while one is available; near-duplicates are never picked."""
    chosen = list(chosen)
    vectors = {c.text: embed_one(c.text) for c in [*chosen, *pool]}
    remaining = list(pool)
    while remaining and len(chosen) < k:
        used_skills = {c.skill for c in chosen}
        fresh = [c for c in remaining if c.skill not in used_skills]
        options = fresh or remaining

        def similarity(c: Candidate) -> float:
            if not chosen:
                return 0.0
            return max(float(np.dot(vectors[c.text], vectors[p.text])) for p in chosen)

        options = [c for c in options if similarity(c) < NEAR_DUPLICATE]
        if not options:
            break

        def key(c: Candidate) -> tuple[float, str]:
            value = MMR_LAMBDA * c.relevance - (1 - MMR_LAMBDA) * similarity(c)
            return (-round(value, 6), c.exemplar_id)

        pick = min(options, key=key)
        chosen.append(pick)
        remaining = [c for c in remaining if c.text != pick.text]
    return chosen
