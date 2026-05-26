"""Qdrant Cloud retriever implementation."""

from __future__ import annotations

import re
from functools import lru_cache

from qdrant_client import QdrantClient

from src.retrieval.types import RetrievalResult
from src.utils.env import getenv, load_dotenv
from src.utils.text import clean_title

DEFAULT_MODEL_NAME = "BAAI/bge-small-en-v1.5"
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


class QdrantRetriever:
    """Semantic search over a Qdrant collection."""

    def __init__(
        self,
        *,
        url: str | None = None,
        api_key: str | None = None,
        collection_name: str = "vite_docs",
        model_name: str = DEFAULT_MODEL_NAME,
        retrieval_mode: str | None = None,
    ) -> None:
        load_dotenv()

        resolved_url = (url or getenv("QDRANT_URL") or "").strip()
        resolved_api_key = (api_key or getenv("QDRANT_API_KEY") or "").strip()
        if not resolved_url:
            raise ValueError("Missing QDRANT_URL (or pass url=...).")
        if not resolved_api_key:
            raise ValueError("Missing QDRANT_API_KEY (or pass api_key=...).")

        self.collection_name = collection_name
        self.model_name = model_name
        self.retrieval_mode = (retrieval_mode or getenv("QDRANT_RETRIEVAL_MODE") or "semantic").strip().lower()
        self.client = QdrantClient(url=resolved_url, api_key=resolved_api_key)
        self.embedder = None
        if self.retrieval_mode != "lexical":
            from src.embeddings.huggingface import create_embedder

            self.embedder = create_embedder(model_name=self.model_name)

    @staticmethod
    def _extract_scored_points(response: object) -> list[object]:
        points = getattr(response, "points", None)
        if isinstance(points, list):
            return points

        result = getattr(response, "result", None)
        if isinstance(result, list):
            return result
        nested_points = getattr(result, "points", None) if result is not None else None
        if isinstance(nested_points, list):
            return nested_points

        return []

    def retrieve(self, query: str, k: int = 5, fetch_k: int = 20) -> list[RetrievalResult]:
        """Return the top `k` documents sorted by query similarity."""
        if self.retrieval_mode == "lexical":
            return self._retrieve_lexical(query=query, k=k)

        if self.embedder is None:
            return []

        query_embedding = self.embedder.embed_query(query)
        limit = max(k, fetch_k)

        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )

        results: list[RetrievalResult] = []
        for hit in self._extract_scored_points(response):
            payload = dict(getattr(hit, "payload", None) or {})
            results.append(
                RetrievalResult(
                    score=float(getattr(hit, "score", 0.0) or 0.0),
                    url=str(payload.get("url", "")),
                    title=clean_title(str(payload.get("title", ""))),
                    section=str(payload.get("section", "")),
                    chunk_id=str(payload.get("chunk_id", "")) or str(getattr(hit, "id", "")),
                    text=str(payload.get("text", "")),
                )
            )

        return results[:k]

    @lru_cache(maxsize=1)
    def _load_payloads(self) -> tuple[dict, ...]:
        """Load Qdrant payloads once for lightweight lexical retrieval."""
        payloads: list[dict] = []
        next_offset = None

        while True:
            points, next_offset = self.client.scroll(
                collection_name=self.collection_name,
                limit=256,
                offset=next_offset,
                with_payload=True,
                with_vectors=False,
            )

            for point in points or []:
                payload = dict(getattr(point, "payload", None) or {})
                if payload:
                    payloads.append(payload)

            if next_offset is None:
                break

        return tuple(payloads)

    @staticmethod
    def _tokens(text: str) -> list[str]:
        return [token for token in _TOKEN_RE.findall(text.lower()) if token not in _STOPWORDS]

    @staticmethod
    def _lexical_confidence(score: float) -> float:
        if score <= 0:
            return 0.0
        return min(0.98, 0.55 + (score / (score + 8.0)) * 0.43)

    def _retrieve_lexical(self, query: str, k: int) -> list[RetrievalResult]:
        query_tokens = self._tokens(query)
        if not query_tokens:
            return []

        query_phrase = " ".join(query_tokens)
        scored: list[tuple[float, dict]] = []
        for payload in self._load_payloads():
            title = str(payload.get("title", ""))
            section = str(payload.get("section", ""))
            text = str(payload.get("text", ""))
            haystack = f"{title} {section} {text}".lower()

            score = 0.0
            for token in query_tokens:
                title_count = title.lower().count(token)
                section_count = section.lower().count(token)
                text_count = haystack.count(token)
                score += (title_count * 4.0) + (section_count * 2.0) + min(text_count, 8)

            if query_phrase and query_phrase in haystack:
                score += 6.0

            if score > 0:
                scored.append((score, payload))

        scored.sort(key=lambda item: item[0], reverse=True)
        results: list[RetrievalResult] = []
        for score, payload in scored[:k]:
            results.append(
                RetrievalResult(
                    score=self._lexical_confidence(score),
                    url=str(payload.get("url", "")),
                    title=clean_title(str(payload.get("title", ""))),
                    section=str(payload.get("section", "")),
                    chunk_id=str(payload.get("chunk_id", "")) or str(payload.get("chroma_id", "")),
                    text=str(payload.get("text", "")),
                )
            )

        return results
