"""Phase 7 acceptance: explicit decisions compose a typed staged preview."""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from pathlib import Path

from data_transform_tool.aggregation import AggregationApproach, PeriodSpec
from data_transform_tool.app.averaging_configuration import (
    AveragingStageDraft,
    build_averaging_recipe,
    create_averaging_draft,
    validate_averaging_draft,
)
from data_transform_tool.app.averaging_preview import build_averaging_preview
from data_transform_tool.io.cancellation import CancellationToken
from data_transform_tool.io.inspector import FileInspector
from data_transform_tool.io.options import InspectionOptions
from data_transform_tool.transformation.recipe import OutputMissingPolicy

FIXTURE = Path(__file__).parents[1] / "fixtures" / "monitoring_gap.csv"


def test_phase7_explicit_incremental_plan_retains_preview_evidence() -> None:
    inspection = FileInspector.default().inspect(
        FIXTURE,
        InspectionOptions(),
        cancellation=CancellationToken(),
    )
    draft = create_averaging_draft(inspection)
    draft = replace(
        draft,
        fields=tuple(
            replace(field, statistic_confirmed=True) if field.include else field
            for field in draft.fields
        ),
        timestamp_confirmed=True,
        source_timezone_confirmed=True,
        reporting_timezone_confirmed=True,
        interval_confirmed=True,
        confirmed_missing_markers=draft.detected_missing_markers,
        missing_marker_decisions_confirmed=True,
        approach=AggregationApproach.INCREMENTAL,
        stages=(
            AveragingStageDraft(PeriodSpec.clock(timedelta(hours=1)), label="1 hour"),
            AveragingStageDraft(PeriodSpec.clock(timedelta(hours=8)), label="8 hours"),
        ),
        output_missing_policy=OutputMissingPolicy.NA,
    )

    recipe = build_averaging_recipe(draft)
    preview = build_averaging_preview(inspection, draft)

    assert validate_averaging_draft(draft).ready
    assert recipe.aggregation is not None
    assert recipe.aggregation.to_runtime().approach is AggregationApproach.INCREMENTAL
    assert preview.error is None
    assert [stage.label for stage in preview.stages] == ["1 hour", "8 hours"]
    assert len(preview.stages[0].completeness_rows) == 10
    assert preview.stages[0].rejected == 2
    assert any("N/A" in row for row in preview.final_table.rows)
