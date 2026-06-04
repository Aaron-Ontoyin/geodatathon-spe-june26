"""API-specific request/response schemas (the pipeline's own models are reused elsewhere)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """A grounded chat turn: the question, prior turns, and the report to ground on."""

    question: str
    history: list[tuple[str, str]] = Field(default_factory=list)
    context: str = Field(default="", description="The report markdown to ground answers in.")
    api_key: str | None = None
