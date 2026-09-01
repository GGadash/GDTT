"""Canonical-null row-removal rules with previewable counts.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from data_transform_tool.domain.table import DataRow, DataTable


class RemoveNullMode(StrEnum):
    ALL_MEASUREMENTS_MISSING = "all_measurements_missing"
    ALL_SELECTED_MISSING = "all_selected_missing"
    ANY_REQUIRED_MISSING = "any_required_missing"
    SELECTED_SUBSET_MISSING = "selected_subset_missing"
    BELOW_PRESENT_THRESHOLD = "below_present_threshold"


@dataclass(frozen=True)
class RemoveNullRule:
    mode: RemoveNullMode
    columns: tuple[str, ...]
    minimum_present: int | None = None

    def __post_init__(self) -> None:
        if not self.columns:
            raise ValueError("A remove-null rule requires at least one column.")
        if len(set(self.columns)) != len(self.columns):
            raise ValueError("Remove-null rule columns must be unique.")
        if self.mode is RemoveNullMode.BELOW_PRESENT_THRESHOLD:
            if self.minimum_present is None:
                raise ValueError("A threshold rule requires minimum_present.")
            if not 0 <= self.minimum_present <= len(self.columns):
                raise ValueError("minimum_present must be within the selected column count.")
        elif self.minimum_present is not None:
            raise ValueError("minimum_present is only valid for threshold rules.")


@dataclass(frozen=True)
class RowRemovalPreview:
    matching_row_numbers: tuple[int, ...]
    input_rows: int

    @property
    def remove_count(self) -> int:
        return len(self.matching_row_numbers)

    @property
    def remaining_rows(self) -> int:
        return self.input_rows - self.remove_count


@dataclass(frozen=True)
class RowRemovalResult:
    table: DataTable
    preview: RowRemovalPreview


def preview_remove_null_rows(table: DataTable, rule: RemoveNullRule) -> RowRemovalPreview:
    indexes = tuple(table.column_index(column) for column in rule.columns)
    matching = tuple(
        row_number
        for row_number, row in enumerate(table.rows, start=1)
        if row_matches_null_rule(row, indexes, rule)
    )
    return RowRemovalPreview(matching, table.row_count)


def remove_null_rows(table: DataTable, rule: RemoveNullRule) -> RowRemovalResult:
    preview = preview_remove_null_rows(table, rule)
    removed = set(preview.matching_row_numbers)
    rows = tuple(
        row for row_number, row in enumerate(table.rows, start=1) if row_number not in removed
    )
    return RowRemovalResult(DataTable(table.columns, rows), preview)


def row_matches_null_rule(
    row: DataRow,
    indexes: tuple[int, ...],
    rule: RemoveNullRule,
) -> bool:
    """Return whether one canonical-null row matches an explicit removal rule."""
    missing_count = sum(row[index] is None for index in indexes)
    if rule.mode is RemoveNullMode.ANY_REQUIRED_MISSING:
        return missing_count > 0
    if rule.mode is RemoveNullMode.BELOW_PRESENT_THRESHOLD:
        if rule.minimum_present is None:
            raise AssertionError("Threshold rules must declare minimum_present.")
        return len(indexes) - missing_count < rule.minimum_present
    return missing_count == len(indexes)
