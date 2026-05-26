"""Structural markdown chunking for the Vite knowledge base."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class MarkdownChunk:
    """A single chunk prepared for embedding and retrieval."""

    id: str
    title: str
    section: str
    content: str
    url: str


@dataclass(frozen=True)
class MarkdownDocument:
    """A markdown knowledge-base document."""

    path: Path
    url: str
    title: str
    created_at: str
    markdown: str


_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?", re.DOTALL)
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}, text

    frontmatter: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        frontmatter[key.strip()] = value.strip().strip('"').strip("'")
    return frontmatter, text[match.end() :]


def load_markdown_documents(knowledge_base_dir: Path) -> list[MarkdownDocument]:
    """Load markdown pages from the knowledge base."""
    documents: list[MarkdownDocument] = []
    for path in sorted(knowledge_base_dir.rglob("*.md")):
        raw = path.read_text(encoding="utf-8")
        metadata, markdown = _parse_frontmatter(raw)
        url = metadata.get("url", "")
        title = metadata.get("title", "")
        created_at = metadata.get("created_at", "")
        if not url or not title:
            continue
        documents.append(
            MarkdownDocument(
                path=path,
                url=url,
                title=title,
                created_at=created_at,
                markdown=markdown.strip(),
            )
        )
    return documents


def _split_long_text(text: str, limit: int) -> list[str]:
    """Split very long text into smaller paragraph-aware segments."""
    if len(text) <= limit:
        return [text.strip()]

    paragraphs = [part.strip() for part in re.split(r"\n\s*\n+", text) if part.strip()]
    if not paragraphs:
        return [text[:limit].strip()]

    pieces: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if len(paragraph) > limit:
            if current.strip():
                pieces.append(current.strip())
                current = ""
            for start in range(0, len(paragraph), limit):
                pieces.append(paragraph[start : start + limit].strip())
            continue

        candidate = paragraph if not current else f"{current}\n\n{paragraph}"
        if len(candidate) > limit and current:
            pieces.append(current.strip())
            current = paragraph
        else:
            current = candidate

    if current.strip():
        pieces.append(current.strip())
    return pieces


def _section_label(section_stack: list[str]) -> str:
    return " > ".join(label for label in section_stack if label).strip()


def chunk_markdown_document(document: MarkdownDocument, max_chars: int = 1200, min_chars: int = 300) -> list[MarkdownChunk]:
    """Chunk a markdown document using its heading hierarchy."""
    lines = document.markdown.splitlines()
    chunks: list[MarkdownChunk] = []
    section_stack: dict[int, str] = {}
    current_blocks: list[str] = []
    current_section = ""
    chunk_index = 1

    def flush_block() -> None:
        nonlocal current_blocks, chunk_index
        body = "\n".join(line.rstrip() for line in current_blocks).strip()
        current_blocks = []
        if not body:
            return

        section_label = current_section or "document"
        full_text = f"# {document.title}\n\n"
        if section_label != "document":
            full_text += f"## {section_label}\n\n"
        full_text += body

        for piece in _split_long_text(full_text, max_chars):
            if not piece.strip():
                continue
            chunks.append(
                MarkdownChunk(
                    id=f"{path_to_chunk_prefix(document.path)}_{chunk_index:04d}",
                    title=document.title,
                    section=section_label,
                    content=piece.strip(),
                    url=document.url,
                )
            )
            chunk_index += 1

    in_code_block = False
    code_buffer: list[str] = []

    for line in lines:
        heading_match = _HEADING_RE.match(line)
        if line.strip().startswith("```"):
            if in_code_block:
                code_buffer.append(line)
                current_blocks.append("\n".join(code_buffer))
                code_buffer = []
                in_code_block = False
            else:
                in_code_block = True
                code_buffer = [line]
            continue

        if in_code_block:
            code_buffer.append(line)
            continue

        if heading_match:
            level = len(heading_match.group(1))
            heading = heading_match.group(2).strip()
            if current_blocks:
                flush_block()
            if level == 1:
                section_stack.clear()
                current_section = ""
            else:
                section_stack[level] = heading
                for deeper_level in list(section_stack.keys()):
                    if deeper_level > level:
                        section_stack.pop(deeper_level, None)
                current_section = _section_label([section_stack[level] for level in sorted(section_stack) if level >= 2])
            current_blocks.append(line.strip())
            continue

        if not line.strip():
            if current_blocks and current_blocks[-1] != "":
                current_blocks.append("")
            continue

        current_blocks.append(line)
        if len("\n".join(current_blocks)) >= max_chars:
            flush_block()

    if in_code_block and code_buffer:
        current_blocks.append("\n".join(code_buffer))

    if current_blocks:
        flush_block()

    return _merge_short_chunks(chunks, min_chars=min_chars, max_chars=max_chars)


def _merge_short_chunks(chunks: list[MarkdownChunk], *, min_chars: int, max_chars: int) -> list[MarkdownChunk]:
    """Merge adjacent short chunks within the same document and section."""
    if not chunks:
        return []

    merged: list[MarkdownChunk] = []
    for chunk in chunks:
        if not merged:
            merged.append(chunk)
            continue

        previous = merged[-1]
        if (
            previous.title == chunk.title
            and previous.section == chunk.section
            and len(previous.content) < min_chars
            and len(previous.content) + len(chunk.content) <= max_chars
        ):
            merged[-1] = MarkdownChunk(
                id=previous.id,
                title=previous.title,
                section=previous.section,
                content=f"{previous.content}\n\n{chunk.content}".strip(),
                url=previous.url,
            )
            continue

        merged.append(chunk)

    return merged


def path_to_chunk_prefix(path: Path) -> str:
    """Create a stable chunk prefix from a markdown file path."""
    relative = path.as_posix().replace("/", "_")
    relative = re.sub(r"[^a-zA-Z0-9_]+", "_", relative)
    return relative.strip("_") or "chunk"


def save_chunks(path: Path, chunks: Iterable[MarkdownChunk]) -> None:
    """Persist chunk records to JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [chunk.__dict__ for chunk in chunks]
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

