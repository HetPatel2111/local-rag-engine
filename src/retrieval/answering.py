"""RAG answer orchestration and CLI formatting."""

from __future__ import annotations

from dataclasses import dataclass
import logging
import re
import textwrap
from time import perf_counter
from typing import Protocol

from src.generation.context_builder import BuiltContext, build_context
from src.generation.llm import MODEL_NAME, REFUSAL_MESSAGE, GenerationResult, generate_answer
from src.retrieval.types import RetrievalResult
from src.utils.env import getenv

logger = logging.getLogger(__name__)

TOP_K = 5
MIN_CONFIDENCE = 0.70
KEEP_RATIO = 0.90
EXTRACTIVE_MODEL_NAME = "Extractive fallback"
_WORD_RE = re.compile(r"[a-z0-9]+")
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+|\n+")
_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "can",
    "do",
    "does",
    "for",
    "how",
    "i",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "to",
    "what",
    "when",
    "where",
    "why",
}


class Retriever(Protocol):
    """Minimal retriever protocol used by answer orchestration."""

    def retrieve(self, query: str, k: int = TOP_K) -> list[RetrievalResult]: ...


@dataclass(frozen=True)
class AnswerResult:
    """Structured output returned by the phase-2 RAG pipeline."""

    answer: str
    confidence: float
    found: bool
    sources: list[str]
    title: str = ""
    url: str = ""
    model: str = MODEL_NAME
    latency_ms: float = 0.0
    token_count: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    finish_reason: str = ""
    response_length: int = 0
    retrieved_count: int = 0
    context_chars: int = 0


def search(retriever: Retriever, query: str, k: int = TOP_K) -> list[RetrievalResult]:
    """Fetch the top semantic matches for a query."""
    return retriever.retrieve(query=query, k=k)


def _best_chunk_filter(results: list[RetrievalResult]) -> list[RetrievalResult]:
    """Keep only chunks within 90% of the best score."""
    if not results:
        return []

    best_score = results[0].score
    threshold = best_score * KEEP_RATIO
    return [result for result in results if result.score >= threshold]


def _build_rag_context(results: list[RetrievalResult]) -> BuiltContext:
    """Construct a compact prompt context from the strongest chunks."""
    return build_context(_best_chunk_filter(results))


def _query_terms(query: str) -> set[str]:
    return {word for word in _WORD_RE.findall(query.lower()) if word not in _STOPWORDS}


def _extractive_fallback(query: str, results: list[RetrievalResult]) -> str:
    """Return a concise answer from retrieved text when generation is unavailable."""
    terms = _query_terms(query)
    candidates: list[tuple[float, str]] = []

    for result in results:
        for sentence in _SENTENCE_RE.split(result.text):
            cleaned = " ".join(sentence.split()).strip()
            if len(cleaned) < 40:
                continue

            sentence_terms = set(_WORD_RE.findall(cleaned.lower()))
            score = len(terms & sentence_terms)
            if result.title and result.title.lower() in cleaned.lower():
                score += 1
            if score > 0:
                candidates.append((score + result.score, cleaned))

    if not candidates and results:
        first = " ".join(results[0].text.split()).strip()
        if first:
            return first[:420].rstrip()

    if not candidates:
        return REFUSAL_MESSAGE

    candidates.sort(key=lambda item: item[0], reverse=True)
    selected: list[str] = []
    seen: set[str] = set()
    for _, sentence in candidates:
        key = sentence.lower()
        if key in seen:
            continue
        seen.add(key)
        selected.append(sentence)
        if len(selected) >= 2:
            break

    return " ".join(selected).strip() or REFUSAL_MESSAGE


def answer_query(retriever: Retriever, query: str) -> AnswerResult:
    """Retrieve, filter, build context, and optionally call Gemini."""
    results = search(retriever, query=query, k=TOP_K)
    if not results:
        return AnswerResult(
            answer=REFUSAL_MESSAGE,
            confidence=0.0,
            found=False,
            sources=[],
            model=MODEL_NAME,
        )

    best_score = results[0].score
    if best_score < MIN_CONFIDENCE:
        return AnswerResult(
            answer=REFUSAL_MESSAGE,
            confidence=best_score,
            found=False,
            sources=[],
            title=results[0].title,
            url=results[0].url,
            model=MODEL_NAME,
            retrieved_count=len(results),
        )

    context = _build_rag_context(results)
    if not context.text.strip():
        return AnswerResult(
            answer=REFUSAL_MESSAGE,
            confidence=best_score,
            found=False,
            sources=[],
            title=results[0].title,
            url=results[0].url,
            model=MODEL_NAME,
            retrieved_count=len(results),
        )

    logger.info(
        "query=%s retrieved_docs=%s confidence=%.4f context_chars=%s",
        query,
        len(results),
        best_score,
        context.char_count,
    )

    filtered_results = _best_chunk_filter(results)
    if (getenv("GENERATION_MODE") or "").strip().lower() == "extractive":
        answer = _extractive_fallback(query, filtered_results)
        found = answer != REFUSAL_MESSAGE
        return AnswerResult(
            answer=answer,
            confidence=best_score,
            found=found,
            sources=context.sources if found else [],
            title=results[0].title,
            url=results[0].url,
            model=EXTRACTIVE_MODEL_NAME,
            latency_ms=0.0,
            finish_reason="EXTRACTIVE",
            response_length=len(answer),
            retrieved_count=len(results),
            context_chars=context.char_count,
        )

    started = perf_counter()
    generation: GenerationResult = generate_answer(query, context.text)
    latency_ms = (perf_counter() - started) * 1000.0
    answer = generation.answer.strip()
    if generation.finish_reason == "ERROR":
        answer = _extractive_fallback(query, filtered_results)
    elif not answer:
        answer = REFUSAL_MESSAGE
    found = answer != REFUSAL_MESSAGE
    sources = context.sources if found else []

    logger.info(
        "query=%s input_tokens=%s output_tokens=%s finish_reason=%s latency_ms=%.2f response_length=%s found=%s",
        query,
        generation.input_tokens,
        generation.output_tokens,
        generation.finish_reason or "UNKNOWN",
        latency_ms,
        len(answer),
        found,
    )

    return AnswerResult(
        answer=answer,
        confidence=best_score,
        found=found,
        sources=sources,
        title=results[0].title,
        url=results[0].url,
        model=EXTRACTIVE_MODEL_NAME if generation.finish_reason == "ERROR" and found else generation.model,
        latency_ms=latency_ms,
        token_count=generation.token_count,
        input_tokens=generation.input_tokens,
        output_tokens=generation.output_tokens,
        finish_reason=generation.finish_reason,
        response_length=len(answer),
        retrieved_count=len(results),
        context_chars=context.char_count,
    )


def retrieve(query: str, retriever: Retriever | None = None) -> AnswerResult:
    """Public retrieval entrypoint for a single query."""
    if retriever is None:
        from src.retrieval.retriever import ChromaRetriever

        retriever = ChromaRetriever()
    return answer_query(retriever, query)


def format_answer(query: str, result: AnswerResult) -> str:
    """Format the single-answer CLI output."""
    lines: list[str] = []
    lines.append("=" * 50)
    lines.append("QUERY")
    lines.append(query)
    lines.append("")
    lines.append("ANSWER")
    lines.extend(textwrap.wrap(result.answer, width=88, break_long_words=False, break_on_hyphens=False) or [""])
    lines.append("")
    lines.append("CONFIDENCE")
    lines.append(f"{result.confidence:.4f}")
    lines.append("")
    lines.append("SOURCES")
    if result.sources:
        lines.extend(result.sources)
    else:
        lines.append("")
    lines.append("")
    lines.append("MODEL")
    lines.append(result.model or MODEL_NAME)
    lines.append("")
    lines.append("FINISH REASON")
    lines.append(result.finish_reason or "UNKNOWN")
    lines.append("")
    lines.append("CHAR COUNT")
    lines.append(str(result.response_length))
    lines.append("=" * 50)
    return "\n".join(lines).rstrip()
