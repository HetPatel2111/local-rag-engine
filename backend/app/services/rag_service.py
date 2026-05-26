"""RAG orchestration service for the HTTP API."""

from __future__ import annotations

from functools import lru_cache
import logging

from src.retrieval.answering import AnswerResult, answer_query
from src.retrieval.retriever import ChromaRetriever

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_retriever() -> ChromaRetriever:
    """Return a cached retriever instance."""
    return ChromaRetriever()


def ask_rag(query: str) -> AnswerResult:
    """Run the full RAG pipeline for a single query."""
    retriever = get_retriever()
    logger.info("api query=%s", query)
    return answer_query(retriever, query)

