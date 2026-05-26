"""Shared retrieval result types."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalResult:
    """A single retrieved chunk."""

    score: float
    url: str
    title: str
    section: str = ""
    chunk_id: str = ""
    text: str = ""
