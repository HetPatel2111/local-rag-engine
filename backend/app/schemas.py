"""API request and response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    """Incoming user query."""

    query: str = Field(min_length=1, max_length=2000)


class AskResponse(BaseModel):
    """Response returned by the RAG backend."""

    query: str
    answer: str
    confidence: float
    sources: list[str]
    model: str
    latency_ms: float
    found: bool
    title: str = ""
    url: str = ""
    finish_reason: str = ""
    response_length: int = 0


class ErrorResponse(BaseModel):
    """Standard error response body."""

    detail: str

