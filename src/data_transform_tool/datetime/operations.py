"""Date parsing/formatting, combine/split, interval derivation, and time shifts.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from data_transform_tool.datetime.models import (
    IntervalEndMode,
    TimestampRole,
    TimestampSemantics,
)
from data_transform_tool.datetime.parser import DateTimeParser
from data_transform_tool.domain.table import CellValue, DataTable
from data_transform_tool.transformation.base import (
    Diagnostic,
    InvalidValuePolicy,
    OperationResult,
    TransformationError,
    TransformationOperation,
    write_column,
)


@dataclass(frozen=True)
class ParseDateTimeColumn(TransformationOperation):
    source: str
    profile_id: str
    output: str | None = None
    invalid_policy: InvalidValuePolicy = InvalidValuePolicy.STOP

    @property
    def operation_id(self) -> str:
        return "parse_datetime"

    def apply(self, table: DataTable) -> OperationResult:
        parser = DateTimeParser()
        values, diagnostics = _map_temporal(
            table,
            source=self.source,
            operation_id=self.operation_id,
            invalid_policy=self.invalid_policy,
            transform=lambda value: parser.parse(value, self.profile_id),
        )
        return OperationResult(
            write_column(
                table,
                source_name=self.source,
                output_name=self.output,
                values=values,
            ),
            diagnostics,
        )


@dataclass(frozen=True)
class FormatDateTimeColumn(TransformationOperation):
    source: str
    profile_id: str
    output: str | None = None
    invalid_policy: InvalidValuePolicy = InvalidValuePolicy.STOP

    @property
    def operation_id(self) -> str:
        return "format_datetime"

    def apply(self, table: DataTable) -> OperationResult:
        parser = DateTimeParser()

        def format_value(value: object) -> str:
            if not isinstance(value, (date, datetime, time)):
                raise ValueError("A parsed date/time value is required before formatting.")
            return parser.format(value, self.profile_id)

        values, diagnostics = _map_temporal(
            table,
            source=self.source,
            operation_id=self.operation_id,
            invalid_policy=self.invalid_policy,
            transform=format_value,
        )
        return OperationResult(
            write_column(
                table,
                source_name=self.source,
                output_name=self.output,
                values=values,
            ),
            diagnostics,
        )


@dataclass(frozen=True)
class CombineDateAndTime(TransformationOperation):
    date_column: str
    time_column: str
    output: str = "DateTime"

    @property
    def operation_id(self) -> str:
        return "combine_date_time"

    def apply(self, table: DataTable) -> OperationResult:
        dates = table.column_values(self.date_column)
        times = table.column_values(self.time_column)
        combined: list[CellValue] = []
        for row_number, (date_value, time_value) in enumerate(zip(dates, times, strict=True), 1):
            if date_value is None or time_value is None:
                combined.append(None)
                continue
            try:
                resolved_date = _as_date(date_value)
                resolved_time = _as_time(time_value)
            except ValueError as error:
                raise TransformationError(
                    f"Date and time could not be combined at row {row_number}.",
                    detail=str(error),
                ) from error
            combined.append(datetime.combine(resolved_date, resolved_time))
        return OperationResult(table.add_column(self.output, tuple(combined)))


@dataclass(frozen=True)
class SplitDateTime(TransformationOperation):
    source: str
    date_output: str = "Date"
    time_output: str = "Time"

    @property
    def operation_id(self) -> str:
        return "split_datetime"

    def apply(self, table: DataTable) -> OperationResult:
        date_values: list[CellValue] = []
        time_values: list[CellValue] = []
        for row_number, value in enumerate(table.column_values(self.source), start=1):
            if value is None:
                date_values.append(None)
                time_values.append(None)
            elif isinstance(value, datetime):
                date_values.append(value.date())
                time_values.append(value.timetz() if value.tzinfo else value.time())
            else:
                raise TransformationError(
                    f"Column '{self.source}' contains a non-DateTime value at row {row_number}."
                )
        result = table.add_column(self.date_output, tuple(date_values))
        result = result.add_column(self.time_output, tuple(time_values))
        return OperationResult(result)


@dataclass(frozen=True)
class DeriveIntervalFields(TransformationOperation):
    semantics: TimestampSemantics
    start_output: str | None = "Start"
    midpoint_output: str | None = "Mid"
    end_output: str | None = "End"

    @property
    def operation_id(self) -> str:
        return "derive_interval_fields"

    def apply(self, table: DataTable) -> OperationResult:
        duration = self.semantics.duration
        if duration is None:
            raise ValueError("Sampling duration is required to derive interval fields.")
        if self.semantics.role not in {
            TimestampRole.START,
            TimestampRole.MIDPOINT,
            TimestampRole.END,
        }:
            raise ValueError(
                f"Timestamp role '{self.semantics.role.value}' cannot define interval boundaries."
            )

        starts: list[CellValue] = []
        mids: list[CellValue] = []
        ends: list[CellValue] = []
        for row_number, value in enumerate(table.column_values(self.semantics.column), start=1):
            if value is None:
                starts.append(None)
                mids.append(None)
                ends.append(None)
                continue
            if not isinstance(value, datetime):
                raise TransformationError(
                    f"Timestamp column contains a non-DateTime value at row {row_number}."
                )
            start = _interval_start(value, self.semantics.role, duration)
            starts.append(start)
            mids.append(start + duration / 2)
            ends.append(start + duration)

        result = table
        for name, values in (
            (self.start_output, starts),
            (self.midpoint_output, mids),
            (self.end_output, ends),
        ):
            if name is not None:
                result = result.add_column(name, tuple(values))
        return OperationResult(result)


@dataclass(frozen=True)
class NormalizeIntervalEnd(TransformationOperation):
    start_column: str
    end_column: str
    duration: timedelta
    mode: IntervalEndMode = IntervalEndMode.SEMANTIC_NORMALIZE
    inclusive_tolerance: timedelta = timedelta(minutes=1)

    def __post_init__(self) -> None:
        if self.duration <= timedelta(0):
            raise ValueError("Sampling duration must be positive.")
        if self.inclusive_tolerance < timedelta(0):
            raise ValueError("Inclusive-end tolerance must not be negative.")

    @property
    def operation_id(self) -> str:
        return "normalize_interval_end"

    def apply(self, table: DataTable) -> OperationResult:
        if self.mode is IntervalEndMode.RETAIN:
            return OperationResult(table)
        starts = table.column_values(self.start_column)
        supplied_ends = table.column_values(self.end_column)
        output: list[CellValue] = []
        normalized = 0
        unresolved = 0
        for row_number, (start, supplied) in enumerate(zip(starts, supplied_ends, strict=True), 1):
            if start is None:
                output.append(supplied)
                continue
            if not isinstance(start, datetime):
                raise TransformationError(
                    f"Start column contains a non-DateTime value at row {row_number}."
                )
            expected = start + self.duration
            if self.mode is IntervalEndMode.CALCULATE or supplied is None:
                output.append(expected)
                normalized += 1
            elif not isinstance(supplied, datetime):
                raise TransformationError(
                    f"End column contains a non-DateTime value at row {row_number}."
                )
            elif supplied == expected:
                output.append(supplied)
            elif timedelta(0) < expected - supplied <= self.inclusive_tolerance:
                output.append(expected)
                normalized += 1
            else:
                output.append(supplied)
                unresolved += 1

        diagnostics: list[Diagnostic] = []
        if normalized:
            diagnostics.append(
                Diagnostic(
                    "interval_ends_normalized",
                    "Supplied interval ends were normalized using confirmed duration semantics.",
                    normalized,
                    (self.start_column, self.end_column),
                )
            )
        if unresolved:
            diagnostics.append(
                Diagnostic(
                    "interval_ends_unresolved",
                    "Some supplied ends were outside the inclusive-end tolerance and retained.",
                    unresolved,
                    (self.start_column, self.end_column),
                )
            )
        return OperationResult(
            table.replace_column(self.end_column, tuple(output)), tuple(diagnostics)
        )


@dataclass(frozen=True)
class TimeShift(TransformationOperation):
    source: str
    offset: timedelta
    output: str | None = None

    @property
    def operation_id(self) -> str:
        return "time_shift"

    def apply(self, table: DataTable) -> OperationResult:
        values: list[CellValue] = []
        for row_number, value in enumerate(table.column_values(self.source), start=1):
            if value is None:
                values.append(None)
            elif isinstance(value, datetime):
                values.append(value + self.offset)
            elif isinstance(value, date):
                if self.offset.seconds or self.offset.microseconds:
                    raise TransformationError(
                        "Sub-day shifts require DateTime rather than Date values."
                    )
                values.append(value + self.offset)
            elif isinstance(value, time):
                anchor = datetime.combine(date(2000, 1, 1), value)
                values.append(
                    (anchor + self.offset).timetz()
                    if value.tzinfo
                    else (anchor + self.offset).time()
                )
            else:
                raise TransformationError(
                    f"Time shift found a non-temporal value at row {row_number}."
                )
        return OperationResult(
            write_column(
                table,
                source_name=self.source,
                output_name=self.output,
                values=tuple(values),
            )
        )


def _map_temporal(
    table: DataTable,
    *,
    source: str,
    operation_id: str,
    invalid_policy: InvalidValuePolicy,
    transform: Callable[[object], CellValue],
) -> tuple[tuple[CellValue, ...], tuple[Diagnostic, ...]]:
    values: list[CellValue] = []
    invalid_count = 0
    for row_number, value in enumerate(table.column_values(source), start=1):
        if value is None:
            values.append(None)
            continue
        try:
            values.append(transform(value))
        except ValueError as error:
            invalid_count += 1
            if invalid_policy is InvalidValuePolicy.STOP:
                raise TransformationError(
                    f"Date/time operation failed in '{source}' at row {row_number}.",
                    detail=str(error),
                ) from error
            values.append(value if invalid_policy is InvalidValuePolicy.PRESERVE else None)
    diagnostics = (
        (
            Diagnostic(
                "invalid_temporal_values",
                f"{invalid_count} value(s) followed the '{invalid_policy.value}' policy "
                f"during {operation_id}.",
                invalid_count,
                (source,),
            ),
        )
        if invalid_count
        else ()
    )
    return tuple(values), diagnostics


def _as_date(value: object) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    raise ValueError("A parsed Date value is required.")


def _as_time(value: object) -> time:
    if isinstance(value, datetime):
        return value.timetz() if value.tzinfo else value.time()
    if isinstance(value, time):
        return value
    raise ValueError("A parsed Time value is required.")


def _interval_start(value: datetime, role: TimestampRole, duration: timedelta) -> datetime:
    if role is TimestampRole.START:
        return value
    if role is TimestampRole.MIDPOINT:
        return value - duration / 2
    return value - duration
