from __future__ import annotations

from backend.app.contracts import Node, State
from backend.app.session import SessionStore, add_node, create_session, path_to, rewind


def _node(node_id: str, parent: str | None, trust: float) -> Node:
    return Node(
        id=node_id, parent_id=parent, role="friend", bubbles=["x"], state_after=State(trust=trust)
    )


def test_path_and_rewind_create_branches():
    session = create_session("after-the-breakup", "en", "US", _node("a", None, 30))
    add_node(session, _node("b", "a", 40))
    add_node(session, _node("c", "b", 20))
    assert [n.id for n in path_to(session)] == ["a", "b", "c"]
    assert rewind(session, "b").trust == 40
    add_node(session, _node("d", "b", 55))
    assert [n.id for n in path_to(session)] == ["a", "b", "d"]
    assert set(session.nodes) == {"a", "b", "c", "d"}


def test_store_expires_sessions():
    store = SessionStore(ttl_seconds=0)
    session = create_session("after-the-breakup", "en", "US", _node("a", None, 30))
    store.put(session)
    assert store.get(session.id) is None
