"""Tests for answer synthesis and confidence gating."""

from __future__ import annotations

import unittest

from src.retrieval.answering import AnswerResult, answer_query, format_answer, synthesize_answer
from src.retrieval.retriever import RetrievalResult


class DummyRetriever:
    def __init__(self, results: list[RetrievalResult]) -> None:
        self._results = results

    def retrieve(self, query: str, k: int = 5) -> list[RetrievalResult]:
        return self._results[:k]


class AnsweringTests(unittest.TestCase):
    def test_answer_query_refuses_low_confidence(self) -> None:
        retriever = DummyRetriever(
            [
                RetrievalResult(
                    score=0.10,
                    url="https://example.com",
                    title="Example",
                    chunk_id="001_0001",
                    text="Low confidence chunk.",
                )
            ]
        )
        result = answer_query(retriever, "What is Vite?")
        self.assertFalse(result.found)
        self.assertIn("I don't know", result.answer)

    def test_synthesize_answer_uses_strong_chunks(self) -> None:
        results = [
            RetrievalResult(
                score=0.95,
                url="https://vite.dev/a",
                title="A",
                chunk_id="001_0001",
                text="Vite uses native ES modules to start quickly in the browser. HMR updates changed modules without a full reload.",
            ),
            RetrievalResult(
                score=0.91,
                url="https://vite.dev/b",
                title="B",
                chunk_id="001_0002",
                text="It also provides fast startup and a development server.",
            ),
        ]
        answer = synthesize_answer("What is Vite?", results)
        self.assertIn("Vite uses native ES modules to start quickly in the browser.", answer)

    def test_format_answer_includes_sources(self) -> None:
        result = AnswerResult(
            answer="Vite is a build tool.",
            confidence=0.8123,
            found=True,
            sources=["https://vite.dev/"],
            title="Vite",
            url="https://vite.dev/",
        )
        output = format_answer("What is Vite?", result)
        self.assertIn("ANSWER", output)
        self.assertIn("SOURCES", output)
        self.assertIn("https://vite.dev/", output)


if __name__ == "__main__":
    unittest.main()
