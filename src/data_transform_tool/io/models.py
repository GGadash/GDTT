"""Immutable file-inspection and profiling results.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class FileKind(StrEnum):
    """File families supported by the Phase 2 reader registry."""

    CSV = "CSV"
    TSV = "TSV"
    TXT = "Delimited TXT"
    XLSX = "XLSX"


class SemanticType(StrEnum):
    """Advisory semantic types detected during inspection."""

    EMPTY = "Empty"
    INTEGER = "Integer"
    DECIMAL = "Decimal / Numeric"
    BOOLEAN = "Boolean"
    DATE = "Date"
    TIME = "Time"
    DATETIME = "DateTime"
    CATEGORY = "Category / Text-like"
    TEXT = "Text"
    AUTO = "Auto / Unconfirmed"


@dataclass(frozen=True)
class MissingMarkerDetection:
    """A value that may represent missing data and requires user confirmation."""

    value: str
    count: int


@dataclass(frozen=True)
class ColumnProfile:
    """Advisory statistics and type inference for one source column."""

    name: str
    inferred_type: SemanticType
    confidence: float
    blank_count: int
    potential_missing_count: int
    missing_percent: float
    unique_sample_count: int
    examples: tuple[str, ...]
    entirely_empty: bool
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class PreviewSlice:
    """A first, middle, or last bounded preview window."""

    label: str
    start_row: int
    rows: tuple[tuple[object | None, ...], ...]


@dataclass(frozen=True)
class FileInspection:
    """Complete read-only profile returned by a registered reader."""

    path: Path
    file_kind: FileKind
    file_size_bytes: int
    estimated_memory_bytes: int
    processing_strategy: str
    worksheet: str | None
    available_worksheets: tuple[str, ...]
    encoding: str | None
    encoding_confidence: float | None
    delimiter: str | None
    quote_character: str | None
    header_detected: bool
    header_confidence: float
    row_count: int
    column_count: int
    columns: tuple[ColumnProfile, ...]
    potential_missing_markers: tuple[MissingMarkerDetection, ...]
    likely_datetime_column: str | None
    likely_interval_seconds: float | None
    likely_interval_label: str | None
    previews: tuple[PreviewSlice, ...]
    large_file: bool
    warnings: tuple[str, ...]

    @property
    def column_names(self) -> tuple[str, ...]:
        return tuple(column.name for column in self.columns)

    @property
    def empty_columns(self) -> tuple[str, ...]:
        return tuple(column.name for column in self.columns if column.entirely_empty)
