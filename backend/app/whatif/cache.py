"""Per-text embedding reuse while "what if" runs.

A rollout asks the skill detector (and the Guardian's classifier) about the same ~40 exemplar replies at
every look-ahead step, and both re-embed every text on every call. `embed.cached_scope()` makes embed()
reuse one vector per distinct text for this request only (other requests are unaffected), and its cache
expires with the session TTL like everything else that holds conversation text.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from backend.app import content, embed


@contextmanager
def cached_embeddings() -> Iterator[None]:
    """Reuse per-text vectors inside this block (this request's context only)."""
    with embed.cached_scope():
        yield


def warm(texts: list[str]) -> None:
    """Embed texts ahead of time so the first "what if" click doesn't pay for them."""
    with cached_embeddings():
        embed.embed(list(texts))


def warm_up() -> None:
    """Warm every scenario's exemplars in every language it supports (call once at startup)."""
    for scenario in content.load_scenarios().values():
        for locale in content.scenario_locales(scenario):
            texts = [ex.text for ex in content.load_exemplars(scenario.id, locale)]
            if texts:
                warm(texts)
