"""Arithmetic rounding and explicit ppm/ppb conversion operations.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from enum import StrEnum

from data_transform_tool.domain.table import CellValue, DataTable
from data_transform_tool.transformation.base import (
    Diagnostic,
    InvalidValuePolicy,
    OperationResult,
    TransformationError,
    TransformationOperation,
    write_column,
)


class ConcentrationConversion(StrEnum):
    PPM_TO_PPB = "ppm_to_ppb"
    PPB_TO_PPM = "ppb_to_ppm"

    @property
    def factor(self) -> Decimal:
        return Decimal("1000") if self is self.PPM_TO_PPB else Decimal("0.001")


@dataclass(frozen=True)
class RoundNumeric(TransformationOperation):
    source: str
    decimals: int
    output: str | None = None
    invalid_policy: InvalidValuePolicy = InvalidValuePolicy.NULL

    def __post_init__(self) -> None:
        if not -12 <= self.decimals <= 12:
            raise ValueError("Rounding decimals must be between -12 and 12.")

    @property
    def operation_id(self) -> str:
        return "round_numeric"

    def apply(self, table: DataTable) -> OperationResult:
        quantum = Decimal(1).scaleb(-self.decimals)
        return _transform_numeric(
            table,
            source=self.source,
            output=self.output,
            invalid_policy=self.invalid_policy,
            transform=lambda value: value.quantize(quantum, rounding=ROUND_HALF_UP),
            operation_id=self.operation_id,
        )


@dataclass(frozen=True)
class ConvertConcentration(TransformationOperation):
    source: str
    conversion: ConcentrationConversion
    output: str | None = None
    invalid_policy: InvalidValuePolicy = InvalidValuePolicy.NULL

    @property
    def operation_id(self) -> str:
        return self.conversion.value

    @property
    def suggested_output_name(self) -> str:
        if self.output:
            return self.output
        old, new = (
            ("ppm", "ppb")
            if self.conversion is ConcentrationConversion.PPM_TO_PPB
            else ("ppb", "ppm")
        )
        if old in self.source.casefold():
            start = self.source.casefold().index(old)
            return self.source[:start] + new + self.source[start + len(old) :]
        return f"{self.source}_{new}"

    def apply(self, table: DataTable) -> OperationResult:
        return _transform_numeric(
            table,
            source=self.source,
            output=self.output,
            invalid_policy=self.invalid_policy,
            transform=lambda value: value * self.conversion.factor,
            operation_id=self.operation_id,
        )


def to_decimal(value: CellValue) -> Decimal:
    """Convert a supported finite numeric value without accepting booleans."""
    if isinstance(value, bool) or value is None:
        raise ValueError("Value is not numeric.")
    if isinstance(value, Decimal):
        result = value
    elif isinstance(value, int):
        result = Decimal(value)
    elif isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Value is not finite.")
        result = Decimal(str(value))
    elif isinstance(value, str):
        try:
            result = Decimal(value.strip())
        except InvalidOperation as error:
            raise ValueError("Value is not numeric.") from error
    else:
        raise ValueError("Value is not numeric.")
    if not result.is_finite():
        raise ValueError("Value is not finite.")
    return result


def _transform_numeric(
    table: DataTable,
    *,
    source: str,
    output: str | None,
    invalid_policy: InvalidValuePolicy,
    transform: Callable[[Decimal], Decimal],
    operation_id: str,
) -> OperationResult:
    transformed: list[CellValue] = []
    invalid_count = 0
    for row_number, value in enumerate(table.column_values(source), start=1):
        if value is None:
            transformed.append(None)
            continue
        try:
            transformed.append(transform(to_decimal(value)))
        except (ArithmeticError, ValueError) as error:
            invalid_count += 1
            if invalid_policy is InvalidValuePolicy.STOP:
                raise TransformationError(
                    f"Invalid numeric value in '{source}' at row {row_number}.",
                    detail=str(error),
                ) from error
            transformed.append(value if invalid_policy is InvalidValuePolicy.PRESERVE else None)

    diagnostics = (
        (
            Diagnostic(
                code="invalid_numeric_values",
                message=(
                    f"{invalid_count} invalid numeric value(s) followed the "
                    f"'{invalid_policy.value}' policy during {operation_id}."
                ),
                count=invalid_count,
                columns=(source,),
            ),
        )
        if invalid_count
        else ()
    )
    return OperationResult(
        write_column(
            table,
            source_name=source,
            output_name=output,
            values=tuple(transformed),
        ),
        diagnostics,
    )
