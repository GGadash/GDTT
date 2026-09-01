"""Safe expression-tree calculated fields without unrestricted evaluation.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, DivisionByZero
from enum import StrEnum

from data_transform_tool.domain.table import CellValue, DataTable
from data_transform_tool.transformation.base import (
    Diagnostic,
    InvalidValuePolicy,
    OperationResult,
    TransformationError,
    TransformationOperation,
)
from data_transform_tool.transformation.numeric import to_decimal


class ArithmeticOperator(StrEnum):
    ADD = "add"
    SUBTRACT = "subtract"
    MULTIPLY = "multiply"
    DIVIDE = "divide"


class NumericExpression(ABC):
    """A validated expression node; nesting represents parentheses."""

    @abstractmethod
    def evaluate(self, record: Mapping[str, CellValue]) -> Decimal:
        """Evaluate one row or raise a numeric error."""


@dataclass(frozen=True)
class ColumnValue(NumericExpression):
    name: str

    def evaluate(self, record: Mapping[str, CellValue]) -> Decimal:
        if self.name not in record:
            raise ValueError(f"Column '{self.name}' does not exist.")
        return to_decimal(record[self.name])


@dataclass(frozen=True)
class ConstantValue(NumericExpression):
    value: Decimal | int | float | str

    def evaluate(self, record: Mapping[str, CellValue]) -> Decimal:
        del record
        return to_decimal(self.value)


@dataclass(frozen=True)
class BinaryExpression(NumericExpression):
    left: NumericExpression
    operator: ArithmeticOperator
    right: NumericExpression

    def evaluate(self, record: Mapping[str, CellValue]) -> Decimal:
        left = self.left.evaluate(record)
        right = self.right.evaluate(record)
        if self.operator is ArithmeticOperator.ADD:
            return left + right
        if self.operator is ArithmeticOperator.SUBTRACT:
            return left - right
        if self.operator is ArithmeticOperator.MULTIPLY:
            return left * right
        if right == 0:
            raise DivisionByZero("Calculated-field division by zero.")
        return left / right


@dataclass(frozen=True)
class AddCalculatedField(TransformationOperation):
    output: str
    expression: NumericExpression
    position: int | None = None
    invalid_policy: InvalidValuePolicy = InvalidValuePolicy.NULL

    @property
    def operation_id(self) -> str:
        return "add_calculated_field"

    @classmethod
    def linear(
        cls,
        *,
        source: str,
        output: str,
        multiplier: Decimal | int | float | str,
        intercept: Decimal | int | float | str = 0,
        position: int | None = None,
        invalid_policy: InvalidValuePolicy = InvalidValuePolicy.NULL,
    ) -> AddCalculatedField:
        expression = BinaryExpression(
            BinaryExpression(
                ConstantValue(multiplier),
                ArithmeticOperator.MULTIPLY,
                ColumnValue(source),
            ),
            ArithmeticOperator.ADD,
            ConstantValue(intercept),
        )
        return cls(output, expression, position, invalid_policy)

    def apply(self, table: DataTable) -> OperationResult:
        values: list[CellValue] = []
        invalid_count = 0
        for row_number, record in enumerate(table.records(), start=1):
            try:
                values.append(self.expression.evaluate(record))
            except (ArithmeticError, ValueError) as error:
                invalid_count += 1
                if self.invalid_policy is InvalidValuePolicy.STOP:
                    raise TransformationError(
                        f"Calculated field '{self.output}' failed at row {row_number}.",
                        detail=str(error),
                    ) from error
                values.append(None)

        diagnostics = (
            (
                Diagnostic(
                    code="calculation_failures",
                    message=(
                        f"{invalid_count} row(s) could not be calculated and were written "
                        "as canonical nulls."
                    ),
                    count=invalid_count,
                    columns=(self.output,),
                ),
            )
            if invalid_count
            else ()
        )
        return OperationResult(
            table.add_column(self.output, tuple(values), position=self.position),
            diagnostics,
        )
