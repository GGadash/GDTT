"""GUI integration coverage for the Phase 5 configuration workspace."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt

from data_transform_tool.io.cancellation import CancellationToken
from data_transform_tool.io.inspector import FileInspector
from data_transform_tool.io.options import InspectionOptions
from data_transform_tool.transformation.recipe import OutputMissingPolicy
from data_transform_tool.ui.views.configuration_view import ReformatConfigurationView

FIXTURE = Path(__file__).parents[1] / "fixtures" / "monitoring_gap.csv"


def _inspection():  # type: ignore[no-untyped-def]
    return FileInspector.default().inspect(
        FIXTURE,
        InspectionOptions(),
        cancellation=CancellationToken(),
    )


def test_configuration_view_exposes_defaults_choices_preview_and_history(qtbot) -> None:  # type: ignore[no-untyped-def]
    view = ReformatConfigurationView()
    qtbot.addWidget(view)
    view.set_inspection(_inspection())
    view.show()

    assert view.mapping_model.rowCount() == 5
    assert view.preview_model.rowCount() > 0
    assert view.gap_fill_check.isChecked()
    assert view.missing_policy_combo.currentData() == OutputMissingPolicy.TRUE_NULL.value
    assert [
        view.missing_policy_combo.itemText(index)
        for index in range(view.missing_policy_combo.count())
    ] == [
        "True Null / blank (recommended)",
        "N/A",
        "-999",
        "Custom sentinel",
    ]
    assert view.custom_sentinel_edit.isHidden()
    assert view.custom_sentinel_label.isHidden()
    assert view.custom_interval_spin.isHidden()
    assert view.custom_interval_label.isHidden()
    assert (
        view.mapping_model.data(view.mapping_model.index(4, 0), Qt.ItemDataRole.CheckStateRole)
        == Qt.CheckState.Unchecked
    )

    view.gap_fill_check.setChecked(False)
    assert view.draft is not None and not view.draft.gap_fill_enabled
    assert view.undo_button.isEnabled()
    view.undo_button.click()
    assert view.draft is not None and view.draft.gap_fill_enabled


def test_custom_missing_option_requires_and_reveals_a_sentinel(qtbot) -> None:  # type: ignore[no-untyped-def]
    view = ReformatConfigurationView()
    qtbot.addWidget(view)
    view.set_inspection(_inspection())
    view.show()

    view.missing_policy_combo.setCurrentIndex(
        view.missing_policy_combo.findData(OutputMissingPolicy.CUSTOM)
    )
    view.editor_tabs.setCurrentIndex(1)

    assert view.custom_sentinel_edit.isVisible()
    assert view.custom_sentinel_label.isVisible()
    assert view.draft is not None
    assert view.draft.output_missing_policy is OutputMissingPolicy.CUSTOM
    assert "custom missing-value sentinel" in view.validation_label.text()
