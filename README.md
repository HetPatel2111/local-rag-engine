# semantic-docs-rag
Production-style Retrieval-Augmented Generation for website ingestion, semantic search, and grounded Gemini 2.5 Flash answers using Python, Hugging Face embeddings, ChromaDB, and Google AI Studio.

## Overview
This project turns the Vite documentation site into a local knowledge system. It downloads sitemap URLs, cleans HTML, converts pages into Markdown, chunks by document structure, embeds the chunks, stores them in a persistent Chroma database, and answers questions with confidence gating plus Gemini generation.

The architecture is designed to be easy to debug, easy to explain in interviews, and resilient against noisy HTML, weak matches, and out-of-domain questions.

## Features
- [x] Sitemap-driven ingestion
- [x] HTML to Markdown knowledge base
- [x] Structural chunking from Markdown hierarchy
- [x] Hugging Face embeddings with `BAAI/bge-small-en-v1.5`
- [x] Persistent local Chroma storage
- [x] Confidence-aware retrieval filtering
- [x] Out-of-domain refusal behavior
- [x] Gemini 2.5 Flash answer generation
- [x] Interactive CLI
- [x] Markdown evaluation reports

## Architecture
```text
Website
  ->
Sitemap Extraction
  ->
Fetch HTML
  ->
Convert HTML to Markdown
  ->
Store Markdown Knowledge Base
  ->
Structural Chunking
  ->
Embeddings
  ->
Local ChromaDB
  ->
Retrieval
  ->
Confidence Filtering
  ->
Gemini 2.5 Flash
```

## Tech Stack
| Layer | Tooling | Purpose |
|---|---|---|
| Language | Python | Pipeline, retrieval, generation, CLI |
| HTML parsing | BeautifulSoup | Clean extraction of meaningful content |
| Embeddings | HuggingFaceEmbeddings | Dense semantic vectors |
| Vector store | ChromaDB | Local persistent retrieval index |
| Generation | Google AI Studio / Gemini 2.5 Flash | Grounded answer synthesis |
| HTTP | requests | Sitemap and page downloads |
| Testing | unittest | Lightweight validation |

## Retrieval Pipeline
`sitemap -> HTML fetch -> Markdown KB -> structural chunking -> embedding -> Chroma -> retrieval -> confidence filtering -> Gemini`

1. The sitemap is fetched and deduplicated.
2. Each page is downloaded and cleaned.
3. Clean content is converted to Markdown and stored under `knowledge_base/`.
4. Markdown is chunked by heading structure instead of fixed-size windows.
5. Chunks are embedded with `BAAI/bge-small-en-v1.5`.
6. Embeddings are persisted in local Chroma at `./chroma_db`.
7. Retrieval keeps the strongest chunks, filters weak matches, builds a compact context, and sends it to Gemini 2.5 Flash.

## Installation
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Recommended Python version: `3.11` or `3.12`.

## Environment
Create a local `.env` file with:
```env
GOOGLE_API_KEY=your_google_ai_studio_api_key
```

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

To generate the RAG evaluation report:
```powershell
python evaluate.py
```

## Example Queries
- `What is Vite?`
- `How does HMR work?`
- `What is the capital of France?`

## Example Output
```text
==================================================
QUERY
What is Vite?

ANSWER
Vite is a build tool designed to provide a faster and leaner development experience for modern web projects.

CONFIDENCE
0.8200

SOURCES
https://vite.dev/guide/

MODEL
Gemini 2.5 Flash
==================================================
```

```text
ANSWER
I don't know based on the indexed documents.
```

## Confidence Threshold Logic
- Retrieve the top `5` chunks.
- Keep chunks with score at least `90%` of the best score.
- Reject the response when the best score is below `0.70`.
- If the query is out of domain or the retrieved content is too weak, return:
  - `I don't know based on the indexed documents.`

## Folder Structure
```text
repo/
├── src/
│   ├── ingestion/
│   ├── processing/
│   ├── embeddings/
│   ├── retrieval/
│   ├── generation/
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
Run `python evaluate.py` to generate `docs/rag_evaluation.md`.
The report captures:
- retrieval confidence
- generation latency
- answer quality
- hallucination count

## Design Decisions
- Markdown is stored as an intermediate knowledge base to remove HTML noise before chunking.
- Structural chunking follows heading hierarchy to keep sections stable and debuggable.
- Chroma was selected because it is local, persistent, and simple to inspect.
- Confidence thresholds reduce false positives and keep out-of-domain queries from producing fabricated answers.
- Gemini is only called after retrieval passes the confidence gate.

## Limitations
- The system depends on the quality of the source documentation and the cleaning rules.
- CPU-only embedding can still be slow on some machines.
- Gemini output quality depends on retrieved context quality.
- The current design is grounded and concise, but not fully autonomous or agentic.

## Future Improvements
- Add cross-encoder reranking.
- Add hybrid keyword + semantic search.
- Add a lightweight web API or UI.
- Add deployment support for cloud or local serving.
- Add stronger answer evaluation with human review.

## Key Learnings
- RAG quality improves more from document hygiene than from prompt tricks.
- Structural chunking is easier to debug than fixed-size windows.
- Confidence gating is essential for honest refusal behavior.
- A clean intermediate Markdown corpus makes the system much easier to maintain.

## License
This project is licensed under the MIT License. See [LICENSE](LICENSE).

## GitHub Polish
- Suggested repository name: `semantic-docs-rag`
- Suggested description: `Production-inspired Retrieval-Augmented Generation (RAG) system for website ingestion, semantic search, and confidence-aware retrieval using Python, Hugging Face embeddings, ChromaDB, and Gemini 2.5 Flash.`
- Suggested topics: `python`, `rag`, `chromadb`, `huggingface`, `beautifulsoup`, `semantic-search`, `retrieval-augmented-generation`, `gemini`, `vite`, `nlp`
- Suggested commit messages:
  - `feat: add markdown knowledge base pipeline`
  - `feat: introduce structural chunking`
  - `feat: add Gemini generation`
  - `docs: rewrite repository for publication`
  - `test: add smoke tests for synthesis`
- First release notes:
  - `v1.0.0`
  - Markdown knowledge base
  - Structural chunking
  - Persistent Chroma retrieval
  - Confidence-aware refusal behavior
  - Gemini 2.5 Flash generation
  - Interactive CLI
