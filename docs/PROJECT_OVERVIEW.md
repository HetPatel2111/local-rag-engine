# Project Overview

## Architecture
The system is organized as a local, offline-capable RAG pipeline:

1. `src/ingestion/sitemap.py` downloads and parses `sitemap.xml`.
2. `src/processing/html_cleaner.py` extracts readable document text.
3. `src/processing/chunker.py` turns pages into overlapping chunks.
4. `src/embeddings/huggingface.py` creates normalized embeddings.
5. `src/retrieval/retriever.py` stores and queries vectors in Chroma.
6. `src/retrieval/answering.py` gates confidence and synthesizes a concise answer.
7. `main.py` exposes the interactive CLI.

## Tradeoffs
- The pipeline is intentionally local-first to avoid dependency on paid infrastructure.
- The answer stage is extractive, not generative, which reduces hallucinations but limits fluency.
- Sentence-level synthesis improves readability while keeping implementation lightweight.
- Chroma was chosen for simplicity and persistence rather than maximum scale.

## Chunking Decisions
- Chunk size: `600` characters
- Chunk overlap: `100` characters
- Rationale: this keeps chunks small enough for stable retrieval while preserving local context across section boundaries.

## Why Chroma
- Persistent on-disk storage
- Easy local setup
- Strong fit for single-machine demos and portfolio projects
- Simple query interface for dense vector search

## Confidence Threshold
- Retrieval is intentionally conservative.
- If the best retrieved chunk is below the confidence threshold, the system returns a refusal instead of guessing.
- This is especially important for out-of-domain questions and weak semantic matches.

## Notes for Reviewers
- The project was designed to be easy to inspect, reproduce, and demo locally.
- The code favors clarity and maintainability over framework complexity.
- The repository keeps legacy step scripts for reference, but `main.py` is the recommended entrypoint.

