"""Local retriever backed by the precomputed chunk corpus."""

from __future__ import annotations

from functools import lru_cache
import json
import re
from pathlib import Path

from src.retrieval.types import RetrievalResult
from src.utils.text import clean_title, normalize_whitespace

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "can",
    "do",
    "does",
    "for",
    "how",
    "i",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "to",
    "what",
    "when",
    "where",
    "why",
}


class ChromaRetriever:
    """Load the local chunk corpus and expose lightweight semantic-style search."""

    def __init__(
        self,
        *,
        chunk_path: str | Path = Path("data/chunks/chunks.json"),
        collection_name: str = "vite_docs",
    ) -> None:
        self.chunk_path = Path(chunk_path)
        self.collection_name = collection_name

    @staticmethod
    def _tokens(text: str) -> list[str]:
        return [token for token in _TOKEN_RE.findall(text.lower()) if token not in _STOPWORDS]

    @staticmethod
    def _confidence(score: float) -> float:
        if score <= 0:
            return 0.0
        return min(0.98, 0.55 + (score / (score + 8.0)) * 0.43)

    @lru_cache(maxsize=1)
    def _load_chunks(self) -> tuple[dict, ...]:
        if not self.chunk_path.exists():
            return ()

        raw = json.loads(self.chunk_path.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            return ()

        chunks: list[dict] = []
        for item in raw:
            if isinstance(item, dict):
                chunks.append(item)
        return tuple(chunks)

    def _score_chunk(self, query_tokens: list[str], query_phrase: str, chunk: dict) -> float:
        title = normalize_whitespace(str(chunk.get("title", "")))
        section = normalize_whitespace(str(chunk.get("section", "")))
        content = normalize_whitespace(str(chunk.get("content", "")))
        haystack = f"{title} {section} {content}".lower()

        score = 0.0
        for token in query_tokens:
            score += title.lower().count(token) * 4.0
            score += section.lower().count(token) * 2.0
            score += min(haystack.count(token), 8)

        if query_phrase and query_phrase in haystack:
            score += 6.0

        if title and title.lower() in query_phrase:
            score += 2.0

        return score

    def retrieve(self, query: str, k: int = 5, fetch_k: int = 20) -> list[RetrievalResult]:
        """Return the top `k` chunks sorted by query similarity."""
        del fetch_k  # The local corpus is small enough that we score the full set.
        chunks = self._load_chunks()
        if not chunks:
            return []

        query_tokens = self._tokens(query)
        if not query_tokens:
            return []

        query_phrase = " ".join(query_tokens)
        scored: list[tuple[float, dict]] = []
        for chunk in chunks:
            score = self._score_chunk(query_tokens, query_phrase, chunk)
            if score > 0:
                scored.append((score, chunk))

        scored.sort(key=lambda item: item[0], reverse=True)

        results: list[RetrievalResult] = []
        for score, chunk in scored[:k]:
            results.append(
                RetrievalResult(
                    score=self._confidence(score),
                    url=str(chunk.get("url", "")),
                    title=clean_title(str(chunk.get("title", ""))),
                    section=str(chunk.get("section", "")),
                    chunk_id=str(chunk.get("id", "")),
                    text=str(chunk.get("content", "")),
                )
            )

        return results


# Backward-compatible name so the rest of the app keeps working.
QdrantRetriever = ChromaRetriever
