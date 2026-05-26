# Vite Docs RAG Engine
A local Retrieval-Augmented Generation pipeline that ingests the Vite documentation, builds a persistent Chroma index, and returns confidence-gated answers from retrieved chunks.

## Overview
This project solves a practical documentation question-answering problem: how to turn a large public website into a searchable, local RAG system without relying on a hosted vector database or an external application server.

The pipeline ingests `sitemap.xml`, downloads pages, cleans HTML, chunks content, generates Hugging Face embeddings, stores vectors in local Chroma, and exposes a CLI that answers queries with confidence thresholding and out-of-domain rejection.

## Features
- [x] Website ingestion from `sitemap.xml`
- [x] HTML fetching and content cleaning
- [x] Recursive chunking with overlap
- [x] Hugging Face embeddings with `BAAI/bge-small-en-v1.5`
- [x] Persistent local Chroma database
- [x] Semantic retrieval with score sorting
- [x] Confidence threshold filtering
- [x] Out-of-domain rejection
- [x] Multi-chunk answer synthesis
- [x] CLI interaction

## Architecture
```text
                    +----------------------+
                    |   Vite sitemap.xml   |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    |   Ingestion layer    |
                    | sitemap -> URLs      |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    |   HTML cleaning      |
                    | remove noise/tags    |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    |   Chunking layer     |
                    | 600 chars / overlap  |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    |   Embeddings layer   |
                    | BAAI/bge-small-en-v1.5
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    |   Local Chroma DB    |
                    |   ./chroma_db        |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    | Retrieval + gating   |
                    | threshold + synthesis|
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    |        CLI           |
                    +----------------------+
```

## Tech Stack
| Layer | Tooling | Purpose |
|---|---|---|
| Language | Python | End-to-end pipeline and CLI |
| HTML parsing | BeautifulSoup | Clean extraction from HTML pages |
| Embeddings | HuggingFaceEmbeddings | Semantic vector generation |
| Vector store | ChromaDB | Persistent local retrieval index |
| Orchestration | LangChain | Embedding integration and supporting utilities |
| HTTP | requests | Sitemap and page downloads |
| Testing | pytest | Smoke checks and unit tests |

## Retrieval Pipeline
`sitemap -> clean -> chunk -> embedding -> Chroma -> retrieval`

1. The sitemap is downloaded and parsed into canonical URLs.
2. Pages are fetched and cleaned to remove navigation, headers, scripts, and other page chrome.
3. Clean documents are chunked with overlap so semantically related text stays together.
4. Chunks are embedded with `BAAI/bge-small-en-v1.5`.
5. Chroma stores the vectors locally in `./chroma_db`.
6. Queries are embedded, matched against the index, confidence-gated, and synthesized into a concise answer.

## Installation
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Recommended Python version: `3.11` or `3.12`.

## Quick Start
1. Ingest and build the index:
```powershell
python step1.py
python step2.py
python step3.py
python step4.py
python step5.py
```
2. Start the CLI:
```powershell
python main.py
```
3. Ask questions interactively.

## Example Queries
- `What is Vite?`
- `How does HMR work?`
- `What is the capital of France?`

## Example Outputs
Representative CLI output:
```text
==================================================
QUERY
What is Vite?
==================================================

ANSWER
Vite is a modern frontend build tool. It starts fast and serves source files over native ES modules. It also provides
Hot Module Replacement for rapid local development.

CONFIDENCE
0.8123

SOURCES
https://vite.dev/
https://vite.dev/guide/
==================================================
```

For an out-of-domain query:
```text
ANSWER
I don't know based on the indexed documents.
```

## Confidence Threshold Logic
- The retriever ranks the top `5` chunks.
- If the best score is below `MIN_CONFIDENCE = 0.70`, the system refuses to answer.
- If the query is in-domain, the answer is synthesized from the strongest chunks only.
- The output remains conservative so the system does not invent answers for unrelated queries.

## Folder Structure
```text
repo/
├── src/
│   ├── ingestion/
│   ├── processing/
│   ├── embeddings/
│   ├── retrieval/
│   ├── evaluation/
│   └── utils/
├── data/
├── tests/
├── docs/
├── screenshots/
├── README.md
├── requirements.txt
├── .gitignore
├── LICENSE
└── main.py
```

## Evaluation Results
Smoke-test checks on the indexed Vite corpus:
- `What is HMR in Vite?` returned a confident in-domain answer with matching sources.
- `What is Vite?` returned a confident in-domain answer.
- `What is the capital of France?` returned `I don't know based on the indexed documents.`

## Design Decisions
- Chroma was chosen because it is simple, local-first, and persistent without requiring external infrastructure.
- Hugging Face embeddings were chosen to keep the system fully reproducible and easy to run locally.
- Confidence gating was added to reduce false positives for unrelated questions.
- Chunk overlap was kept to preserve context across adjacent sections.
- Sentence-level synthesis was preferred over raw chunk concatenation to keep answers concise and readable.

## Limitations
- The system does not generate novel answers with an LLM yet.
- Retrieval quality depends on the quality of the source documentation and chunking strategy.
- The current answer synthesis is extractive rather than generative.
- Running the embedding model can still be slow on CPU-only machines.

## Future Improvements
- Add LLM generation for richer final answers.
- Add reranking for more precise document selection.
- Add hybrid search to combine dense and keyword retrieval.
- Add deployment options for a web API or lightweight UI.

## Key Learnings
- Good RAG systems depend more on retrieval quality than on answer formatting.
- Clean text extraction matters as much as embedding choice.
- Confidence thresholds are necessary to prevent hallucinated answers.
- Local persistence makes the pipeline easy to iterate on and demo.

## License
This project is licensed under the MIT License. See [LICENSE](LICENSE).

## GitHub Publishing Notes
- First release notes:
  - `v1.0.0`
  - Local Vite documentation ingestion
  - Persistent Chroma index
  - Confidence-gated retrieval
  - Extractive multi-chunk answer synthesis
  - Interactive CLI
