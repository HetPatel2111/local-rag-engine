"""Hugging Face embedding model factory."""

from __future__ import annotations

from typing import Protocol

from langchain_huggingface import HuggingFaceEmbeddings

from src.utils.env import getenv, load_dotenv

DEFAULT_MODEL_NAME = "BAAI/bge-small-en-v1.5"


class Embedder(Protocol):
    """Minimal embedding interface used by this repo."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


def _create_huggingface_embedder(model_name: str) -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(model_name=model_name, encode_kwargs={"normalize_embeddings": True})


def _create_fastembed_embedder(model_name: str) -> Embedder:
    from fastembed import TextEmbedding

    model = TextEmbedding(model_name)
    passage_fn = getattr(model, "passage_embed", None) or getattr(model, "embed")
    query_fn = getattr(model, "query_embed", None) or getattr(model, "embed")

    class _FastEmbedWrapper:
        def embed_documents(self, texts: list[str]) -> list[list[float]]:
            return [list(vector) for vector in passage_fn(texts)]

        def embed_query(self, text: str) -> list[float]:
            vectors = list(query_fn([text]))
            return list(vectors[0]) if vectors else []

    return _FastEmbedWrapper()


def create_embedder(model_name: str = DEFAULT_MODEL_NAME) -> Embedder:
    """Create an embedder.

    Set `EMBEDDINGS_BACKEND=fastembed` to reduce memory usage in small deploys.
    """
    load_dotenv()
    backend = (getenv("EMBEDDINGS_BACKEND") or "huggingface").strip().lower()
    if backend == "fastembed":
        return _create_fastembed_embedder(model_name)
    return _create_huggingface_embedder(model_name)
