"""Shared local text embeddings (free, offline after the first download).

- FastEmbedder: ONNX multilingual sentence model via fastembed (no PyTorch, small enough for free hosting).
- HashEmbedder: deterministic character-n-gram hashing; used by tests and CI (FR_EMBED=hash).

All vectors are L2-normalised, so cosine similarity is a dot product.

Privacy: embeddings of conversation text are cached in memory only, and every entry expires with the
session TTL (60 min), like the sessions themselves; `purge_expired()` runs with the session purge.
`cached_scope()` lets one request (e.g. "what if", which re-scores the same replies many times) reuse
vectors without changing how any other request is embedded.
"""

from __future__ import annotations

import hashlib
import threading
import time
from collections import OrderedDict
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Protocol

import numpy as np

from backend.app.config import embed_backend, embed_model_name, session_ttl_seconds

HASH_DIM = 512


class Embedder(Protocol):
    name: str

    def embed(self, texts: list[str]) -> np.ndarray: ...


def _normalise(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return (vectors / norms).astype(np.float32)


class HashEmbedder:
    """Signed hashing of character 3-5 grams into 512 dims. Fast, dependency-free, deterministic."""

    name = "hash-char-ngrams-512"

    def embed(self, texts: list[str]) -> np.ndarray:
        out = np.zeros((len(texts), HASH_DIM), dtype=np.float32)
        for row, text in enumerate(texts):
            padded = f" {text.lower()} "
            for n in (3, 4, 5):
                for i in range(len(padded) - n + 1):
                    digest = hashlib.blake2b(padded[i : i + n].encode(), digest_size=8).digest()
                    h = int.from_bytes(digest, "little")
                    out[row, h % HASH_DIM] += 1.0 if (h >> 63) & 1 else -1.0
        return _normalise(out)


class FastEmbedder:
    """Real multilingual sentence embeddings (384 dims) via fastembed / ONNX Runtime."""

    def __init__(self, model_name: str) -> None:
        from fastembed import TextEmbedding

        self.name = model_name
        self._model = TextEmbedding(model_name=model_name)

    def embed(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, 384), dtype=np.float32)
        return _normalise(np.array(list(self._model.embed(list(texts))), dtype=np.float32))


_lock = threading.Lock()
_instance: Embedder | None = None


def get_embedder() -> Embedder:
    """Process-wide singleton chosen by FR_EMBED (fastembed | hash)."""
    global _instance
    with _lock:
        if _instance is None:
            if embed_backend() == "hash":
                _instance = HashEmbedder()
            else:
                _instance = FastEmbedder(embed_model_name())
        return _instance


def embed(texts: list[str]) -> np.ndarray:
    """Embed a batch of texts -> (n, dim) normalised matrix."""
    texts = list(texts)
    if _scoped.get() and texts:
        return np.stack([_cached_vector(text) for text in texts])
    return get_embedder().embed(texts)


# ---------------------------------------------------------------- per-text cache (expires with sessions)

CACHE_MAX_TEXTS = 8192
_cache_lock = threading.Lock()
_cache: OrderedDict[tuple[str, str], tuple[float, np.ndarray]] = OrderedDict()
_scoped: ContextVar[bool] = ContextVar("firstreply_embed_cached_scope", default=False)


def _evict_locked(now: float) -> None:
    ttl = session_ttl_seconds()
    while _cache:
        stamp = next(iter(_cache.values()))[0]
        if now - stamp >= ttl or len(_cache) > CACHE_MAX_TEXTS:
            _cache.popitem(last=False)
        else:
            break


def _cached_vector(text: str) -> np.ndarray:
    """One text's vector, embedded on its own (so it never depends on batch-mates) and cached."""
    embedder = get_embedder()
    key = (embedder.name, text)
    now = time.time()
    with _cache_lock:
        item = _cache.get(key)
        if item is not None and now - item[0] < session_ttl_seconds():
            _cache[key] = (now, item[1])
            _cache.move_to_end(key)
            return item[1].copy()
    vector = embedder.embed([text])[0]
    with _cache_lock:
        _cache[key] = (now, vector)
        _cache.move_to_end(key)
        _evict_locked(now)
    return vector.copy()


def embed_one(text: str) -> np.ndarray:
    """Embed a single text (cached until the session TTL passes without it being used)."""
    return _cached_vector(text)


@contextmanager
def cached_scope() -> Iterator[None]:
    """Within this block, and only in this request's context, embed() reuses cached per-text vectors."""
    token = _scoped.set(True)
    try:
        yield
    finally:
        _scoped.reset(token)


def purge_expired() -> int:
    """Drop cached vectors unused for longer than the session TTL. Returns how many were dropped."""
    with _cache_lock:
        before = len(_cache)
        _evict_locked(time.time())
        return before - len(_cache)


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity of two normalised vectors."""
    return float(np.dot(a, b))


def reset_embedder() -> None:
    """Drop the singleton and cache (tests switch backends with this)."""
    global _instance
    with _lock:
        _instance = None
    with _cache_lock:
        _cache.clear()
