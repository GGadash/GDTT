"""Immutable configuration and result contracts for completeness-aware aggregation.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from enum import StrEnum
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from data_transform_tool.domain.errors import AppError
from data_transform_tool.domain.table import DataTable

if TYPE_CHECKING:
    from data_transform_tool.transformation.base import Diagnostic


class AggregationError(AppError):
    """A blocking, user-readable aggregation configuration or data error."""


class AggregationApproach(StrEnum):
    DIRECT = "direct"
    INCREMENTAL = "incremental"


class AggregationStatistic(StrEnum):
    ARITHMETIC_MEAN = "arithmetic_mean"
    MINIMUM = "minimum"
    MAXIMUM = "maximum"
    SUM = "sum"
    MEDIAN = "median"
    STANDARD_DEVIATION = "standard_deviation"
    COUNT = "count"
    ENERGY_AVERAGE_LEQ = "energy_average_leq"
    RAINFALL_ACCUMULATION = "rainfall_accumulation"
    RAIN_RATE_MEAN = "rain_rate_mean"


class PeriodKind(StrEnum):
    FIXED_CLOCK = "fixed_clock"
    DAY = "day"
    WEEK = "week"
    CALENDAR_MONTH = "calendar_month"
    FIXED_DAYS = "fixed_days"
    QUARTER = "quarter"
    SEASON = "season"
    CALENDAR_YEAR = "calendar_year"
    FIXED_YEAR = "fixed_year"


@dataclass(frozen=True)
class SeasonBoundary:
    """One named local-calendar season boundary."""

    name: str
    month: int
    day: int = 1

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("A season name must not be blank.")
        try:
            date(2001, self.month, self.day)
        except ValueError as error:
            raise ValueError("A season boundary must be a valid non-leap date.") from error


@dataclass(frozen=True)
class PeriodSpec:
    """Explicit reporting-period semantics, separate from the input interval."""

    kind: PeriodKind
    duration: timedelta | None = None
    day_start: time = time(0, 0)
    week_start: int = 0
    anchor: datetime | None = None
    quarter_start_month: int = 1
    year_start_month: int = 1
    year_start_day: int = 1
    seasons: tuple[SeasonBoundary, ...] = ()

    def __post_init__(self) -> None:
        if self.day_start.tzinfo is not None:
            raise ValueError("A reporting day start must be a local wall-clock time.")
        if not 0 <= self.week_start <= 6:
            raise ValueError("Week start must use Monday=0 through Sunday=6.")
        if not 1 <= self.quarter_start_month <= 12:
            raise ValueError("Quarter start month must be between 1 and 12.")
        try:
            date(2001, self.year_start_month, self.year_start_day)
        except ValueError as error:
            raise ValueError("Reporting-year start must be a valid non-leap date.") from error

        fixed_clock = self.kind is PeriodKind.FIXED_CLOCK
        fixed_days = self.kind is PeriodKind.FIXED_DAYS
        if fixed_clock or fixed_days:
            if self.duration is None or self.duration <= timedelta(0):
                raise ValueError("Fixed periods require a positive duration.")
        elif self.duration is not None:
            raise ValueError("Duration is only valid for fixed-clock and fixed-day periods.")

        if fixed_clock:
            if self.duration is None:
                raise AssertionError("Validated fixed-clock periods always have a duration.")
            if self.duration > timedelta(days=1):
                raise ValueError("Fixed clock intervals cannot exceed one reporting day.")
            if timedelta(days=1) % self.duration:
                raise ValueError("A clock interval must divide a 24-hour wall-clock day exactly.")

        anchor_required = self.kind in {PeriodKind.FIXED_DAYS, PeriodKind.FIXED_YEAR}
        if anchor_required and self.anchor is None:
            raise ValueError("Fixed-day and fixed-year periods require an explicit anchor.")
        if not anchor_required and self.anchor is not None:
            raise ValueError("An anchor is only valid for fixed-day and fixed-year periods.")

        if self.kind is PeriodKind.SEASON:
            if len(self.seasons) < 2:
                raise ValueError("A season set requires at least two boundaries.")
            names = tuple(boundary.name.casefold() for boundary in self.seasons)
            dates = tuple((boundary.month, boundary.day) for boundary in self.seasons)
            if len(set(names)) != len(names):
                raise ValueError("Season names must be unique.")
            if len(set(dates)) != len(dates):
                raise ValueError("Season boundaries must be unique.")
        elif self.seasons:
            raise ValueError("Season boundaries are only valid for season periods.")

    @classmethod
    def clock(cls, duration: timedelta, *, day_start: time = time(0, 0)) -> PeriodSpec:
        return cls(PeriodKind.FIXED_CLOCK, duration=duration, day_start=day_start)

    @classmethod
    def day(cls, *, day_start: time = time(0, 0)) -> PeriodSpec:
        return cls(PeriodKind.DAY, day_start=day_start)


@dataclass(frozen=True)
class CompletenessRule:
    threshold: float = 0.75
    allow_two_of_three: bool = False

    def __post_init__(self) -> None:
        if not 0 < self.threshold <= 1:
            raise ValueError("Completeness threshold must be greater than zero and at most one.")

    def accepts(self, valid_count: int, expected_count: int) -> bool:
        if valid_count < 0 or expected_count <= 0 or valid_count > expected_count:
            raise ValueError("Completeness counts must satisfy 0 <= valid <= expected.")
        if self.allow_two_of_three and expected_count == 3 and valid_count >= 2:
            return True
        return valid_count / expected_count >= self.threshold


@dataclass(frozen=True)
class FieldAggregation:
    column: str
    statistic: AggregationStatistic = AggregationStatistic.ARITHMETIC_MEAN
    output_name: str | None = None
    duration_column: str | None = None

    def __post_init__(self) -> None:
        if not self.column.strip():
            raise ValueError("An aggregation source column must not be blank.")
        if self.output_name is not None and not self.output_name.strip():
            raise ValueError("An aggregation output name must not be blank.")
        if self.duration_column is not None and not self.duration_column.strip():
            raise ValueError("A duration column name must not be blank.")
        if (
            self.duration_column is not None
            and self.statistic is not AggregationStatistic.ENERGY_AVERAGE_LEQ
        ):
            raise ValueError("Duration weighting is only valid for Energy Average / Leq.")

    @property
    def resolved_output_name(self) -> str:
        return self.output_name or self.column


@dataclass(frozen=True)
class AggregationStage:
    period: PeriodSpec
    completeness: CompletenessRule = CompletenessRule()
    label: str | None = None

    def __post_init__(self) -> None:
        if self.label is not None and not self.label.strip():
            raise ValueError("An aggregation stage label must not be blank.")


@dataclass(frozen=True)
class AggregationConfig:
    timestamp_column: str
    input_interval: timedelta
    reporting_timezone: str
    fields: tuple[FieldAggregation, ...]
    stages: tuple[AggregationStage, ...]
    approach: AggregationApproach = AggregationApproach.DIRECT
    allow_reorder: bool = False
    max_periods: int = 1_000_000

    def __post_init__(self) -> None:
        if not self.timestamp_column.strip():
            raise ValueError("The aggregation timestamp column must not be blank.")
        if self.input_interval <= timedelta(0):
            raise ValueError("The confirmed input interval must be greater than zero.")
        if not self.reporting_timezone.strip():
            raise ValueError("A reporting timezone is required.")
        try:
            ZoneInfo(self.reporting_timezone)
        except ZoneInfoNotFoundError as error:
            raise ValueError(f"Unknown reporting timezone '{self.reporting_timezone}'.") from error
        if not self.fields:
            raise ValueError("At least one field must be configured for aggregation.")
        source_names = tuple(field.column for field in self.fields)
        output_names = tuple(field.resolved_output_name for field in self.fields)
        if len(set(source_names)) != len(source_names):
            raise ValueError("Aggregation source fields must be unique.")
        if len(set(output_names)) != len(output_names):
            raise ValueError("Aggregation output field names must be unique.")
        if not self.stages:
            raise ValueError("At least one aggregation stage is required.")
        if self.approach is AggregationApproach.DIRECT:
            if len(self.stages) != 1:
                raise ValueError("Direct aggregation requires exactly one target stage.")
            if self.stages[0].completeness.allow_two_of_three:
                raise ValueError("The two-of-three rule is only valid for Incremental stages.")
        elif len(self.stages) < 2:
            raise ValueError("Incremental aggregation requires at least two visible stages.")
        if self.max_periods <= 0:
            raise ValueError("Maximum aggregation periods must be greater than zero.")


@dataclass(frozen=True)
class PeriodBounds:
    start: datetime
    end: datetime
    label: str

    def __post_init__(self) -> None:
        if self.start.utcoffset() is None or self.end.utcoffset() is None:
            raise ValueError("Reporting-period boundaries must be timezone-aware.")
        if self.end.timestamp() <= self.start.timestamp():
            raise ValueError("A reporting period must end after it starts.")
        if not self.label.strip():
            raise ValueError("A reporting-period label must not be blank.")


@dataclass(frozen=True)
class CompletenessRecord:
    stage_index: int
    period_start: datetime
    period_end: datetime
    field: str
    valid_count: int
    expected_count: int
    availability: float
    accepted: bool
    used_two_of_three: bool = False


@dataclass(frozen=True)
class AggregationStageReport:
    stage_index: int
    label: str
    period_kind: PeriodKind
    periods_evaluated: int
    values_accepted: int
    values_rejected: int
    completeness: CompletenessRule


@dataclass(frozen=True)
class AggregationStageResult:
    table: DataTable
    report: AggregationStageReport
    completeness: tuple[CompletenessRecord, ...]


@dataclass(frozen=True)
class AggregationResult:
    stages: tuple[AggregationStageResult, ...]
    diagnostics: tuple[Diagnostic, ...] = ()

    def __post_init__(self) -> None:
        if not self.stages:
            raise ValueError("An aggregation result requires at least one stage.")

    @property
    def table(self) -> DataTable:
        return self.stages[-1].table
