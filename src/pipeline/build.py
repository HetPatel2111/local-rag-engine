"""End-to-end pipeline for building the markdown KB, chunks, and Chroma index."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import chromadb

from src.embeddings.huggingface import DEFAULT_MODEL_NAME, create_embedder
from src.ingestion.sitemap import dedupe_urls, download_sitemap, extract_urls, save_json
from src.processing.chunker import chunk_markdown_document, load_markdown_documents, save_chunks
from src.processing.html_cleaner import html_to_markdown, save_markdown_page


LOGGER = logging.getLogger("pipeline.build")
DEFAULT_SITEMAP_URL = "https://vite.dev/sitemap.xml"


@dataclass(frozen=True)
class BuildStats:
    """Summary of a completed build run."""

    urls: int
    pages_written: int
    chunks_written: int
    documents_indexed: int


def _load_or_fetch_urls(sitemap_url: str, urls_path: Path) -> list[str]:
    if urls_path.exists():
        raw = json.loads(urls_path.read_text(encoding="utf-8"))
        if isinstance(raw, list) and all(isinstance(item, str) for item in raw):
            return raw

    sitemap_xml = download_sitemap(sitemap_url)
    urls = dedupe_urls(extract_urls(sitemap_xml))
    save_json(urls_path, urls)
    return urls


def build_knowledge_base(
    *,
    sitemap_url: str = DEFAULT_SITEMAP_URL,
    urls_path: Path = Path("data/urls/urls.json"),
    knowledge_base_dir: Path = Path("knowledge_base"),
) -> int:
    """Download HTML pages and persist cleaned markdown documents."""
    import requests

    urls = _load_or_fetch_urls(sitemap_url, urls_path)
    knowledge_base_dir.mkdir(parents=True, exist_ok=True)
    for category in ("guide", "config", "api", "index"):
        (knowledge_base_dir / category).mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "semantic-docs-rag/1.0 (+https://github.com/HetPatel2111/local-rag-engine)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
    )

    pages_written = 0
    for index, url in enumerate(urls, start=1):
        LOGGER.info("[%d/%d] Fetching %s", index, len(urls), url)
        response = session.get(url, timeout=30)
        response.raise_for_status()

        page = html_to_markdown(response.text, url=url)
        if page.category == "skip" or not page.markdown.strip():
            continue

        save_markdown_page(page, knowledge_base_dir)
        pages_written += 1

    LOGGER.info("Knowledge base written: %d pages", pages_written)
    return pages_written


def build_chunks(
    *,
    knowledge_base_dir: Path = Path("knowledge_base"),
    output_path: Path = Path("data/chunks/chunks.json"),
) -> int:
    """Chunk the markdown knowledge base into deterministic structural chunks."""
    documents = load_markdown_documents(knowledge_base_dir)
    all_chunks = []
    for document in documents:
        all_chunks.extend(chunk_markdown_document(document))

    save_chunks(output_path, all_chunks)
    LOGGER.info("Chunks written: %d", len(all_chunks))
    return len(all_chunks)


def build_chroma_index(
    *,
    chunk_path: Path = Path("data/chunks/chunks.json"),
    persist_dir: Path = Path("chroma_db"),
    collection_name: str = "vite_docs",
    model_name: str = DEFAULT_MODEL_NAME,
) -> int:
    """Generate embeddings and persist them into Chroma."""
    import json

    raw = json.loads(chunk_path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"Invalid chunks JSON in {chunk_path.as_posix()}")

    persist_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(persist_dir))
    try:
        client.delete_collection(name=collection_name)
    except Exception:  # noqa: BLE001
        pass
    collection = client.create_collection(name=collection_name)

    embedder = create_embedder(model_name=model_name)
    documents = [str(item.get("content", "")) for item in raw]
    metadatas = [
        {
            "title": str(item.get("title", "")),
            "section": str(item.get("section", "")),
            "url": str(item.get("url", "")),
            "chunk_id": str(item.get("id", "")),
        }
        for item in raw
    ]
    ids = [str(item.get("id", "")) for item in raw]
    embeddings = embedder.embed_documents(documents)

    batch_size = 64
    for start in range(0, len(ids), batch_size):
        end = start + batch_size
        collection.add(
            ids=ids[start:end],
            documents=documents[start:end],
            embeddings=embeddings[start:end],
            metadatas=metadatas[start:end],
        )

    LOGGER.info("Chroma collection size: %d", collection.count())
    return collection.count()


def build_all() -> BuildStats:
    """Run the full build pipeline."""
    urls = _load_or_fetch_urls(DEFAULT_SITEMAP_URL, Path("data/urls/urls.json"))
    pages_written = build_knowledge_base()
    chunks_written = build_chunks()
    documents_indexed = build_chroma_index()
    return BuildStats(
        urls=len(urls),
        pages_written=pages_written,
        chunks_written=chunks_written,
        documents_indexed=documents_indexed,
    )

