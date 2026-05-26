# semantic-docs-rag
Production-inspired Retrieval-Augmented Generation system for website ingestion, semantic search, and confidence-aware retrieval using Python, Hugging Face embeddings, and ChromaDB.

## Overview
This project turns the Vite documentation website into a searchable local knowledge system. It downloads sitemap URLs, converts meaningful HTML into Markdown, chunks by document structure, embeds the chunks, stores them in a persistent local Chroma database, and answers queries with confidence filtering and out-of-domain rejection.

The main goal is to keep retrieval clean, deterministic, and easy to debug while avoiding the noise introduced by raw HTML and fixed-size chunking.

## Features
- [x] Sitemap-driven website ingestion
- [x] HTML to Markdown knowledge-base generation
- [x] Structural chunking from Markdown headings
- [x] Hugging Face embeddings with `BAAI/bge-small-en-v1.5`
- [x] Persistent local Chroma storage
- [x] Confidence-aware retrieval
- [x] Out-of-domain refusal behavior
- [x] Multi-sentence answer synthesis
- [x] Interactive CLI
- [x] Evaluation report generation

## Architecture
```text
Website
  ↓
Sitemap Extraction
  ↓
Fetch HTML
  ↓
Convert HTML → Markdown
  ↓
Store Markdown Knowledge Base
  ↓
Structural Chunking
  ↓
Embeddings
  ↓
Local ChromaDB
  ↓
Retrieval
  ↓
Confidence Filtering
```

## Tech Stack
| Layer | Tooling | Purpose |
|---|---|---|
| Language | Python | Pipeline, retrieval, and CLI |
| HTML parsing | BeautifulSoup | Clean extraction of meaningful content |
| Embeddings | HuggingFaceEmbeddings | Dense semantic vectors |
| Vector store | ChromaDB | Local persistent retrieval index |
| HTTP | requests | Sitemap and page downloads |
| Testing | unittest | Lightweight validation without extra setup |
| Evaluation | Markdown report | Query-level smoke evaluation |

## Retrieval Pipeline
`sitemap -> HTML fetch -> Markdown KB -> structural chunking -> embedding -> Chroma -> retrieval -> confidence filtering`

1. The sitemap is fetched and deduplicated.
2. Each page is downloaded and cleaned.
3. Clean content is converted to Markdown and stored under `knowledge_base/`.
4. Markdown is chunked by heading structure instead of fixed character windows.
5. Chunks are embedded with `BAAI/bge-small-en-v1.5`.
6. Embeddings are persisted in local Chroma at `./chroma_db`.
7. Retrieval returns the strongest chunks, filters weak matches, and synthesizes a concise answer.

## Installation
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Recommended Python version: `3.11` or `3.12`.

## Quick Start
1. Build the corpus and index:
```powershell
python build.py
```
2. Start the CLI:
```powershell
python main.py
```
3. Ask a question in the prompt.

To generate the evaluation report:
```powershell
python evaluate.py
```

## Example Queries
- `What is Vite?`
- `How does HMR work?`
- `What is the capital of France?`

## Example Outputs
```text
==================================================
QUERY
What is Vite?
==================================================

ANSWER
Vite is a build tool designed to provide a faster and leaner development experience for modern web projects.

CONFIDENCE
0.8200

SOURCES
https://vite.dev/guide/
==================================================
```

```text
ANSWER
I don't know based on indexed documents.
```

## Confidence Threshold Logic
- Retrieve the top `5` chunks.
- Keep chunks with score at least `90%` of the best score.
- Reject the response when the best score is below `0.70`.
- If the query is out of domain or the retrieved content is too weak, return:
  - `I don't know based on indexed documents.`

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
├── knowledge_base/
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
Generated from `docs/evaluation_report.md`:
- top1 relevance: `0.7665`
- false positives: `0`
- avg confidence: `0.6901`
- avg latency: `115.97 ms`

## Design Decisions
- Markdown is stored as an intermediate knowledge base to remove HTML noise before chunking.
- Structural chunking follows heading hierarchy to keep sections stable and debuggable.
- Chroma was selected because it is simple, local, and persistent.
- Confidence thresholds reduce false positives and keep out-of-domain queries from producing fabricated answers.
- Sentence-based synthesis keeps answers concise without requiring an LLM.

## Limitations
- The system is extractive, not generative, so it does not yet write new prose with an LLM.
- Retrieval quality depends on the source document structure and cleaning rules.
- CPU-only embedding can still be slow on some machines.
- The current answer synthesis is heuristic and not a trained reranker.

## Future Improvements
- Add LLM generation for final answers.
- Add cross-encoder reranking.
- Add hybrid keyword + semantic search.
- Add a lightweight web API or UI.
- Add deployment support for cloud or local serving.

## Key Learnings
- RAG quality improves more from document hygiene than from prompt tricks.
- Structural chunking is easier to debug than fixed-size windows.
- Confidence gating is essential for honest refusal behavior.
- A clean intermediate Markdown corpus makes the system much easier to maintain.

## License
This project is licensed under the MIT License. See [LICENSE](LICENSE).

## GitHub Polish
- Suggested repository name: `semantic-docs-rag`
- Suggested description: `Production-inspired Retrieval-Augmented Generation (RAG) system for website ingestion, semantic search, and confidence-aware retrieval using Python, Hugging Face embeddings, and ChromaDB.`
- Suggested topics: `python`, `rag`, `chromadb`, `huggingface`, `beautifulsoup`, `semantic-search`, `retrieval-augmented-generation`, `vite`, `nlp`
- Suggested commit messages:
  - `feat: add markdown knowledge base pipeline`
  - `feat: introduce structural chunking`
  - `feat: add confidence-aware retrieval`
  - `docs: rewrite repository for publication`
  - `test: add smoke tests for synthesis`
- First release notes:
  - `v1.0.0`
  - Markdown knowledge base
  - Structural chunking
  - Persistent Chroma retrieval
  - Confidence-aware refusal behavior
  - Interactive CLI

