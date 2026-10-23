"""Background purge of expired sessions.

The session store already drops expired sessions whenever someone reads a session, but on a quiet
server nobody reads, so old conversations would sit in memory. This thread purges once a minute.
"""

from __future__ import annotations

import logging
import threading

from backend.app.session import SessionStore

log = logging.getLogger("firstreply.ops")


class Purger:
    """Daemon thread calling store.purge() every `interval` seconds. start() is idempotent."""

    def __init__(self, store: SessionStore, interval: float = 60.0) -> None:
        self.store = store
        self.interval = interval
        self.removed = 0
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def run_once(self) -> int:
        removed = self.store.purge()
        self.removed += removed
        return removed

    def _loop(self) -> None:
        while not self._stop.wait(self.interval):
            try:
                self.run_once()
            except Exception:  # never let the purge thread die silently
                log.exception("session purge failed")

    def start(self) -> None:
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._stop.clear()
            self._thread = threading.Thread(target=self._loop, name="session-purge", daemon=True)
            self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2)

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()
