"""Cooperative cancellation for bounded-memory file inspection.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from threading import Event


class InspectionCancelled(Exception):
    """Raised when a caller cancels an in-progress inspection."""


class CancellationToken:
    """Thread-safe cooperative cancellation flag."""

    def __init__(self) -> None:
        self._cancelled = Event()

    def cancel(self) -> None:
        self._cancelled.set()

    @property
    def is_cancelled(self) -> bool:
        return self._cancelled.is_set()

    def raise_if_cancelled(self) -> None:
        if self.is_cancelled:
            raise InspectionCancelled
