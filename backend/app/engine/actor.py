"""Line-bank actor: decides the friend's reaction and picks a bank line (ENGINE lane). See docs/how/engine.md.

The reaction chosen here steers every voice: the LLM voice (voice.py) words it, and when the LLM is off or
its reply fails the verifier, the friend uses a pre-written, reviewed line from the line bank
(data/lines/<scenario>.<locale>.jsonl), chosen in four steps:
  1. reaction: WHY the friend replies this way (from the helper's detected labels and the state),
  2. candidates: lines with that reaction at the current level, widening to lower levels, then NEUTRAL,
  3. filters: no facts above the current level, no lines already used on this path,
  4. ranking: cosine similarity between the helper's message and each line's cue, plus a small bonus
     for lines written for exactly this level, with a deterministic tie-break.
"""

from __future__ import annotations

import hashlib
import os
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from backend.app import content
from backend.app.contracts import (
    ActorOutput,
    Line,
    Node,
    Reaction,
    Scenario,
    SkillLabel,
    SkillProbs,
    State,
)
from backend.app.embed import cosine, embed_one
from backend.app.engine.state import (
    EngineConfig,
    active_labels,
    default_config,
    secrecy_broken,
)

# Reaction priority (first match wins), applied after the ending and secrecy-broken checks.
# Harm first (a dismissal outweighs anything kind in the same message), then the moves that matter most
# for suicide prevention (asking directly, referring), then listening, then the rest.
LABEL_PRIORITY: tuple[tuple[SkillLabel, Reaction], ...] = (
    (SkillLabel.DISMISSED, Reaction.DISMISSED),
    (SkillLabel.PROMISED_SECRECY, Reaction.PROMISED_SECRECY),
    (SkillLabel.ASKED_DIRECTLY, Reaction.ASKED_DIRECTLY),
    (SkillLabel.REFERRED_ADULT, Reaction.REFERRED),
    (SkillLabel.REFERRED_988, Reaction.REFERRED),
    (SkillLabel.VALIDATED, Reaction.VALIDATED),
    (SkillLabel.ADVICE_DUMP, Reaction.ADVICE_DUMP),
    (SkillLabel.CHECKED_IN, Reaction.CHECKED_IN),
    (SkillLabel.ENCOURAGED_HELP, Reaction.ENCOURAGED_HELP),
    (SkillLabel.FOLLOW_UP, Reaction.FOLLOW_UP),
)

# Supportive moves after which a friend who just opened up a level says what's newly on their mind.
DISCLOSING_REACTIONS = frozenset(
    {
        Reaction.NEUTRAL,
        Reaction.CHECKED_IN,
        Reaction.VALIDATED,
        Reaction.ASKED_DIRECTLY,
        Reaction.REFERRED,
        Reaction.ENCOURAGED_HELP,
        Reaction.FOLLOW_UP,
    }
)

BANK_DIR_ENV = "FR_ENGINE_BANK_DIR"  # optional override (eval / believability runs on another bank)


def load_bank(
    scenario_id: str, locale: str = "en", bank_dir: Path | None = None
) -> tuple[Line, ...]:
    """The scenario's line bank in `locale`, falling back to English when that locale has none."""
    bank_dir = bank_dir or (Path(os.environ[BANK_DIR_ENV]) if os.getenv(BANK_DIR_ENV) else None)
    if bank_dir is None:
        return content.load_lines(scenario_id, locale) or content.load_lines(scenario_id, "en")
    for loc in (locale, "en"):
        path = bank_dir / f"{scenario_id}.{loc}.jsonl"
        if path.exists():
            return tuple(Line.model_validate(row) for row in content.read_jsonl(path))
    return ()


def fact_levels(scenario: Scenario) -> dict[str, int]:
    """fact id -> the disclosure level that unlocks it."""
    return {fact.id: int(level) for level, spec in scenario.levels.items() for fact in spec.facts}


def state_before(history: Sequence[Node]) -> State | None:
    """The state before the latest helper message (history ends with that message's user node)."""
    return history[-2].state_after if len(history) >= 2 else None


def choose_reaction(
    state: State,
    active: frozenset[SkillLabel],
    user_text: str,
    history: Sequence[Node],
    cfg: EngineConfig,
    before: State | None = None,
) -> Reaction:
    """Why the friend replies the way they do. Priority:

    SUCCESS / FAIL (conversation ended) > SECRECY_BROKEN > DISMISSED > PROMISED_SECRECY >
    ASKED_DIRECTLY > REFERRED > VALIDATED > ADVICE_DUMP > CHECKED_IN > ENCOURAGED_HELP > FOLLOW_UP >
    OFF_TOPIC (no labels and the message is unrelated to the conversation) > NEUTRAL.
    """
    if state.status == "ended_success":
        return Reaction.SUCCESS
    if state.status == "ended_fail":
        return Reaction.FAIL
    if before is not None and secrecy_broken(before, state):
        return Reaction.SECRECY_BROKEN
    for label, reaction in LABEL_PRIORITY:
        if label in active:
            return reaction
    if is_off_topic(user_text, history, cfg):
        return Reaction.OFF_TOPIC
    return Reaction.NEUTRAL


def is_off_topic(user_text: str, history: Sequence[Node], cfg: EngineConfig) -> bool:
    """A real message (>= off_topic_min_words words) that resembles nothing said recently."""
    if len(user_text.split()) < cfg.off_topic_min_words:
        return False
    recent = [b for node in history[:-1][-6:] if node.role != "system" for b in node.bubbles]
    if not recent:
        return False
    query = embed_one(user_text)
    best = max(cosine(query, embed_one(text)) for text in recent)
    return best < cfg.off_topic_max_similarity


@dataclass(frozen=True)
class Candidate:
    """A ranked bank line (or a scenario fallback line when line is None)."""

    reaction: Reaction
    bubbles: tuple[str, ...]
    line: Line | None


def tie_break(path_len: int, line_id: str) -> int:
    """Stable pseudo-random tie-break (Python's hash() is salted per process, so don't use it)."""
    digest = hashlib.blake2b(f"{path_len}:{line_id}".encode(), digest_size=8).digest()
    return int.from_bytes(digest, "big")


def rank_lines(
    lines: Sequence[Line],
    user_text: str,
    level: int,
    path_len: int,
    cfg: EngineConfig,
    revealed: frozenset[str] = frozenset(),
) -> list[Line]:
    """Best match first: cosine(helper message, line cue) + a small bonus for lines written for exactly
    this level + a small bonus for revealing a fact not yet told on this path, then tie-break."""
    query = embed_one(user_text)

    def key(line: Line) -> tuple[float, int]:
        score = cosine(query, embed_one(line.cue or " ".join(line.bubbles)))
        if line.level == level:
            score += cfg.exact_level_bonus
        if set(line.fact_ids) - revealed:
            score += cfg.new_fact_bonus
        return (-round(score, 6), tie_break(path_len, line.id))

    return sorted(lines, key=key)


def candidates(
    scenario: Scenario,
    state: State,
    history: Sequence[Node],
    user_text: str,
    reaction: Reaction,
    bank: Sequence[Line],
    cfg: EngineConfig,
    leveled_up: bool = False,
    locale: str = "en",
) -> list[Candidate]:
    """Every acceptable reply, best first. The service walks this list until one verifies.

    Order: unused lines with the reaction (current level, then lower levels), unused NEUTRAL lines,
    then already-used lines least recently used first, then the scenario's fallback lines.
    On a turn where the friend just moved UP a level (and the helper's move was a supportive one), lines
    that actually disclose something new from that level go first: opening up is the point of the
    level change, so it shouldn't be skipped because the reaction's lines at that level are fact-free.
    """
    facts = fact_levels(scenario)
    last_used = {node.line_id: i for i, node in enumerate(history) if node.line_id}
    revealed = frozenset(f for ln in bank if ln.id in last_used for f in ln.fact_ids)
    level = state.level

    def eligible(line: Line) -> bool:
        return line.level <= level and all(facts.get(f, 99) <= level for f in line.fact_ids)

    tiers: list[tuple[Reaction, list[Line]]] = []
    if leveled_up and reaction in DISCLOSING_REACTIONS:
        new_facts = {f for f, lvl in facts.items() if lvl == level} - revealed
        # A direct question gets a direct answer, so it is never swapped for a NEUTRAL disclosure.
        subs = [reaction] if reaction == Reaction.ASKED_DIRECTLY else [reaction, Reaction.NEUTRAL]
        for want in dict.fromkeys(subs):
            tier = [
                ln
                for ln in bank
                if ln.reaction == want
                and ln.level == level
                and eligible(ln)
                and set(ln.fact_ids) & new_facts
            ]
            if tier:
                tiers.append((want, tier))
    wanted = [reaction] if reaction == Reaction.NEUTRAL else [reaction, Reaction.NEUTRAL]
    for want in wanted:
        for lvl in range(level, -1, -1):
            tier = [ln for ln in bank if ln.reaction == want and ln.level == lvl and eligible(ln)]
            if tier:
                tiers.append((want, tier))
        if want in (Reaction.SUCCESS, Reaction.FAIL) and tiers:
            break  # an ending line exists: don't dilute it with NEUTRAL

    out: list[Candidate] = []
    used_lines: list[tuple[Reaction, Line]] = []
    seen: set[str] = set()
    for want, tier in tiers:
        fresh = [ln for ln in tier if ln.id not in last_used and ln.id not in seen]
        used_lines += [(want, ln) for ln in tier if ln.id in last_used and ln.id not in seen]
        seen.update(ln.id for ln in tier)
        for ln in rank_lines(fresh, user_text, level, len(history), cfg, revealed):
            out.append(Candidate(want, tuple(ln.bubbles), ln))
    used_lines.sort(key=lambda item: last_used[item[1].id])  # least recently used first
    out += [Candidate(want, tuple(ln.bubbles), ln) for want, ln in used_lines]
    if locale == "en":
        out += fallback_candidates(scenario, state, history, reaction)
    else:
        # The scenario's fallback lines are English and a chat never mixes languages, so the last
        # resort is any calm, level-appropriate line from this language's bank.
        calm = (Reaction.NEUTRAL, Reaction.CHECKED_IN, Reaction.VALIDATED, Reaction.FOLLOW_UP)
        rest = [ln for ln in bank if ln.reaction in calm and eligible(ln) and ln.id not in seen]
        rest.sort(key=lambda ln: (ln.id in last_used, last_used.get(ln.id, -1), -ln.level, ln.id))
        out += [Candidate(Reaction.NEUTRAL, tuple(ln.bubbles), ln) for ln in rest]
    return out


def fallback_candidates(
    scenario: Scenario, state: State, history: Sequence[Node], reaction: Reaction
) -> list[Candidate]:
    """The scenario's safe generic lines (current level first, then lower), unused ones first."""
    said = {b for node in history if node.role == "friend" for b in node.bubbles}
    pool: list[str] = []
    for lvl in range(state.level, -1, -1):
        lines = scenario.fallback_lines.get(lvl, [])
        start = state.turn % len(lines) if lines else 0
        pool += lines[start:] + lines[:start]
    ordered = [t for t in pool if t not in said] + [t for t in pool if t in said]
    return [Candidate(reaction, (text,), None) for text in dict.fromkeys(ordered)]


def to_output(candidate: Candidate) -> ActorOutput:
    line = candidate.line
    return ActorOutput(
        bubbles=list(candidate.bubbles),
        line_id=line.id if line else None,
        reaction=candidate.reaction,
        fact_ids=list(line.fact_ids) if line else [],
        source="bank" if line else "fallback",
    )


def generate(
    scenario: Scenario,
    state: State,
    history: Sequence[Node],
    user_text: str,
    events: SkillProbs,
    locale: str = "en",
    bank: Sequence[Line] | None = None,
    cfg: EngineConfig | None = None,
) -> ActorOutput:
    """The friend's next reply (unverified: the service runs the verifier over the ranked list)."""
    return to_output(
        ranked_candidates(scenario, state, history, user_text, events, locale, bank, cfg)[0]
    )


def decide_reaction(
    state: State,
    history: Sequence[Node],
    user_text: str,
    events: SkillProbs,
    cfg: EngineConfig | None = None,
) -> Reaction:
    """The reaction for this turn, from the detected labels and the state change."""
    cfg = cfg or default_config()
    active = active_labels(events, cfg.event_threshold)
    return choose_reaction(state, active, user_text, history, cfg, state_before(history))


def ranked_candidates(
    scenario: Scenario,
    state: State,
    history: Sequence[Node],
    user_text: str,
    events: SkillProbs,
    locale: str = "en",
    bank: Sequence[Line] | None = None,
    cfg: EngineConfig | None = None,
) -> list[Candidate]:
    """All candidate replies, best first (never empty: the last ones are scenario fallbacks)."""
    cfg = cfg or default_config()
    if state.status == "silent":
        return [Candidate(Reaction.DISMISSED, (), None)]
    bank = load_bank(scenario.id, locale) if bank is None else bank
    reaction = decide_reaction(state, history, user_text, events, cfg)
    before = state_before(history)
    leveled_up = before is not None and state.level > before.level
    found = candidates(scenario, state, history, user_text, reaction, bank, cfg, leveled_up, locale)
    return found or [Candidate(reaction, ("...",), None)]
