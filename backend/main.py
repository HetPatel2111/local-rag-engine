"""Uvicorn entrypoint for the FastAPI backend."""

from __future__ import annotations

import sys
from pathlib import Path
import uvicorn


if __name__ == "__main__":
    # When invoked as `python backend/main.py`, Python adds `backend/` (this file's
    # directory) to `sys.path`, which makes `import backend...` fail because it
    # would require a nested `backend/backend` directory. Ensure the repo root is
    # on `sys.path` so the `backend` package can be imported reliably.
    repo_root = Path(__file__).resolve().parent.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
