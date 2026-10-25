"""Operational hardening for the public demo: rate limits, security headers, session purge,
startup warm-up. Owned by the DEPLOY lane.

install(app) adds one middleware (see middleware.py) and on_startup() (called by main.warm_up after
the models are loaded) starts the session purge and logs one readiness line.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time

from fastapi import FastAPI

from backend.app.config import FRONTEND_DIST, env_int, is_prod
from backend.app.ops.headers import app_csp, docs_csp, inline_script_hashes
from backend.app.ops.middleware import OpsMiddleware
from backend.app.ops.purge import Purger
from backend.app.ops.ratelimit import RateLimiter, proxy_hops, rate_limit_enabled, trust_proxy
from backend.app.session import store

IMPLEMENTED = True

PROCESS_STARTED = time.time()
log = logging.getLogger("unsent.ops")
purger = Purger(store, interval=float(env_int("FR_PURGE_INTERVAL_S", 60)))


def max_body_bytes() -> int:
    return env_int("FR_MAX_BODY_BYTES", 32 * 1024)


def max_upload_bytes() -> int:
    """Screenshot uploads (base64): up to 3 images of about 1.5 MB each."""
    return env_int("FR_MAX_UPLOAD_BYTES", 6 * 1024 * 1024)


def _configure_logging() -> None:
    """Plain JSON lines on stdout for our loggers (Hugging Face shows stdout in its Logs tab)."""
    root = logging.getLogger("unsent")
    if any(getattr(h, "_fr_ops", False) for h in root.handlers):
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    handler._fr_ops = True  # type: ignore[attr-defined]
    root.addHandler(handler)
    root.setLevel(logging.INFO)


def install(app: FastAPI) -> None:
    """Attach the ops middleware (rate limits, body limit, security headers, request log)."""
    _configure_logging()
    limiter = RateLimiter() if rate_limit_enabled() else None
    app.state.rate_limiter = limiter
    app.add_middleware(
        OpsMiddleware,
        limiter=limiter,
        max_body_bytes=max_body_bytes(),
        app_csp=app_csp(inline_script_hashes(FRONTEND_DIST / "index.html")),
        docs_csp=docs_csp(),
        trust_proxy=trust_proxy(),
        proxy_hops=proxy_hops(),
        upload_paths={"/api/friends/analyze": max_upload_bytes()},
    )


def on_startup() -> None:
    """Start the session purge and log readiness with every component's status (no secrets)."""
    from backend.app import embed, llm, services

    purger.start()
    llm_status = llm.status()
    entry = {
        "evt": "ready",
        "env": "prod" if is_prod() else "dev",
        "startup_s": round(time.time() - PROCESS_STARTED, 2),
        "components": services.status(),
        "embedder": embed.get_embedder().name,
        "llm_enabled": bool(llm_status.get("enabled")),
        "llm_has_key": bool(llm_status.get("has_key")),
        "rate_limits": rate_limit_enabled(),
        "trust_proxy": trust_proxy(),
        "frontend": (FRONTEND_DIST / "index.html").is_file(),
        "session_ttl_min": env_int("FR_SESSION_TTL_MIN", 60),
        "pid": os.getpid(),
    }
    _configure_logging()
    log.info(json.dumps(entry))
