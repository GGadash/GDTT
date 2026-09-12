"""Bounded proposed-output previews compiled from Phase 5 configuration drafts.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import cast

from data_transform_tool.app.reformat_configuration import (
    ColumnDraft,
    ReformatDraft,
    TimezoneSourceMode,
    TransformChoice,
)
from data_transform_tool.datetime.custom_formats import apply_profile, decode
from data_transform_tool.datetime.models import TimestampSemantics
from data_transform_tool.datetime.operations import (
    DeriveIntervalFields,
    ParseDateTimeColumn,
)
from data_transform_tool.domain.errors import AppError
from data_transform_tool.domain.table import CellValue, DataTable
from data_transform_tool.gaps.generator import generate_gap_rows
from data_transform_tool.gaps.models import (
    ConfirmedInterval,
    GapFieldPolicy,
    GapGenerationConfig,
    MetadataBehavior,
    TimestampDerivation,
)
from data_transform_tool.io.models import FileInspection
from data_transform_tool.timezone.converter import TimezoneConversion, TimezoneSource
from data_transform_tool.transformation.base import Diagnostic, InvalidValuePolicy
from data_transform_tool.transformation.nulls import NormalizeConfirmedNulls
from data_transform_tool.transformation.numeric import (
    ConcentrationConversion,
    ConvertConcentration,
    RoundNumeric,
)
from data_transform_tool.transformation.recipe import OutputMissingPolicy
from data_transform_tool.validation.numeric import InvalidNumericPolicy, resolve_invalid_numeric
from data_transform_tool.validation.rows import RemoveNullRule, remove_null_rows


@dataclass(frozen=True)
class ProposedPreview:
    headers: tuple[str, ...]
    rows: tuple[tuple[object | None, ...], ...]
    source_row_start: int
    diagnostics: tuple[Diagnostic, ...] = ()
    error: str | None = None


@dataclass(frozen=True)
class ReformatExecution:
    table: DataTable
    diagnostics: tuple[Diagnostic, ...]
    generated_gap_rows: int = 0
    removed_rows: int = 0


def build_proposed_preview(
    inspection: FileInspection,
    draft: ReformatDraft,
) -> ProposedPreview:
    """Compile a bounded inspection slice through tested semantic operations."""
    if not inspection.previews:
        return ProposedPreview((), (), 1, error="No source preview rows are available.")
    preview = inspection.previews[0]
    source = _preview_table(inspection, preview.rows)
    try:
        transformed, diagnostics = _apply_preview_operations(source, draft)
        headers, selected_rows = _select_and_rename(transformed, draft)
        output_rows = _apply_output_missing_policy(selected_rows, draft)
        displayed = [list(row) for row in output_rows]
        for index, column in enumerate(draft.exported_columns):
            spec = decode(column.output_profile)
            if spec is not None and spec.kind == "number":
                for row_index, row in enumerate(selected_rows):
                    value = row[index]
                    if value is not None and not isinstance(value, (str, bool)):
                        displayed[row_index][index] = spec.display(value)
        output_rows = tuple(tuple(row) for row in displayed)
        return ProposedPreview(headers, output_rows, preview.start_row, diagnostics)
    except (AppError, ArithmeticError, ValueError) as error:
        headers, output_rows = _raw_selected_preview(source, draft)
        return ProposedPreview(headers, output_rows, preview.start_row, error=str(error))


def execute_reformat_table(table: DataTable, draft: ReformatDraft) -> ReformatExecution:
    """Execute a validated reformat draft against a complete guarded source table."""
    current, diagnostics = _apply_preview_operations(table, draft, format_output=False)
    generated = 0
    removed = 0
    if draft.gap_fill_enabled:
        if draft.timestamp_column is None or draft.interval_seconds is None:
            raise ValueError("Gap execution requires a confirmed timestamp and interval.")
        policies = tuple(
            _runtime_gap_policy(column)
            for column in draft.columns
            if not column.is_numeric and column.source_name != draft.timestamp_column
        )
        gap_result = generate_gap_rows(
            current,
            GapGenerationConfig(
                timestamp_column=draft.timestamp_column,
                interval=ConfirmedInterval(timedelta(seconds=draft.interval_seconds), "confirmed"),
                measurement_columns=tuple(
                    column.source_name for column in draft.measurement_columns
                ),
                field_policies=policies,
                allow_reorder=draft.allow_reorder,
            ),
        )
        current = gap_result.table
        generated = gap_result.report.generated_rows
    if draft.remove_empty_enabled:
        columns = tuple(column.source_name for column in draft.measurement_columns) or tuple(
            column.source_name for column in draft.exported_columns
        )
        removal = remove_null_rows(current, RemoveNullRule(draft.remove_empty_mode, columns))
        current = removal.table
        removed = removal.preview.remove_count
    current, formatting_diagnostics = _apply_output_formats(current, draft)
    diagnostics = (*diagnostics, *formatting_diagnostics)
    headers, rows = _select_and_rename(current, draft)
    return ReformatExecution(DataTable(headers, rows), diagnostics, generated, removed)


def prepare_reformat_batch(table: DataTable, draft: ReformatDraft) -> ReformatExecution:
    """Apply only row-local operations before global gap/order/removal handling."""
    current, diagnostics = _apply_preview_operations(table, draft, format_output=False)
    return ReformatExecution(current, diagnostics)


def finalize_reformat_batch(table: DataTable, draft: ReformatDraft) -> ReformatExecution:
    """Apply output formatting, selection, and rename to one globally resolved batch."""
    current, diagnostics = _apply_output_formats(table, draft)
    headers, rows = _select_and_rename(current, draft)
    return ReformatExecution(DataTable(headers, rows), diagnostics)


def proposed_column_samples(
    inspection: FileInspection,
    draft: ReformatDraft,
    source_name: str,
    *,
    limit: int = 4,
) -> tuple[str, ...]:
    column = draft.column(source_name)
    raw = column.samples[:limit]
    preview = build_proposed_preview(inspection, draft)
    try:
        output_index = preview.headers.index(column.output_name)
    except ValueError:
        return tuple(f"{value}  →  not exported" for value in raw)
    proposed = tuple(row[output_index] for row in preview.rows[:limit])
    pairs = zip(raw, proposed, strict=False)
    return tuple(f"{source}  →  {_display_sample(target)}" for source, target in pairs)


def _preview_table(
    inspection: FileInspection, rows: tuple[tuple[object | None, ...], ...]
) -> DataTable:
    safe_rows = tuple(
        tuple(_as_cell(value) for value in row[: inspection.column_count]) for row in rows
    )
    return DataTable(inspection.column_names, safe_rows)


def _as_cell(value: object | None) -> CellValue:
    try:
        DataTable(("Value",), ((cast(CellValue, value),),))
    except ValueError:
        return str(value)
    return cast(CellValue, value)


def _apply_preview_operations(
    table: DataTable, draft: ReformatDraft, *, format_output: bool = True
) -> tuple[DataTable, tuple[Diagnostic, ...]]:
    current = table
    diagnostics: list[Diagnostic] = []
    if draft.confirmed_missing_markers:
        result = NormalizeConfirmedNulls(draft.confirmed_missing_markers).apply(current)
        current = result.table
        diagnostics.extend(result.diagnostics)

    for column in draft.columns:
        if decode(column.input_profile) is not None and column.input_profile is not None:
            result = apply_profile(
                current,
                column.source_name,
                column.input_profile,
                _operation_invalid_policy(draft.invalid_numeric_policy),
                parsing=True,
            )
            if draft.invalid_numeric_policy is InvalidNumericPolicy.PRESERVE_SOURCE:
                before = current.column_values(column.source_name)
                after = result.table.column_values(column.source_name)
                preserved = tuple(
                    original if original is not None and converted is None else None
                    for original, converted in zip(before, after, strict=True)
                )
                current = result.table
                if any(value is not None for value in preserved):
                    current = current.add_column(f"{column.source_name}_source", preserved)
            else:
                current = result.table
            diagnostics.extend(result.diagnostics)
    numeric_sources = tuple(column.source_name for column in draft.measurement_columns)
    if numeric_sources:
        resolution = resolve_invalid_numeric(
            current,
            numeric_sources,
            draft.invalid_numeric_policy,
        )
        current = resolution.table
        if resolution.report.invalid_count:
            diagnostics.append(
                Diagnostic(
                    "invalid_numeric_preview",
                    "Invalid numeric values follow the selected file-level policy.",
                    resolution.report.invalid_count,
                    numeric_sources,
                )
            )

    for column in draft.columns:
        current, column_diagnostics = _apply_column(
            current,
            column,
            draft.interval_seconds,
            draft.invalid_numeric_policy,
            format_output=format_output,
        )
        diagnostics.extend(column_diagnostics)
    return current, tuple(diagnostics)


def _apply_column(
    table: DataTable,
    column: ColumnDraft,
    interval_seconds: float | None,
    invalid_numeric_policy: InvalidNumericPolicy,
    *,
    format_output: bool = True,
) -> tuple[DataTable, tuple[Diagnostic, ...]]:
    current = table
    diagnostics: list[Diagnostic] = []
    policy = _operation_invalid_policy(invalid_numeric_policy)
    if column.input_profile is not None and decode(column.input_profile) is None:
        result = ParseDateTimeColumn(
            column.source_name,
            column.input_profile,
            invalid_policy=policy,
        ).apply(current)
        current = result.table
        diagnostics.extend(result.diagnostics)

    if column.transform is TransformChoice.ROUND_2:
        result = RoundNumeric(column.source_name, 2, invalid_policy=policy).apply(current)
        current = result.table
        diagnostics.extend(result.diagnostics)
    elif column.transform in {TransformChoice.PPM_TO_PPB, TransformChoice.PPB_TO_PPM}:
        conversion = (
            ConcentrationConversion.PPM_TO_PPB
            if column.transform is TransformChoice.PPM_TO_PPB
            else ConcentrationConversion.PPB_TO_PPM
        )
        result = ConvertConcentration(column.source_name, conversion, invalid_policy=policy).apply(
            current
        )
        current = result.table
        diagnostics.extend(result.diagnostics)

    if column.target_timezone:
        result = TimezoneConversion(
            column.source_name,
            column.target_timezone,
            _timezone_source(column),
        ).apply(current)
        current = result.table
        diagnostics.extend(result.diagnostics)

    if any((column.derive_start, column.derive_midpoint, column.derive_end)):
        if interval_seconds is None:
            raise ValueError("Sampling duration is required for derived interval fields.")
        result = DeriveIntervalFields(
            TimestampSemantics(
                column.source_name,
                column.timestamp_role,
                timedelta(seconds=interval_seconds),
            ),
            start_output=f"{column.output_name} Start" if column.derive_start else None,
            midpoint_output=(f"{column.output_name} Mid" if column.derive_midpoint else None),
            end_output=f"{column.output_name} End" if column.derive_end else None,
        ).apply(current)
        current = result.table
        diagnostics.extend(result.diagnostics)

    if format_output and column.output_profile is not None:
        result = apply_profile(
            current, column.source_name, column.output_profile, policy, parsing=False
        )
        current = result.table
        diagnostics.extend(result.diagnostics)
    return current, tuple(diagnostics)


def _apply_output_formats(
    table: DataTable, draft: ReformatDraft
) -> tuple[DataTable, tuple[Diagnostic, ...]]:
    current = table
    diagnostics: list[Diagnostic] = []
    policy = _operation_invalid_policy(draft.invalid_numeric_policy)
    for column in draft.columns:
        if column.output_profile is None:
            continue
        result = apply_profile(
            current, column.source_name, column.output_profile, policy, parsing=False
        )
        current = result.table
        diagnostics.extend(result.diagnostics)
    return current, tuple(diagnostics)


def _select_and_rename(
    table: DataTable, draft: ReformatDraft
) -> tuple[tuple[str, ...], tuple[tuple[CellValue, ...], ...]]:
    selected = draft.exported_columns
    source_indexes = tuple(table.column_index(column.source_name) for column in selected)
    derived_names = tuple(
        name
        for column in selected
        for enabled, name in (
            (column.derive_start, f"{column.output_name} Start"),
            (column.derive_midpoint, f"{column.output_name} Mid"),
            (column.derive_end, f"{column.output_name} End"),
        )
        if enabled and name in table.columns
    )
    derived_indexes = tuple(table.column_index(name) for name in derived_names)
    headers = tuple(column.output_name for column in selected) + derived_names
    rows = tuple(
        tuple(row[index] for index in source_indexes + derived_indexes) for row in table.rows
    )
    return headers, rows


def _raw_selected_preview(
    table: DataTable, draft: ReformatDraft
) -> tuple[tuple[str, ...], tuple[tuple[object | None, ...], ...]]:
    selected = draft.exported_columns
    indexes = tuple(table.column_index(column.source_name) for column in selected)
    return (
        tuple(column.output_name for column in selected),
        tuple(tuple(row[index] for index in indexes) for row in table.rows),
    )


def _apply_output_missing_policy(
    rows: tuple[tuple[CellValue, ...], ...], draft: ReformatDraft
) -> tuple[tuple[object | None, ...], ...]:
    sentinel: object | None = {
        OutputMissingPolicy.TRUE_NULL: None,
        OutputMissingPolicy.NA: "N/A",
        OutputMissingPolicy.MINUS_999: -999,
        OutputMissingPolicy.CUSTOM: draft.custom_missing_sentinel,
    }[draft.output_missing_policy]
    return tuple(tuple(sentinel if value is None else value for value in row) for row in rows)


def _timezone_source(column: ColumnDraft) -> TimezoneSource:
    value = column.timezone_source_value or ""
    if column.timezone_source_mode is TimezoneSourceMode.EMBEDDED:
        return TimezoneSource.embedded()
    if column.timezone_source_mode is TimezoneSourceMode.FIXED_IANA:
        return TimezoneSource.fixed(value)
    if column.timezone_source_mode is TimezoneSourceMode.IANA_COLUMN:
        return TimezoneSource.from_column(value)
    if column.timezone_source_mode is TimezoneSourceMode.MANUAL_OFFSET:
        return TimezoneSource.manual_offset(_offset_minutes(value))
    raise ValueError("Timezone conversion requires an explicit source mode.")


def _runtime_gap_policy(column: ColumnDraft) -> GapFieldPolicy:
    behavior = MetadataBehavior(column.gap_behavior.value)
    derivation = (
        TimestampDerivation.COPY if behavior is MetadataBehavior.DERIVED_FROM_TIMESTAMP else None
    )
    return GapFieldPolicy(
        column.source_name,
        behavior,
        fixed_value=column.gap_fixed_value,
        derivation=derivation,
    )


def _offset_minutes(value: str) -> int:
    text = value.strip()
    sign = -1 if text.startswith("-") else 1
    text = text.removeprefix("+").removeprefix("-")
    parts = text.split(":")
    if len(parts) not in {1, 2} or not all(part.isdigit() for part in parts):
        raise ValueError("Manual offsets must look like +05:30 or -04:00.")
    hours = int(parts[0])
    minutes = int(parts[1]) if len(parts) == 2 else 0
    if minutes > 59:
        raise ValueError("Manual offset minutes must be between 00 and 59.")
    return sign * (hours * 60 + minutes)


def _operation_invalid_policy(policy: InvalidNumericPolicy) -> InvalidValuePolicy:
    return {
        InvalidNumericPolicy.NULL_AND_CONTINUE: InvalidValuePolicy.NULL,
        InvalidNumericPolicy.INSPECT: InvalidValuePolicy.PRESERVE,
        InvalidNumericPolicy.STOP: InvalidValuePolicy.STOP,
        InvalidNumericPolicy.PRESERVE_SOURCE: InvalidValuePolicy.NULL,
    }[policy]


def _display_sample(value: object | None) -> str:
    if value is None:
        return "∅ True Null"
    return str(value)
