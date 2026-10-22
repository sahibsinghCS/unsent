"""Shared test setup: offline hash embeddings and a fresh component registry for every test."""

from __future__ import annotations

import os

os.environ.setdefault("FR_EMBED", "hash")

import pytest  # noqa: E402

from backend.app import services  # noqa: E402
from backend.app.embed import reset_embedder  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_registry(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("FR_EMBED", "hash")
    services.reset()
    reset_embedder()
    yield
    services.reset()


@pytest.fixture
def stub_mode(monkeypatch: pytest.MonkeyPatch):
    """Force every component to its stub."""
    monkeypatch.setenv("FR_STUB", "1")
    services.reset()
