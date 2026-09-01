"""Direct and incremental completeness-aware aggregation reference executor.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from data_transform_tool.aggregation.models import (
    AggregationApproach,
    AggregationConfig,
    AggregationError,
    AggregationResult,
    AggregationStage,
    AggregationStageReport,
    AggregationStageResult,
    AggregationStatistic,
    CompletenessRecord,
    FieldAggregation,
    PeriodBounds,
)
from data_transform_tool.aggregation.periods import Periodizer
from data_transform_tool.aggregation.strategies import aggregate_numeric, duration_seconds
from data_transform_tool.domain.errors import Severity
from data_transform_tool.domain.table import CellValue, DataTable
from data_transform_tool.transformation.base import Diagnostic

PERIOD_START_COLUMN = "Period_Start"
PERIOD_END_COLUMN = "Period_End"


@dataclass(frozen=True)
class _Observation:
    row_number: int
    timestamp: datetime
    values: dict[str, CellValue]


@dataclass(frozen=True)
class _Component:
    bounds: PeriodBounds
    values: dict[str, CellValue]


def aggregate_table(
    table: DataTable,
    config: AggregationConfig,
    *,
    cancellation_check: Callable[[], None] | None = None,
) -> AggregationResult:
    """Execute Direct or visible multi-stage Incremental aggregation immutably."""
    _validate_columns(table, config)
    observations, reordered = _validated_observations(
        table, config, cancellation_check=cancellation_check
    )
    periodizers = tuple(
        Periodizer(stage.period, config.reporting_timezone) for stage in config.stages
    )
    if not observations:
        stages = tuple(
            _empty_stage(config, stage, index) for index, stage in enumerate(config.stages, start=1)
        )
        return AggregationResult(stages)

    _validate_input_grid(observations, config, periodizers[0], cancellation_check)
    diagnostics: list[Diagnostic] = []
    if reordered:
        diagnostics.append(
            Diagnostic(
                code="aggregation.input_reordered",
                message="Input rows were explicitly reordered by timestamp before aggregation.",
                severity=Severity.INFORMATION,
            )
        )

    first_result, first_diagnostics = _aggregate_observations(
        observations,
        config,
        config.stages[0],
        periodizers[0],
        stage_index=1,
        cancellation_check=cancellation_check,
    )
    stage_results = [first_result]
    diagnostics.extend(first_diagnostics)
    previous_periodizer = periodizers[0]
    for stage_index, (stage, periodizer) in enumerate(
        zip(config.stages[1:], periodizers[1:], strict=True), start=2
    ):
        stage_result, stage_diagnostics = _aggregate_components(
            stage_results[-1],
            config,
            stage,
            periodizer,
            previous_periodizer,
            stage_index=stage_index,
            cancellation_check=cancellation_check,
        )
        stage_results.append(stage_result)
        diagnostics.extend(stage_diagnostics)
        previous_periodizer = periodizer
    _cancel(cancellation_check)
    return AggregationResult(tuple(stage_results), tuple(diagnostics))


def continue_incremental_stages(
    first_stage: AggregationStageResult,
    config: AggregationConfig,
    *,
    cancellation_check: Callable[[], None] | None = None,
) -> AggregationResult:
    """Continue exact Incremental stages from a streamed first-stage result."""
    if config.approach is AggregationApproach.DIRECT:
        return AggregationResult((first_stage,))
    periodizers = tuple(
        Periodizer(stage.period, config.reporting_timezone) for stage in config.stages
    )
    stage_results = [first_stage]
    diagnostics: list[Diagnostic] = []
    previous_periodizer = periodizers[0]
    for stage_index, (stage, periodizer) in enumerate(
        zip(config.stages[1:], periodizers[1:], strict=True),
        start=2,
    ):
        stage_result, stage_diagnostics = _aggregate_components(
            stage_results[-1],
            config,
            stage,
            periodizer,
            previous_periodizer,
            stage_index=stage_index,
            cancellation_check=cancellation_check,
        )
        stage_results.append(stage_result)
        diagnostics.extend(stage_diagnostics)
        previous_periodizer = periodizer
    _cancel(cancellation_check)
    return AggregationResult(tuple(stage_results), tuple(diagnostics))


def aggregate_first_stage(
    table: DataTable,
    config: AggregationConfig,
    *,
    cancellation_check: Callable[[], None] | None = None,
) -> tuple[AggregationStageResult, tuple[Diagnostic, ...]]:
    """Execute only the configured first stage for an ordered source window."""
    _validate_columns(table, config)
    observations, reordered = _validated_observations(
        table,
        config,
        cancellation_check=cancellation_check,
    )
    stage = config.stages[0]
    periodizer = Periodizer(stage.period, config.reporting_timezone)
    if not observations:
        return _empty_stage(config, stage, 1), ()
    _validate_input_grid(observations, config, periodizer, cancellation_check)
    result, diagnostics = _aggregate_observations(
        observations,
        config,
        stage,
        periodizer,
        stage_index=1,
        cancellation_check=cancellation_check,
    )
    if not reordered:
        return result, diagnostics
    reordered_diagnostic = Diagnostic(
        code="aggregation.input_reordered",
        message="Input rows were explicitly reordered by timestamp before aggregation.",
        severity=Severity.INFORMATION,
    )
    return result, (reordered_diagnostic, *diagnostics)


def _validate_columns(table: DataTable, config: AggregationConfig) -> None:
    required = {config.timestamp_column}
    required.update(field.column for field in config.fields)
    required.update(
        field.duration_column for field in config.fields if field.duration_column is not None
    )
    missing = sorted(required.difference(table.columns))
    if missing:
        raise AggregationError("Aggregation source columns are missing: " + ", ".join(missing))
    reserved = {PERIOD_START_COLUMN, PERIOD_END_COLUMN}
    conflicts = sorted(
        field.resolved_output_name
        for field in config.fields
        if field.resolved_output_name in reserved
    )
    if conflicts:
        raise AggregationError(
            "Aggregation output fields cannot replace period-boundary columns: "
            + ", ".join(conflicts)
        )


def _validated_observations(
    table: DataTable,
    config: AggregationConfig,
    *,
    cancellation_check: Callable[[], None] | None,
) -> tuple[tuple[_Observation, ...], bool]:
    timestamp_index = table.column_index(config.timestamp_column)
    observations: list[_Observation] = []
    seen: dict[datetime, int] = {}
    chronological_breaks: list[int] = []
    previous: datetime | None = None
    for row_number, row in enumerate(table.rows, start=1):
        _cancel(cancellation_check)
        value = row[timestamp_index]
        if not isinstance(value, datetime):
            raise AggregationError(
                f"The aggregation timestamp is missing or invalid at row {row_number}."
            )
        if value.utcoffset() is None:
            raise AggregationError(
                f"The aggregation timestamp at row {row_number} is timezone-naive; resolve "
                "its source timezone before aggregation."
            )
        instant = value.astimezone(UTC)
        if instant in seen:
            raise AggregationError(
                f"Duplicate timestamp instants occur at rows {seen[instant]} and {row_number}."
            )
        seen[instant] = row_number
        if previous is not None and instant < previous:
            chronological_breaks.append(row_number)
        previous = instant
        observations.append(
            _Observation(
                row_number,
                value,
                dict(zip(table.columns, row, strict=True)),
            )
        )
    if chronological_breaks and not config.allow_reorder:
        raise AggregationError(
            "Input timestamps are not chronological; enable explicit reordering to continue."
        )
    if chronological_breaks:
        observations.sort(key=lambda item: item.timestamp.astimezone(UTC))
    return tuple(observations), bool(chronological_breaks)


def _validate_input_grid(
    observations: tuple[_Observation, ...],
    config: AggregationConfig,
    periodizer: Periodizer,
    cancellation_check: Callable[[], None] | None,
) -> None:
    off_grid: list[int] = []
    for observation in observations:
        _cancel(cancellation_check)
        bounds = periodizer.period_for(observation.timestamp)
        elapsed = observation.timestamp.astimezone(UTC) - bounds.start.astimezone(UTC)
        if elapsed % config.input_interval:
            off_grid.append(observation.row_number)
    if off_grid:
        preview = ", ".join(str(row) for row in off_grid[:5])
        suffix = "…" if len(off_grid) > 5 else ""
        raise AggregationError(
            f"{len(off_grid)} timestamp(s) are off the confirmed input grid; rows "
            f"{preview}{suffix}."
        )


def _aggregate_observations(
    observations: tuple[_Observation, ...],
    config: AggregationConfig,
    stage: AggregationStage,
    periodizer: Periodizer,
    *,
    stage_index: int,
    cancellation_check: Callable[[], None] | None,
) -> tuple[AggregationStageResult, tuple[Diagnostic, ...]]:
    periods = periodizer.periods_between(
        observations[0].timestamp,
        observations[-1].timestamp,
        max_periods=config.max_periods,
    )
    grouped: dict[datetime, list[_Observation]] = defaultdict(list)
    for observation in observations:
        bounds = periodizer.period_for(observation.timestamp)
        grouped[_instant(bounds.start)].append(observation)

    rows: list[tuple[CellValue, ...]] = []
    completeness: list[CompletenessRecord] = []
    accepted_count = 0
    rejected_count = 0
    for bounds in periods:
        _cancel(cancellation_check)
        expected = periodizer.expected_observations(bounds, config.input_interval)
        source_rows = grouped.get(_instant(bounds.start), [])
        outputs: list[CellValue] = []
        for field in config.fields:
            values, weights = _raw_components(source_rows, field)
            _validate_numeric_components(values)
            accepted, used_two = _acceptance(stage, len(values), expected)
            output = (
                aggregate_numeric(values, field.statistic, weights=weights) if accepted else None
            )
            outputs.append(output)
            completeness.append(
                _completeness_record(
                    stage_index,
                    bounds,
                    field.resolved_output_name,
                    len(values),
                    expected,
                    accepted,
                    used_two,
                )
            )
            accepted_count += int(accepted)
            rejected_count += int(not accepted)
        rows.append((bounds.start, bounds.end, *outputs))
    return _stage_result(
        config,
        stage,
        stage_index,
        rows,
        tuple(completeness),
        accepted_count,
        rejected_count,
    )


def _aggregate_components(
    previous: AggregationStageResult,
    config: AggregationConfig,
    stage: AggregationStage,
    periodizer: Periodizer,
    component_periodizer: Periodizer,
    *,
    stage_index: int,
    cancellation_check: Callable[[], None] | None,
) -> tuple[AggregationStageResult, tuple[Diagnostic, ...]]:
    if not previous.table.rows:
        return _empty_stage(config, stage, stage_index), ()
    components = tuple(
        _Component(
            PeriodBounds(
                _required_datetime(row[0], PERIOD_START_COLUMN),
                _required_datetime(row[1], PERIOD_END_COLUMN),
                "Incremental component",
            ),
            dict(zip(previous.table.columns[2:], row[2:], strict=True)),
        )
        for row in previous.table.rows
    )
    periods = periodizer.periods_between(
        components[0].bounds.start,
        components[-1].bounds.start,
        max_periods=config.max_periods,
    )
    grouped: dict[datetime, list[_Component]] = defaultdict(list)
    for component in components:
        target = periodizer.period_for(component.bounds.start)
        if _instant(component.bounds.end) > _instant(target.end):
            raise AggregationError("An incremental component crosses its target-period boundary.")
        grouped[_instant(target.start)].append(component)

    rows: list[tuple[CellValue, ...]] = []
    completeness: list[CompletenessRecord] = []
    accepted_count = 0
    rejected_count = 0
    for bounds in periods:
        _cancel(cancellation_check)
        expected = len(
            component_periodizer.component_periods(bounds, max_periods=config.max_periods)
        )
        source_components = grouped.get(_instant(bounds.start), [])
        outputs: list[CellValue] = []
        for field in config.fields:
            values = tuple(
                component.values[field.resolved_output_name]
                for component in source_components
                if component.values[field.resolved_output_name] is not None
            )
            _validate_numeric_components(values)
            weights = (
                tuple(
                    (
                        _instant(component.bounds.end) - _instant(component.bounds.start)
                    ).total_seconds()
                    for component in source_components
                    if component.values[field.resolved_output_name] is not None
                )
                if field.statistic is AggregationStatistic.ENERGY_AVERAGE_LEQ
                else None
            )
            accepted, used_two = _acceptance(stage, len(values), expected)
            output = (
                aggregate_numeric(values, field.statistic, weights=weights) if accepted else None
            )
            outputs.append(output)
            completeness.append(
                _completeness_record(
                    stage_index,
                    bounds,
                    field.resolved_output_name,
                    len(values),
                    expected,
                    accepted,
                    used_two,
                )
            )
            accepted_count += int(accepted)
            rejected_count += int(not accepted)
        rows.append((bounds.start, bounds.end, *outputs))
    return _stage_result(
        config,
        stage,
        stage_index,
        rows,
        tuple(completeness),
        accepted_count,
        rejected_count,
    )


def _raw_components(
    observations: list[_Observation], field: FieldAggregation
) -> tuple[tuple[CellValue, ...], tuple[float, ...] | None]:
    values: list[CellValue] = []
    weights: list[float] = []
    for observation in observations:
        value = observation.values[field.column]
        if value is None:
            continue
        if field.duration_column is not None:
            duration = observation.values[field.duration_column]
            if duration is None:
                continue
            weights.append(duration_seconds(duration))
        values.append(value)
    return tuple(values), tuple(weights) if field.duration_column is not None else None


def _validate_numeric_components(values: tuple[CellValue, ...]) -> None:
    if values:
        aggregate_numeric(values, AggregationStatistic.COUNT)


def _acceptance(stage: AggregationStage, valid: int, expected: int) -> tuple[bool, bool]:
    threshold_accepts = valid / expected >= stage.completeness.threshold
    special_accepts = stage.completeness.allow_two_of_three and expected == 3 and valid >= 2
    return threshold_accepts or special_accepts, special_accepts and not threshold_accepts


def _completeness_record(
    stage_index: int,
    bounds: PeriodBounds,
    field: str,
    valid: int,
    expected: int,
    accepted: bool,
    used_two: bool,
) -> CompletenessRecord:
    return CompletenessRecord(
        stage_index=stage_index,
        period_start=bounds.start,
        period_end=bounds.end,
        field=field,
        valid_count=valid,
        expected_count=expected,
        availability=valid / expected,
        accepted=accepted,
        used_two_of_three=used_two,
    )


def _stage_result(
    config: AggregationConfig,
    stage: AggregationStage,
    stage_index: int,
    rows: list[tuple[CellValue, ...]],
    completeness: tuple[CompletenessRecord, ...],
    accepted_count: int,
    rejected_count: int,
) -> tuple[AggregationStageResult, tuple[Diagnostic, ...]]:
    label = stage.label or stage.period.kind.value.replace("_", " ").title()
    table = DataTable(
        (
            PERIOD_START_COLUMN,
            PERIOD_END_COLUMN,
            *(field.resolved_output_name for field in config.fields),
        ),
        tuple(rows),
    )
    report = AggregationStageReport(
        stage_index=stage_index,
        label=label,
        period_kind=stage.period.kind,
        periods_evaluated=len(rows),
        values_accepted=accepted_count,
        values_rejected=rejected_count,
        completeness=stage.completeness,
    )
    diagnostics = (
        (
            Diagnostic(
                code="aggregation.insufficient_completeness",
                message=(
                    f"{rejected_count} field-period value(s) were missing because the '{label}' "
                    "completeness rule was not satisfied."
                ),
                count=rejected_count,
                columns=tuple(field.resolved_output_name for field in config.fields),
            ),
        )
        if rejected_count
        else ()
    )
    return AggregationStageResult(table, report, completeness), diagnostics


def _empty_stage(
    config: AggregationConfig, stage: AggregationStage, stage_index: int
) -> AggregationStageResult:
    label = stage.label or stage.period.kind.value.replace("_", " ").title()
    table = DataTable(
        (
            PERIOD_START_COLUMN,
            PERIOD_END_COLUMN,
            *(field.resolved_output_name for field in config.fields),
        ),
        (),
    )
    report = AggregationStageReport(
        stage_index,
        label,
        stage.period.kind,
        0,
        0,
        0,
        stage.completeness,
    )
    return AggregationStageResult(table, report, ())


def _required_datetime(value: CellValue, column: str) -> datetime:
    if not isinstance(value, datetime):
        raise AggregationError(f"Incremental stage column '{column}' is not a timestamp.")
    return value


def _instant(value: datetime) -> datetime:
    if value.utcoffset() is None:
        raise AggregationError("Aggregation timestamps must be timezone-aware.")
    return value.astimezone(UTC)


def _cancel(cancellation_check: Callable[[], None] | None) -> None:
    if cancellation_check is not None:
        cancellation_check()
