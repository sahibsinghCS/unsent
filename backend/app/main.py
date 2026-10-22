"""FastAPI application: the API under /api, plus the built frontend (frontend/dist) at /.

Run locally:  make dev        (real components where implemented)
              make dev-stub   (everything stubbed; for frontend work)
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.app import ops
from backend.app.api.routes import router
from backend.app.config import FRONTEND_DIST
from backend.app.contracts import CONTRACTS_VERSION

app = FastAPI(
    title="FirstReply API",
    version=CONTRACTS_VERSION,
    description="Practice the text that could save a friend. Runs fully locally; no paid AI services.",
)
app.include_router(router, prefix="/api")
ops.install(app)

if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
