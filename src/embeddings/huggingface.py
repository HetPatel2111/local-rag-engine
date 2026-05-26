"""Hugging Face embedding model factory."""

from __future__ import annotations

from langchain_huggingface import HuggingFaceEmbeddings

DEFAULT_MODEL_NAME = "BAAI/bge-small-en-v1.5"


def create_embedder(model_name: str = DEFAULT_MODEL_NAME) -> HuggingFaceEmbeddings:
    """Create a normalized Hugging Face embedder."""
    return HuggingFaceEmbeddings(
        model_name=model_name,
        encode_kwargs={"normalize_embeddings": True},
    )

