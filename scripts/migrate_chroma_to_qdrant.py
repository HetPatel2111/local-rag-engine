"""One-time migration from local Chroma (PersistentClient) to Qdrant Cloud.

Usage (from repo root):
  $env:QDRANT_URL="https://xxxxxx.cloud.qdrant.io"
  $env:QDRANT_API_KEY="..."
  python scripts/migrate_chroma_to_qdrant.py
"""

from __future__ import annotations

import math
from pathlib import Path

import chromadb
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from src.utils.env import getenv, load_dotenv


def _require_env(name: str) -> str:
    value = (getenv(name) or "").strip()
    if not value:
        raise SystemExit(f"Missing required env var: {name}")
    return value


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
    sample_embeddings = (sample.get("embeddings") or [[]])[0]
    if not sample_embeddings:
        raise SystemExit("Chroma collection has no embeddings to migrate.")
    vector_size = len(sample_embeddings[0])

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
        embeddings = (raw.get("embeddings") or [[]])[0]
        documents = (raw.get("documents") or [[]])[0]
        metadatas = (raw.get("metadatas") or [[]])[0]

        points: list[qmodels.PointStruct] = []
        for idx, point_id in enumerate(ids):
            meta = metadatas[idx] if idx < len(metadatas) and isinstance(metadatas[idx], dict) else {}
            payload = {
                "url": str(meta.get("url", "")),
                "title": str(meta.get("title", "")),
                "section": str(meta.get("section", "")),
                "chunk_id": str(meta.get("chunk_id", "")) or str(point_id),
                "text": str(documents[idx]) if idx < len(documents) else "",
            }
            vector = embeddings[idx] if idx < len(embeddings) else None
            if vector is None:
                continue
            points.append(qmodels.PointStruct(id=str(point_id), vector=vector, payload=payload))

        qdrant.upsert(collection_name=collection_name, points=points, wait=True)
        print(f"[{batch_index + 1}/{batches}] Upserted {len(points)} points")

    print("Done.")


if __name__ == "__main__":
    main()

