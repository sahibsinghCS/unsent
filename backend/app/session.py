"""Conversation sessions stored as a tree of nodes, which is what makes rewind and branching possible.

Privacy: sessions live only in server memory and are deleted after FR_SESSION_TTL_MIN minutes
without activity. Nothing is written to disk.
"""

from __future__ import annotations

import threading
import time
import uuid
from collections.abc import Callable

from backend.app.config import session_ttl_seconds
from backend.app.contracts import Node, Session, State


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def create_session(scenario_id: str, locale: str, country: str, opening: Node) -> Session:
    """New session whose root is the friend's opening message."""
    return Session(
        id=new_id("s"),
        scenario_id=scenario_id,
        locale=locale,
        country=country,
        nodes={opening.id: opening},
        root_id=opening.id,
        head_id=opening.id,
    )


def add_node(session: Session, node: Node) -> None:
    """Attach a node and move the head to it."""
    session.nodes[node.id] = node
    session.head_id = node.id


def path_to(session: Session, node_id: str | None = None) -> list[Node]:
    """Nodes from the root down to node_id (default: the current head)."""
    current = session.nodes[node_id or session.head_id]
    path = [current]
    while current.parent_id is not None:
        current = session.nodes[current.parent_id]
        path.append(current)
    path.reverse()
    return path


def head_state(session: Session) -> State:
    return session.nodes[session.head_id].state_after


def rewind(session: Session, node_id: str) -> State:
    """Move the head back to node_id; the next message starts a new branch from there."""
    if node_id not in session.nodes:
        raise KeyError(node_id)
    session.head_id = node_id
    return session.nodes[node_id].state_after


_SWEEP_EVERY_S = 30.0
_last_sweep = 0.0
_sweepers: list[Callable[[], object]] = []


def register_sweeper(purge: Callable[[], object]) -> None:
    """Register a cache's purge function. Any component that keeps text derived from conversations in
    memory (embeddings, explanations, ...) must drop entries older than the session TTL when it runs."""
    if purge not in _sweepers:
        _sweepers.append(purge)


def sweep_derived_caches(force: bool = False) -> None:
    """Expire everything derived from conversations together with the sessions: cached text embeddings,
    the in-memory LLM cache and every registered cache (each keeps entries at most one session TTL)."""
    global _last_sweep
    now = time.time()
    if not force and now - _last_sweep < _SWEEP_EVERY_S:
        return
    _last_sweep = now
    from backend.app import embed, llm  # local import: both are light, and this avoids cycles

    embed.purge_expired()
    llm.purge_expired()
    for purge in list(_sweepers):
        purge()


class SessionStore:
    """Thread-safe in-memory store with inactivity expiry."""

    def __init__(self, ttl_seconds: int | None = None) -> None:
        self._ttl = ttl_seconds
        self._items: dict[str, tuple[Session, float]] = {}
        self._turn_locks: dict[str, threading.Lock] = {}
        self._lock = threading.Lock()

    @property
    def ttl(self) -> int:
        return self._ttl if self._ttl is not None else session_ttl_seconds()

    def put(self, session: Session) -> None:
        with self._lock:
            self._items[session.id] = (session, time.time())
            self._turn_locks.setdefault(session.id, threading.Lock())

    def turn_lock(self, session_id: str) -> threading.Lock:
        """One lock per session: rewinding, checking the status and running a turn happen together,
        so two requests for the same chat (a double-click, two tabs) can't interleave."""
        with self._lock:
            return self._turn_locks.setdefault(session_id, threading.Lock())

    def get(self, session_id: str) -> Session | None:
        self.purge()
        with self._lock:
            item = self._items.get(session_id)
            if item is None:
                return None
            self._items[session_id] = (item[0], time.time())
            return item[0]

    def purge(self) -> int:
        """Delete expired sessions; returns how many were removed."""
        cutoff = time.time() - self.ttl
        with self._lock:
            expired = [sid for sid, (_, seen) in self._items.items() if seen < cutoff]
            for sid in expired:
                del self._items[sid]
                self._turn_locks.pop(sid, None)
        sweep_derived_caches()
        return len(expired)

    def __len__(self) -> int:
        with self._lock:
            return len(self._items)


store = SessionStore()
