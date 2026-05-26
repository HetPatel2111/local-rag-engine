"""Tests for text normalization helpers."""

from __future__ import annotations

import unittest

from src.utils.text import clean_title, extract_answer, sentence_score, split_sentences


class TextUtilsTests(unittest.TestCase):
    def test_clean_title_removes_duplicates_and_noise(self) -> None:
        title = "Vite Vite HMR hmr boundary boundary rootrootrootrootrootrootrootroot"
        self.assertEqual(clean_title(title), "Vite HMR boundary")

    def test_split_sentences_returns_complete_segments(self) -> None:
        text = "First sentence. Second sentence! Third sentence?"
        self.assertEqual(split_sentences(text), ["First sentence.", "Second sentence!", "Third sentence?"])

    def test_extract_answer_keeps_complete_sentences(self) -> None:
        text = "First sentence. Second sentence! Third sentence? Fourth sentence."
        self.assertEqual(
            extract_answer(text, max_sentences=3, max_chars=500),
            "First sentence. Second sentence! Third sentence?",
        )

    def test_sentence_score_prefers_shared_terms(self) -> None:
        self.assertGreater(sentence_score("What is Vite HMR", "HMR in Vite handles hot reload updates."), 0.0)


if __name__ == "__main__":
    unittest.main()

