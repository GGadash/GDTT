"""Explicit, user-overridable file inspection options.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InspectionOptions:
    """Overrides for consequential auto-detection decisions."""

    worksheet: str | None = None
    encoding: str | None = None
    delimiter: str | None = None
    has_header: bool | None = None
    sample_limit: int = 1_000

    def __post_init__(self) -> None:
        if self.delimiter is not None and len(self.delimiter) != 1:
            raise ValueError("Delimiter must contain exactly one character.")
        if self.sample_limit < 10:
            raise ValueError("sample_limit must be at least 10.")
