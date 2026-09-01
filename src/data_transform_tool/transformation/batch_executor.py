"""Bounded-memory Reformat execution with private spill and cross-batch semantics.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from data_transform_tool.app.reformat_configuration import (
    GapBehaviorChoice,
    ReformatDraft,
)
from data_transform_tool.app.reformat_preview import (
    finalize_reformat_batch,
    prepare_reformat_batch,
)
from data_transform_tool.domain.batches import DEFAULT_BATCH_SIZE, TabularData, iter_rows
from data_transform_tool.domain.spill import (
    DuplicateSortKeyError,
    SpillTable,
    SpillWorkspace,
)
from data_transform_tool.domain.table import CellValue, DataRow, DataTable
from data_transform_tool.io.cancellation import CancellationToken
from data_transform_tool.transformation.base import Diagnostic, TransformationError
from data_transform_tool.validation.rows import RemoveNullRule, row_matches_null_rule

ProgressCallback = Callable[[str, int], None]
_MAX_EXPECTED_ROWS = 1_000_000


@dataclass(frozen=True)
class BatchReformatResult:
    table: SpillTable
    diagnostics: tuple[Diagnostic, ...]
    generated_gap_rows: int = 0
    removed_rows: int = 0


def execute_reformat_batches(
    source: TabularData,
    draft: ReformatDraft,
    workspace: SpillWorkspace,
    cancellation: CancellationToken,
    *,
    batch_size: int = DEFAULT_BATCH_SIZE,
    progress: ProgressCallback | None = None,
) -> BatchReformatResult:
    """Execute row-local work in chunks and global gap/order rules through spill passes."""
    if batch_size <= 0:
        raise ValueError("Batch size must be greater than zero.")
    diagnostics = _DiagnosticAccumulator()
    local_columns = prepare_reformat_batch(DataTable(source.columns, ()), draft).table.columns

    def local_rows() -> Iterator[DataRow]:
        processed = 0
        for batch in source.iter_batches(batch_size):
            cancellation.raise_if_cancelled()
            result = prepare_reformat_batch(DataTable(source.columns, batch.rows), draft)
            diagnostics.extend(result.diagnostics)
            yield from result.table.rows
            processed += len(batch.rows)
            if progress is not None:
                progress("Applying row-local transformations", processed)

    local = workspace.write_table(
        "reformat-local",
        local_columns,
        local_rows(),
        cancellation,
        batch_size=batch_size,
    )
    ordered = local
    stable_values: dict[str, CellValue] = {}
    if draft.gap_fill_enabled:
        ordered, stable_values = _prepare_gap_source(
            local,
            draft,
            workspace,
            cancellation,
            batch_size=batch_size,
        )

    generated = 0
    removed = 0
    removal_rule, removal_indexes = _removal_rule(ordered, draft)
    final_columns = finalize_reformat_batch(DataTable(ordered.columns, ()), draft).table.columns

    def output_rows() -> Iterator[DataRow]:
        nonlocal generated, removed
        buffer: list[DataRow] = []

        def mark_generated() -> None:
            nonlocal generated
            generated += 1

        resolved_rows = (
            _gap_rows(ordered, draft, stable_values, cancellation, mark_generated)
            if draft.gap_fill_enabled
            else iter_rows(ordered, batch_size)
        )
        for row in resolved_rows:
            cancellation.raise_if_cancelled()
            if removal_rule is not None and row_matches_null_rule(
                row,
                removal_indexes,
                removal_rule,
            ):
                removed += 1
                continue
            buffer.append(row)
            if len(buffer) < batch_size:
                continue
            finalized = finalize_reformat_batch(
                DataTable(ordered.columns, tuple(buffer)),
                draft,
            )
            diagnostics.extend(finalized.diagnostics)
            yield from finalized.table.rows
            buffer.clear()
        if buffer:
            finalized = finalize_reformat_batch(
                DataTable(ordered.columns, tuple(buffer)),
                draft,
            )
            diagnostics.extend(finalized.diagnostics)
            yield from finalized.table.rows

    output = workspace.write_table(
        "reformat-output",
        final_columns,
        output_rows(),
        cancellation,
        batch_size=batch_size,
    )
    if progress is not None:
        progress("Reformat spill execution complete", output.row_count)
    return BatchReformatResult(
        output,
        diagnostics.result(),
        generated,
        removed,
    )


def _prepare_gap_source(
    source: SpillTable,
    draft: ReformatDraft,
    workspace: SpillWorkspace,
    cancellation: CancellationToken,
    *,
    batch_size: int,
) -> tuple[SpillTable, dict[str, CellValue]]:
    timestamp_name, _ = _gap_settings(draft)
    timestamp_index = source.columns.index(timestamp_name)
    stable_columns = tuple(
        column.source_name
        for column in draft.columns
        if not column.is_numeric
        and column.source_name != timestamp_name
        and column.gap_behavior is GapBehaviorChoice.CARRY_STABLE
    )
    stable_indexes = {column: source.columns.index(column) for column in stable_columns}
    stable_values: dict[str, CellValue] = {}
    previous_key: int | None = None
    awareness: bool | None = None
    needs_sort = False
    for row_number, row in enumerate(iter_rows(source, batch_size), start=1):
        cancellation.raise_if_cancelled()
        value = row[timestamp_index]
        if not isinstance(value, datetime):
            raise TransformationError(
                f"Gap generation requires a valid primary timestamp in row {row_number}."
            )
        current_awareness = value.utcoffset() is not None
        if awareness is None:
            awareness = current_awareness
        elif awareness != current_awareness:
            raise TransformationError(
                "The primary timestamp column mixes timezone-aware and timezone-naive values."
            )
        current_key = _datetime_key(value)
        if previous_key is not None:
            if current_key == previous_key:
                raise TransformationError(
                    f"Duplicate primary timestamps occur at rows {row_number - 1} and {row_number}."
                )
            needs_sort = needs_sort or current_key < previous_key
        previous_key = current_key
        for column, index in stable_indexes.items():
            candidate = row[index]
            if candidate is None:
                continue
            if column not in stable_values:
                stable_values[column] = candidate
            elif not _same_scalar(stable_values[column], candidate):
                raise TransformationError(
                    f"Column '{column}' is not stable and cannot be carried into gap rows."
                )
    for column in stable_columns:
        stable_values.setdefault(column, None)
    if not needs_sort:
        return source, stable_values
    try:
        ordered = workspace.write_sorted_table(
            "reformat-ordered",
            source.columns,
            iter_rows(source, batch_size),
            lambda row: _datetime_key(_required_datetime(row[timestamp_index])),
            cancellation,
            require_unique=True,
            batch_size=batch_size,
        )
    except DuplicateSortKeyError as error:
        raise TransformationError(
            f"Duplicate primary timestamps occur at rows {error.first_row} and {error.second_row}."
        ) from error
    if not draft.allow_reorder:
        raise TransformationError(
            "Primary timestamps are not chronological; explicitly allow reordering first."
        )
    return ordered, stable_values


def _gap_rows(
    source: SpillTable,
    draft: ReformatDraft,
    stable_values: dict[str, CellValue],
    cancellation: CancellationToken,
    on_generated: Callable[[], None],
) -> Iterator[DataRow]:
    timestamp_name, interval = _gap_settings(draft)
    timestamp_index = source.columns.index(timestamp_name)
    rows = iter_rows(source)
    first = next(rows, None)
    if first is None:
        return
    first_timestamp = _required_datetime(first[timestamp_index])
    first_key = _datetime_key(first_timestamp)
    last_key = first_key
    yield first
    for row_number, row in enumerate(rows, start=2):
        cancellation.raise_if_cancelled()
        current_timestamp = _required_datetime(row[timestamp_index])
        current_key = _datetime_key(current_timestamp)
        if current_key == last_key:
            raise TransformationError(
                f"Duplicate primary timestamps occur at rows {row_number - 1} and {row_number}."
            )
        if current_key < last_key:
            raise TransformationError("The external timestamp ordering pass did not remain stable.")
        if (current_key - first_key) % interval:
            raise TransformationError(
                f"The primary timestamp at row {row_number} is off the confirmed interval grid."
            )
        expected_rows = (current_key - first_key) // interval + 1
        if expected_rows > _MAX_EXPECTED_ROWS:
            raise TransformationError(
                f"The confirmed interval would create {expected_rows:,} expected rows, "
                f"above the configured limit of {_MAX_EXPECTED_ROWS:,}."
            )
        missing_key = last_key + interval
        while missing_key < current_key:
            timestamp = _timestamp_from_key(missing_key, first_timestamp)
            on_generated()
            yield _generated_row(source.columns, timestamp, draft, stable_values)
            missing_key += interval
        yield row
        last_key = current_key


def _generated_row(
    columns: tuple[str, ...],
    timestamp: datetime,
    draft: ReformatDraft,
    stable_values: dict[str, CellValue],
) -> DataRow:
    if draft.timestamp_column is None:
        raise AssertionError("Validated gap execution always has a timestamp column.")
    measurements = {column.source_name for column in draft.measurement_columns}
    policies = {column.source_name: column for column in draft.columns}
    values: list[CellValue] = []
    for name in columns:
        if name == draft.timestamp_column:
            values.append(timestamp)
        elif name in measurements or name not in policies:
            values.append(None)
        else:
            column = policies[name]
            if column.gap_behavior is GapBehaviorChoice.CARRY_STABLE:
                values.append(stable_values.get(name))
            elif column.gap_behavior is GapBehaviorChoice.FIXED_VALUE:
                values.append(column.gap_fixed_value)
            elif column.gap_behavior is GapBehaviorChoice.DERIVED_FROM_TIMESTAMP:
                values.append(timestamp)
            else:
                values.append(None)
    return tuple(values)


def _removal_rule(
    table: SpillTable,
    draft: ReformatDraft,
) -> tuple[RemoveNullRule | None, tuple[int, ...]]:
    if not draft.remove_empty_enabled:
        return None, ()
    columns = tuple(column.source_name for column in draft.measurement_columns) or tuple(
        column.source_name for column in draft.exported_columns
    )
    rule = RemoveNullRule(draft.remove_empty_mode, columns)
    return rule, tuple(table.columns.index(column) for column in columns)


def _gap_settings(draft: ReformatDraft) -> tuple[str, int]:
    if draft.timestamp_column is None or draft.interval_seconds is None:
        raise ValueError("Gap execution requires a confirmed timestamp and interval.")
    interval = timedelta(seconds=draft.interval_seconds)
    microseconds = _timedelta_microseconds(interval)
    if microseconds <= 0:
        raise ValueError("The confirmed interval must be greater than zero.")
    return draft.timestamp_column, microseconds


def _required_datetime(value: CellValue) -> datetime:
    if not isinstance(value, datetime):
        raise TransformationError("Gap execution encountered an invalid primary timestamp.")
    return value


def _datetime_key(value: datetime) -> int:
    epoch = (
        datetime(1970, 1, 1, tzinfo=UTC) if value.utcoffset() is not None else datetime(1970, 1, 1)
    )
    normalized = value.astimezone(UTC) if value.utcoffset() is not None else value
    return _timedelta_microseconds(normalized - epoch)


def _timestamp_from_key(value: int, representative: datetime) -> datetime:
    if representative.utcoffset() is None:
        return datetime(1970, 1, 1) + timedelta(microseconds=value)
    instant = datetime(1970, 1, 1, tzinfo=UTC) + timedelta(microseconds=value)
    return instant.astimezone(representative.tzinfo)


def _timedelta_microseconds(value: timedelta) -> int:
    return (value.days * 86_400 + value.seconds) * 1_000_000 + value.microseconds


def _same_scalar(left: CellValue, right: CellValue) -> bool:
    return type(left) is type(right) and left == right


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
