"""Tests for Gemini generation retry behavior."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from src.generation.llm import GenerationResult, MODEL_NAME, generate_answer


class GenerationTests(unittest.TestCase):
    def test_generate_answer_retries_on_max_tokens(self) -> None:
        first_result = GenerationResult(
            answer="Vite is a build tool designed to provide a faster and",
            model=MODEL_NAME,
            attempts=1,
            latency_ms=10.0,
            token_count=40,
            input_tokens=20,
            output_tokens=20,
            finish_reason="MAX_TOKENS",
            response_length=54,
        )
        second_result = GenerationResult(
            answer="Vite is a build tool designed to provide a faster and leaner development experience.",
            model=MODEL_NAME,
            attempts=1,
            latency_ms=11.0,
            token_count=50,
            input_tokens=25,
            output_tokens=25,
            finish_reason="STOP",
            response_length=84,
        )

        with patch("src.generation.llm._generate_with_tokens", side_effect=[first_result, second_result]):
            result = generate_answer("What is Vite?", "Title: Vite\nURL: https://vite.dev\nContent: Vite is fast.")

        self.assertEqual(result.answer, second_result.answer)
        self.assertEqual(result.finish_reason, "STOP")
        self.assertEqual(result.response_length, len(second_result.answer))


if __name__ == "__main__":
    unittest.main()
