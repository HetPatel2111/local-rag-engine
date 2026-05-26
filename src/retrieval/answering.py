"""Answer synthesis and output formatting for the CLI."""

from __future__ import annotations

from dataclasses import dataclass
import re
from statistics import mean
import textwrap
from typing import Sequence

from src.retrieval.retriever import ChromaRetriever, RetrievalResult
from src.utils.text import normalize_whitespace, sentence_score, split_sentences

TOP_K = 5
MIN_CONFIDENCE = 0.70
KEEP_RATIO = 0.90
MIN_SENTENCE_LEN = 40
MAX_SENTENCE_LEN = 300
MAX_ANSWER_CHARS = 700
PREFERRED_TERMS = ("is", "provides", "allows", "supports", "uses")
BOOSTED_PATHS = ("guide/", "config/")
PENALIZED_PATHS = ("blog/", "homepage/")
REJECT_PHRASES = (
    "i feel",
    "every time",
    "check out",
    "viteconf",
    "view replay",
    "view the replays",
    "is gonna",
    "i think",
    "in my opinion",
    "we think",
    "highly recommend",
    "works great",
    "testimonial",
    "testimonials",
    "announcement",
    "announcements",
)
QUOTE_RE = re.compile(r'[\"“”]')
DEFINITION_PREFIXES = ("what is", "explain", "define")


@dataclass(frozen=True)
class AnswerResult:
    """Structured answer payload returned by the retrieval pipeline."""

    answer: str
    confidence: float
    found: bool
    sources: list[str]
    title: str = ""
    url: str = ""


def search(retriever: ChromaRetriever, query: str, k: int = TOP_K) -> list[RetrievalResult]:
    """Fetch the top semantic matches for a query."""
    return retriever.retrieve(query=query, k=k)


def _unique_urls(results: Sequence[RetrievalResult]) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()
    for result in results:
        if result.url and result.url not in seen:
            seen.add(result.url)
            urls.append(result.url)
    return urls


def _best_chunk_filter(results: Sequence[RetrievalResult]) -> list[RetrievalResult]:
    if not results:
        return []
    best_score = results[0].score
    threshold = best_score * KEEP_RATIO
    return [result for result in results if result.score >= threshold]


def _is_definition_query(query: str) -> bool:
    normalized = normalize_whitespace(query).lower()
    return normalized.startswith(DEFINITION_PREFIXES)


def _reject_sentence(sentence: str) -> bool:
    lowered = sentence.lower()
    if QUOTE_RE.search(sentence):
        return True
    return any(phrase in lowered for phrase in REJECT_PHRASES)


def _chunk_path_bonus(url: str) -> float:
    lowered = url.lower()
    bonus = 0.0
    if any(path in lowered for path in BOOSTED_PATHS):
        bonus += 0.12
    if any(path in lowered for path in PENALIZED_PATHS):
        bonus -= 0.10
    return bonus


def _sentence_term_bonus(sentence: str) -> float:
    lowered = sentence.lower()
    bonus = 0.0
    if any(re.search(rf"\b{re.escape(term)}\b", lowered) for term in PREFERRED_TERMS):
        bonus += 0.08
    return bonus


def _factual_paragraphs(text: str, min_length: int = 1) -> list[str]:
    paragraphs = [normalize_whitespace(part) for part in re.split(r"\n\s*\n+", text or "") if normalize_whitespace(part)]
    return [paragraph for paragraph in paragraphs if len(paragraph) >= min_length]


def _select_definition_paragraph(query: str, results: Sequence[RetrievalResult]) -> str:
    ranked = sorted(
        results,
        key=lambda result: result.score + _chunk_path_bonus(result.url),
        reverse=True,
    )
    for chunk in ranked:
        for paragraph in _factual_paragraphs(chunk.text):
            if _reject_sentence(paragraph):
                continue
            if _sentence_term_bonus(paragraph) > 0.0 or sentence_score(query, paragraph) > 0.0:
                return paragraph
    return "I don't know based on the indexed documents."


def synthesize_answer(query: str, results: Sequence[RetrievalResult]) -> str:
    """Create a concise answer from the strongest chunks."""
    kept_chunks = _best_chunk_filter(results)
    if not kept_chunks:
        return "I don't know based on the indexed documents."

    if _is_definition_query(query):
        return _select_definition_paragraph(query, kept_chunks)

    scored_sentences: list[tuple[float, int, str]] = []
    order_index = 0
    seen_sentences: set[str] = set()

    ranked_chunks = sorted(
        kept_chunks,
        key=lambda result: result.score + _chunk_path_bonus(result.url),
        reverse=True,
    )

    for chunk in ranked_chunks:
        for sentence in split_sentences(chunk.text):
            cleaned = normalize_whitespace(sentence)
            if len(cleaned) < MIN_SENTENCE_LEN or len(cleaned) > MAX_SENTENCE_LEN:
                continue
            if _reject_sentence(cleaned):
                continue
            normalized = cleaned.lower()
            if normalized in seen_sentences:
                continue
            seen_sentences.add(normalized)
            score = sentence_score(query, cleaned) + _sentence_term_bonus(cleaned) + _chunk_path_bonus(chunk.url)
            scored_sentences.append((score, order_index, cleaned))
            order_index += 1

    if not scored_sentences:
        return "I don't know based on the indexed documents."

    scored_sentences.sort(key=lambda item: item[0], reverse=True)
    top_sentences = sorted(scored_sentences[:3], key=lambda item: item[1])

    answer_parts: list[str] = []
    current_length = 0
    for _, _, sentence in top_sentences:
        next_length = current_length + len(sentence) + (1 if answer_parts else 0)
        if next_length > MAX_ANSWER_CHARS:
            if not answer_parts and sentence:
                return sentence
            break
        answer_parts.append(sentence)
        current_length = next_length

    if not answer_parts:
        return "I don't know based on the indexed documents."
    return " ".join(answer_parts).strip()


def answer_query(retriever: ChromaRetriever, query: str) -> AnswerResult:
    """Return a single answer decision with confidence and sources."""
    results = search(retriever, query=query, k=TOP_K)
    if not results:
        return AnswerResult(
            answer="I don't know based on the indexed documents.",
            confidence=0.0,
            found=False,
            sources=[],
        )

    best_score = results[0].score
    average_score = mean(result.score for result in results)

    if best_score < MIN_CONFIDENCE:
        return AnswerResult(
            answer="I don't know based on the indexed documents.",
            confidence=average_score,
            found=False,
            sources=[],
        )

    answer = synthesize_answer(query, results)
    if answer == "I don't know based on the indexed documents.":
        return AnswerResult(
            answer=answer,
            confidence=average_score,
            found=False,
            sources=[],
        )

    sources = _unique_urls(results)
    return AnswerResult(
        answer=answer,
        confidence=average_score,
        found=True,
        sources=sources,
        title=results[0].title,
        url=results[0].url,
    )


def retrieve(query: str, retriever: ChromaRetriever | None = None) -> AnswerResult:
    """Public retrieval entrypoint for a single query."""
    retriever = retriever or ChromaRetriever()
    return answer_query(retriever, query)


def format_answer(query: str, result: AnswerResult) -> str:
    """Format one result block for CLI output."""
    lines: list[str] = []
    lines.append("=" * 50)
    lines.append("QUERY")
    lines.append(query)
    lines.append("=" * 50)
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
    lines.append("=" * 50)
    return "\n".join(lines).rstrip()
