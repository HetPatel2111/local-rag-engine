"""Generate a phase-2 RAG evaluation report."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import statistics
import time

from src.generation.llm import REFUSAL_MESSAGE
from src.retrieval.answering import answer_query
from src.retrieval.retriever import ChromaRetriever


@dataclass(frozen=True)
class RagEvaluationCase:
    """A single query used to smoke-test the end-to-end RAG pipeline."""

    query: str
    expected_answerable: bool


@dataclass(frozen=True)
class RagEvaluationRow:
    """Measured output for a single evaluation query."""

    query: str
    expected_answerable: bool
    found: bool
    confidence: float
    latency_ms: float
    answer: str
    sources: list[str]
    token_count: int
    response_length: int


DEFAULT_CASES = [
    RagEvaluationCase("What is Vite?", True),
    RagEvaluationCase("What is HMR?", True),
    RagEvaluationCase("Why is Vite fast?", True),
    RagEvaluationCase("How do env variables work?", True),
    RagEvaluationCase("What is the capital of France?", False),
]


def run_evaluation(retriever: ChromaRetriever, cases: list[RagEvaluationCase] | None = None) -> list[RagEvaluationRow]:
    """Run the standard RAG evaluation set."""
    rows: list[RagEvaluationRow] = []
    for case in cases or DEFAULT_CASES:
        started = time.perf_counter()
        result = answer_query(retriever, case.query)
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        rows.append(
            RagEvaluationRow(
                query=case.query,
                expected_answerable=case.expected_answerable,
                found=result.found,
                confidence=result.confidence,
                latency_ms=max(elapsed_ms, result.latency_ms),
                answer=result.answer,
                sources=result.sources,
                token_count=result.token_count,
                response_length=result.response_length,
            )
        )
    return rows


def _answer_quality(rows: list[RagEvaluationRow]) -> float:
    """Estimate answer quality using answerable-query success rate."""
    answerable_rows = [row for row in rows if row.expected_answerable]
    if not answerable_rows:
        return 0.0
    successful = [
        row
        for row in answerable_rows
        if row.found and row.answer.strip() and row.answer.strip() != REFUSAL_MESSAGE
    ]
    return len(successful) / len(answerable_rows)


def generate_report(rows: list[RagEvaluationRow]) -> str:
    """Render the report as markdown."""
    confidences = [row.confidence for row in rows]
    latencies = [row.latency_ms for row in rows]
    hallucinations = [
        row for row in rows if not row.expected_answerable and row.found and row.answer.strip() != REFUSAL_MESSAGE
    ]

    lines: list[str] = []
    lines.append("# RAG Evaluation Report")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- retrieval confidence: {statistics.mean(confidences):.4f}" if confidences else "- retrieval confidence: 0.0000")
    lines.append(f"- generation latency ms: {statistics.mean(latencies):.2f}" if latencies else "- generation latency ms: 0.00")
    lines.append(f"- answer quality: {_answer_quality(rows):.4f}")
    lines.append(f"- hallucination count: {len(hallucinations)}")
    lines.append("")
    lines.append("## Query Results")
    lines.append("| query | expected | found | confidence | latency_ms | tokens | response_length | sources |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---|")
    for row in rows:
        sources = ", ".join(row.sources) if row.sources else "-"
        lines.append(
            f"| {row.query} | {str(row.expected_answerable).lower()} | {str(row.found).lower()} | "
            f"{row.confidence:.4f} | {row.latency_ms:.2f} | {row.token_count} | {row.response_length} | {sources} |"
        )
    lines.append("")
    lines.append("## Notes")
    lines.append("- Answer quality is estimated from answerable-query success rate.")
    lines.append("- Hallucinations are counted when an out-of-domain query produces a grounded answer.")
    lines.append("- Confidence is a retrieval gate; Gemini only runs when the gate passes.")
    return "\n".join(lines)


def write_report(path: Path, rows: list[RagEvaluationRow]) -> Path:
    """Write the markdown report to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(generate_report(rows) + "\n", encoding="utf-8")
    return path
