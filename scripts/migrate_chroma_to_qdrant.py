"""One-time migration from local Chroma (PersistentClient) to Qdrant Cloud.

Usage (from repo root):
  $env:QDRANT_URL="https://xxxxxx.cloud.qdrant.io"
  $env:QDRANT_API_KEY="..."
  python scripts/migrate_chroma_to_qdrant.py
"""

from __future__ import annotations

import math
import sys
import uuid
from pathlib import Path

import chromadb
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.utils.env import getenv, load_dotenv


def _require_env(name: str) -> str:
    value = (getenv(name) or "").strip()
    if not value:
        raise SystemExit(f"Missing required env var: {name}")
    return value


def _normalize_embeddings(raw: object) -> list[list[float]]:
    """Normalize Chroma embeddings output into List[List[float]]."""
    if raw is None:
        return []

    # Chroma may return: List[vector], List[List[vector]], or a numpy array.
    if hasattr(raw, "tolist"):
        raw = raw.tolist()  # type: ignore[assignment]

    if not isinstance(raw, list) or not raw:
        return []

    first = raw[0]
    if hasattr(first, "tolist"):
        first = first.tolist()  # type: ignore[assignment]

    # Case: raw is [float, float, ...] (single vector)
    if isinstance(first, (int, float)):
        return [[float(v) for v in raw]]  # type: ignore[arg-type]

    # Case: raw is [[float, ...], [float, ...], ...]
    if isinstance(first, list) and first and isinstance(first[0], (int, float)):
        return [[float(v) for v in vec] for vec in raw]  # type: ignore[arg-type]

    # Case: raw is [[vector]] (extra nesting)
    if isinstance(first, list) and first and isinstance(first[0], list):
        flattened: list[list[float]] = []
        for item in raw:  # type: ignore[assignment]
            if hasattr(item, "tolist"):
                item = item.tolist()
            if isinstance(item, list) and item and isinstance(item[0], list):
                for vec in item:
                    if isinstance(vec, list):
                        flattened.append([float(v) for v in vec])
        return flattened

    return []


def _normalize_list_field(raw: object) -> list:
    """Normalize Chroma fields (documents/metadatas) into a simple list."""
    if raw is None:
        return []
    if hasattr(raw, "tolist"):
        raw = raw.tolist()  # type: ignore[assignment]
    if isinstance(raw, dict):
        return list(raw.values())
    if not isinstance(raw, list):
        return []
    if raw and isinstance(raw[0], list):
        return raw[0]
    return raw


def main() -> None:
    load_dotenv()

    qdrant_url = _require_env("QDRANT_URL")
    qdrant_api_key = _require_env("QDRANT_API_KEY")

    chroma_dir = Path(getenv("CHROMA_PERSIST_DIR") or "chroma_db")
    collection_name = (getenv("QDRANT_COLLECTION") or getenv("CHROMA_COLLECTION") or "vite_docs").strip()

    if not chroma_dir.exists():
        raise SystemExit(f"Chroma persist dir not found: {chroma_dir.as_posix()}")

    chroma = chromadb.PersistentClient(path=str(chroma_dir))
    collection = chroma.get_collection(name=collection_name)
    total = int(collection.count())
    if total <= 0:
        raise SystemExit(f"Chroma collection is empty: {collection_name}")

    qdrant = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)

    sample = collection.get(limit=1, include=["embeddings"])
    sample_vectors = _normalize_embeddings(sample.get("embeddings", None))
    if not sample_vectors:
        raise SystemExit("Chroma collection has no embeddings to migrate.")
    vector_size = len(sample_vectors[0])

    qdrant.recreate_collection(
        collection_name=collection_name,
        vectors_config=qmodels.VectorParams(size=vector_size, distance=qmodels.Distance.COSINE),
    )

    batch_size = int(getenv("MIGRATE_BATCH_SIZE") or 128)
    batches = math.ceil(total / batch_size)
    print(f"Migrating {total} points to Qdrant collection '{collection_name}' in {batches} batches…")

    for batch_index in range(batches):
        offset = batch_index * batch_size
        raw = collection.get(
            limit=batch_size,
            offset=offset,
            include=["embeddings", "documents", "metadatas"],
        )

        ids = list(raw.get("ids") or [])
        embeddings = _normalize_embeddings(raw.get("embeddings", None))
        documents = _normalize_list_field(raw.get("documents", None))
        metadatas = _normalize_list_field(raw.get("metadatas", None))

        points: list[qmodels.PointStruct] = []
        for idx, point_id in enumerate(ids):
            meta = metadatas[idx] if idx < len(metadatas) and isinstance(metadatas[idx], dict) else {}
            original_id = str(point_id)
            payload = {
                "url": str(meta.get("url", "")),
                "title": str(meta.get("title", "")),
                "section": str(meta.get("section", "")),
                "chunk_id": str(meta.get("chunk_id", "")) or original_id,
                "chroma_id": original_id,
                "text": str(documents[idx]) if idx < len(documents) else "",
            }
            vector = embeddings[idx] if idx < len(embeddings) else None
            if vector is None:
                continue
            # Qdrant point IDs must be an unsigned int or UUID.
            point_uuid = uuid.uuid5(uuid.NAMESPACE_URL, original_id)
            points.append(qmodels.PointStruct(id=str(point_uuid), vector=vector, payload=payload))

        qdrant.upsert(collection_name=collection_name, points=points, wait=True)
        print(f"[{batch_index + 1}/{batches}] Upserted {len(points)} points")

    print("Done.")


if __name__ == "__main__":
    main()
