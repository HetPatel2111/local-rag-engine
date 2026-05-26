"""Shared text normalization, sentence splitting, and scoring helpers."""

from __future__ import annotations

import re

_WHITESPACE = re.compile(r"\s+")
_ZERO_WIDTH = re.compile(r"[\u200b\u200c\u200d\ufeff]")
_TOKEN_NOISE = re.compile(r"^[A-Za-z0-9]{18,}$")


def normalize_whitespace(text: str) -> str:
    """Collapse whitespace and strip zero-width characters."""
    cleaned = _ZERO_WIDTH.sub("", text or "")
    return _WHITESPACE.sub(" ", cleaned).strip()


def clean_title(title: str, max_length: int = 120) -> str:
    """Remove UI artifacts and duplicate words from a document title."""
    cleaned = normalize_whitespace(title)
    if not cleaned:
        return ""

    seen_words: set[str] = set()
    words: list[str] = []
    for part in re.split(r"\s+", cleaned):
        token = part.strip(" |-_:/\\")
        if not token or _TOKEN_NOISE.match(token):
            continue
        lowered = token.lower()
        if lowered in seen_words:
            continue
        seen_words.add(lowered)
        words.append(token)

    result = " ".join(words).strip()
    return result[:max_length].rstrip() if len(result) > max_length else result


def split_sentences(text: str) -> list[str]:
    """Split normalized text into sentence-like segments."""
    cleaned = normalize_whitespace(text)
    if not cleaned:
        return []
    pieces = re.findall(r"[^.!?]+[.!?]?", cleaned)
    return [piece.strip() for piece in pieces if piece.strip()]


def clean_preview(text: str, max_chars: int = 300) -> str:
    """Produce a short, whitespace-normalized preview."""
    return normalize_whitespace(text)[:max_chars]


def extract_answer(text: str, max_sentences: int = 3, max_chars: int = 500) -> str:
    """Return complete sentences only, without cutting mid-sentence."""
    sentences = split_sentences(text)
    if not sentences:
        return normalize_whitespace(text)[:max_chars]

    if len(sentences[0]) > max_chars:
        return sentences[0]

    answer_parts: list[str] = []
    current_length = 0
    for sentence in sentences[:max_sentences]:
        next_length = current_length + len(sentence) + (1 if answer_parts else 0)
        if next_length > max_chars:
            break
        answer_parts.append(sentence)
        current_length = next_length

    if not answer_parts:
        return sentences[0]
    return " ".join(answer_parts)


def sentence_score(query: str, sentence: str) -> float:
    """Score a sentence against a query using token overlap."""
    query_tokens = {
        token
        for token in re.findall(r"[a-zA-Z0-9]+", query.lower())
        if len(token) > 2
    }
    sentence_tokens = {
        token
        for token in re.findall(r"[a-zA-Z0-9]+", sentence.lower())
        if len(token) > 2
    }
    if not query_tokens or not sentence_tokens:
        return 0.0

    overlap = len(query_tokens & sentence_tokens)
    if overlap == 0:
        return 0.0

    query_ratio = overlap / len(query_tokens)
    sentence_ratio = overlap / len(sentence_tokens)
    return (0.7 * query_ratio) + (0.3 * sentence_ratio)

