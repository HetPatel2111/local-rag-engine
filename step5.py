import json
import logging
from pathlib import Path
from typing import Any


LOGGER = logging.getLogger("step5")


def iter_chunk_files(chunks_dir: Path) -> list[Path]:
    files = sorted(p for p in chunks_dir.rglob("*.json") if p.is_file())
    if not files:
        raise FileNotFoundError(f"No .json files found under {chunks_dir.as_posix()}")
    return files


def load_chunks_from_dir(chunks_dir: Path) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    for path in iter_chunk_files(chunks_dir):
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    chunks.append(item)
        elif isinstance(data, dict):
            chunks.append(data)
        else:
            raise ValueError(f"Unsupported JSON shape in {path.as_posix()}")
    return chunks


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    try:
        import chromadb
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise SystemExit("Missing dependency: chromadb. Install with `pip install chromadb`.") from exc

    try:
        from langchain_huggingface import HuggingFaceEmbeddings
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise SystemExit(
            "Missing dependency: langchain-huggingface. Install with `pip install langchain-huggingface`."
        ) from exc

    chunks_dir = Path("data/chunks")
    persist_dir = Path("chroma_db")
    collection_name = "vite_docs"
    model_name = "BAAI/bge-small-en-v1.5"
    batch_size = 64

    LOGGER.info("Loading chunks from %s", chunks_dir.as_posix())
    chunks = load_chunks_from_dir(chunks_dir)
    if not chunks:
        raise SystemExit(f"No chunks found under {chunks_dir.as_posix()}")

    LOGGER.info("Initializing local Chroma at %s", persist_dir.as_posix())
    client = chromadb.PersistentClient(path=str(persist_dir))
    try:
        client.delete_collection(name=collection_name)
    except Exception:  # noqa: BLE001
        pass
    collection = client.create_collection(name=collection_name)
    supports_upsert = hasattr(collection, "upsert")

    LOGGER.info("Loading HuggingFaceEmbeddings model=%s", model_name)
    embedder = HuggingFaceEmbeddings(
        model_name=model_name,
        encode_kwargs={"normalize_embeddings": True},
    )

    ids: list[str] = []
    docs: list[str] = []
    metas: list[dict[str, str]] = []
    stored = 0

    def flush() -> None:
        nonlocal stored, ids, docs, metas
        if not ids:
            return

        vectors = embedder.embed_documents(docs)
        if supports_upsert:
            collection.upsert(ids=ids, documents=docs, metadatas=metas, embeddings=vectors)
        else:
            collection.add(ids=ids, documents=docs, metadatas=metas, embeddings=vectors)
        stored += len(ids)
        ids, docs, metas = [], [], []

    total = len(chunks)
    for index, chunk in enumerate(chunks, start=1):
        chunk_id = str(chunk.get("chunk_id", "")).strip() or f"chunk_{index:06d}"
        text = str(chunk.get("text", "") or "").strip()
        url = str(chunk.get("url", "")).strip()
        title = str(chunk.get("title", "")).strip()

        if not text:
            continue

        ids.append(chunk_id)
        docs.append(text)
        metas.append({"url": url, "title": title, "chunk_id": chunk_id})

        if len(ids) >= batch_size:
            flush()
        if index % 50 == 0 or index == total:
            print(f"[{index}/{total}] processed")

    flush()

    collection_size = collection.count()
    print(f"total documents stored: {stored}")
    print(f"collection size: {collection_size}")


if __name__ == "__main__":
    main()
