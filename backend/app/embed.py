"""Shared local text embeddings (free, offline after the first download).

- FastEmbedder: ONNX multilingual sentence model via fastembed (no PyTorch, small enough for free hosting).
- HashEmbedder: deterministic character-n-gram hashing; used by tests and CI (FR_EMBED=hash).

All vectors are L2-normalised, so cosine similarity is a dot product.
"""

from __future__ import annotations

import hashlib
import threading
from functools import lru_cache
from typing import Protocol

import numpy as np

from backend.app.config import embed_backend, embed_model_name

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
    return get_embedder().embed(list(texts))


@lru_cache(maxsize=8192)
def _embed_one_cached(text: str) -> tuple[float, ...]:
    return tuple(get_embedder().embed([text])[0].tolist())


def embed_one(text: str) -> np.ndarray:
    """Embed a single text (cached)."""
    return np.array(_embed_one_cached(text), dtype=np.float32)


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity of two normalised vectors."""
    return float(np.dot(a, b))


def reset_embedder() -> None:
    """Drop the singleton and cache (tests switch backends with this)."""
    global _instance
    with _lock:
        _instance = None
    _embed_one_cached.cache_clear()
