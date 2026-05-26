"""RAG answer orchestration and CLI formatting."""

from __future__ import annotations

from dataclasses import dataclass
import logging
import textwrap
from time import perf_counter

from src.generation.context_builder import BuiltContext, build_context
from src.generation.llm import MODEL_NAME, REFUSAL_MESSAGE, GenerationResult, generate_answer
from src.retrieval.retriever import ChromaRetriever, RetrievalResult

logger = logging.getLogger(__name__)

TOP_K = 5
MIN_CONFIDENCE = 0.70
KEEP_RATIO = 0.90


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


def search(retriever: ChromaRetriever, query: str, k: int = TOP_K) -> list[RetrievalResult]:
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


def answer_query(retriever: ChromaRetriever, query: str) -> AnswerResult:
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

    started = perf_counter()
    generation: GenerationResult = generate_answer(query, context.text)
    latency_ms = (perf_counter() - started) * 1000.0
    answer = generation.answer.strip()
    if not answer:
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
        model=generation.model,
        latency_ms=latency_ms,
        token_count=generation.token_count,
        input_tokens=generation.input_tokens,
        output_tokens=generation.output_tokens,
        finish_reason=generation.finish_reason,
        response_length=len(answer),
        retrieved_count=len(results),
        context_chars=context.char_count,
    )


def retrieve(query: str, retriever: ChromaRetriever | None = None) -> AnswerResult:
    """Public retrieval entrypoint for a single query."""
    retriever = retriever or ChromaRetriever()
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
