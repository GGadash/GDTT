"""Headless output-field defaults based only on canonical null counts.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from dataclasses import dataclass

from data_transform_tool.domain.table import DataTable


@dataclass(frozen=True)
class ColumnMissingness:
    column: str
    missing_count: int
    row_count: int

    @property
    def missing_fraction(self) -> float:
        return self.missing_count / self.row_count if self.row_count else 0.0


@dataclass(frozen=True)
class ExportFieldSuggestion:
    selected_columns: tuple[str, ...]
    deselected_empty_columns: tuple[str, ...]
    missingness: tuple[ColumnMissingness, ...]


def suggest_export_fields(table: DataTable) -> ExportFieldSuggestion:
    missingness = tuple(
        ColumnMissingness(
            column,
            sum(value is None for value in table.column_values(column)),
            table.row_count,
        )
        for column in table.columns
    )
    empty = tuple(
        item.column
        for item in missingness
        if item.row_count > 0 and item.missing_count == item.row_count
    )
    empty_set = set(empty)
    selected = tuple(column for column in table.columns if column not in empty_set)
    return ExportFieldSuggestion(selected, empty, missingness)
