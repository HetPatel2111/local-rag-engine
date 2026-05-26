# Project Overview

## Architecture
The repository is organized around a Markdown knowledge base rather than raw HTML.

1. `src/ingestion/sitemap.py` loads and deduplicates sitemap URLs.
2. `src/processing/html_cleaner.py` removes site chrome and converts HTML to Markdown.
3. `src/processing/chunker.py` splits Markdown by heading hierarchy.
4. `src/embeddings/huggingface.py` creates normalized embeddings.
5. `src/pipeline/build.py` writes the Chroma index.
6. `src/retrieval/retriever.py` loads the persistent collection.
7. `src/retrieval/answering.py` filters weak results and synthesizes the final answer.
8. `main.py` and `step6.py` provide the CLI entrypoint.

## Tradeoffs
- A Markdown knowledge base adds one more build stage, but it removes HTML noise and makes debugging much easier.
- Structural chunking is more deterministic than fixed-size splitting, but it requires cleaner source markup.
- The system is extractive rather than generative, which reduces hallucination risk.
- Chroma keeps the stack simple and local, but it is not a distributed retrieval backend.

## Chunking Decisions
- The document title is taken from the page metadata or the most meaningful heading.
- `#` represents the document title.
- `##` and `###` drive section boundaries.
- A chunk is split when it grows beyond roughly `1200` characters.
- Small neighboring chunks are merged when they are below `300` characters.

## Why Chroma
- It persists locally on disk.
- It keeps the demo self-contained.
- It is easy to inspect during development.
- It fits the scale of a documentation corpus without added infrastructure.

## Confidence Threshold
- The retriever keeps the top `5` matches.
- Only chunks within `90%` of the best score are considered for synthesis.
- If the best score is below `0.70`, the system refuses to answer.
- This prevents weak semantic matches from being presented as facts.

## Evaluation Notes
- The repository includes a generated evaluation report in `docs/evaluation_report.md`.
- The report captures top1 relevance, false positives, confidence distribution, and latency.

## Reviewer Notes
- The code favors clear module boundaries and typed data models.
- Build artifacts are separated from source code.
- The repository is ready for a portfolio review or a technical screening discussion.

