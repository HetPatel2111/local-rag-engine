"""Environment variable helpers for local development."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

_DOTENV_LOADED = False


def _parse_env_lines(lines: Iterable[str]) -> None:
    """Populate ``os.environ`` from ``KEY=VALUE`` lines."""
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue

        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def load_dotenv(path: str | Path = ".env") -> None:
    """Load a local `.env` file once without adding a new dependency."""
    global _DOTENV_LOADED
    if _DOTENV_LOADED:
        return

    env_path = Path(path)
    if env_path.exists():
        _parse_env_lines(env_path.read_text(encoding="utf-8").splitlines())

    _DOTENV_LOADED = True


def getenv(key: str, default: str = "") -> str:
    """Read an environment variable after ensuring `.env` is loaded."""
    load_dotenv()
    return os.getenv(key, default)
