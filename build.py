"""Build the semantic-docs-rag pipeline."""

from __future__ import annotations

import logging

from src.pipeline.build import build_all


def main() -> None:
    """Run the full indexing pipeline."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    stats = build_all()
    print(f"urls: {stats.urls}")
    print(f"pages_written: {stats.pages_written}")
    print(f"chunks_written: {stats.chunks_written}")
    print(f"documents_indexed: {stats.documents_indexed}")


if __name__ == "__main__":
    main()

