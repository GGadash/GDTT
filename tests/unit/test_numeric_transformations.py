"""Arithmetic, concentration conversion, and safe calculated-field tests."""

from __future__ import annotations

from decimal import Decimal

import pytest

from data_transform_tool.domain.table import DataTable
from data_transform_tool.transformation.base import InvalidValuePolicy, TransformationError
from data_transform_tool.transformation.calculated import (
    AddCalculatedField,
    ArithmeticOperator,
    BinaryExpression,
    ColumnValue,
    ConstantValue,
)
from data_transform_tool.transformation.numeric import (
    ConcentrationConversion,
    ConvertConcentration,
    RoundNumeric,
)


def test_rounding_is_arithmetic_not_string_truncation() -> None:
    table = DataTable(("Value",), (("25.679",), ("-1.235",), (None,)))

    result = RoundNumeric("Value", 2).apply(table).table

    assert result.column_values("Value") == (Decimal("25.68"), Decimal("-1.24"), None)


def test_ppm_ppb_conversion_can_replace_or_create_a_field() -> None:
    table = DataTable(("CO_ppm",), (("0.025",), (Decimal("1.2"),)))

    created = (
        ConvertConcentration("CO_ppm", ConcentrationConversion.PPM_TO_PPB, output="CO_ppb")
        .apply(table)
        .table
    )
    restored = (
        ConvertConcentration("CO_ppb", ConcentrationConversion.PPB_TO_PPM).apply(created).table
    )

    assert created.column_values("CO_ppb") == (Decimal("25.000"), Decimal("1200.0"))
    assert restored.column_values("CO_ppb") == (Decimal("0.025000"), Decimal("1.2000"))
    assert (
        ConvertConcentration("CO_ppm", ConcentrationConversion.PPM_TO_PPB).suggested_output_name
        == "CO_ppb"
    )


def test_expression_tree_supports_parenthesized_arithmetic_without_eval() -> None:
    table = DataTable(("X", "Y"), ((2, 10), (4, 20)))
    expression = BinaryExpression(
        BinaryExpression(ColumnValue("X"), ArithmeticOperator.ADD, ConstantValue(3)),
        ArithmeticOperator.MULTIPLY,
        BinaryExpression(ColumnValue("Y"), ArithmeticOperator.DIVIDE, ConstantValue(2)),
    )

    result = AddCalculatedField("Calculated", expression).apply(table).table

    assert result.column_values("Calculated") == (Decimal("25"), Decimal("70"))


def test_linear_formula_and_invalid_numeric_policies_are_explicit() -> None:
    table = DataTable(("Raw",), (("2",), ("ERROR",), (None,)))

    nullable = AddCalculatedField.linear(
        source="Raw", output="Scaled", multiplier=2, intercept=1
    ).apply(table)
    preserved = RoundNumeric("Raw", 0, invalid_policy=InvalidValuePolicy.PRESERVE).apply(table)

    assert nullable.table.column_values("Scaled") == (Decimal("5"), None, None)
    assert nullable.diagnostics[0].count == 2
    assert preserved.table.column_values("Raw") == (Decimal("2"), "ERROR", None)
    assert preserved.diagnostics[0].count == 1

    with pytest.raises(TransformationError, match="Invalid numeric value"):
        RoundNumeric("Raw", 1, invalid_policy=InvalidValuePolicy.STOP).apply(table)


def test_division_by_zero_becomes_counted_null_by_default() -> None:
    table = DataTable(("Value",), ((1,), (0,)))
    expression = BinaryExpression(
        ConstantValue(10), ArithmeticOperator.DIVIDE, ColumnValue("Value")
    )

    result = AddCalculatedField("Ratio", expression).apply(table)

    assert result.table.column_values("Ratio") == (Decimal("10"), None)
    assert result.diagnostics[0].count == 1
