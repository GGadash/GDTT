"""Common contracts for immutable transformation execution.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

from data_transform_tool.domain.errors import AppError, Severity
from data_transform_tool.domain.table import CellValue, DataTable


class InvalidValuePolicy(StrEnum):
    """Explicit action for source values an operation cannot interpret."""

    NULL = "null"
    STOP = "stop"
    PRESERVE = "preserve"


class TransformationError(AppError):
    """A blocking, user-readable transformation configuration or data error."""


@dataclass(frozen=True)
class Diagnostic:
    """Counted, non-dataset diagnostic suitable for previews and reports."""

    code: str
    message: str
    count: int = 1
    columns: tuple[str, ...] = ()
    severity: Severity = Severity.WARNING


@dataclass(frozen=True)
class OperationResult:
    table: DataTable
    diagnostics: tuple[Diagnostic, ...] = ()


class TransformationOperation(ABC):
    """One deterministic, UI-independent transformation step."""

    @property
    @abstractmethod
    def operation_id(self) -> str:
        """Return the stable operation identifier used in audit entries."""

    @abstractmethod
    def apply(self, table: DataTable) -> OperationResult:
        """Return a new table and diagnostics without mutating the input."""


@dataclass(frozen=True)
class AuditEntry:
    operation_id: str
    input_columns: tuple[str, ...]
    output_columns: tuple[str, ...]
    row_count: int
    diagnostic_count: int


@dataclass(frozen=True)
class PlanResult:
    table: DataTable
    diagnostics: tuple[Diagnostic, ...]
    audit: tuple[AuditEntry, ...]


@dataclass(frozen=True)
class TransformationPlan:
    """Versioned sequence of operations derived from confirmed user intent."""

    operations: tuple[TransformationOperation, ...]
    schema_version: int = 1

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError(f"Unsupported transformation plan version: {self.schema_version}.")

    def execute(
        self,
        table: DataTable,
        *,
        cancellation_check: Callable[[], None] | None = None,
    ) -> PlanResult:
        current = table
        diagnostics: list[Diagnostic] = []
        audit: list[AuditEntry] = []
        for operation in self.operations:
            if cancellation_check is not None:
                cancellation_check()
            input_columns = current.columns
            result = operation.apply(current)
            current = result.table
            diagnostics.extend(result.diagnostics)
            audit.append(
                AuditEntry(
                    operation_id=operation.operation_id,
                    input_columns=input_columns,
                    output_columns=current.columns,
                    row_count=current.row_count,
                    diagnostic_count=sum(item.count for item in result.diagnostics),
                )
            )
        if cancellation_check is not None:
            cancellation_check()
        return PlanResult(current, tuple(diagnostics), tuple(audit))


def write_column(
    table: DataTable,
    *,
    source_name: str,
    output_name: str | None,
    values: tuple[CellValue, ...],
    position: int | None = None,
) -> DataTable:
    """Replace a source column or append a separately named derived column."""
    resolved_name = output_name or source_name
    if resolved_name == source_name:
        return table.replace_column(source_name, values)
    return table.add_column(resolved_name, values, position=position)
