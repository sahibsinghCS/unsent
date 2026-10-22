"""Stub "what if": replays 3 template replies through whichever engine is active.

The WHATIF lane replaces it with exemplar-bank candidates and scored multi-turn rollouts.
"""

from __future__ import annotations

from backend.app import services
from backend.app.content import get_scenario
from backend.app.contracts import Node, Session, SkillLabel, WhatIfPath, WhatIfResult
from backend.app.pipeline import friend_context
from backend.app.session import new_id

CANDIDATES: list[tuple[str, str, str]] = [
    (
        "ask_directly",
        "that sounds really heavy. are you thinking about killing yourself?",
        "i'm really glad you told me. can we talk to the counselor tomorrow? i'll go with you",
    ),
    (
        "validate",
        "that sounds really hard, i'm sorry. i'm here",
        "are you thinking about suicide? you can tell me",
    ),
    (
        "refer",
        "i care about you. can we talk to a trusted adult together?",
        "you can also call or text 988 anytime, i'll stay with you",
    ),
]


class StubWhatIf:
    def simulate(self, session: Session, path: list[Node], node_id: str) -> WhatIfResult:
        scenario = get_scenario(session.scenario_id)
        index = next(i for i, node in enumerate(path) if node.id == node_id)
        base_path = path[:index] if path[index].role == "user" else path[: index + 1]
        engine, detector = services.engine(), services.skills()
        paths: list[WhatIfPath] = []
        for strategy, first, follow_up in CANDIDATES:
            history = list(base_path)
            state = history[-1].state_after
            series = [state.trust]
            new_nodes: list[Node] = []
            first_score = 0.0
            for turn_text in (first, follow_up):
                events = detector.predict(turn_text, friend_context(history))
                if not new_nodes:
                    first_score = max(events.get(SkillLabel.ASKED_DIRECTLY, 0.0), 0.0)
                state = engine.update(state, events, scenario)
                user = Node(
                    id=new_id("w"),
                    parent_id=history[-1].id,
                    role="user",
                    bubbles=[turn_text],
                    events=events,
                    state_after=state,
                )
                out = engine.generate(scenario, state, [*history, user], turn_text, events, "en")
                friend = Node(
                    id=new_id("w"),
                    parent_id=user.id,
                    role="friend",
                    bubbles=out.bubbles,
                    state_after=state,
                    line_id=out.line_id,
                    reaction=out.reaction,
                )
                history += [user, friend]
                new_nodes += [user, friend]
                series.append(state.trust)
            value = (
                state.trust
                + 10 * (state.level - base_path[-1].state_after.level)
                + (15 if state.status == "ended_success" else 0)
            )
            paths.append(
                WhatIfPath(
                    candidate_text=first,
                    strategy=strategy,
                    critic_score=first_score,
                    nodes=new_nodes,
                    trust_series=series,
                    value=value,
                )
            )
        best = max(range(len(paths)), key=lambda i: paths[i].value)
        return WhatIfResult(from_node_id=node_id, paths=paths, best_index=best)


def get_service() -> StubWhatIf:
    return StubWhatIf()
