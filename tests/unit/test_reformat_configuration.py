"""Phase 5 immutable draft, recipe, history, and proposed-preview coverage."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from data_transform_tool.app.reformat_configuration import (
    ConfigurationSession,
    GapBehaviorChoice,
    build_transformation_recipe,
    create_reformat_draft,
    validate_reformat_draft,
)
from data_transform_tool.app.reformat_preview import build_proposed_preview
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


def test_detected_configuration_defaults_are_safe_and_option_rich() -> None:
    draft = create_reformat_draft(_inspection())

    assert draft.gap_fill_enabled
    assert draft.timestamp_column == "DateTime_UTC"
    assert draft.interval_seconds == 3600
    assert not draft.timestamp_confirmed
    assert not draft.interval_confirmed
    assert draft.output_missing_policy is OutputMissingPolicy.TRUE_NULL
    assert not draft.column("Unused").export
    assert draft.column("Source").gap_behavior is GapBehaviorChoice.CARRY_STABLE
    validation = validate_reformat_draft(draft)
    assert "Confirm the primary timestamp" in " ".join(validation.errors)
    assert "Confirm the expected interval" in " ".join(validation.errors)


def test_confirmed_draft_builds_typed_gap_and_global_missing_recipe() -> None:
    draft = replace(
        create_reformat_draft(_inspection()),
        timestamp_confirmed=True,
        interval_confirmed=True,
        confirmed_missing_markers=("N/A", "-999"),
        output_missing_policy=OutputMissingPolicy.NA,
    )

    recipe = build_transformation_recipe(draft)

    assert recipe.gap_policy is not None
    assert recipe.gap_policy.interval_seconds == 3600
    assert recipe.gap_policy.timestamp_column == "DateTime_UTC"
    assert recipe.output.missing_policy is OutputMissingPolicy.NA
    assert recipe.missing_data is not None
    assert recipe.missing_data.confirmed_null_markers == ("N/A", "-999")


def test_gap_insertion_can_be_disabled_without_timestamp_confirmation() -> None:
    draft = replace(create_reformat_draft(_inspection()), gap_fill_enabled=False)

    assert validate_reformat_draft(draft).ready
    assert build_transformation_recipe(draft).gap_policy is None


def test_configuration_history_supports_undo_redo_and_reset() -> None:
    initial = create_reformat_draft(_inspection())
    session = ConfigurationSession(initial)
    changed = replace(initial, gap_fill_enabled=False)

    assert session.apply(changed)
    assert session.can_undo
    assert session.undo()
    assert session.current == initial
    assert session.redo()
    assert session.current == changed
    assert session.reset()
    assert session.current == initial


def test_proposed_preview_uses_confirmed_markers_and_output_representation() -> None:
    inspection = _inspection()
    draft = replace(
        create_reformat_draft(inspection),
        gap_fill_enabled=False,
        confirmed_missing_markers=("N/A",),
        output_missing_policy=OutputMissingPolicy.NA,
    )

    preview = build_proposed_preview(inspection, draft)

    pm_index = preview.headers.index("PM2.5")
    assert preview.error is None
    assert preview.rows[1][pm_index] == "N/A"
    assert "Unused" not in preview.headers
