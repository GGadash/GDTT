"""Phase 7 averaging draft, recipe, and bounded-preview tests."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path

from data_transform_tool.aggregation import (
    AggregationApproach,
    AggregationStatistic,
    PeriodSpec,
)
from data_transform_tool.app.averaging_configuration import (
    AveragingStageDraft,
    build_averaging_recipe,
    create_averaging_draft,
    validate_averaging_draft,
)
from data_transform_tool.app.averaging_preview import build_averaging_preview
from data_transform_tool.app.template_application import apply_averaging_template
from data_transform_tool.io.cancellation import CancellationToken
from data_transform_tool.io.inspector import FileInspector
from data_transform_tool.io.options import InspectionOptions
from data_transform_tool.transformation.recipe import OutputMissingPolicy

FIXTURE = Path(__file__).parents[1] / "fixtures" / "monitoring_gap.csv"


def _inspection():  # type: ignore[no-untyped-def]
    return FileInspector.default().inspect(
        FIXTURE,
        InspectionOptions(),
        cancellation=CancellationToken(),
    )


def _confirmed_draft():  # type: ignore[no-untyped-def]
    draft = create_averaging_draft(_inspection())
    fields = tuple(
        replace(field, statistic_confirmed=True) if field.include else field
        for field in draft.fields
    )
    return replace(
        draft,
        fields=fields,
        timestamp_confirmed=True,
        source_timezone_confirmed=True,
        reporting_timezone_confirmed=True,
        interval_confirmed=True,
        missing_marker_decisions_confirmed=True,
    )


def test_detected_choices_are_advisory_and_require_confirmation() -> None:
    draft = create_averaging_draft(_inspection())

    assert draft.timestamp_column == "DateTime_UTC"
    assert draft.reporting_timezone == "UTC"
    assert draft.interval_seconds == 3600
    assert {field.source_name for field in draft.selected_fields} == {
        "PM2.5",
        "Temperature",
    }
    assert all(
        field.statistic is AggregationStatistic.ARITHMETIC_MEAN for field in draft.selected_fields
    )
    validation = validate_averaging_draft(draft)
    assert not validation.ready
    assert "Confirm the timestamp field." in validation.errors
    assert "Confirm the aggregation rule for every selected field." in validation.errors


def test_ready_draft_builds_typed_average_recipe_and_preview() -> None:
    draft = _confirmed_draft()

    validation = validate_averaging_draft(draft)
    recipe = build_averaging_recipe(draft)
    preview = build_averaging_preview(_inspection(), draft)

    assert validation.ready
    assert recipe.mode == "average"
    assert recipe.aggregation is not None
    assert recipe.aggregation.to_runtime().input_interval == timedelta(hours=1)
    assert preview.error is None
    assert preview.final_table.headers[:2] == ("Period_Start", "Period_End")
    assert len(preview.final_table.rows) == len(_inspection().previews[0].rows)
    assert len(preview.stages) == 1


def test_exact_schema_average_template_round_trips_to_reviewable_draft() -> None:
    confirmed = _confirmed_draft()
    recipe = build_averaging_recipe(confirmed)
    unconfirmed = replace(
        confirmed,
        timestamp_confirmed=False,
        source_timezone_confirmed=False,
        reporting_timezone_confirmed=False,
        interval_confirmed=False,
        missing_marker_decisions_confirmed=False,
    )

    applied = apply_averaging_template(unconfirmed, recipe)

    assert applied.timestamp_confirmed
    assert applied.source_timezone_confirmed
    assert applied.reporting_timezone_confirmed
    assert build_averaging_recipe(applied) == recipe


def test_incremental_chain_and_null_representation_remain_explicit() -> None:
    draft = replace(
        _confirmed_draft(),
        approach=AggregationApproach.INCREMENTAL,
        stages=(
            AveragingStageDraft(PeriodSpec.clock(timedelta(hours=1)), label="1 hour"),
            AveragingStageDraft(
                PeriodSpec.clock(timedelta(hours=8)),
                threshold=0.75,
                label="8 hours",
            ),
        ),
        output_missing_policy=OutputMissingPolicy.MINUS_999,
    )

    preview = build_averaging_preview(_inspection(), draft)

    assert validate_averaging_draft(draft).ready
    assert preview.error is None
    assert [stage.label for stage in preview.stages] == ["1 hour", "8 hours"]
    assert any(-999 in row for row in preview.final_table.rows)


def test_source_timezone_and_reporting_timezone_remain_distinct() -> None:
    draft = replace(
        _confirmed_draft(),
        source_timezone="UTC",
        reporting_timezone="Asia/Colombo",
        interval_seconds=1800,
        stages=(AveragingStageDraft(PeriodSpec.day(), label="Colombo day"),),
    )

    preview = build_averaging_preview(_inspection(), draft)

    assert preview.error is None
    start = preview.final_table.rows[0][0]
    assert isinstance(start, datetime)
    assert getattr(start.tzinfo, "key", None) == "Asia/Colombo"
    assert (start.hour, start.minute) == (0, 0)
