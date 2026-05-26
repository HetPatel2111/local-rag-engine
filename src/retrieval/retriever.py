"""Persistent Chroma retriever for the Vite documentation corpus."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chromadb

from src.embeddings.huggingface import DEFAULT_MODEL_NAME, create_embedder
from src.utils.text import clean_title


@dataclass(frozen=True)
class RetrievalResult:
    """A single retrieved chunk."""

    score: float
    url: str
    title: str
    chunk_id: str
    text: str


class ChromaRetriever:
    """Load a local Chroma collection and expose semantic search."""

    def __init__(
        self,
        *,
        persist_dir: str = "chroma_db",
        collection_name: str = "vite_docs",
        model_name: str = DEFAULT_MODEL_NAME,
    ) -> None:
        self._load_dotenv()
        self.persist_dir = Path(persist_dir)
        self.collection_name = collection_name
        self.model_name = model_name

        if not self.persist_dir.exists():
            raise FileNotFoundError(f"Persist directory not found: {self.persist_dir.as_posix()}")

        self.client = chromadb.PersistentClient(path=str(self.persist_dir))
        self.collection = self.client.get_collection(name=self.collection_name)
        self.embedder = create_embedder(model_name=self.model_name)

    @staticmethod
    def _load_dotenv() -> None:
        """Load `.env` without introducing an extra dependency."""
        env_path = Path(".env")
        if not env_path.exists():
            return

        for line in env_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value

    def retrieve(self, query: str, k: int = 5, fetch_k: int = 20) -> list[RetrievalResult]:
        """Return the top `k` documents sorted by query similarity."""
        query_embedding = self.embedder.embed_query(query)
        raw = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=max(k, fetch_k),
            include=["documents", "metadatas", "embeddings"],
        )

        documents = raw.get("documents", [[]])[0]
        metadatas = raw.get("metadatas", [[]])[0]
        embeddings = raw.get("embeddings", [[]])[0]

        if embeddings is None or len(embeddings) == 0 or len(embeddings) != len(documents):
            embeddings = self.embedder.embed_documents([str(document) for document in documents])

        results: list[RetrievalResult] = []
        for index in range(min(len(documents), len(metadatas), len(embeddings))):
            metadata = metadatas[index] if isinstance(metadatas[index], dict) else {}
            embedding = embeddings[index]
            if embedding is None or len(embedding) == 0:
                continue
            score = self._dot([float(value) for value in query_embedding], [float(value) for value in embedding])
            results.append(
                RetrievalResult(
                    score=float(score),
                    url=str(metadata.get("url", "")),
                    title=clean_title(str(metadata.get("title", ""))),
                    chunk_id=str(metadata.get("chunk_id", "")),
                    text=str(documents[index]),
                )
            )

        return sorted(results, key=lambda item: item.score, reverse=True)[:k]

    @staticmethod
    def _dot(left: list[float], right: list[float]) -> float:
        """Compute a simple dot product for similarity ranking."""
        return float(sum(left_value * right_value for left_value, right_value in zip(left, right)))

