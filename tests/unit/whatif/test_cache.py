"""The per-text embedding cache: same vectors, each text embedded once, removed after the block."""

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


def test_cache_reuses_vectors_and_restores_the_embedder(monkeypatch):
    fake = CountingEmbedder()
    monkeypatch.setattr(embed, "_instance", fake)
    texts = ["that sounds really hard", "are you ok?", "that sounds really hard"]
    with cache.cached_embeddings():
        assert isinstance(embed.get_embedder(), cache.CachedEmbedder)
        first = embed.embed(texts)
        second = embed.embed(texts[:2])
    assert embed.get_embedder() is fake
    assert sorted(fake.calls) == sorted(set(texts))  # each distinct text embedded once
    assert np.allclose(first, fake.inner.embed(texts))
    assert np.allclose(second, first[:2])


def test_hash_embedder_is_never_wrapped():
    with cache.cached_embeddings():
        assert isinstance(embed.get_embedder(), embed.HashEmbedder)
