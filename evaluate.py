"""Run the phase-2 RAG evaluation suite and write a markdown report."""

from __future__ import annotations

import logging
from pathlib import Path

from src.evaluation.rag_report import run_evaluation, write_report
from src.retrieval.retriever import ChromaRetriever
from src.utils.app_logging import configure_logging


def main() -> None:
    """Run the standard evaluation queries and write ``docs/rag_evaluation.md``."""
    configure_logging(log_file="rag_evaluation.log")
    logging.getLogger(__name__).info("Starting RAG evaluation")
    retriever = ChromaRetriever()
    rows = run_evaluation(retriever)
    output_path = write_report(Path("docs/rag_evaluation.md"), rows)
    print(output_path.as_posix())


if __name__ == "__main__":
    main()
