"""Operational hardening for the public demo: rate limits, security headers, session purge,
startup warm-up. Owned by the DEPLOY lane.
"""

from __future__ import annotations

from fastapi import FastAPI

IMPLEMENTED = False


def install(app: FastAPI) -> None:
    """Attach middleware and background tasks to the app. No-op until the DEPLOY lane implements it."""
    return None
