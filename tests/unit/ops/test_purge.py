"""The background purge removes expired sessions even when nobody reads the store."""

from __future__ import annotations

import time

from backend.app.contracts import Node
from backend.app.ops.purge import Purger
from backend.app.session import SessionStore, create_session


def _session():
    opening = Node.model_construct(id="n_root", parent_id=None)
    return create_session("scn", "en", "US", opening)


def test_run_once_removes_only_expired():
    store = SessionStore(ttl_seconds=60)
    fresh, old = _session(), _session()
    store.put(fresh)
    store.put(old)
    store._items[old.id] = (old, time.time() - 120)  # last seen two minutes ago
    purger = Purger(store)
    assert purger.run_once() == 1
    assert len(store) == 1 and purger.removed == 1


def test_thread_purges_in_the_background_and_start_is_idempotent():
    store = SessionStore(ttl_seconds=60)
    old = _session()
    store.put(old)
    store._items[old.id] = (old, time.time() - 120)
    purger = Purger(store, interval=0.02)
    purger.start()
    first = purger._thread
    purger.start()
    assert purger._thread is first
    deadline = time.time() + 2
    while len(store) and time.time() < deadline:
        time.sleep(0.01)
    purger.stop()
    assert len(store) == 0
    assert not purger.running
