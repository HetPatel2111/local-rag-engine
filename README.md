# semantic-docs-rag
Local-first retrieval-augmented generation for website ingestion, semantic search, and grounded answers using Python, local chunk retrieval, ChromaDB, and optional Gemini generation.

## Overview
This project turns the Vite documentation site into a local knowledge system. It downloads sitemap URLs, cleans HTML, converts pages into Markdown, chunks by document structure, and answers questions with confidence gating plus an offline extractive fallback.

The default setup is now fully local:
- retrieval runs over `data/chunks/chunks.json`
- answers default to `GENERATION_MODE=extractive`
- the browser UI talks to the local FastAPI backend

## Features
- [x] Sitemap-driven ingestion
- [x] HTML to Markdown knowledge base
- [x] Structural chunking from Markdown hierarchy
- [x] Local chunk retrieval
- [x] Persistent local Chroma storage
- [x] Confidence-aware retrieval filtering
- [x] Out-of-domain refusal behavior
- [x] Offline extractive answer generation
- [x] Interactive CLI
- [x] FastAPI backend
- [x] React frontend

## Architecture
```text
Website
  ->
Sitemap extraction
  ->
Fetch HTML
  ->
Convert HTML to Markdown
  ->
Store Markdown knowledge base
  ->
Structural chunking
  ->
Local chunk corpus
  ->
Local retrieval
  ->
Confidence filtering
  ->
Answer formatting
```

## Tech Stack
| Layer | Tooling | Purpose |
|---|---|---|
| Language | Python | Pipeline, retrieval, generation, CLI |
| HTML parsing | BeautifulSoup | Clean extraction of meaningful content |
| Retrieval | Local lexical scorer | Offline matching over the chunk corpus |
| Vector store | ChromaDB | Optional persistent index for future semantic builds |
| Generation | Offline extractive fallback | Grounded answer synthesis without external APIs |
| HTTP | FastAPI | Local API server |
| Frontend | React + Vite | Browser UI |
| Testing | unittest | Lightweight validation |

## Retrieval Pipeline
`sitemap -> HTML fetch -> Markdown KB -> structural chunking -> local chunk corpus -> retrieval -> confidence filtering -> extractive answer`

1. The sitemap is fetched and deduplicated.
2. Each page is downloaded and cleaned.
3. Clean content is converted to Markdown and stored under `knowledge_base/`.
4. Markdown is chunked by heading structure instead of fixed-size windows.
5. Chunks are written to `data/chunks/chunks.json`.
6. Local retrieval scores the corpus directly.
7. Strong matches are turned into grounded answers with the extractive fallback path.

## Local Setup
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Recommended Python version: `3.11` or `3.12`.

## Environment
Create a local `.env` file with:
```env
RETRIEVAL_BACKEND=local
GENERATION_MODE=extractive
```

If you want Gemini generation instead of offline extractive answers, add:
```env
GOOGLE_API_KEY=your_google_ai_studio_api_key
GENERATION_MODE=gemini
```

## Run Local
1. Build the corpus and local artifacts:
```powershell
python build.py
```
2. Start the FastAPI server:
```powershell
python backend\main.py
```
3. Start the React UI:
```powershell
cd frontend
npm run dev
```
4. Optional CLI:
```powershell
python main.py
```

The browser UI calls `POST /ask` on `http://localhost:8000` by default. To override, set `VITE_API_BASE_URL` in `frontend/.env.local`.

## Example Queries
- `What is Vite?`
- `How does HMR work?`
- `What is the capital of France?`

## Confidence Threshold Logic
- Retrieve the top `5` chunks.
- Keep chunks with score at least `90%` of the best score.
- Reject the response when the best score is below `0.70`.
- If the query is out of domain or the retrieved content is too weak, return:
  - `I don't know based on the indexed documents.`

## Frontend Notes
The UI now uses a stronger visual hierarchy:
- a layered hero section
- quick example prompts
- clearer runtime status
- richer answer cards
- improved source cards

## Optional Qdrant
If you want Qdrant instead of the local retriever, set:
```env
QDRANT_URL=https://xxxxxx.cloud.qdrant.io
QDRANT_API_KEY=your_qdrant_api_key
QDRANT_COLLECTION=vite_docs
RETRIEVAL_BACKEND=qdrant
```

## License
This project is licensed under the MIT License. See [LICENSE](LICENSE).
