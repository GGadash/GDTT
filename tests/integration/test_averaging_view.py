"""GUI integration coverage for the Phase 7 averaging workspace."""

from __future__ import annotations

from pathlib import Path

from data_transform_tool.aggregation import AggregationApproach
from data_transform_tool.io.cancellation import CancellationToken
from data_transform_tool.io.inspector import FileInspector
from data_transform_tool.io.options import InspectionOptions
from data_transform_tool.transformation.recipe import OutputMissingPolicy
from data_transform_tool.ui.views.averaging_view import AveragingConfigurationView

FIXTURE = Path(__file__).parents[1] / "fixtures" / "monitoring_gap.csv"


def _inspection():  # type: ignore[no-untyped-def]
    return FileInspector.default().inspect(
        FIXTURE,
        InspectionOptions(),
        cancellation=CancellationToken(),
    )


def test_averaging_view_exposes_explicit_choices_preview_and_history(qtbot) -> None:  # type: ignore[no-untyped-def]
    view = AveragingConfigurationView()
    qtbot.addWidget(view)
    view.set_inspection(_inspection())
    view.show()

    assert view.field_model.rowCount() == 4
    assert view.draft is not None
    assert len(view.draft.selected_fields) == 2
    assert view.threshold_spin.value() == 75
    assert view.approach_combo.currentData() == AggregationApproach.DIRECT.value
    assert view.final_preview_model.rowCount() == 0
    assert [
        view.missing_policy_combo.itemText(index)
        for index in range(view.missing_policy_combo.count())
    ] == [
        "True Null / blank (recommended)",
        "N/A",
        "-999",
        "Custom sentinel",
    ]
    assert "Configured season" in [
        view.period_combo.itemText(index) for index in range(view.period_combo.count())
    ]

    view.timestamp_confirm_check.setChecked(True)
    view.timezone_confirm_check.setChecked(True)
    view.reporting_timezone_confirm_check.setChecked(True)
    view.interval_confirm_check.setChecked(True)
    view.missing_markers_reviewed_check.setChecked(True)
    view._confirm_selected_fields()

    assert view.draft is not None
    assert view.draft.timestamp_confirmed
    assert all(field.statistic_confirmed for field in view.draft.selected_fields)
    assert view.final_preview_model.rowCount() > 0
    assert view.completeness_model.rowCount() > 0

    view.approach_combo.setCurrentIndex(
        view.approach_combo.findData(AggregationApproach.INCREMENTAL)
    )
    assert view.draft is not None
    assert view.draft.approach is AggregationApproach.INCREMENTAL
    assert len(view.draft.stages) == 2
    assert view.two_of_three_check.isEnabled()
    view.undo_button.click()
    assert view.draft is not None
    assert view.draft.approach is AggregationApproach.DIRECT


def test_custom_missing_result_is_optional_but_requires_a_value(qtbot) -> None:  # type: ignore[no-untyped-def]
    view = AveragingConfigurationView()
    qtbot.addWidget(view)
    view.set_inspection(_inspection())
    view.show()

    view.missing_policy_combo.setCurrentIndex(
        view.missing_policy_combo.findData(OutputMissingPolicy.CUSTOM)
    )

    assert view.custom_sentinel_edit.isVisible()
    assert view.custom_sentinel_label.isVisible()
    assert "custom missing-value sentinel" in view.validation_label.text()
