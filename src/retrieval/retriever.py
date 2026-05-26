"""Persistent Chroma retriever for the Vite documentation corpus."""

from __future__ import annotations

from pathlib import Path

import chromadb

from src.embeddings.huggingface import DEFAULT_MODEL_NAME, create_embedder
from src.retrieval.types import RetrievalResult
from src.utils.env import load_dotenv
from src.utils.text import clean_title


class ChromaRetriever:
    """Load a local Chroma collection and expose semantic search."""

    def __init__(
        self,
        *,
        persist_dir: str = "chroma_db",
        collection_name: str = "vite_docs",
        model_name: str = DEFAULT_MODEL_NAME,
    ) -> None:
        load_dotenv()
        candidate_dir = Path(persist_dir)
        if not candidate_dir.is_absolute():
            repo_root = Path(__file__).resolve().parents[2]
            candidate_dir = repo_root / candidate_dir
        self.persist_dir = candidate_dir
        self.collection_name = collection_name
        self.model_name = model_name

        if not self.persist_dir.exists():
            raise FileNotFoundError(f"Persist directory not found: {self.persist_dir.as_posix()}")

        self.client = chromadb.PersistentClient(path=str(self.persist_dir))
        self.collection = self.client.get_collection(name=self.collection_name)
        self.embedder = create_embedder(model_name=self.model_name)

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
                    section=str(metadata.get("section", "")),
                    chunk_id=str(metadata.get("chunk_id", "")),
                    text=str(documents[index]),
                )
            )

        return sorted(results, key=lambda item: item.score, reverse=True)[:k]

    @staticmethod
    def _dot(left: list[float], right: list[float]) -> float:
        """Compute a simple dot product for similarity ranking."""
        return float(sum(left_value * right_value for left_value, right_value in zip(left, right)))
