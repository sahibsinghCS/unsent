"""what-if's embedding reuse goes through embed.cached_scope(): same vectors, each text embedded once."""

from __future__ import annotations

import numpy as np

from backend.app import embed
from backend.app.whatif import cache


class CountingEmbedder:
    name = "counting-test"

    def __init__(self) -> None:
        self.calls: list[str] = []
        self.inner = embed.HashEmbedder()

    def embed(self, texts: list[str]) -> np.ndarray:
        self.calls += list(texts)
        return self.inner.embed(texts)


def test_scope_reuses_vectors_without_swapping_the_embedder(monkeypatch):
    fake = CountingEmbedder()
    monkeypatch.setattr(embed, "_instance", fake)
    texts = ["that sounds really hard", "are you ok?", "that sounds really hard"]
    with cache.cached_embeddings():
        assert embed.get_embedder() is fake  # nothing global is swapped
        first = embed.embed(texts)
        second = embed.embed(texts[:2])
    assert sorted(fake.calls) == sorted(set(texts))  # each distinct text embedded once
    assert np.allclose(first, fake.inner.embed(texts))
    assert np.allclose(second, first[:2])


def test_warm_up_runs_offline():
    cache.warm_up()
