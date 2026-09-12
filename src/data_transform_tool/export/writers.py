"""Atomic CSV and XLSX data writers with explicit canonical-null handling.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

import os
import tempfile
from collections.abc import Callable
from contextlib import suppress
from dataclasses import replace
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import xlsxwriter  # type: ignore[import-untyped]

from data_transform_tool.datetime.custom_formats import decode
from data_transform_tool.domain.batches import TabularData, iter_rows
from data_transform_tool.domain.errors import AppError
from data_transform_tool.domain.table import CellValue, DataRow
from data_transform_tool.export.models import ExportArtifact, ExportPlan, XlsxStyle
from data_transform_tool.export.naming import data_output_path
from data_transform_tool.io.cancellation import CancellationToken
from data_transform_tool.transformation.recipe import OutputFormat, OutputMissingPolicy
from data_transform_tool.validation.serialization import serialize_delimited_row

_XLSX_MAX_ROWS = 1_048_576
ProgressCallback = Callable[[int, str], None]


def write_data_outputs(
    table: TabularData,
    plan: ExportPlan,
    cancellation: CancellationToken,
    progress: ProgressCallback | None = None,
) -> tuple[ExportArtifact, ...]:
    """Write selected formats through same-directory temporary files."""
    plan.destination.mkdir(parents=True, exist_ok=True)
    artifacts: list[ExportArtifact] = []
    total = len(plan.formats)
    for index, output_format in enumerate(plan.formats):
        cancellation.raise_if_cancelled()
        target = data_output_path(plan.destination, plan.base_name, output_format)
        _ensure_available(target, plan.allow_overwrite)
        if progress is not None:
            progress(int(index / total * 100), f"Writing {target.name}")
        if output_format is OutputFormat.CSV:
            _write_csv_atomic(target, table, plan, cancellation)
        else:
            _write_xlsx_atomic(
                target,
                table,
                plan,
                formatted=output_format is OutputFormat.XLSX_FORMATTED,
                cancellation=cancellation,
            )
        artifacts.append(ExportArtifact(output_format.value, target, table.row_count))
    if progress is not None:
        progress(100, "Data outputs written")
    return tuple(artifacts)


def output_value(value: CellValue, plan: ExportPlan) -> CellValue:
    if value is not None:
        return value
    if plan.missing_policy is OutputMissingPolicy.TRUE_NULL:
        return None
    if plan.missing_policy is OutputMissingPolicy.NA:
        return "N/A"
    if plan.missing_policy is OutputMissingPolicy.MINUS_999:
        return -999
    return plan.custom_missing_sentinel


def output_row(row: DataRow, plan: ExportPlan) -> DataRow:
    return tuple(output_value(value, plan) for value in row)


def csv_output_row(row: DataRow, plan: ExportPlan, columns: tuple[str, ...]) -> DataRow:
    profiles = dict(plan.number_profiles)
    return tuple(
        spec.display(value, csv=True)
        if value is not None
        and not isinstance(value, (bool, str))
        and (spec := decode(profiles.get(name))) is not None
        else output_value(value, plan)
        for name, value in zip(columns, row, strict=True)
    )


def _write_csv_atomic(
    target: Path,
    table: TabularData,
    plan: ExportPlan,
    cancellation: CancellationToken,
) -> None:
    temporary = _temporary_path(target)
    try:
        with temporary.open("w", encoding="utf-8-sig", newline="") as stream:
            stream.write(serialize_delimited_row(table.columns) + "\n")
            for index, row in enumerate(iter_rows(table)):
                if index % 10_000 == 0:
                    cancellation.raise_if_cancelled()
                stream.write(
                    serialize_delimited_row(csv_output_row(row, plan, table.columns)) + "\n"
                )
        cancellation.raise_if_cancelled()
        os.replace(temporary, target)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _write_xlsx_atomic(
    target: Path,
    table: TabularData,
    plan: ExportPlan,
    *,
    formatted: bool,
    cancellation: CancellationToken,
) -> None:
    if table.row_count + 1 > _XLSX_MAX_ROWS:
        raise AppError(
            "The output exceeds Excel's 1,048,576-row worksheet limit. "
            "Choose CSV, reduce the dataset, or split the output."
        )
    temporary = _temporary_path(target)
    workbook: Any | None = None
    try:
        workbook = xlsxwriter.Workbook(
            temporary,
            {"constant_memory": True, "default_date_format": "yyyy-mm-dd hh:mm:ss"},
        )
        worksheet = workbook.add_worksheet("Data")
        formats = _xlsx_formats(workbook, plan.xlsx_style) if formatted else {}
        column_formats = {}
        for name, profile in plan.number_profiles:
            spec = decode(profile)
            if spec is None:
                continue
            specific = (
                _xlsx_formats(workbook, replace(plan.xlsx_style, numeric_format=spec.pattern))
                if formatted
                else {"numeric": workbook.add_format({"num_format": spec.pattern})}
            )
            column_formats[name] = specific
        header_format = formats.get("header")
        for column, name in enumerate(table.columns):
            worksheet.write(0, column, name, header_format)
        for row_index, source_row in enumerate(iter_rows(table), start=1):
            if row_index % 10_000 == 0:
                cancellation.raise_if_cancelled()
            values = output_row(source_row, plan)
            for column_index, value in enumerate(values):
                _write_xlsx_cell(
                    worksheet,
                    row_index,
                    column_index,
                    value,
                    column_formats.get(table.columns[column_index], formats),
                    alternate=formatted and row_index % 2 == 0,
                )
        if formatted:
            _apply_xlsx_layout(worksheet, table, plan.xlsx_style)
        workbook.close()
        workbook = None
        cancellation.raise_if_cancelled()
        os.replace(temporary, target)
    except Exception:
        if workbook is not None:
            with suppress(Exception):
                workbook.close()
        temporary.unlink(missing_ok=True)
        raise


def _xlsx_formats(workbook: Any, style: XlsxStyle) -> dict[str, Any]:
    common = {
        "font_name": style.font_name,
        "font_size": style.font_size,
        "border": 1,
        "border_color": style.border_color,
    }
    return {
        "header": workbook.add_format(
            {
                **common,
                "bold": True,
                "bg_color": style.header_fill,
                "font_color": style.header_text,
                "align": "center",
                "valign": "vcenter",
            }
        ),
        "body": workbook.add_format(common),
        "alternate": workbook.add_format({**common, "bg_color": style.alternating_fill}),
        "datetime": workbook.add_format({**common, "num_format": style.datetime_format}),
        "datetime_alternate": workbook.add_format(
            {
                **common,
                "bg_color": style.alternating_fill,
                "num_format": style.datetime_format,
            }
        ),
        "numeric": workbook.add_format({**common, "num_format": style.numeric_format}),
        "numeric_alternate": workbook.add_format(
            {
                **common,
                "bg_color": style.alternating_fill,
                "num_format": style.numeric_format,
            }
        ),
    }


def _write_xlsx_cell(
    worksheet: Any,
    row: int,
    column: int,
    value: CellValue,
    formats: dict[str, Any],
    *,
    alternate: bool,
) -> None:
    body = formats.get("alternate" if alternate else "body")
    if value is None:
        if body is not None:
            worksheet.write_blank(row, column, None, body)
        return
    if isinstance(value, datetime):
        local_value = value.replace(tzinfo=None) if value.tzinfo is not None else value
        cell_format = formats.get("datetime_alternate" if alternate else "datetime")
        worksheet.write_datetime(row, column, local_value, cell_format)
        return
    if isinstance(value, date):
        cell_format = formats.get("datetime_alternate" if alternate else "datetime")
        worksheet.write_datetime(row, column, value, cell_format)
        return
    if isinstance(value, time | timedelta):
        worksheet.write(row, column, str(value), body)
        return
    if isinstance(value, Decimal):
        value = float(value)
    if isinstance(value, str):
        worksheet.write_string(row, column, value, body)
        return
    if isinstance(value, int | float) and not isinstance(value, bool):
        cell_format = formats.get("numeric_alternate" if alternate else "numeric")
        worksheet.write_number(row, column, value, cell_format)
        return
    worksheet.write(row, column, value, body)


def _apply_xlsx_layout(worksheet: Any, table: TabularData, style: XlsxStyle) -> None:
    last_row = table.row_count
    last_column = max(table.column_count - 1, 0)
    if style.autofilter and table.column_count:
        worksheet.autofilter(0, 0, last_row, last_column)
    if style.freeze_header:
        worksheet.freeze_panes(1, 0)
    for index, name in enumerate(table.columns):
        width = min(max(float(len(name) + 2), style.column_width), 100.0)
        worksheet.set_column(index, index, width)


def _ensure_available(target: Path, allow_overwrite: bool) -> None:
    if target.exists() and not allow_overwrite:
        raise AppError(
            f"'{target.name}' already exists. Choose another name or explicitly allow overwrite."
        )


def _temporary_path(target: Path) -> Path:
    descriptor, path = tempfile.mkstemp(
        prefix=f".{target.stem}-", suffix=target.suffix, dir=target.parent
    )
    os.close(descriptor)
    return Path(path)
