# Project Overview

## Architecture
The repository is organized around a Markdown knowledge base and a grounded generation layer.

1. `src/ingestion/sitemap.py` loads and deduplicates sitemap URLs.
2. `src/processing/html_cleaner.py` removes site chrome and converts HTML to Markdown.
3. `src/processing/chunker.py` splits Markdown by heading hierarchy.
4. `src/embeddings/huggingface.py` creates normalized embeddings.
5. `src/pipeline/build.py` writes the Chroma index.
6. `src/retrieval/retriever.py` loads the persistent collection.
7. `src/generation/context_builder.py` builds a compact prompt context.
8. `src/generation/llm.py` calls Gemini 2.5 Flash through Google AI Studio.
9. `src/retrieval/answering.py` applies the confidence gate and formats the final output.
10. `main.py` and `step6.py` provide the CLI entrypoint.

## Tradeoffs
- A Markdown knowledge base adds one more build stage, but it removes HTML noise and makes debugging much easier.
- Structural chunking is more deterministic than fixed-size splitting, but it requires cleaner source markup.
- The system is grounded before generation, which reduces hallucination risk compared with direct prompt-only generation.
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
- Only chunks within `90%` of the best score are considered for generation.
- If the best score is below `0.70`, the system refuses to answer.
- Gemini is never called when the confidence gate fails.

## Evaluation Notes
- The repository includes a generated evaluation report in `docs/rag_evaluation.md`.
- The report captures retrieval confidence, generation latency, answer quality, and hallucination count.

## Reviewer Notes
- The code favors clear module boundaries and typed data models.
- Build artifacts are separated from source code.
- The repository is ready for a portfolio review or a technical screening discussion.
