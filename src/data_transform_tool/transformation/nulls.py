"""Confirmed input-marker normalization to the canonical internal null value.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from data_transform_tool.domain.table import CellValue, DataTable
from data_transform_tool.transformation.base import (
    Diagnostic,
    OperationResult,
    TransformationOperation,
)


@dataclass(frozen=True)
class NormalizeConfirmedNulls(TransformationOperation):
    """Normalize only markers the user explicitly confirmed; never infer here."""

    markers: tuple[CellValue, ...]
    columns: tuple[str, ...] | None = None
    case_sensitive: bool = False
    strip_text: bool = True

    @property
    def operation_id(self) -> str:
        return "normalize_confirmed_nulls"

    def apply(self, table: DataTable) -> OperationResult:
        selected = self.columns or table.columns
        selected_indexes = {table.column_index(name) for name in selected}
        count = 0
        rows: list[tuple[CellValue, ...]] = []
        for row in table.rows:
            output = list(row)
            for index in selected_indexes:
                if output[index] is not None and self._matches(output[index]):
                    output[index] = None
                    count += 1
            rows.append(tuple(output))
        diagnostics = (
            (
                Diagnostic(
                    code="null_markers_normalized",
                    message="Confirmed source markers were normalized to canonical nulls.",
                    count=count,
                    columns=tuple(selected),
                ),
            )
            if count
            else ()
        )
        return OperationResult(DataTable(table.columns, tuple(rows)), diagnostics)

    def _matches(self, value: CellValue) -> bool:
        return any(self._equal(value, marker) for marker in self.markers)

    def _equal(self, value: CellValue, marker: CellValue) -> bool:
        if isinstance(value, float) and math.isnan(value):
            return isinstance(marker, float) and math.isnan(marker)
        if isinstance(value, str) and isinstance(marker, str):
            left = value.strip() if self.strip_text else value
            right = marker.strip() if self.strip_text else marker
            if not self.case_sensitive:
                left = left.casefold()
                right = right.casefold()
            return left == right
        return value == marker
