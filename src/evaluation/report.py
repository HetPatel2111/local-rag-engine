"""Generate a markdown evaluation report for the retrieval system."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import statistics
import time

from src.retrieval.answering import answer_query
from src.retrieval.retriever import ChromaRetriever


@dataclass(frozen=True)
class EvaluationCase:
    """A single evaluation query and its expected domain label."""

    query: str
    expected_answerable: bool


@dataclass(frozen=True)
class EvaluationRow:
    """A single measured evaluation row."""

    query: str
    expected_answerable: bool
    found: bool
    confidence: float
    latency_ms: float
    answer: str
    sources: list[str]


DEFAULT_CASES = [
    EvaluationCase("What is Vite?", True),
    EvaluationCase("What is HMR?", True),
    EvaluationCase("Why is Vite fast?", True),
    EvaluationCase("How do env variables work?", True),
    EvaluationCase("What is the capital of France?", False),
]


def run_evaluation(retriever: ChromaRetriever, cases: list[EvaluationCase] | None = None) -> list[EvaluationRow]:
    """Run evaluation queries against the retriever."""
    cases = cases or DEFAULT_CASES
    rows: list[EvaluationRow] = []

    for case in cases:
        start = time.perf_counter()
        result = answer_query(retriever, case.query)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        rows.append(
            EvaluationRow(
                query=case.query,
                expected_answerable=case.expected_answerable,
                found=result.found,
                confidence=result.confidence,
                latency_ms=elapsed_ms,
                answer=result.answer,
                sources=result.sources,
            )
        )

    return rows


def _bucket_confidence(confidence: float) -> str:
    if confidence >= 0.85:
        return "high"
    if confidence >= 0.70:
        return "medium"
    return "low"


def generate_report(rows: list[EvaluationRow]) -> str:
    """Render evaluation results as markdown."""
    answerable_rows = [row for row in rows if row.expected_answerable]
    out_of_domain_rows = [row for row in rows if not row.expected_answerable]
    false_positives = [row for row in out_of_domain_rows if row.found]
    confidences = [row.confidence for row in rows]
    latencies = [row.latency_ms for row in rows]
    top1_relevance = statistics.mean(row.confidence for row in answerable_rows if row.found) if any(row.found for row in answerable_rows) else 0.0

    confidence_distribution = {
        "high": sum(1 for confidence in confidences if confidence >= 0.85),
        "medium": sum(1 for confidence in confidences if 0.70 <= confidence < 0.85),
        "low": sum(1 for confidence in confidences if confidence < 0.70),
    }

    lines: list[str] = []
    lines.append("# Evaluation Report")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- top1 relevance: {top1_relevance:.4f}")
    lines.append(f"- false positives: {len(false_positives)}")
    lines.append(f"- avg confidence: {statistics.mean(confidences):.4f}" if confidences else "- avg confidence: 0.0000")
    lines.append(f"- avg latency ms: {statistics.mean(latencies):.2f}" if latencies else "- avg latency ms: 0.00")
    lines.append("")
    lines.append("## Confidence Distribution")
    for label, count in confidence_distribution.items():
        lines.append(f"- {label}: {count}")
    lines.append("")
    lines.append("## Query Results")
    lines.append("| query | expected | found | confidence | latency_ms | sources |")
    lines.append("|---|---:|---:|---:|---:|---|")
    for row in rows:
        sources = ", ".join(row.sources) if row.sources else "-"
        lines.append(
            f"| {row.query} | {str(row.expected_answerable).lower()} | {str(row.found).lower()} | "
            f"{row.confidence:.4f} | {row.latency_ms:.2f} | {sources} |"
        )
    lines.append("")
    lines.append("## Notes")
    lines.append("- The out-of-domain query should remain unanswered.")
    lines.append("- Confidence is used as a refusal gate, not as a generative guarantee.")
    return "\n".join(lines)


def write_report(path: Path, rows: list[EvaluationRow]) -> Path:
    """Write the markdown report to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    report = generate_report(rows)
    path.write_text(report + "\n", encoding="utf-8")
    return path

