"""Small evaluation helpers for manual smoke checks."""

from __future__ import annotations

from dataclasses import dataclass

from src.retrieval.answering import answer_query
from src.retrieval.retriever import ChromaRetriever


@dataclass(frozen=True)
class SmokeResult:
    """A simple evaluation row for documentation or manual checks."""

    query: str
    found: bool
    confidence: float
    answer: str


def run_smoke_queries(retriever: ChromaRetriever, queries: list[str]) -> list[SmokeResult]:
    """Run a small set of manual verification queries."""
    results: list[SmokeResult] = []
    for query in queries:
        response = answer_query(retriever, query)
        results.append(
            SmokeResult(
                query=query,
                found=response.found,
                confidence=response.confidence,
                answer=response.answer,
            )
        )
    return results

