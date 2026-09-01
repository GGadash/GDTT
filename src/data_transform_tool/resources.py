"""Packaged visual resources for GDTT.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QIcon


def icon_path(extension: str = "svg") -> Path:
    """Return the bundled application icon path for a supported format."""
    normalized = extension.casefold().removeprefix(".")
    if normalized not in {"svg", "png", "ico"}:
        raise ValueError(f"Unsupported application icon format: {extension}.")
    return (
        Path(__file__).resolve().parent
        / "resources"
        / "icons"
        / f"data-transform-tool.{normalized}"
    )


def application_icon() -> QIcon:
    """Load the canonical icon shared by source and packaged execution."""
    return QIcon(str(icon_path()))
