"""WHATIF lane entry point: "if you'd said this instead, here's where it would have gone."

A small look-ahead search, like a chess engine thinking a few moves ahead (docs/how/whatif.md):
  1. candidates.select() picks up to 3 verified, diverse better replies for the chosen helper message;
  2. each one replaces that message and is played forward through the REAL state engine with the
     reviewed line-bank voice (no LLM, so it is deterministic and free) for up to HORIZON more helper
     turns, each chosen by a one-step look-ahead over the exemplar bank;
  3. every path gets a documented value (path_value) and the best one is marked.

Faithfulness: the engine's diminishing-returns rule needs the labels of the previous helper message,
which the live engine remembers per State *object*. Rollouts never rely on that memory: they pass
`prev_active` explicitly, starting from the labels of the helper message that produced the starting
state (the same lookup the live engine would make), so a replay of the user's own messages reproduces
the live conversation exactly (tests/unit/whatif/test_faithful.py).
"""

from __future__ import annotations

import threading
from collections.abc import Sequence
from dataclasses import dataclass, field

from backend.app import content, services
from backend.app.contracts import (
    NEGATIVE_LABELS,
    Exemplar,
    Node,
    Reaction,
    Scenario,
    Session,
    SkillLabel,
    SkillProbs,
    State,
    WhatIfPath,
    WhatIfResult,
)
from backend.app.engine.service import Engine
from backend.app.engine.state import active_labels
from backend.app.pipeline import friend_context
from backend.app.whatif import candidates as cands

IMPLEMENTED = True

HORIZON = 3  # helper turns simulated after the replaced message
LEVEL_POINTS = 10  # value per disclosure level gained
END_POINTS = 25  # bonus for ended_success, penalty for ended_fail
TURN_COST = 10  # per helper turn after the first: reaching help sooner beats piling up trust


def path_value(start: State, end: State, helper_turns: int) -> float:
    """value = final trust + 10 x levels gained + 25 if ended_success - 25 if ended_fail
    - 10 per helper turn after the first."""
    value = (
        end.trust + LEVEL_POINTS * (end.level - start.level) - TURN_COST * max(0, helper_turns - 1)
    )
    if end.status == "ended_success":
        value += END_POINTS
    elif end.status == "ended_fail":
        value -= END_POINTS
    return round(value, 4)


def step_score(before: State, after: State) -> float:
    """One-step look-ahead score: trust change + 10 x level change +/- 25 for an ending."""
    score = after.trust - before.trust + LEVEL_POINTS * (after.level - before.level)
    if after.status == "ended_success":
        score += END_POINTS
    elif after.status == "ended_fail":
        score -= END_POINTS
    return round(score, 6)


def labels_before(base_path: Sequence[Node], cfg_threshold: float) -> frozenset[SkillLabel]:
    """Labels of the helper message that produced the last state on `base_path`, exactly as the live
    engine remembers them: the latest scored helper node whose state_after IS that State object.
    A blocked message keeps the previous State object (so it is skipped); a crisis pause copies the state
    (so the live engine remembers nothing, and neither do we)."""
    if not base_path:
        return frozenset()
    state = base_path[-1].state_after
    for node in reversed(base_path):
        if node.role == "user" and node.events is not None and node.state_after is state:
            return active_labels(node.events, cfg_threshold)
    return frozenset()


@dataclass
class Rollout:
    """A simulated continuation: the new nodes, the trust after each helper turn, the final state."""

    nodes: list[Node] = field(default_factory=list)
    trust_series: list[float] = field(default_factory=list)
    final: State | None = None
    helper_turns: int = 0
    unsafe_friend_lines: int = 0


class Simulator:
    """Plays helper messages forward through the real engine with the bank voice only."""

    def __init__(self, scenario: Scenario, locale: str, engine: Engine, detector, guardian) -> None:
        self.scenario, self.locale = scenario, locale
        self.engine, self.detector, self.guardian = engine, detector, guardian
        self.threshold = engine.cfg.event_threshold
        self.bank = engine.bank(scenario.id, locale)

    def predict(self, texts: list[str], context: list[str]) -> list[SkillProbs]:
        if hasattr(self.detector, "predict_many"):
            return self.detector.predict_many(list(texts), context)
        return [self.detector.predict(text, context) for text in texts]

    def turn(
        self,
        history: list[Node],
        state: State,
        prev: frozenset[SkillLabel],
        text: str,
        events: SkillProbs,
        ids: tuple[str, str],
        created: float,
    ) -> tuple[Node, Node, State, bool]:
        """One helper message + the friend's reply, mirroring pipeline.run_turn / _friend_reply."""
        after = self.engine.update(state, events, self.scenario, prev_active=prev)
        user = Node(
            id=ids[0],
            parent_id=history[-1].id,
            role="user",
            bubbles=[text],
            events=events,
            # latency zeroed so the same input always gives byte-identical output
            guardian=self.guardian.check_user(text, history).model_copy(update={"latency_ms": 0.0}),
            state_after=after,
            created_at=created,
        )
        friend, unsafe = self.reply([*history, user], after, text, events, ids[1], created)
        return user, friend, after, unsafe

    def reply(
        self,
        history: list[Node],
        state: State,
        text: str,
        events: SkillProbs,
        node_id: str,
        created: float,
    ) -> tuple[Node, bool]:
        """The friend's reply (or "Seen"), exactly as the pipeline builds it, but always the bank voice."""
        common = {
            "id": node_id,
            "parent_id": history[-1].id,
            "role": "friend",
            "created_at": created,
        }
        if state.status == "silent":
            node = Node(
                **common,
                bubbles=[],
                state_after=state,
                seen_no_reply=True,
                reaction=Reaction.DISMISSED,
            )
            return node, False
        output = self.engine.generate(self.scenario, state, history, text, events, self.locale)
        verified = self.engine.verify(output, self.scenario, state, self.bank).ok
        safe = all(self.guardian.check_friend(b).level == "none" for b in output.bubbles)
        if verified and safe and output.bubbles:
            node = Node(
                **common,
                bubbles=output.bubbles,
                state_after=state,
                line_id=output.line_id,
                reaction=output.reaction,
                voice=output.source,
            )
            return node, False
        fallback = (
            self.scenario.fallback_lines.get(state.level)
            or self.scenario.fallback_lines.get(0)
            or ["..."]
        )
        line = fallback[state.turn % len(fallback)]
        node = Node(
            **common,
            bubbles=[line],
            state_after=state,
            reaction=Reaction.NEUTRAL,
            voice="fallback",
        )
        return node, self.guardian.check_friend(line).level != "none"

    def replay(self, base_path: list[Node], texts: Sequence[str], prefix: str) -> Rollout:
        """Play fixed helper messages forward from the end of `base_path` (used for tests and eval)."""
        return self.rollout(
            base_path, texts[0], prefix, follow_ups=list(texts[1:]), horizon=len(texts) - 1
        )

    def rollout(
        self,
        base_path: list[Node],
        first_text: str,
        prefix: str,
        pool: Sequence[Exemplar] = (),
        follow_ups: list[str] | None = None,
        avoid: frozenset[str] = frozenset(),
        horizon: int = HORIZON,
    ) -> Rollout:
        """`first_text`, then up to `horizon` more helper turns: either the given `follow_ups`, or the
        exemplar with the best one-step look-ahead each turn (never repeating a text)."""
        history = list(base_path)
        state = history[-1].state_after
        prev = labels_before(base_path, self.threshold)
        created = history[-1].created_at
        out = Rollout(trust_series=[state.trust], final=state)
        used = set(avoid) | {first_text.strip()}
        text: str | None = first_text
        events = self.predict([first_text], friend_context(history))[0]
        for step in range(horizon + 1):
            if text is None:
                break
            created += 0.001
            ids = (f"{prefix}.{step}u", f"{prefix}.{step}f")
            user, friend, after, unsafe = self.turn(
                history, state, prev, text, events, ids, created
            )
            history += [user, friend]
            out.nodes += [user, friend]
            out.trust_series.append(after.trust)
            out.helper_turns += 1
            out.unsafe_friend_lines += int(unsafe)
            prev, state, out.final = active_labels(events, self.threshold), after, after
            if after.status in ("ended_success", "ended_fail") or step == horizon:
                break
            if follow_ups is not None:
                text = follow_ups[step] if step < len(follow_ups) else None
                if text is not None:
                    events = self.predict([text], friend_context(history))[0]
            else:
                text, events = self.best_next(history, state, prev, pool, used)
                if text is not None:
                    used.add(text.strip())
        return out

    def best_next(
        self,
        history: list[Node],
        state: State,
        prev: frozenset[SkillLabel],
        pool: Sequence[Exemplar],
        used: set[str],
    ) -> tuple[str | None, SkillProbs]:
        """The unused exemplar whose next engine step scores best (trust delta + level progress),
        that the Guardian lets through. Ties go to the exemplar id."""
        options = [ex for ex in pool if ex.text.strip() not in used]
        if not options:
            return None, {}
        probs = self.predict([ex.text for ex in options], friend_context(history))
        scored = []
        for exemplar, events in zip(options, probs, strict=True):
            if cands.has_negative(events):
                continue
            after = self.engine.update(state, events, self.scenario, prev_active=prev)
            scored.append((-step_score(state, after), exemplar.id, exemplar.text, events))
        for _, _, text, events in sorted(scored, key=lambda row: (row[0], row[1])):
            if self.guardian.check_user(text, history).action == "continue":
                return text, events
        return None, {}


_engine_lock = threading.Lock()
_bank_engine: Engine | None = None


def bank_engine() -> Engine:
    """A real engine with the LLM voice switched off (llm_attempts = 0 -> verified bank lines only)."""
    global _bank_engine
    with _engine_lock:
        if _bank_engine is None:
            _bank_engine = Engine()
            _bank_engine.llm_attempts = 0
    return _bank_engine


def split_at(path: list[Node], node_id: str) -> tuple[list[Node], Node | None, list[Node]]:
    """(path before the replaced helper message, that message or None, what actually came after).
    A friend node means "what should I have said next?", so nothing is replaced."""
    index = next(i for i, node in enumerate(path) if node.id == node_id)
    if path[index].role == "user":
        return path[:index], path[index], path[index + 1 :]
    if path[index].role == "system" and index > 0 and path[index - 1].role == "user":
        return path[: index - 1], path[index - 1], path[index + 1 :]
    rest = path[index + 1 :]
    if rest and rest[0].role == "user":
        return path[: index + 1], rest[0], rest[1:]
    return path[: index + 1], None, rest


def scored_user_nodes(path: Sequence[Node]) -> list[Node]:
    return [n for n in path if n.role == "user" and n.events is not None]


def actual_outcome(path: list[Node], node_id: str, horizon: int = HORIZON) -> tuple[float, State]:
    """The value and final state of what the user ACTUALLY did from the chosen message, over the same
    horizon (the replaced message + up to `horizon` more helper turns)."""
    base, original, after = split_at(path, node_id)
    start = base[-1].state_after
    turns = scored_user_nodes([original] if original else []) + scored_user_nodes(after)
    turns = turns[: horizon + 1]
    if not turns:
        return path_value(start, start, 0), start
    return path_value(start, turns[-1].state_after, len(turns)), turns[-1].state_after


class WhatIf:
    """Exemplar-bank candidates simulated through the real engine and the bank voice."""

    def __init__(self, detector=None, guardian=None, engine: Engine | None = None, exemplars=None):
        self._detector, self._guardian, self._engine = detector, guardian, engine
        self._exemplars = exemplars  # optional (scenario_id, locale) -> exemplars, for tests

    def exemplars(self, scenario_id: str, locale: str) -> tuple[Exemplar, ...]:
        """The session's own language only: a chat never mixes languages."""
        if self._exemplars is not None:
            return tuple(self._exemplars(scenario_id, locale))
        return content.load_exemplars(scenario_id, locale)

    def simulator(self, session: Session) -> Simulator:
        scenario = content.get_scenario(session.scenario_id)
        return Simulator(
            scenario,
            session.locale,
            self._engine or bank_engine(),
            self._detector or services.skills(),
            self._guardian or services.guardian(),
        )

    def simulate(self, session: Session, path: list[Node], node_id: str) -> WhatIfResult:
        sim = self.simulator(session)
        base, original, _ = split_at(path, node_id)
        before = base[-1].state_after
        context = friend_context(base)
        original_text = " ".join(original.bubbles) if original else ""
        original_probs = dict(original.events) if original and original.events else {}
        scored = scored_user_nodes(path)
        first = not scored_user_nodes(base)
        exemplars = list(self.exemplars(session.scenario_id, session.locale))

        def predict(texts: list[str]) -> list[SkillProbs]:
            return sim.predict(texts, context)

        picked = cands.select(
            exemplars,
            original_text,
            original_probs,
            before,
            first,
            [dict(n.events) for n in scored if n.events],
            context,
            base,
            predict,
            sim.guardian,
        )
        pool = [ex for ex in exemplars if not set(ex.labels) & set(NEGATIVE_LABELS)]
        avoid = frozenset(" ".join(n.bubbles).strip() for n in path if n.role == "user")
        paths: list[WhatIfPath] = []
        for i, candidate in enumerate(picked):
            run = sim.rollout(base, candidate.text, f"{node_id}.w{i}", pool, avoid=avoid)
            paths.append(
                WhatIfPath(
                    candidate_text=candidate.text,
                    strategy=candidate.strategy,
                    critic_score=candidate.score,
                    nodes=run.nodes,
                    trust_series=run.trust_series,
                    value=path_value(before, run.final, run.helper_turns),
                )
            )
        best = max(range(len(paths)), key=lambda i: (paths[i].value, -i)) if paths else 0
        return WhatIfResult(from_node_id=node_id, paths=paths, best_index=best, simulated=True)


def get_service() -> WhatIf:
    return WhatIf()
