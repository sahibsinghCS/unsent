"""Embedding cache: per-request scope only, and nothing derived from a conversation outlives the session TTL."""

from __future__ import annotations

import threading

import numpy as np
import pytest

from backend.app import embed, llm
from backend.app.session import sweep_derived_caches


@pytest.fixture(autouse=True)
def _fresh():
    embed.reset_embedder()
    yield
    embed.reset_embedder()


class CountingEmbedder:
    name = "counting"

    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def embed(self, texts: list[str]) -> np.ndarray:
        self.calls.append(list(texts))
        return np.ones((len(texts), 4), dtype=np.float32) / 2.0


@pytest.fixture
def counting(monkeypatch):
    inner = CountingEmbedder()
    monkeypatch.setattr(embed, "get_embedder", lambda: inner)
    return inner


def test_scope_reuses_vectors_only_inside_the_block(counting):
    with embed.cached_scope():
        embed.embed(["a", "b"])
        embed.embed(["a", "b", "c"])
    assert sorted(t for call in counting.calls for t in call) == ["a", "b", "c"]
    counting.calls.clear()
    embed.embed(["a", "b"])  # outside the scope: a normal batched call
    assert counting.calls == [["a", "b"]]


def test_scope_does_not_leak_to_other_threads(counting):
    entered, release = threading.Event(), threading.Event()
    seen: list[list[str]] = []

    def other_request() -> None:
        entered.wait()
        before = len(counting.calls)
        embed.embed(["x", "y"])
        seen.extend(counting.calls[before:])
        release.set()

    worker = threading.Thread(target=other_request)
    worker.start()
    with embed.cached_scope():
        entered.set()
        release.wait(5)
    worker.join(5)
    assert seen == [["x", "y"]], "another request inside a what-if run must embed normally"


def test_cached_vectors_expire_with_the_session_ttl(counting, monkeypatch):
    embed.embed_one("hello")
    assert embed.purge_expired() == 0
    monkeypatch.setenv("FR_SESSION_TTL_MIN", "0")
    assert embed.purge_expired() == 1
    counting.calls.clear()
    embed.embed_one("hello")
    assert counting.calls == [["hello"]], "an expired entry is never reused"


def test_session_purge_sweeps_conversation_caches(counting, monkeypatch):
    embed.embed_one("a message")
    llm._memory_cache["k"] = (0.0, {"bubbles": ["hi"]})  # an old production cache entry
    monkeypatch.setenv("FR_SESSION_TTL_MIN", "0")
    sweep_derived_caches(force=True)
    assert embed.purge_expired() == 0 and "k" not in llm._memory_cache
    llm._memory_cache.clear()
