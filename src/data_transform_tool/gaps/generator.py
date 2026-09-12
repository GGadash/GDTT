"""Deterministic gap-row generation with explicit metadata policies.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from data_transform_tool.domain.table import CellValue, DataRow, DataTable
from data_transform_tool.gaps.analyzer import analyze_timestamps
from data_transform_tool.gaps.models import (
    GapFieldPolicy,
    GapGenerationConfig,
    GapGenerationReport,
    GapGenerationResult,
    MetadataBehavior,
    TimestampDerivation,
)
from data_transform_tool.timezone.zones import resolve_zone
from data_transform_tool.transformation.base import TransformationError


def suggest_stable_metadata(
    table: DataTable, *, excluded_columns: tuple[str, ...] = ()
) -> tuple[GapFieldPolicy, ...]:
    """Suggest carry policies only for effectively constant, non-null fields."""
    excluded = set(excluded_columns)
    suggestions: list[GapFieldPolicy] = []
    for column in table.columns:
        if column in excluded:
            continue
        values = tuple(value for value in table.column_values(column) if value is not None)
        if values and all(_same_scalar(values[0], value) for value in values[1:]):
            suggestions.append(GapFieldPolicy(column, MetadataBehavior.CARRY_STABLE))
    return tuple(suggestions)


def generate_gap_rows(table: DataTable, config: GapGenerationConfig) -> GapGenerationResult:
    """Return an expected-grid table without interpolating measurement values."""
    _validate_columns(table, config)
    analysis = analyze_timestamps(
        table,
        config.timestamp_column,
        config.interval,
        max_expected_rows=config.max_expected_rows,
    )
    if analysis.invalid_timestamp_rows:
        raise TransformationError("Gap generation requires a valid primary timestamp in every row.")
    if analysis.duplicate_row_groups:
        raise TransformationError("Resolve duplicate primary timestamps before generating gaps.")
    if analysis.off_grid_rows:
        raise TransformationError(
            "One or more primary timestamps do not align with the confirmed interval grid."
        )
    if analysis.chronological_break_rows and not config.allow_reorder:
        raise TransformationError(
            "Primary timestamps are not chronological; explicitly allow reordering first."
        )

    timestamp_index = table.column_index(config.timestamp_column)
    source_by_instant = {
        _instant_key(row[timestamp_index]): row
        for row in table.rows
        if isinstance(row[timestamp_index], datetime)
    }
    policy_by_column = {policy.column: policy for policy in config.field_policies}
    stable_values = _resolve_stable_values(table, config.field_policies)
    missing_instants = {_instant_key(value) for value in analysis.missing_timestamps}
    output_rows: list[DataRow] = []
    for timestamp in analysis.expected_timestamps:
        instant = _instant_key(timestamp)
        source_row = source_by_instant.get(instant)
        if source_row is not None:
            values = list(source_row)
        else:
            values = [
                _generated_value(
                    column,
                    timestamp,
                    config.interval.duration,
                    config,
                    policy_by_column.get(column),
                    stable_values,
                )
                for column in table.columns
            ]
        output_rows.append(tuple(values))

    rows = [list(row) for row in output_rows]
    if config.index_column is not None:
        index = table.column_index(config.index_column)
        for offset, row in enumerate(rows):
            row[index] = config.index_start + offset
    if config.generated_flag_column is not None:
        index = table.column_index(config.generated_flag_column)
        for timestamp, row in zip(analysis.expected_timestamps, rows, strict=True):
            row[index] = _instant_key(timestamp) in missing_instants

    return GapGenerationResult(
        table=DataTable(table.columns, tuple(tuple(row) for row in rows)),
        report=GapGenerationReport(
            analysis=analysis,
            original_rows=table.row_count,
            generated_rows=len(analysis.missing_timestamps),
            stable_metadata_columns=tuple(sorted(stable_values)),
        ),
    )


def _validate_columns(table: DataTable, config: GapGenerationConfig) -> None:
    configured = (
        config.timestamp_column,
        *config.measurement_columns,
        *(policy.column for policy in config.field_policies),
        *(
            column
            for column in (config.index_column, config.generated_flag_column)
            if column is not None
        ),
    )
    for column in configured:
        table.column_index(column)


def _resolve_stable_values(
    table: DataTable, policies: tuple[GapFieldPolicy, ...]
) -> dict[str, CellValue]:
    resolved: dict[str, CellValue] = {}
    for policy in policies:
        if policy.behavior is not MetadataBehavior.CARRY_STABLE:
            continue
        values = tuple(value for value in table.column_values(policy.column) if value is not None)
        if not values:
            resolved[policy.column] = None
            continue
        if not all(_same_scalar(values[0], value) for value in values[1:]):
            raise TransformationError(
                f"Column '{policy.column}' is not stable and cannot be carried into gap rows."
            )
        resolved[policy.column] = values[0]
    return resolved


def _generated_value(
    column: str,
    timestamp: datetime,
    interval: timedelta,
    config: GapGenerationConfig,
    policy: GapFieldPolicy | None,
    stable_values: dict[str, CellValue],
) -> CellValue:
    if column == config.timestamp_column:
        return timestamp
    if column in config.measurement_columns:
        return None
    if column in (config.index_column, config.generated_flag_column):
        return None
    if policy is None or policy.behavior is MetadataBehavior.NULL:
        return None
    if policy.behavior is MetadataBehavior.CARRY_STABLE:
        return stable_values[policy.column]
    if policy.behavior is MetadataBehavior.FIXED_VALUE:
        return policy.fixed_value
    if policy.derivation is None:
        raise AssertionError("Timestamp-derived policies must declare a derivation.")
    return _derive_timestamp(timestamp, interval, policy.derivation, policy.timezone_name)


def _derive_timestamp(
    timestamp: datetime,
    interval: timedelta,
    derivation: TimestampDerivation,
    timezone_name: str | None,
) -> CellValue:
    value = _in_timezone(timestamp, timezone_name)
    if derivation in (TimestampDerivation.COPY, TimestampDerivation.INTERVAL_START):
        return value
    if derivation is TimestampDerivation.INTERVAL_MIDPOINT:
        return _add_elapsed(value, interval / 2)
    if derivation is TimestampDerivation.INTERVAL_END:
        return _add_elapsed(value, interval)
    if derivation is TimestampDerivation.DATE:
        return value.date()
    if derivation is TimestampDerivation.TIME:
        return value.timetz() if value.utcoffset() is not None else value.time()
    if derivation is TimestampDerivation.YEAR:
        return value.year
    if derivation is TimestampDerivation.MONTH:
        return value.month
    if derivation is TimestampDerivation.DAY:
        return value.day
    return value.isoweekday()


def _in_timezone(timestamp: datetime, timezone_name: str | None) -> datetime:
    if timezone_name is None:
        return timestamp
    if timestamp.utcoffset() is None:
        raise TransformationError(
            "A timezone-derived gap field requires timezone-aware primary timestamps."
        )
    try:
        return timestamp.astimezone(resolve_zone(timezone_name))
    except ValueError as error:
        raise TransformationError(f"Unknown timezone: {timezone_name}.") from error


def _add_elapsed(timestamp: datetime, interval: timedelta) -> datetime:
    if timestamp.utcoffset() is None:
        return timestamp + interval
    return (timestamp.astimezone(UTC) + interval).astimezone(timestamp.tzinfo)


def _instant_key(value: CellValue) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError("Expected a datetime value.")
    return value.astimezone(UTC) if value.utcoffset() is not None else value


def _same_scalar(left: CellValue, right: CellValue) -> bool:
    return type(left) is type(right) and left == right
