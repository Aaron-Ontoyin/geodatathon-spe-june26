"""FastAPI backend for the demo app.

The app is exposed as ``geothermal.api:app`` for ``uvicorn``.

If the frontend has been built (``frontend/dist``), it is served from the same app so
one ``uvicorn`` process hosts both the API and the UI. Set ``GEO_FRONTEND_DIST`` to
point at a build in a non-default location.
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from geothermal.api.routes import router


def _frontend_dist() -> Path | None:
    """Locate the built frontend, returning None if it has not been built yet."""
    override = os.environ.get("GEO_FRONTEND_DIST")
    dist = Path(override) if override else Path(__file__).resolve().parents[3] / "frontend" / "dist"
    return dist if (dist / "index.html").is_file() else None


def create_app() -> FastAPI:
    """Build the FastAPI app with CORS open (demo), all routes, and the built UI if present."""
    app = FastAPI(title="Geothermal Datathon API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)

    if (dist := _frontend_dist()) is not None:
        app.mount("/", StaticFiles(directory=dist, html=True), name="frontend")
    return app


app = create_app()

__all__ = ["app", "create_app"]
