"""Build grounded prompts from retrieved chunks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from src.retrieval.types import RetrievalResult
from src.utils.text import normalize_whitespace


@dataclass(frozen=True)
class BuiltContext:
    """Structured prompt context passed to the generation layer."""

    text: str
    sources: list[str]
    chunk_count: int
    char_count: int


def _format_block(result: RetrievalResult) -> str:
    """Format a single retrieval result as grounded context text."""
    title = normalize_whitespace(result.title) or "Untitled"
    url = normalize_whitespace(result.url) or ""
    content = normalize_whitespace(result.text)
    section = normalize_whitespace(result.section)

    lines = [f"Title: {title}"]
    if section:
        lines.append(f"Section: {section}")
    lines.append(f"URL: {url}")
    lines.append("Content:")
    lines.append(content)
    return "\n".join(lines).strip()


def build_context(results: Sequence[RetrievalResult], max_chars: int = 3000) -> BuiltContext:
    """Create a deduplicated, ordered context bundle for Gemini."""
    unique_results: list[RetrievalResult] = []
    seen_chunks: set[str] = set()
    seen_texts: set[str] = set()
    for result in results:
        dedupe_key = result.chunk_id or f"{result.url}:{result.title}"
        text_key = normalize_whitespace(result.text).lower()
        if dedupe_key in seen_chunks or text_key in seen_texts:
            continue
        seen_chunks.add(dedupe_key)
        seen_texts.add(text_key)
        unique_results.append(result)

    blocks: list[str] = []
    sources: list[str] = []
    current_length = 0

    for result in unique_results:
        block = _format_block(result)
        if not block:
            continue

        separator_length = 2 if blocks else 0
        available = max_chars - current_length - separator_length
        if available <= 0:
            break

        if len(block) > available:
            if not blocks:
                block = block[:available].rstrip()
            else:
                break

        blocks.append(block)
        current_length += len(block) + separator_length
        if result.url and result.url not in sources:
            sources.append(result.url)

    context_text = "\n\n".join(blocks).strip()
    return BuiltContext(
        text=context_text,
        sources=sources,
        chunk_count=len(blocks),
        char_count=len(context_text),
    )
