"""Interactive CLI for the local RAG engine."""

from __future__ import annotations

import sys

from src.retrieval.answering import answer_query, format_answer
from src.retrieval.retriever import ChromaRetriever
from src.utils.app_logging import configure_logging


def main() -> None:
    """Run a query-driven CLI against the local Chroma database."""
    configure_logging()
    retriever = ChromaRetriever()

    initial_query = " ".join(sys.argv[1:]).strip()
    if initial_query:
        result = answer_query(retriever, initial_query)
        print(format_answer(initial_query, result))
        return

    while True:
        query = input("Enter query (or 'exit'): ").strip()
        if not query:
            continue
        if query.lower() in {"exit", "quit"}:
            break

        result = answer_query(retriever, query)
        print(format_answer(query, result))
        print()


if __name__ == "__main__":
    main()

