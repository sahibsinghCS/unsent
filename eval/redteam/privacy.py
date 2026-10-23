"""I8: nothing remembers your words after the session expires.

A full conversation (messages, finish, what-if, rewind) goes through the HTTP app with a unique marker word
in the helper's messages. Then every session is expired (FR_SESSION_TTL_MIN=0, store.purge()), every
registered derived-text cache is swept (session.sweep_derived_caches(force=True)), the garbage collector
runs, and we search every live Python container (dicts incl. keys, lists, tuples, sets, deques, numpy object
arrays, and lru_cache tables, which are dicts) for any string or bytes holding the marker. Expect 0.

Run: uv run python -m eval.redteam.privacy [--embed hash|fastembed]
"""

from __future__ import annotations

import argparse
import gc
import os
from collections import deque

from eval.redteam import common

# Built from parts at run time, so no code constant or test local holds the whole word.
MARKER_PARTS = ("quor", "bellix", "ten")


def marker() -> str:
    return "".join(MARKER_PARTS) + str(common.SEED % 97)


def helper_script(word: str) -> list[str]:
    """Strong helper turns that carry the marker (each passes the Guardian, so the pipeline runs fully)."""
    return [
        f"hey, are you ok? you seemed off at lunch, {word} is what i call bad days",
        f"that sounds really heavy. {word} days are the worst",
        f"lol you'll be fine {word}",
        "are you thinking about killing yourself?",
        f"i'm really glad you told me. can we talk to the counselor tomorrow? {word}",
    ]


def converse(word: str) -> None:
    """One full conversation through the HTTP API. Keeps nothing: every response is dropped here."""
    from fastapi.testclient import TestClient

    from backend.app.main import app

    with TestClient(app) as client:
        view = client.post("/api/sessions", json={"scenario_id": "after-the-breakup"}).json()
        sid = view["session_id"]
        anchor = None
        for text in helper_script(word):
            response = client.post(f"/api/sessions/{sid}/messages", json={"text": text})
            if response.status_code != 200:
                break
            anchor = anchor or response.json()["user_node"]["parent_id"]
        client.post(f"/api/sessions/{sid}/finish")
        client.post(f"/api/sessions/{sid}/whatif", json={})
        if anchor:
            client.post(f"/api/sessions/{sid}/rewind", json={"node_id": anchor})
            client.post(f"/api/sessions/{sid}/messages", json={"text": f"sorry, {word}, i'm here"})
        client.post("/api/guardian/check", json={"text": f"is {word} ok to say"})
        del response, view


def expire_everything() -> None:
    from backend.app import session

    old = os.environ.get("FR_SESSION_TTL_MIN")
    os.environ["FR_SESSION_TTL_MIN"] = "0"
    try:
        session.store.purge()
        session.sweep_derived_caches(force=True)
    finally:
        if old is None:
            os.environ.pop("FR_SESSION_TTL_MIN", None)
        else:
            os.environ["FR_SESSION_TTL_MIN"] = old
    gc.collect()


def _items(obj) -> list:
    if isinstance(obj, dict):
        return [*obj.keys(), *obj.values()]
    if isinstance(obj, list | tuple | set | frozenset | deque):
        return list(obj)
    try:
        import numpy as np

        if isinstance(obj, np.ndarray) and obj.dtype == object:
            return obj.ravel().tolist()
    except ImportError:
        pass
    return []


def find(word: str) -> list[str]:
    """Where the marker still lives: one '<container type> ...' line per hit."""
    needle, raw = word, word.encode()
    hits = []
    for obj in gc.get_objects():
        for item in _items(obj):
            text = item if isinstance(item, str) else None
            if text is None and isinstance(item, bytes | bytearray) and raw in item:
                text = item.decode("utf-8", "replace")
            if text is not None and needle in text:
                where = type(obj).__name__
                if isinstance(obj, dict):
                    where += f" keys={[k for k in list(obj)[:4] if isinstance(k, str)]}"
                hits.append(f"{where}: {text[:80]!r}")
                break
    return hits


def check() -> tuple[list[str], int]:
    """(leaks, checks): run the conversation, expire everything, scan memory."""
    word = marker()
    converse(word)
    expire_everything()
    leaks = find(word)
    return leaks, 1  # one end-to-end conversation


def run(embed: str = "auto") -> dict:
    embed = common.configure(embed)
    leaks, n = check()
    records = [
        common.record(
            "invariants.I8.violations",
            len(leaks),
            n,
            "full conversation incl. finish, what-if, rewind",
            "places in memory still holding the helper's words after every session expired and "
            "every derived cache was swept; must be 0",
        )
    ]
    common.write_report("privacy", records, embed, {"embed": embed, "leaks": leaks})
    return {"records": records, "leaks": leaks}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--embed", default="auto", choices=["auto", "hash", "fastembed"])
    out = run(parser.parse_args().embed)
    print(f"I8 leaks: {len(out['leaks'])}")
    for leak in out["leaks"]:
        print("  ", leak)


if __name__ == "__main__":
    main()
