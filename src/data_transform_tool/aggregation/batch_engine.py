"""Streaming first-stage aggregation over replayable spill batches.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from data_transform_tool.aggregation.engine import (
    aggregate_first_stage,
    continue_incremental_stages,
)
from data_transform_tool.aggregation.models import (
    AggregationConfig,
    AggregationError,
    AggregationResult,
    AggregationStageReport,
    AggregationStageResult,
    CompletenessRecord,
)
from data_transform_tool.aggregation.periods import Periodizer
from data_transform_tool.app.averaging_configuration import (
    AveragingDraft,
    build_aggregation_config,
)
from data_transform_tool.app.averaging_preview import prepare_averaging_source
from data_transform_tool.domain.batches import DEFAULT_BATCH_SIZE, TabularData, iter_rows
from data_transform_tool.domain.errors import Severity
from data_transform_tool.domain.spill import (
    DuplicateSortKeyError,
    SpillTable,
    SpillWorkspace,
)
from data_transform_tool.domain.table import CellValue, DataRow, DataTable
from data_transform_tool.io.cancellation import CancellationToken
from data_transform_tool.transformation.base import Diagnostic
from data_transform_tool.transformation.nulls import NormalizeConfirmedNulls

ProgressCallback = Callable[[str, int], None]


@dataclass(frozen=True)
class BatchAggregationResult:
    table: SpillTable
    stages: tuple[AggregationStageResult, ...]
    diagnostics: tuple[Diagnostic, ...] = ()


def execute_averaging_batches(
    source: TabularData,
    draft: AveragingDraft,
    workspace: SpillWorkspace,
    cancellation: CancellationToken,
    *,
    batch_size: int = DEFAULT_BATCH_SIZE,
    progress: ProgressCallback | None = None,
) -> BatchAggregationResult:
    """Stream-normalize source rows and aggregate exact first-stage period windows."""
    if batch_size <= 0:
        raise ValueError("Batch size must be greater than zero.")
    config = build_aggregation_config(draft)
    normalized_columns = source.columns

    def normalized_rows() -> Iterator[DataRow]:
        processed = 0
        for batch in source.iter_batches(batch_size):
            cancellation.raise_if_cancelled()
            current = DataTable(source.columns, batch.rows)
            if draft.confirmed_missing_markers:
                current = (
                    NormalizeConfirmedNulls(draft.confirmed_missing_markers).apply(current).table
                )
            prepared = prepare_averaging_source(current, draft)
            yield from prepared.rows
            processed += len(batch.rows)
            if progress is not None:
                progress("Normalizing Averaging source", processed)

    normalized = workspace.write_table(
        "average-local",
        normalized_columns,
        normalized_rows(),
        cancellation,
        batch_size=batch_size,
    )
    ordered, reordered = _ordered_source(
        normalized,
        config,
        workspace,
        cancellation,
        batch_size=batch_size,
    )
    first_stage, first_diagnostics = _stream_first_stage(
        ordered,
        config,
        cancellation,
        batch_size=batch_size,
        progress=progress,
    )
    continuation = continue_incremental_stages(
        first_stage,
        config,
        cancellation_check=cancellation.raise_if_cancelled,
    )
    diagnostics = _DiagnosticAccumulator()
    diagnostics.extend(first_diagnostics)
    diagnostics.extend(continuation.diagnostics)
    if reordered:
        diagnostics.extend(
            (
                Diagnostic(
                    code="aggregation.input_reordered",
                    message=(
                        "Input rows were explicitly reordered by timestamp before aggregation."
                    ),
                    severity=Severity.INFORMATION,
                ),
            )
        )
    result = AggregationResult(continuation.stages, diagnostics.result())
    output = workspace.write_table(
        "average-output",
        result.table.columns,
        result.table.rows,
        cancellation,
        batch_size=batch_size,
    )
    if progress is not None:
        progress("Averaging spill execution complete", output.row_count)
    return BatchAggregationResult(output, result.stages, result.diagnostics)


def _ordered_source(
    source: SpillTable,
    config: AggregationConfig,
    workspace: SpillWorkspace,
    cancellation: CancellationToken,
    *,
    batch_size: int,
) -> tuple[SpillTable, bool]:
    timestamp_index = source.columns.index(config.timestamp_column)
    previous: int | None = None
    needs_sort = False
    for row_number, row in enumerate(iter_rows(source, batch_size), start=1):
        cancellation.raise_if_cancelled()
        timestamp = _required_aware_timestamp(row[timestamp_index], row_number)
        current = _datetime_key(timestamp)
        if previous is not None:
            if current == previous:
                raise AggregationError(
                    f"Duplicate timestamp instants occur at rows {row_number - 1} and {row_number}."
                )
            needs_sort = needs_sort or current < previous
        previous = current
    if not needs_sort:
        return source, False
    try:
        ordered = workspace.write_sorted_table(
            "average-ordered",
            source.columns,
            iter_rows(source, batch_size),
            lambda row: _datetime_key(_required_aware_timestamp(row[timestamp_index], 0)),
            cancellation,
            require_unique=True,
            batch_size=batch_size,
        )
    except DuplicateSortKeyError as error:
        raise AggregationError(
            f"Duplicate timestamp instants occur at rows {error.first_row} and {error.second_row}."
        ) from error
    if not config.allow_reorder:
        raise AggregationError(
            "Input timestamps are not chronological; enable explicit reordering to continue."
        )
    return ordered, True


def _stream_first_stage(
    source: SpillTable,
    config: AggregationConfig,
    cancellation: CancellationToken,
    *,
    batch_size: int,
    progress: ProgressCallback | None,
) -> tuple[AggregationStageResult, tuple[Diagnostic, ...]]:
    periodizer = Periodizer(config.stages[0].period, config.reporting_timezone)
    timestamp_index = source.columns.index(config.timestamp_column)
    rows: list[DataRow] = []
    completeness: list[CompletenessRecord] = []
    diagnostics = _DiagnosticAccumulator()
    accepted = 0
    rejected = 0
    periods = 0
    current_key: int | None = None
    current_bounds = None
    group: list[DataRow] = []

    def append_group(values: tuple[DataRow, ...]) -> None:
        nonlocal accepted, rejected, periods
        stage, stage_diagnostics = aggregate_first_stage(
            DataTable(source.columns, values),
            config,
            cancellation_check=cancellation.raise_if_cancelled,
        )
        if stage.table.row_count != 1:
            raise AggregationError("A streamed first-stage window did not produce one period.")
        rows.extend(stage.table.rows)
        completeness.extend(stage.completeness)
        accepted += stage.report.values_accepted
        rejected += stage.report.values_rejected
        periods += 1
        diagnostics.extend(stage_diagnostics)
        if periods > config.max_periods:
            raise AggregationError(
                f"The selected range exceeds the configured {config.max_periods:,}-period limit."
            )
        if progress is not None and periods % 1_000 == 0:
            progress("Aggregating reporting periods", periods)

    for row in iter_rows(source, batch_size):
        cancellation.raise_if_cancelled()
        timestamp = _required_aware_timestamp(row[timestamp_index], 0)
        bounds = periodizer.period_for(timestamp)
        key = _datetime_key(bounds.start)
        if current_key is None:
            current_key = key
            current_bounds = bounds
        elif key != current_key:
            append_group(tuple(group))
            if current_bounds is None:
                raise AssertionError("A current period is required after the first row.")
            missing = periodizer.next_period(current_bounds)
            while _datetime_key(missing.start) < key:
                synthetic = tuple(
                    missing.start if index == timestamp_index else None
                    for index in range(source.column_count)
                )
                append_group((synthetic,))
                missing = periodizer.next_period(missing)
            current_key = key
            current_bounds = bounds
            group.clear()
        group.append(row)
    if group:
        append_group(tuple(group))
    if not rows:
        empty, empty_diagnostics = aggregate_first_stage(
            DataTable(source.columns, ()),
            config,
            cancellation_check=cancellation.raise_if_cancelled,
        )
        return empty, empty_diagnostics
    stage = config.stages[0]
    label = stage.label or stage.period.kind.value.replace("_", " ").title()
    report = AggregationStageReport(
        stage_index=1,
        label=label,
        period_kind=stage.period.kind,
        periods_evaluated=periods,
        values_accepted=accepted,
        values_rejected=rejected,
        completeness=stage.completeness,
    )
    return (
        AggregationStageResult(
            DataTable(
                (
                    "Period_Start",
                    "Period_End",
                    *(field.resolved_output_name for field in config.fields),
                ),
                tuple(rows),
            ),
            report,
            tuple(completeness),
        ),
        diagnostics.result(),
    )


def _required_aware_timestamp(value: CellValue, row_number: int) -> datetime:
    if not isinstance(value, datetime):
        location = f" at row {row_number}" if row_number else ""
        raise AggregationError(f"The aggregation timestamp is missing or invalid{location}.")
    if value.utcoffset() is None:
        location = f" at row {row_number}" if row_number else ""
        raise AggregationError(f"The aggregation timestamp{location} is timezone-naive.")
    return value


def _datetime_key(value: datetime) -> int:
    epoch = datetime(1970, 1, 1, tzinfo=UTC)
    elapsed = value.astimezone(UTC) - epoch
    return _timedelta_microseconds(elapsed)


def _timedelta_microseconds(value: timedelta) -> int:
    return (value.days * 86_400 + value.seconds) * 1_000_000 + value.microseconds


class _DiagnosticAccumulator:
    def __init__(self) -> None:
        self._items: dict[tuple[object, ...], int] = {}
        self._templates: dict[tuple[object, ...], Diagnostic] = {}

    def extend(self, diagnostics: tuple[Diagnostic, ...]) -> None:
        for item in diagnostics:
            key = (item.code, item.message, item.columns, item.severity)
            self._items[key] = self._items.get(key, 0) + item.count
            self._templates[key] = item

    def result(self) -> tuple[Diagnostic, ...]:
        return tuple(
            Diagnostic(
                template.code,
                template.message,
                self._items[key],
                template.columns,
                template.severity,
            )
            for key, template in self._templates.items()
        )
