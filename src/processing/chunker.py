"""Chunk cleaned pages into retrieval-ready documents."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Page:
    """A cleaned web page ready for chunking."""

    url: str
    title: str
    content: str


@dataclass(frozen=True)
class Chunk:
    """A document chunk used for embedding and retrieval."""

    chunk_id: str
    url: str
    title: str
    text: str


def load_pages(path: Path) -> list[Page]:
    """Load cleaned pages from a JSON file."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"Invalid pages JSON in {path.as_posix()}")

    pages: list[Page] = []
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Invalid page entry at index {index}")
        url = str(item.get("url", "")).strip()
        title = str(item.get("title", "")).strip()
        content = str(item.get("content", "")).strip()
        if not url:
            raise ValueError(f"Missing URL at index {index}")
        pages.append(Page(url=url, title=title, content=content))
    return pages


def _split_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """Split text using a recursive-character strategy with a local fallback."""
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
    except Exception:  # noqa: BLE001
        try:
            from langchain.text_splitter import RecursiveCharacterTextSplitter  # type: ignore[no-redef]
        except Exception:  # noqa: BLE001
            class RecursiveCharacterTextSplitter:  # type: ignore[no-redef]
                def __init__(self, *, chunk_size: int, chunk_overlap: int) -> None:
                    self.chunk_size = chunk_size
                    self.chunk_overlap = chunk_overlap
                    self.separators = ["\n\n", "\n", " ", ""]

                def split_text(self, value: str) -> list[str]:
                    value = (value or "").strip()
                    if not value:
                        return []
                    return self._recursive_split(value, self.separators)

                def _recursive_split(self, value: str, separators: list[str]) -> list[str]:
                    if len(value) <= self.chunk_size:
                        return [value]
                    if not separators:
                        return [value[i : i + self.chunk_size] for i in range(0, len(value), self.chunk_size)]

                    separator = separators[0]
                    if separator == "":
                        return [value[i : i + self.chunk_size] for i in range(0, len(value), self.chunk_size)]

                    pieces = value.split(separator)
                    if len(pieces) == 1:
                        return self._recursive_split(value, separators[1:])

                    chunks: list[str] = []
                    for piece in pieces:
                        if not piece:
                            continue
                        if len(piece) <= self.chunk_size:
                            chunks.append(piece)
                        else:
                            chunks.extend(self._recursive_split(piece, separators[1:]))
                    return chunks

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    return splitter.split_text(text)


def chunk_pages(pages: list[Page], chunk_size: int = 600, chunk_overlap: int = 100) -> list[Chunk]:
    """Chunk pages into retrieval units with deterministic IDs."""
    chunks: list[Chunk] = []
    for page_index, page in enumerate(pages, start=1):
        if not page.content.strip():
            continue
        for chunk_index, text in enumerate(_split_text(page.content, chunk_size, chunk_overlap), start=1):
            chunk_id = f"{page_index:03d}_{chunk_index:04d}"
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    url=page.url,
                    title=page.title,
                    text=text.strip(),
                )
            )
    return chunks


def save_chunks(path: Path, chunks: list[Chunk]) -> None:
    """Persist chunk JSON to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [chunk.__dict__ for chunk in chunks]
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
