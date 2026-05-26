"""Tests for Gemini-backed answer generation and confidence gating."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from src.generation.context_builder import build_context
from src.generation.llm import GenerationResult, MODEL_NAME, REFUSAL_MESSAGE
from src.retrieval.answering import AnswerResult, answer_query, format_answer
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
        self.assertEqual(result.answer, REFUSAL_MESSAGE)

    def test_answer_query_uses_generation_for_confident_results(self) -> None:
        retriever = DummyRetriever(
            [
                RetrievalResult(
                    score=0.95,
                    url="https://vite.dev/guide/",
                    title="Guide",
                    chunk_id="001_0001",
                    text="Vite is a build tool designed to provide a faster and leaner development experience.",
                ),
                RetrievalResult(
                    score=0.91,
                    url="https://vite.dev/guide/hmr",
                    title="HMR",
                    chunk_id="001_0002",
                    text="HMR allows fast updates without a full page reload.",
                ),
            ]
        )
        mocked_generation = GenerationResult(
            answer="Vite is a build tool designed to provide a faster and leaner development experience.",
            model=MODEL_NAME,
            attempts=1,
            latency_ms=12.3,
            token_count=42,
            response_length=84,
        )
        with patch("src.retrieval.answering.generate_answer", return_value=mocked_generation):
            result = answer_query(retriever, "What is Vite?")

        self.assertTrue(result.found)
        self.assertEqual(result.model, MODEL_NAME)
        self.assertIn("https://vite.dev/guide/", result.sources)
        self.assertEqual(result.answer, mocked_generation.answer)

    def test_build_context_deduplicates_chunks(self) -> None:
        results = [
            RetrievalResult(
                score=0.95,
                url="https://vite.dev/a",
                title="A",
                chunk_id="001_0001",
                text="Vite uses native ES modules to start quickly in the browser.",
            ),
            RetrievalResult(
                score=0.91,
                url="https://vite.dev/a",
                title="A",
                chunk_id="001_0001",
                text="Vite uses native ES modules to start quickly in the browser.",
            ),
        ]
        context = build_context(results)
        self.assertEqual(context.chunk_count, 1)
        self.assertIn("Title: A", context.text)
        self.assertEqual(context.sources, ["https://vite.dev/a"])

    def test_format_answer_includes_sources(self) -> None:
        result = AnswerResult(
            answer="Vite is a build tool.",
            confidence=0.8123,
            found=True,
            sources=["https://vite.dev/"],
            title="Vite",
            url="https://vite.dev/",
            model=MODEL_NAME,
        )
        output = format_answer("What is Vite?", result)
        self.assertIn("ANSWER", output)
        self.assertIn("SOURCES", output)
        self.assertIn("https://vite.dev/", output)
        self.assertIn("MODEL", output)
        self.assertIn(MODEL_NAME, output)


if __name__ == "__main__":
    unittest.main()
