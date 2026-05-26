"""Qdrant Cloud retriever implementation."""

from __future__ import annotations

from qdrant_client import QdrantClient

from src.embeddings.huggingface import DEFAULT_MODEL_NAME, create_embedder
from src.retrieval.retriever import RetrievalResult
from src.utils.env import getenv, load_dotenv
from src.utils.text import clean_title


class QdrantRetriever:
    """Semantic search over a Qdrant collection."""

    def __init__(
        self,
        *,
        url: str | None = None,
        api_key: str | None = None,
        collection_name: str = "vite_docs",
        model_name: str = DEFAULT_MODEL_NAME,
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
        self.client = QdrantClient(url=resolved_url, api_key=resolved_api_key)
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
