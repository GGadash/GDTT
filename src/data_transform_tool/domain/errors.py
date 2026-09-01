"""Central application error vocabulary.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from enum import StrEnum


class Severity(StrEnum):
    """User-visible diagnostic levels from the product specification."""

    INFORMATION = "Information"
    WARNING = "Warning"
    BLOCKING_ERROR = "Blocking Error"


class AppError(Exception):
    """Base exception carrying safe user text and optional technical detail."""

    def __init__(
        self,
        user_message: str,
        *,
        severity: Severity = Severity.BLOCKING_ERROR,
        detail: str | None = None,
    ) -> None:
        super().__init__(user_message)
        self.user_message = user_message
        self.severity = severity
        self.detail = detail
