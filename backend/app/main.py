"""FastAPI application: the API under /api, plus the built frontend (frontend/dist) at /.

Run locally:  make dev        (real components where implemented)
              make dev-stub   (everything stubbed; for frontend work)
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response
from starlette.types import Scope

from backend.app import ops
from backend.app.api.routes import router
from backend.app.config import FRONTEND_DIST
from backend.app.contracts import CONTRACTS_VERSION


class SPAStaticFiles(StaticFiles):
    """Serve the single-page app: unknown non-API paths return index.html with status 200,
    so deep links like /chat/abc or /feedback/abc load the app instead of a 404 page."""

    async def get_response(self, path: str, scope: Scope) -> Response:
        is_api = path == "api" or path.startswith("api/")
        try:
            response = await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if exc.status_code == 404 and not is_api:
                return await super().get_response("index.html", scope)
            raise
        if response.status_code == 404 and not is_api:
            return await super().get_response("index.html", scope)
        return response


def mount_frontend(app: FastAPI, directory: Path) -> None:
    """Mount the built frontend at / (after the API routes, so /api/* always wins)."""
    app.mount("/", SPAStaticFiles(directory=directory, html=True), name="frontend")


app = FastAPI(
    title="FirstReply API",
    version=CONTRACTS_VERSION,
    description=(
        "Practice the text that could save a friend. OpenAI writes the friend's wording; "
        "our engine, verifier, Guardian and trained models make every decision."
    ),
)
app.include_router(router, prefix="/api")
ops.install(app)

if FRONTEND_DIST.exists():
    mount_frontend(app, FRONTEND_DIST)
