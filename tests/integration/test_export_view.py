"""GUI integration coverage for Phase 8 review, options, export, and verification."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from data_transform_tool.app.reformat_configuration import (
    build_transformation_recipe,
    create_reformat_draft,
)
from data_transform_tool.io.cancellation import CancellationToken
from data_transform_tool.io.inspector import FileInspector
from data_transform_tool.io.options import InspectionOptions
from data_transform_tool.templates import TemplateRepository
from data_transform_tool.ui.views.export_view import ExportView

FIXTURE = Path(__file__).parents[1] / "fixtures" / "monitoring_gap.csv"


def test_export_view_prepares_full_review_and_verifies_outputs(qtbot, tmp_path) -> None:  # type: ignore[no-untyped-def]
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
    view = ExportView()
    qtbot.addWidget(view)
    view.show()

    view.set_context(inspection, draft, recipe)
    qtbot.waitUntil(lambda: view._prepared is not None, timeout=5_000)
    qtbot.waitUntil(lambda: view._thread is None, timeout=5_000)

    assert view._prepared is not None
    assert view.input_model.rowCount() > 0
    assert view.output_model.rowCount() > 0
    assert view.name_edit.text().endswith("_RF")
    assert view.csv_check.isChecked()
    assert not view.style_card.isVisible()
    assert view.export_button.isEnabled()

    view.destination_edit.setText(str(tmp_path))
    view.formatted_check.setChecked(True)
    view.export_button.click()
    qtbot.waitUntil(lambda: view._thread is None, timeout=8_000)

    assert "Export completed and verified" in view.result_heading.text()
    assert "Passed" in view.result_text.toPlainText()
    assert any(tmp_path.glob("*_RF.csv"))
    assert any(tmp_path.glob("*_RF_F.xlsx"))


def test_matching_template_exposes_apply_review_ignore_choice(qtbot, tmp_path) -> None:  # type: ignore[no-untyped-def]
    inspection = FileInspector.default().inspect(
        FIXTURE,
        InspectionOptions(),
        cancellation=CancellationToken(),
    )
    draft = replace(
        create_reformat_draft(inspection),
        timestamp_confirmed=True,
        interval_confirmed=True,
    )
    recipe = build_transformation_recipe(draft)
    view = ExportView()
    view._template_repository = TemplateRepository(tmp_path / "templates")
    view._template_repository.save("Exact station schema", recipe)
    qtbot.addWidget(view)
    view.show()
    view.set_context(inspection, draft, recipe)
    qtbot.waitUntil(lambda: view._prepared is not None, timeout=5_000)
    qtbot.waitUntil(lambda: view._thread is None, timeout=5_000)

    assert "Exact schema" in view.template_combo.currentText()
    with qtbot.waitSignal(view.template_apply_requested):
        view._apply_selected_template()
    view._ignore_selected_template()
    assert view.template_combo.currentData() is None
