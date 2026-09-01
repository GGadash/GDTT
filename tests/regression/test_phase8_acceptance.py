"""Phase 8 acceptance: complete-file export is verified and auditable."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from data_transform_tool.app.export_workflow import execute_export, prepare_export
from data_transform_tool.app.reformat_configuration import (
    build_transformation_recipe,
    create_reformat_draft,
)
from data_transform_tool.export import ExportPlan, VerificationStatus
from data_transform_tool.io.cancellation import CancellationToken
from data_transform_tool.io.inspector import FileInspector
from data_transform_tool.io.options import InspectionOptions
from data_transform_tool.transformation.recipe import OutputFormat

FIXTURE = Path(__file__).parents[1] / "fixtures" / "monitoring_gap.csv"


def test_phase8_csv_xlsx_reports_and_recipe_are_complete_and_verified(tmp_path) -> None:
    inspection = FileInspector.default().inspect(
        FIXTURE,
        InspectionOptions(),
        cancellation=CancellationToken(),
    )
    draft = replace(
        create_reformat_draft(inspection),
        timestamp_confirmed=True,
        interval_confirmed=True,
        confirmed_missing_markers=("N/A",),
    )
    recipe = build_transformation_recipe(draft)
    prepared = prepare_export(inspection, draft, recipe, CancellationToken())
    result = execute_export(
        prepared,
        ExportPlan(
            tmp_path,
            prepared.suggested_base_name,
            (
                OutputFormat.CSV,
                OutputFormat.XLSX_PLAIN,
                OutputFormat.XLSX_FORMATTED,
            ),
        ),
        CancellationToken(),
    )

    assert prepared.input_table.row_count == 10
    assert prepared.evidence.generated_gap_rows == 0
    assert len(result.verifications) == 3
    assert all(check.status is VerificationStatus.PASSED for check in result.verifications)
    assert {artifact.kind for artifact in result.artifacts} >= {
        "csv",
        "xlsx_plain",
        "xlsx_formatted",
        "transformation_info",
        "recipe",
        "summary",
    }
    assert "Input rows: 10" in result.report_text
    assert "Generated gap rows: 0" in result.report_text
