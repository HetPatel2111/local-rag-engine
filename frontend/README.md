# Frontend (React + Vite)

This frontend connects to the local FastAPI backend (`POST /ask`) and renders:

- Answer
- Confidence (progress bar)
- Sources (clickable cards)
- Model and latency

## Run

From `frontend/`:

```bash
npm install
npm run dev
```

By default it calls `http://localhost:8000`.

To override, create `frontend/.env.local`:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

