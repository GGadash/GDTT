"""Immutable table, column-plan, null, and recipe coverage."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from data_transform_tool.domain.table import DataTable
from data_transform_tool.transformation.base import TransformationPlan
from data_transform_tool.transformation.column_operations import (
    AddEmptyColumn,
    AddIndexColumn,
    DropEntirelyEmptyColumns,
    DuplicateColumn,
    RenameColumn,
    ReorderColumns,
    SelectColumns,
)
from data_transform_tool.transformation.nulls import NormalizeConfirmedNulls
from data_transform_tool.transformation.recipe import (
    ColumnRecipe,
    GapFieldPolicyRecipe,
    GapRecipe,
    MissingDataRecipe,
    OutputFormat,
    OutputMissingPolicy,
    OutputRecipe,
    RemoveNullRecipe,
    SourceFileType,
    SourceRecipe,
    TransformationRecipe,
    TransformationSpec,
)


def test_column_plan_is_immutable_audited_and_ordered() -> None:
    source = DataTable.from_records(
        (
            {"Station": "A", "PM": 10, "Unused": None},
            {"Station": "B", "PM": 20, "Unused": None},
        )
    )
    plan = TransformationPlan(
        (
            RenameColumn("PM", "PM2.5"),
            DuplicateColumn("Station", "Station Copy"),
            AddEmptyColumn("Comment"),
            AddIndexColumn(),
            ReorderColumns(("Index", "Station", "PM2.5")),
            SelectColumns(("Index", "Station", "PM2.5", "Station Copy", "Comment")),
        )
    )

    result = plan.execute(source)

    assert source.columns == ("Station", "PM", "Unused")
    assert result.table.columns == (
        "Index",
        "Station",
        "PM2.5",
        "Station Copy",
        "Comment",
    )
    assert result.table.rows == ((1, "A", 10, "A", None), (2, "B", 20, "B", None))
    assert tuple(entry.operation_id for entry in result.audit) == (
        "rename_column",
        "duplicate_column",
        "add_empty_column",
        "add_index",
        "reorder_columns",
        "select_columns",
    )


def test_entirely_empty_columns_are_deselected_but_exceptions_can_remain() -> None:
    table = DataTable(("Value", "Empty", "Required"), ((1, None, None), (2, None, None)))

    result = DropEntirelyEmptyColumns(keep=("Required",)).apply(table).table

    assert result.columns == ("Value", "Required")


def test_confirmed_null_markers_are_normalized_only_when_selected() -> None:
    table = DataTable(
        ("Measurement", "Code"),
        (("N/A", "N/A"), ("-999", "keep"), ("", "blank"), (12.5, "ok")),
    )

    result = NormalizeConfirmedNulls(markers=("N/A", "-999"), columns=("Measurement",)).apply(table)

    assert result.table.rows == (
        (None, "N/A"),
        (None, "keep"),
        ("", "blank"),
        (12.5, "ok"),
    )
    assert result.diagnostics[0].count == 2
    assert table.rows[0][0] == "N/A"


def test_table_rejects_duplicate_columns_and_inconsistent_rows() -> None:
    with pytest.raises(ValueError, match="unique"):
        DataTable(("A", "A"), ((1, 2),))
    with pytest.raises(ValueError, match="Every row"):
        DataTable(("A", "B"), ((1,),))
    with pytest.raises(ValueError, match="immutable scalar"):
        DataTable(("A",), (([1, 2],),))  # type: ignore[list-item]


def test_recipe_round_trip_matches_machine_readable_contract() -> None:
    recipe = TransformationRecipe(
        recipe_name="Hourly PM cleanup",
        source=SourceRecipe(
            file_type=SourceFileType.CSV,
            expected_columns=("Timestamp", "PM2.5"),
            missing_markers=("N/A", -999),
        ),
        columns=(
            ColumnRecipe(
                source_name="Timestamp",
                output_name="Timestamp_UTC",
                transformations=(
                    TransformationSpec(
                        kind="parse_datetime",
                        parameters={"profile_id": "iso_minute"},
                    ),
                ),
            ),
            ColumnRecipe(source_name="PM2.5", output_name="PM2.5"),
        ),
        missing_data=MissingDataRecipe(
            confirmed_null_markers=("N/A", -999),
            numeric_columns=("PM2.5",),
            remove_null_rule=RemoveNullRecipe(mode="all_measurements_missing", columns=("PM2.5",)),
        ),
        gap_policy=GapRecipe(
            timestamp_column="Timestamp_UTC",
            interval_seconds=3600,
            measurement_columns=("PM2.5",),
            field_policies=(GapFieldPolicyRecipe(column="Station", behavior="carry_stable"),),
        ),
        output=OutputRecipe(
            formats=(OutputFormat.CSV,),
            missing_policy=OutputMissingPolicy.TRUE_NULL,
        ),
    )

    restored = TransformationRecipe.from_json(recipe.to_json())

    assert restored == recipe
    assert restored.schema_version == 1
    assert restored.output.missing_policy is OutputMissingPolicy.TRUE_NULL
    assert restored.gap_policy is not None
    assert restored.gap_policy.interval_seconds == 3600


def test_recipe_rejects_inconsistent_or_unsafe_structure() -> None:
    with pytest.raises(ValidationError, match="worksheet"):
        SourceRecipe(file_type=SourceFileType.XLSX)
    with pytest.raises(ValidationError, match="custom missing policy"):
        OutputRecipe(
            formats=(OutputFormat.CSV,),
            missing_policy=OutputMissingPolicy.CUSTOM,
        )
    with pytest.raises(ValidationError, match="Extra inputs"):
        TransformationSpec.model_validate({"kind": "x", "python_code": "eval('bad')"})
    with pytest.raises(ValidationError, match="generated-flag columns must be different"):
        GapRecipe(
            timestamp_column="Timestamp",
            interval_seconds=3600,
            measurement_columns=("PM",),
            index_column="Index",
            generated_flag_column="Index",
        )
