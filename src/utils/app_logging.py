"""Application logging helpers."""

from __future__ import annotations

import logging
from pathlib import Path


def configure_logging(*, log_dir: str = "logs", log_file: str = "rag.log", level: int = logging.INFO) -> None:
    """Configure console and file logging for the application."""
    output_dir = Path(log_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

    log_path = output_dir / log_file
    has_console_handler = any(isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler) for handler in root_logger.handlers)
    has_file_handler = any(
        isinstance(handler, logging.FileHandler) and Path(getattr(handler, "baseFilename", "")).resolve() == log_path.resolve()
        for handler in root_logger.handlers
    )

    if not has_console_handler:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    if not has_file_handler:
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
