"""Red-team regression suite setup: offline bank voice, no LLM fakes left over from other tests."""

from __future__ import annotations

import pytest

from backend.app import llm


@pytest.fixture(autouse=True)
def _offline(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("FR_LLM", "0")
    monkeypatch.setenv("FR_GUARDIAN_MODERATION", "0")
    llm.clear_fakes()
    yield
    llm.clear_fakes()
