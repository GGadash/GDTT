"""Immutable temporal format and timestamp-semantic models.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum


class TemporalKind(StrEnum):
    DATE = "date"
    TIME = "time"
    DATETIME = "datetime"


class TimestampRole(StrEnum):
    START = "start"
    END = "end"
    MIDPOINT = "midpoint"
    INSTANTANEOUS = "instantaneous"
    UNKNOWN = "unknown"
    CUSTOM = "custom"


class IntervalEndMode(StrEnum):
    RETAIN = "retain"
    CALCULATE = "calculate"
    SEMANTIC_NORMALIZE = "semantic_normalize"


@dataclass(frozen=True)
class DateTimeFormatProfile:
    profile_id: str
    group: str
    name: str
    display_pattern: str
    python_patterns: tuple[str, ...]
    temporal_kind: TemporalKind
    output_pattern: str
    colonize_offset: bool = False
    utc: bool = False
    input_regex: str | None = None


@dataclass(frozen=True)
class TimestampSemantics:
    """Meaning of one timestamp column, kept separate from its printed format."""

    column: str
    role: TimestampRole
    duration: timedelta | None = None

    def __post_init__(self) -> None:
        if self.duration is not None and self.duration <= timedelta(0):
            raise ValueError("Sampling duration must be positive.")
