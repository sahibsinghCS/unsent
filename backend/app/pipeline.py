"""One conversation turn:
Guardian -> skill detector -> state engine -> friend line (line bank) -> verifier -> conversation tree.

The Guardian always runs first. No component here calls a paid API or the network.
"""

from __future__ import annotations

from backend.app import services
from backend.app.content import get_scenario
from backend.app.contracts import Node, Reaction, Scenario, Session, SkillProbs, State, TurnResponse
from backend.app.session import add_node, new_id, path_to

CRISIS_TEXT = (
    "Let's pause the practice for a moment. It sounds like you might be going through something hard "
    "yourself, and that matters. You can call or text 988 any time (in the US), or talk to a trusted "
    "adult today. When you're ready, you can come back."
)

BLOCK_TEXT = {
    "harm_to_other": (
        "That message could really hurt someone who is struggling. In a real conversation, stay calm, "
        "listen, and help them reach a trusted adult or 988. Try a different reply."
    ),
    "method_seeking": (
        "FirstReply never talks about ways people might hurt themselves. Try asking how they're "
        "feeling, or whether they're thinking about suicide, instead."
    ),
    "prompt_injection": "The practice friend stays in character. Try replying to what they said.",
}
BLOCK_DEFAULT = "That message can't be sent in practice mode. Try a different reply."


def friend_context(path: list[Node], limit: int = 2) -> list[str]:
    """The friend's most recent bubbles (context for the skill detector)."""
    bubbles = [bubble for node in path if node.role == "friend" for bubble in node.bubbles]
    return bubbles[-limit:]


def run_turn(session: Session, text: str) -> TurnResponse:
    """Process one helper message and append the resulting nodes to the session tree."""
    scenario = get_scenario(session.scenario_id)
    path = path_to(session)
    state_before = path[-1].state_after

    guardian = services.guardian().check_user(text, path)
    user_node = Node(
        id=new_id("n"),
        parent_id=session.head_id,
        role="user",
        bubbles=[text],
        guardian=guardian,
        state_after=state_before,
    )

    if guardian.action == "pause_roleplay":
        paused = state_before.model_copy(update={"status": "paused_crisis"})
        user_node.state_after = paused
        add_node(session, user_node)
        system = _system_node(user_node.id, CRISIS_TEXT, paused)
        add_node(session, system)
        return TurnResponse(
            user_node=user_node,
            system_node=system,
            state_before=state_before,
            state_after=paused,
            crisis=True,
        )

    if guardian.action == "block_message":
        add_node(session, user_node)
        category = guardian.categories[0] if guardian.categories else ""
        system = _system_node(user_node.id, BLOCK_TEXT.get(category, BLOCK_DEFAULT), state_before)
        add_node(session, system)
        return TurnResponse(
            user_node=user_node,
            system_node=system,
            state_before=state_before,
            state_after=state_before,
            blocked=True,
        )

    events = services.skills().predict(text, friend_context(path))
    state_after = services.engine().update(state_before, events, scenario)
    user_node.events = events
    user_node.state_after = state_after
    add_node(session, user_node)

    friend = _friend_reply(session, scenario, state_after, [*path, user_node], text, events)
    add_node(session, friend)
    return TurnResponse(
        user_node=user_node,
        friend_node=friend,
        state_before=state_before,
        state_after=state_after,
    )


def _system_node(parent_id: str, text: str, state: State) -> Node:
    return Node(
        id=new_id("n"), parent_id=parent_id, role="system", bubbles=[text], state_after=state
    )


def _friend_reply(
    session: Session,
    scenario: Scenario,
    state: State,
    history: list[Node],
    text: str,
    events: SkillProbs,
) -> Node:
    parent_id = history[-1].id
    if state.status == "silent":
        return Node(
            id=new_id("n"),
            parent_id=parent_id,
            role="friend",
            bubbles=[],
            state_after=state,
            seen_no_reply=True,
            reaction=Reaction.DISMISSED,
        )

    engine = services.engine()
    guardian = services.guardian()
    output = engine.generate(scenario, state, history, text, events, session.locale)
    verified = engine.verify(output, scenario, state).ok
    safe = all(guardian.check_friend(bubble).level == "none" for bubble in output.bubbles)
    if verified and safe and output.bubbles:
        return Node(
            id=new_id("n"),
            parent_id=parent_id,
            role="friend",
            bubbles=output.bubbles,
            state_after=state,
            line_id=output.line_id,
            reaction=output.reaction,
        )

    fallback = scenario.fallback_lines.get(state.level) or scenario.fallback_lines.get(0) or ["..."]
    return Node(
        id=new_id("n"),
        parent_id=parent_id,
        role="friend",
        bubbles=[fallback[state.turn % len(fallback)]],
        state_after=state,
        reaction=Reaction.NEUTRAL,
    )
