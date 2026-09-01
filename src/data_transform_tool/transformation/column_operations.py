"""Immutable rename, order, selection, empty, duplicate, and index operations.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from dataclasses import dataclass

from data_transform_tool.domain.table import DataTable
from data_transform_tool.transformation.base import OperationResult, TransformationOperation


@dataclass(frozen=True)
class RenameColumn(TransformationOperation):
    source: str
    output: str

    @property
    def operation_id(self) -> str:
        return "rename_column"

    def apply(self, table: DataTable) -> OperationResult:
        index = table.column_index(self.source)
        if not self.output.strip():
            raise ValueError("Output column name must not be blank.")
        if self.output != self.source and self.output in table.columns:
            raise ValueError(f"Column '{self.output}' already exists.")
        columns = (*table.columns[:index], self.output, *table.columns[index + 1 :])
        return OperationResult(DataTable(columns, table.rows))


@dataclass(frozen=True)
class ReorderColumns(TransformationOperation):
    order: tuple[str, ...]
    append_unlisted: bool = True

    @property
    def operation_id(self) -> str:
        return "reorder_columns"

    def apply(self, table: DataTable) -> OperationResult:
        for name in self.order:
            table.column_index(name)
        if len(set(self.order)) != len(self.order):
            raise ValueError("Reordered columns must be unique.")
        unlisted = tuple(name for name in table.columns if name not in self.order)
        if unlisted and not self.append_unlisted:
            raise ValueError(f"Reorder omitted columns: {', '.join(unlisted)}.")
        return OperationResult(table.select_columns(self.order + unlisted))


@dataclass(frozen=True)
class SelectColumns(TransformationOperation):
    columns: tuple[str, ...]

    @property
    def operation_id(self) -> str:
        return "select_columns"

    def apply(self, table: DataTable) -> OperationResult:
        return OperationResult(table.select_columns(self.columns))


@dataclass(frozen=True)
class AddEmptyColumn(TransformationOperation):
    name: str
    position: int | None = None

    @property
    def operation_id(self) -> str:
        return "add_empty_column"

    def apply(self, table: DataTable) -> OperationResult:
        values = (None,) * table.row_count
        return OperationResult(table.add_column(self.name, values, position=self.position))


@dataclass(frozen=True)
class DuplicateColumn(TransformationOperation):
    source: str
    output: str
    position: int | None = None

    @property
    def operation_id(self) -> str:
        return "duplicate_column"

    def apply(self, table: DataTable) -> OperationResult:
        return OperationResult(
            table.add_column(
                self.output,
                table.column_values(self.source),
                position=self.position,
            )
        )


@dataclass(frozen=True)
class AddIndexColumn(TransformationOperation):
    name: str = "Index"
    start: int = 1
    position: int = 0

    @property
    def operation_id(self) -> str:
        return "add_index"

    def apply(self, table: DataTable) -> OperationResult:
        values = tuple(range(self.start, self.start + table.row_count))
        return OperationResult(table.add_column(self.name, values, position=self.position))


@dataclass(frozen=True)
class DropEntirelyEmptyColumns(TransformationOperation):
    """Deselect fields containing only canonical nulls while retaining named exceptions."""

    keep: tuple[str, ...] = ()

    @property
    def operation_id(self) -> str:
        return "drop_entirely_empty_columns"

    def apply(self, table: DataTable) -> OperationResult:
        selected = tuple(
            name
            for name in table.columns
            if name in self.keep or any(value is not None for value in table.column_values(name))
        )
        return OperationResult(table.select_columns(selected))
