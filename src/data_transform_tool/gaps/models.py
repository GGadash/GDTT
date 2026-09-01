"""Immutable gap-analysis and reconstruction configuration models.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from data_transform_tool.domain.table import CellValue, DataTable


class MetadataBehavior(StrEnum):
    """Explicit behavior for a generated row's non-primary fields."""

    NULL = "null"
    CARRY_STABLE = "carry_stable"
    FIXED_VALUE = "fixed_value"
    DERIVED_FROM_TIMESTAMP = "derived_from_timestamp"


class TimestampDerivation(StrEnum):
    COPY = "copy"
    DATE = "date"
    TIME = "time"
    YEAR = "year"
    MONTH = "month"
    DAY = "day"
    ISO_WEEKDAY = "iso_weekday"
    INTERVAL_START = "interval_start"
    INTERVAL_MIDPOINT = "interval_midpoint"
    INTERVAL_END = "interval_end"


@dataclass(frozen=True)
class ConfirmedInterval:
    """A user-confirmed expected sampling interval."""

    duration: timedelta
    label: str = "Custom"

    def __post_init__(self) -> None:
        if self.duration <= timedelta(0):
            raise ValueError("A confirmed interval must be greater than zero.")
        if not self.label.strip():
            raise ValueError("An interval label must not be blank.")

    @classmethod
    def minutes(cls, value: int) -> ConfirmedInterval:
        if value <= 0:
            raise ValueError("Interval minutes must be greater than zero.")
        return cls(
            timedelta(minutes=value), f"{value} minute" if value == 1 else f"{value} minutes"
        )

    @classmethod
    def hours(cls, value: int) -> ConfirmedInterval:
        if value <= 0:
            raise ValueError("Interval hours must be greater than zero.")
        return cls(timedelta(hours=value), f"{value} hour" if value == 1 else f"{value} hours")


@dataclass(frozen=True)
class IntervalSuggestion:
    interval: ConfirmedInterval
    matching_steps: int
    total_steps: int

    @property
    def confidence(self) -> float:
        return self.matching_steps / self.total_steps if self.total_steps else 0.0


@dataclass(frozen=True)
class GapSpan:
    previous_timestamp: datetime
    next_timestamp: datetime
    missing_timestamps: tuple[datetime, ...]


@dataclass(frozen=True)
class TimestampAnalysis:
    interval: ConfirmedInterval
    expected_timestamps: tuple[datetime, ...]
    missing_timestamps: tuple[datetime, ...]
    gaps: tuple[GapSpan, ...]
    duplicate_row_groups: tuple[tuple[int, ...], ...]
    chronological_break_rows: tuple[int, ...]
    invalid_timestamp_rows: tuple[int, ...]
    off_grid_rows: tuple[int, ...]

    @property
    def can_reconstruct(self) -> bool:
        return not (self.duplicate_row_groups or self.invalid_timestamp_rows or self.off_grid_rows)


@dataclass(frozen=True)
class GapFieldPolicy:
    column: str
    behavior: MetadataBehavior = MetadataBehavior.NULL
    fixed_value: CellValue = None
    derivation: TimestampDerivation | None = None
    timezone_name: str | None = None

    def __post_init__(self) -> None:
        if not self.column.strip():
            raise ValueError("A gap field policy column must not be blank.")
        if self.timezone_name is not None and not self.timezone_name.strip():
            raise ValueError("A derived-field timezone name must not be blank.")
        if self.behavior is MetadataBehavior.DERIVED_FROM_TIMESTAMP and self.derivation is None:
            raise ValueError("Timestamp-derived fields require a derivation.")
        if self.behavior is not MetadataBehavior.DERIVED_FROM_TIMESTAMP and (
            self.derivation is not None or self.timezone_name is not None
        ):
            raise ValueError("Derivation settings are only valid for timestamp-derived fields.")


@dataclass(frozen=True)
class GapGenerationConfig:
    timestamp_column: str
    interval: ConfirmedInterval
    measurement_columns: tuple[str, ...]
    field_policies: tuple[GapFieldPolicy, ...] = ()
    allow_reorder: bool = False
    index_column: str | None = None
    index_start: int = 1
    generated_flag_column: str | None = None
    max_expected_rows: int = 1_000_000

    def __post_init__(self) -> None:
        if not self.timestamp_column.strip():
            raise ValueError("The primary timestamp column must not be blank.")
        if any(not column.strip() for column in self.measurement_columns):
            raise ValueError("Measurement column names must not be blank.")
        if len(set(self.measurement_columns)) != len(self.measurement_columns):
            raise ValueError("Measurement columns must be unique.")
        policy_columns = tuple(policy.column for policy in self.field_policies)
        if len(set(policy_columns)) != len(policy_columns):
            raise ValueError("Each generated-row field may have only one policy.")
        forbidden = set(self.measurement_columns) | {self.timestamp_column}
        conflicts = sorted(forbidden.intersection(policy_columns))
        if conflicts:
            raise ValueError(
                "Primary timestamp and measurement fields cannot receive metadata policies: "
                + ", ".join(conflicts)
            )
        for special_name in (self.index_column, self.generated_flag_column):
            if special_name is not None and not special_name.strip():
                raise ValueError("Special generated-row column names must not be blank.")
            if special_name in forbidden:
                raise ValueError(
                    "Special generated-row columns cannot replace timestamp or measurements."
                )
        if self.index_column is not None and self.index_column == self.generated_flag_column:
            raise ValueError("Index and generated-flag columns must be different.")
        if self.max_expected_rows <= 0:
            raise ValueError("Maximum expected rows must be greater than zero.")


@dataclass(frozen=True)
class GapGenerationReport:
    analysis: TimestampAnalysis
    original_rows: int
    generated_rows: int
    stable_metadata_columns: tuple[str, ...]


@dataclass(frozen=True)
class GapGenerationResult:
    table: DataTable
    report: GapGenerationReport
