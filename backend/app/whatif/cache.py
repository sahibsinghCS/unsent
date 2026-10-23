"""Per-text embedding cache used while "what if" runs.

A rollout asks the skill detector (and the Guardian's classifier) about the same ~40 exemplar replies at
every look-ahead step, and both re-embed every text on every call. While a simulation runs, the shared
embedder is wrapped so each distinct text is embedded once, on its own (so the vector never depends on
which batch it arrived in), and reused afterwards. The wrapper is removed again when the simulation ends.
The hash embedder (tests/CI) is already fast and is never wrapped.
"""

from __future__ import annotations

import threading
from collections import OrderedDict
from collections.abc import Iterator
from contextlib import contextmanager

import numpy as np

from backend.app import embed

MAX_TEXTS = 20_000
_vectors: OrderedDict[tuple[str, str], np.ndarray] = OrderedDict()
_vectors_lock = threading.Lock()
_simulate_lock = threading.RLock()  # one simulation swaps the embedder at a time


class CachedEmbedder:
    """Same name and vectors as the wrapped embedder, one embedding per distinct text."""

    def __init__(self, inner: embed.Embedder) -> None:
        self.inner = inner
        self.name = inner.name

    def embed(self, texts: list[str]) -> np.ndarray:
        texts = list(texts)
        if not texts:
            return self.inner.embed([])
        return np.stack([self.vector(text) for text in texts])

    def vector(self, text: str) -> np.ndarray:
        key = (self.name, text)
        with _vectors_lock:
            hit = _vectors.get(key)
            if hit is not None:
                _vectors.move_to_end(key)
                return hit
        vector = self.inner.embed([text])[0]
        with _vectors_lock:
            _vectors[key] = vector
            while len(_vectors) > MAX_TEXTS:
                _vectors.popitem(last=False)
        return vector


@contextmanager
def cached_embeddings() -> Iterator[None]:
    """Wrap the shared embedder with the per-text cache for the duration of the block."""
    with _simulate_lock:
        inner = embed.get_embedder()
        if isinstance(inner, embed.HashEmbedder | CachedEmbedder):
            yield
            return
        wrapper = CachedEmbedder(inner)
        with embed._lock:
            embed._instance = wrapper
        try:
            yield
        finally:
            with embed._lock:
                if embed._instance is wrapper:
                    embed._instance = inner


def warm(texts: list[str]) -> None:
    """Embed texts ahead of time (e.g. a scenario's exemplars at startup)."""
    with cached_embeddings():
        embed.embed(texts)
