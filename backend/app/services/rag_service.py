"""RAG orchestration service for the HTTP API."""

from __future__ import annotations

from functools import lru_cache
import logging

from src.retrieval.answering import AnswerResult, answer_query
from src.retrieval.retriever import ChromaRetriever
from src.retrieval.qdrant_retriever import QdrantRetriever
from src.utils.env import getenv

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_retriever():
    """Return a cached retriever instance.

    The app now defaults to the fully local retriever. Qdrant remains opt-in
    for deployments that explicitly set ``RETRIEVAL_BACKEND=qdrant``.
    """
    backend = (getenv("RETRIEVAL_BACKEND") or "local").strip().lower()
    if backend == "qdrant":
        qdrant_url = (getenv("QDRANT_URL") or "").strip()
        qdrant_api_key = (getenv("QDRANT_API_KEY") or "").strip()
        if qdrant_url and qdrant_api_key:
            collection = (getenv("QDRANT_COLLECTION") or "vite_docs").strip()
            try:
                return QdrantRetriever(collection_name=collection)
            except Exception as exc:  # pragma: no cover - optional dependency path
                logger.warning("Qdrant is configured but unavailable; falling back to local retriever: %s", exc)

    return ChromaRetriever()


def ask_rag(query: str) -> AnswerResult:
    """Run the full RAG pipeline for a single query."""
    retriever = get_retriever()
    logger.info("api query=%s", query)
    return answer_query(retriever, query)
