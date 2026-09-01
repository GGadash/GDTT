"""Missing-data validation, row filtering, and true-null adapter coverage."""

from __future__ import annotations

import pytest

from data_transform_tool.domain.table import DataTable
from data_transform_tool.transformation.base import TransformationError
from data_transform_tool.transformation.nulls import NormalizeConfirmedNulls
from data_transform_tool.validation import (
    InvalidNumericPolicy,
    MissingDataConfiguration,
    RemoveNullMode,
    RemoveNullRule,
    analyze_invalid_numeric,
    preview_remove_null_rows,
    remove_null_rows,
    resolve_invalid_numeric,
    serialize_delimited_row,
    suggest_export_fields,
    xlsx_cell_value,
)


def test_confirmed_blank_na_sentinel_and_custom_markers_become_canonical_nulls() -> None:
    table = DataTable(
        ("PM",),
        (("",), ("N/A",), (-999,), ("MISSING",), (12.5,)),
    )
    config = MissingDataConfiguration(("PM",), confirmed_null_markers=("", "N/A", -999, "MISSING"))

    normalized = (
        NormalizeConfirmedNulls(config.confirmed_null_markers, columns=config.measurement_columns)
        .apply(table)
        .table
    )

    assert normalized.column_values("PM") == (None, None, None, None, 12.5)
    assert analyze_invalid_numeric(normalized, ("PM",)).invalid_count == 0
    assert config.canonical_null_only


def test_invalid_numeric_report_suggests_null_and_supports_all_policies() -> None:
    table = DataTable(
        ("PM",),
        ((1,), ("2.5",), ("bad",), ("",), (None,), (True,), (float("inf"),)),
    )

    report = analyze_invalid_numeric(table, ("PM",))

    assert report.invalid_count == 4
    assert report.affected_rows == (3, 4, 6, 7)
    assert report.suggested_policy is InvalidNumericPolicy.NULL_AND_CONTINUE
    assert resolve_invalid_numeric(
        table, ("PM",), InvalidNumericPolicy.NULL_AND_CONTINUE
    ).table.column_values("PM") == (1, "2.5", None, None, None, None, None)
    assert resolve_invalid_numeric(table, ("PM",), InvalidNumericPolicy.INSPECT).table is table
    with pytest.raises(TransformationError, match="row 3"):
        resolve_invalid_numeric(table, ("PM",), InvalidNumericPolicy.STOP)


def test_preserve_source_policy_moves_only_invalid_raw_values() -> None:
    table = DataTable(("PM", "Station"), (("bad", "A"), (1, "A")))

    result = resolve_invalid_numeric(table, ("PM",), InvalidNumericPolicy.PRESERVE_SOURCE)

    assert result.table.columns == ("PM", "Station", "PM_source")
    assert result.table.rows == ((None, "A", "bad"), (1, "A", None))


def test_remove_null_rules_preview_without_treating_empty_text_as_null() -> None:
    table = DataTable(
        ("PM", "NO2", "Required"),
        (
            (None, None, "ok"),
            ("", None, "ok"),
            (1, None, None),
            (1, 2, "ok"),
        ),
    )
    all_measurements = RemoveNullRule(RemoveNullMode.ALL_MEASUREMENTS_MISSING, ("PM", "NO2"))
    any_required = RemoveNullRule(RemoveNullMode.ANY_REQUIRED_MISSING, ("Required",))
    threshold = RemoveNullRule(
        RemoveNullMode.BELOW_PRESENT_THRESHOLD,
        ("PM", "NO2", "Required"),
        minimum_present=2,
    )

    assert preview_remove_null_rows(table, all_measurements).matching_row_numbers == (1,)
    assert preview_remove_null_rows(table, any_required).matching_row_numbers == (3,)
    assert preview_remove_null_rows(table, threshold).matching_row_numbers == (1, 3)
    result = remove_null_rows(table, all_measurements)
    assert result.preview.remove_count == 1
    assert result.preview.remaining_rows == 3
    assert result.table.rows[0] == ("", None, "ok")


def test_true_null_serialization_distinguishes_none_from_empty_string() -> None:
    assert serialize_delimited_row(("value1", None, "value3")) == "value1,,value3"
    assert serialize_delimited_row(("value1", "", "value3")) == 'value1,"",value3'
    assert serialize_delimited_row(("a", None, "b"), delimiter="\t") == "a\t\tb"
    assert xlsx_cell_value(None) is None
    assert xlsx_cell_value("") == ""


def test_entirely_null_output_fields_are_deselected_by_default() -> None:
    table = DataTable(
        ("PM", "Empty", "BlankText"),
        ((1, None, ""), (2, None, "")),
    )

    suggestion = suggest_export_fields(table)

    assert suggestion.selected_columns == ("PM", "BlankText")
    assert suggestion.deselected_empty_columns == ("Empty",)
    assert suggestion.missingness[1].missing_fraction == 1.0
