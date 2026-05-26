"""FastAPI application for the RAG backend."""

from __future__ import annotations

import logging
from time import perf_counter

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.app.schemas import AskRequest, AskResponse, ErrorResponse
from backend.app.services.rag_service import ask_rag
from src.utils.app_logging import configure_logging
from src.utils.env import getenv

configure_logging(log_file="api.log")
logger = logging.getLogger(__name__)

app = FastAPI(title="Semantic Docs RAG API", version="2.0.0")

raw_origins = (getenv("CORS_ALLOW_ORIGINS") or "").strip()
extra_origins = [item.strip() for item in raw_origins.split(",") if item.strip()] if raw_origins else []
allow_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://local-rag-engine.vercel.app",
    *extra_origins,
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=dict)
def health() -> dict[str, str]:
    """Simple health check."""
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse, responses={500: {"model": ErrorResponse}})
def ask(request: AskRequest) -> AskResponse:
    """Accept a query and return a grounded answer."""
    started = perf_counter()
    try:
        result = ask_rag(request.query)
    except Exception as exc:  # pragma: no cover - service failure path
        logger.exception("ask endpoint failed")
        raise HTTPException(status_code=500, detail="Failed to process query.") from exc

    elapsed_ms = (perf_counter() - started) * 1000.0
    logger.info(
        "api completed query=%s confidence=%.4f latency_ms=%.2f answer_length=%s",
        request.query,
        result.confidence,
        elapsed_ms,
        len(result.answer),
    )
    return AskResponse(
        query=request.query,
        answer=result.answer,
        confidence=result.confidence,
        sources=result.sources,
        model=result.model,
        latency_ms=result.latency_ms or elapsed_ms,
        found=result.found,
        title=result.title,
        url=result.url,
        finish_reason=result.finish_reason,
        response_length=result.response_length,
    )
