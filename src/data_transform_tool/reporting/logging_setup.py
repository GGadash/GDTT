"""Privacy-preserving local application logging.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from data_transform_tool.settings.paths import logs_directory


def configure_logging() -> None:
    """Configure a rotating local log without recording dataset contents."""
    root_logger = logging.getLogger()
    if any(getattr(handler, "_dtt_handler", False) for handler in root_logger.handlers):
        return

    destination = logs_directory()
    destination.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(
        destination / "data-transform-tool.log",
        maxBytes=2_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    handler._dtt_handler = True  # type: ignore[attr-defined]
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
