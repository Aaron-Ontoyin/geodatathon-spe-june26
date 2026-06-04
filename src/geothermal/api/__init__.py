"""FastAPI backend for the demo app.

Split into focused modules: ``routes`` (handlers), ``schemas`` (API request models),
``serialization`` (domain → JSON payloads), ``streaming`` (SSE bridges). The app is
exposed as ``geothermal.api:app`` for ``uvicorn``.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from geothermal.api.routes import router


def create_app() -> FastAPI:
    """Build the FastAPI app with CORS open (demo) and all routes mounted."""
    app = FastAPI(title="Geothermal Datathon API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    return app


app = create_app()

__all__ = ["app", "create_app"]
