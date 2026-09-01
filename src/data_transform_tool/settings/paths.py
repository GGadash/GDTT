"""Operating-system-specific local storage paths.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

import os
from pathlib import Path

from platformdirs import user_data_path, user_log_path

APP_AUTHOR = "Gadash (Akila DJ)"
APP_NAME = "GDTT"
DATA_DIRECTORY_OVERRIDE = "DTT_DATA_DIRECTORY"
LOG_DIRECTORY_OVERRIDE = "DTT_LOG_DIRECTORY"


def _override(name: str) -> Path | None:
    value = os.environ.get(name)
    return Path(value).expanduser().resolve() if value else None


def application_data_directory() -> Path:
    """Return the private per-user application data directory."""
    return _override(DATA_DIRECTORY_OVERRIDE) or Path(
        user_data_path(APP_NAME, APP_AUTHOR, ensure_exists=False)
    )


def logs_directory() -> Path:
    """Return the private per-user log directory."""
    return _override(LOG_DIRECTORY_OVERRIDE) or Path(
        user_log_path(APP_NAME, APP_AUTHOR, ensure_exists=False)
    )


def templates_directory() -> Path:
    """Return the private per-user recipe-template directory."""
    return application_data_directory() / "templates"


def styles_directory() -> Path:
    """Return the private per-user formatted-XLSX style directory."""
    return application_data_directory() / "xlsx-styles"
