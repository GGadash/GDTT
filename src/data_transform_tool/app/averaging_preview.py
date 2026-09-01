"""Bounded Phase 7 previews executed by the tested aggregation engine.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import cast
from zoneinfo import ZoneInfo

from data_transform_tool.aggregation import (
    AggregationResult,
    AggregationStageResult,
    aggregate_table,
)
from data_transform_tool.app.averaging_configuration import (
    AveragingDraft,
    build_aggregation_config,
    validate_averaging_draft,
)
from data_transform_tool.datetime.parser import DateTimeParser
from data_transform_tool.domain.errors import AppError
from data_transform_tool.domain.table import CellValue, DataTable
from data_transform_tool.io.models import FileInspection
from data_transform_tool.transformation.nulls import NormalizeConfirmedNulls
from data_transform_tool.transformation.numeric import to_decimal
from data_transform_tool.transformation.recipe import OutputMissingPolicy


@dataclass(frozen=True)
class PreviewTable:
    headers: tuple[str, ...]
    rows: tuple[tuple[object | None, ...], ...]


@dataclass(frozen=True)
class StagePreview:
    label: str
    table: PreviewTable
    completeness_headers: tuple[str, ...]
    completeness_rows: tuple[tuple[object | None, ...], ...]
    accepted: int
    rejected: int


@dataclass(frozen=True)
class AveragingPreview:
    final_table: PreviewTable
    stages: tuple[StagePreview, ...]
    diagnostics: tuple[str, ...] = ()
    source_row_start: int = 1
    source_row_count: int = 0
    error: str | None = None


def build_averaging_preview(
    inspection: FileInspection,
    draft: AveragingDraft,
) -> AveragingPreview:
    """Execute one bounded source slice without mutating data or UI state."""
    validation = validate_averaging_draft(draft)
    if validation.errors:
        return _error_preview("Complete the required confirmations to calculate the preview.")
    if not inspection.previews:
        return _error_preview("No bounded source rows are available for preview.")
    source_preview = inspection.previews[0]
    try:
        source_rows = cast(tuple[tuple[CellValue, ...], ...], source_preview.rows)
        source = DataTable(inspection.column_names, source_rows)
        if draft.confirmed_missing_markers:
            source = NormalizeConfirmedNulls(draft.confirmed_missing_markers).apply(source).table
        prepared = prepare_averaging_source(source, draft)
        result = aggregate_table(prepared, build_aggregation_config(draft))
        stages = tuple(_stage_preview(stage, draft) for stage in result.stages)
        final = stages[-1].table if stages else PreviewTable((), ())
        diagnostics = tuple(
            f"{item.message} ({item.count})" if item.count else item.message
            for item in result.diagnostics
        )
        return AveragingPreview(
            final_table=final,
            stages=stages,
            diagnostics=diagnostics,
            source_row_start=source_preview.start_row,
            source_row_count=len(source_preview.rows),
        )
    except (AppError, ValueError, TypeError) as error:
        message = error.user_message if isinstance(error, AppError) else str(error)
        return AveragingPreview(
            final_table=PreviewTable((), ()),
            stages=(),
            source_row_start=source_preview.start_row,
            source_row_count=len(source_preview.rows),
            error=message,
        )


def prepare_averaging_source(table: DataTable, draft: AveragingDraft) -> DataTable:
    """Normalize a complete or bounded source table for the aggregation engine."""
    timestamp_name = draft.timestamp_column
    if timestamp_name is None:
        raise ValueError("Choose a timestamp field before previewing.")
    parser = DateTimeParser()
    zone = ZoneInfo(draft.source_timezone)
    timestamps: list[CellValue] = []
    for row_number, value in enumerate(table.column_values(timestamp_name), start=1):
        if value is None:
            raise ValueError(f"The timestamp is missing in bounded preview row {row_number}.")
        try:
            parsed = (
                value
                if isinstance(value, datetime)
                else parser.parse(value, draft.timestamp_profile)
            )
        except ValueError as error:
            raise ValueError(
                f"The timestamp in bounded preview row {row_number} does not match "
                f"profile '{draft.timestamp_profile}'."
            ) from error
        if not isinstance(parsed, datetime):
            raise ValueError("The selected timestamp profile must produce DateTime values.")
        timestamps.append(parsed.replace(tzinfo=zone) if parsed.utcoffset() is None else parsed)
    current = table.replace_column(timestamp_name, tuple(timestamps))
    numeric_names = {field.source_name for field in draft.selected_fields}
    numeric_names.update(
        field.duration_column
        for field in draft.selected_fields
        if field.duration_column is not None
    )
    for name in sorted(numeric_names):
        values: list[CellValue] = []
        for value in current.column_values(name):
            if value is None:
                values.append(None)
                continue
            try:
                values.append(to_decimal(value))
            except ValueError:
                values.append(None)
        current = current.replace_column(name, tuple(values))
    return current


def execute_averaging_table(table: DataTable, draft: AveragingDraft) -> AggregationResult:
    """Execute an averaging draft against a complete guarded source table."""
    current = table
    if draft.confirmed_missing_markers:
        current = NormalizeConfirmedNulls(draft.confirmed_missing_markers).apply(current).table
    prepared = prepare_averaging_source(current, draft)
    return aggregate_table(prepared, build_aggregation_config(draft))


def _stage_preview(stage: AggregationStageResult, draft: AveragingDraft) -> StagePreview:
    rows = tuple(tuple(_display_value(value, draft) for value in row) for row in stage.table.rows)
    completeness_rows = tuple(
        (
            record.field,
            record.period_start,
            f"{record.valid_count} / {record.expected_count}",
            f"{record.availability:.1%}",
            "Accepted" if record.accepted else "Missing",
            "2 of 3" if record.used_two_of_three else "—",
        )
        for record in stage.completeness
    )
    return StagePreview(
        label=stage.report.label,
        table=PreviewTable(stage.table.columns, rows),
        completeness_headers=(
            "Field",
            "Period start",
            "Valid / expected",
            "Availability",
            "Result",
            "Exception",
        ),
        completeness_rows=completeness_rows,
        accepted=stage.report.values_accepted,
        rejected=stage.report.values_rejected,
    )


def _display_value(value: CellValue, draft: AveragingDraft) -> object | None:
    if value is not None:
        return float(value) if isinstance(value, Decimal) else value
    if draft.output_missing_policy is OutputMissingPolicy.TRUE_NULL:
        return None
    if draft.output_missing_policy is OutputMissingPolicy.NA:
        return "N/A"
    if draft.output_missing_policy is OutputMissingPolicy.MINUS_999:
        return -999
    return draft.custom_missing_sentinel


def _error_preview(message: str) -> AveragingPreview:
    return AveragingPreview(PreviewTable((), ()), (), error=message)
