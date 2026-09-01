"""Invalid-numeric inspection and explicit resolution policies.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from data_transform_tool.domain.table import CellValue, DataTable
from data_transform_tool.transformation.base import TransformationError
from data_transform_tool.transformation.numeric import to_decimal


class InvalidNumericPolicy(StrEnum):
    """Phase 4 choices for values that a numeric field cannot interpret."""

    NULL_AND_CONTINUE = "null_and_continue"
    INSPECT = "inspect"
    STOP = "stop"
    PRESERVE_SOURCE = "preserve_source"


@dataclass(frozen=True)
class InvalidNumericCell:
    row_number: int
    column: str
    source_value: CellValue


@dataclass(frozen=True)
class InvalidNumericReport:
    columns: tuple[str, ...]
    cells: tuple[InvalidNumericCell, ...]
    suggested_policy: InvalidNumericPolicy = InvalidNumericPolicy.NULL_AND_CONTINUE

    @property
    def invalid_count(self) -> int:
        return len(self.cells)

    @property
    def affected_rows(self) -> tuple[int, ...]:
        return tuple(sorted({cell.row_number for cell in self.cells}))


@dataclass(frozen=True)
class InvalidNumericResolution:
    table: DataTable
    report: InvalidNumericReport
    policy: InvalidNumericPolicy


def analyze_invalid_numeric(table: DataTable, columns: tuple[str, ...]) -> InvalidNumericReport:
    if not columns:
        raise ValueError("At least one numeric column must be selected.")
    if len(set(columns)) != len(columns):
        raise ValueError("Numeric analysis columns must be unique.")
    cells: list[InvalidNumericCell] = []
    for column in columns:
        for row_number, value in enumerate(table.column_values(column), start=1):
            if value is None:
                continue
            try:
                to_decimal(value)
            except ValueError:
                cells.append(InvalidNumericCell(row_number, column, value))
    return InvalidNumericReport(columns, tuple(cells))


def resolve_invalid_numeric(
    table: DataTable,
    columns: tuple[str, ...],
    policy: InvalidNumericPolicy,
    *,
    source_suffix: str = "_source",
) -> InvalidNumericResolution:
    report = analyze_invalid_numeric(table, columns)
    if not report.cells or policy is InvalidNumericPolicy.INSPECT:
        return InvalidNumericResolution(table, report, policy)
    if policy is InvalidNumericPolicy.STOP:
        first = report.cells[0]
        raise TransformationError(
            f"Invalid numeric value in '{first.column}' at row {first.row_number}."
        )
    if policy is InvalidNumericPolicy.PRESERVE_SOURCE and not source_suffix:
        raise ValueError("The preserved-source suffix must not be empty.")

    current = table
    invalid_by_column = {
        column: {cell.row_number for cell in report.cells if cell.column == column}
        for column in columns
    }
    for column in columns:
        affected = invalid_by_column[column]
        if not affected:
            continue
        original = current.column_values(column)
        if policy is InvalidNumericPolicy.PRESERVE_SOURCE:
            preserved = tuple(
                value if row_number in affected else None
                for row_number, value in enumerate(original, start=1)
            )
            current = current.add_column(f"{column}{source_suffix}", preserved)
        normalized = tuple(
            None if row_number in affected else value
            for row_number, value in enumerate(original, start=1)
        )
        current = current.replace_column(column, normalized)
    return InvalidNumericResolution(current, report, policy)
