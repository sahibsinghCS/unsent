"""Turning points and missed opportunities in a conversation (ENGINE lane). See docs/how/engine.md.

Both read only the conversation path (the nodes from the start to the current message): each helper
node carries the detected labels (`events`) and the state after it, including `last_delta`.
"""

from __future__ import annotations

from collections.abc import Sequence

from backend.app.contracts import Node, SkillLabel, TurningPoint
from backend.app.engine.state import REFERRAL_LABELS, active_labels, default_config

# Why trust dropped, in words a teen understands (first matching label wins).
DROP_REASONS: tuple[tuple[SkillLabel, str], ...] = (
    (SkillLabel.DISMISSED, "a dismissive reply"),
    (SkillLabel.PROMISED_SECRECY, "promising to keep it a secret"),
    (SkillLabel.ADVICE_DUMP, "jumping straight to advice"),
)


def _helper_nodes(path: Sequence[Node]) -> list[Node]:
    """Helper messages that the engine actually scored (blocked / crisis messages have no events)."""
    return [node for node in path if node.role == "user" and node.events is not None]


def _active(node: Node) -> frozenset[SkillLabel]:
    return active_labels(node.events or {}, default_config().event_threshold)


def drop_reason(node: Node, before_flags_secret: bool) -> str:
    """Plain-language reason for a trust drop at this helper message."""
    active = _active(node)
    drop = -node.state_after.last_delta
    amount = f"{drop:g}" if drop == int(drop) else f"{drop:.1f}"
    for label, words in DROP_REASONS:
        if label in active:
            return f"Trust dropped {amount} after {words}."
    if before_flags_secret and active & REFERRAL_LABELS:
        return (
            f"Trust dropped {amount} because you broke a promise to keep it secret. Getting help was "
            "still the right call; the real mistake was promising secrecy earlier."
        )
    return f"Trust dropped {amount} after a reply that didn't really engage with what they said."


def turning_point(path: Sequence[Node]) -> TurningPoint | None:
    """The helper message with the most negative last_delta (earliest wins ties).

    Only drops of at least `turning_point_min_drop` (5) count: a dip from decay or diminishing returns
    isn't a mistake, so a good conversation gets None (and the critic praises instead).
    """
    worst: tuple[Node, bool] | None = None
    secret = False
    for node in _helper_nodes(path):
        delta = node.state_after.last_delta
        big_enough = delta <= -default_config().turning_point_min_drop
        if big_enough and (worst is None or delta < worst[0].state_after.last_delta):
            worst = (node, secret)
        secret = node.state_after.flags.promised_secrecy
    if worst is None:
        return None
    node, was_secret = worst
    return TurningPoint(
        node_id=node.id,
        trust_drop=round(-node.state_after.last_delta, 4),
        reason=drop_reason(node, was_secret),
    )


def missed_opportunities(path: Sequence[Node], friend_name: str = "your friend") -> list[str]:
    """Moments where a better move was available, each naming the turn:
    - the friend reached level 2 (hopeless) and the next reply didn't ask directly about suicide;
    - the friend disclosed suicidal thoughts (level 3) and no referral followed within 2 turns;
    - a promise to keep it secret;
    - the friend left the helper on Seen.
    """
    missed: list[tuple[int, str]] = []
    helpers = _helper_nodes(path)
    by_id = {node.id: node for node in path}
    asked_before = False
    flagged_ask = flagged_refer = False

    for i, node in enumerate(helpers):
        state, active = node.state_after, _active(node)
        nxt = helpers[i + 1] if i + 1 < len(helpers) else None
        asked_before |= SkillLabel.ASKED_DIRECTLY in active
        if (
            not flagged_ask
            and not asked_before
            and state.level >= 2
            and nxt is not None
            and SkillLabel.ASKED_DIRECTLY not in _active(nxt)
        ):
            missed.append(
                (
                    nxt.state_after.turn,
                    f"Turn {nxt.state_after.turn}: {friend_name} was sounding hopeless. That was the moment "
                    'to ask directly: "are you thinking about suicide?"',
                )
            )
            flagged_ask = True

        reached_3 = state.level >= 3 and (i == 0 or helpers[i - 1].state_after.level < 3)
        if reached_3 and not flagged_refer:
            window = helpers[i : i + 3]  # this reply and the next two
            if not any(_active(n) & REFERRAL_LABELS for n in window):
                missed.append(
                    (
                        state.turn,
                        f"Turn {state.turn}: {friend_name} told you about thoughts of suicide, but no "
                        "trusted adult or 988 came up in the next 2 replies.",
                    )
                )
                flagged_refer = True

        if SkillLabel.PROMISED_SECRECY in active:
            missed.append(
                (
                    state.turn,
                    f"Turn {state.turn}: you promised to keep it secret. Never promise secrecy about "
                    "suicide; say you care too much to keep this to yourself.",
                )
            )

    for node in path:
        if node.role == "friend" and node.seen_no_reply and node.parent_id in by_id:
            parent = by_id[node.parent_id]
            turn = parent.state_after.turn
            missed.append(
                (turn, f"Turn {turn}: {friend_name} left you on Seen after this message.")
            )
    return [text for _, text in sorted(missed, key=lambda item: item[0])]
