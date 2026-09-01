"""Immutable tabular values shared by headless transformation operations.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

type CellValue = str | int | float | bool | Decimal | date | datetime | time | timedelta | None
type DataRow = tuple[CellValue, ...]

if TYPE_CHECKING:
    from data_transform_tool.domain.batches import DataBatch

_CELL_TYPES = (str, int, float, bool, Decimal, date, datetime, time, timedelta)


@dataclass(frozen=True)
class DataTable:
    """A small immutable table used by the semantic engine and preview tests.

    Production backends can compile the same operations to lazy/chunked execution later;
    this representation intentionally keeps Phase 3 independent of a specific dataframe.
    """

    columns: tuple[str, ...]
    rows: tuple[DataRow, ...]

    def __post_init__(self) -> None:
        if any(not name.strip() for name in self.columns):
            raise ValueError("Column names must not be blank.")
        if len(set(self.columns)) != len(self.columns):
            raise ValueError("Column names must be unique.")
        if any(
            value is not None and not isinstance(value, _CELL_TYPES)
            for row in self.rows
            for value in row
        ):
            raise ValueError("Table cells must be immutable scalar values.")
        invalid_widths = sorted({len(row) for row in self.rows if len(row) != len(self.columns)})
        if invalid_widths:
            raise ValueError(
                f"Every row must contain {len(self.columns)} values; found widths {invalid_widths}."
            )

    @classmethod
    def from_records(
        cls,
        records: Iterable[Mapping[str, CellValue]],
        *,
        columns: Sequence[str] | None = None,
    ) -> DataTable:
        """Create a table without mutating or retaining caller-owned mappings."""
        materialized = tuple(dict(record) for record in records)
        resolved_columns = tuple(columns or (tuple(materialized[0]) if materialized else ()))
        rows = tuple(
            tuple(record.get(column) for column in resolved_columns) for record in materialized
        )
        return cls(columns=resolved_columns, rows=rows)

    @property
    def row_count(self) -> int:
        return len(self.rows)

    @property
    def column_count(self) -> int:
        return len(self.columns)

    def iter_batches(self, batch_size: int = 10_000) -> Iterator[DataBatch]:
        """Replay ordered rows in bounded batches through the production-table contract."""
        if batch_size <= 0:
            raise ValueError("Batch size must be greater than zero.")
        from data_transform_tool.domain.batches import DataBatch

        for start in range(0, self.row_count, batch_size):
            yield DataBatch(start, self.rows[start : start + batch_size])

    def read_rows(self, start: int, count: int) -> tuple[DataRow, ...]:
        """Read one bounded positional slice."""
        if start < 0 or count < 0:
            raise ValueError("Row slice bounds must not be negative.")
        return self.rows[start : start + count]

    def column_index(self, name: str) -> int:
        try:
            return self.columns.index(name)
        except ValueError as error:
            raise ValueError(f"Column '{name}' does not exist.") from error

    def column_values(self, name: str) -> tuple[CellValue, ...]:
        index = self.column_index(name)
        return tuple(row[index] for row in self.rows)

    def records(self) -> tuple[dict[str, CellValue], ...]:
        return tuple(dict(zip(self.columns, row, strict=True)) for row in self.rows)

    def replace_column(self, name: str, values: Sequence[CellValue]) -> DataTable:
        if len(values) != self.row_count:
            raise ValueError("Replacement column length must equal the table row count.")
        index = self.column_index(name)
        rows = tuple(
            (*row[:index], values[row_index], *row[index + 1 :])
            for row_index, row in enumerate(self.rows)
        )
        return DataTable(self.columns, rows)

    def add_column(
        self,
        name: str,
        values: Sequence[CellValue],
        *,
        position: int | None = None,
    ) -> DataTable:
        if not name.strip():
            raise ValueError("Column names must not be blank.")
        if name in self.columns:
            raise ValueError(f"Column '{name}' already exists.")
        if len(values) != self.row_count:
            raise ValueError("New column length must equal the table row count.")
        insert_at = self.column_count if position is None else position
        if not 0 <= insert_at <= self.column_count:
            raise ValueError("Column position is outside the table bounds.")
        columns = (*self.columns[:insert_at], name, *self.columns[insert_at:])
        rows = tuple(
            (*row[:insert_at], values[row_index], *row[insert_at:])
            for row_index, row in enumerate(self.rows)
        )
        return DataTable(columns, rows)

    def select_columns(self, names: Sequence[str]) -> DataTable:
        selected = tuple(names)
        if len(set(selected)) != len(selected):
            raise ValueError("Selected columns must be unique.")
        indexes = tuple(self.column_index(name) for name in selected)
        return DataTable(
            selected, tuple(tuple(row[index] for index in indexes) for row in self.rows)
        )
