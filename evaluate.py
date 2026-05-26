"""Generate an evaluation report for the retrieval system."""

from __future__ import annotations

import logging
from pathlib import Path

from src.evaluation.report import run_evaluation, write_report
from src.retrieval.retriever import ChromaRetriever


def main() -> None:
    """Run smoke evaluation queries and write a markdown report."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    retriever = ChromaRetriever()
    rows = run_evaluation(retriever)
    output_path = write_report(Path("docs/evaluation_report.md"), rows)
    print(output_path.as_posix())


if __name__ == "__main__":
    main()

