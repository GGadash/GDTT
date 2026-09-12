"""Shared formatting, selection and appearance regressions for 0.10.0."""

from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QComboBox, QVBoxLayout, QWidget

from data_transform_tool.app.reformat_configuration import create_reformat_draft
from data_transform_tool.datetime.custom_formats import FieldFormat, decode
from data_transform_tool.io.inspector import FileInspector
from data_transform_tool.io.models import SemanticType
from data_transform_tool.ui.dialogs.column_wizard import SequentialColumnWizard
from data_transform_tool.ui.theme import theme_colors
from data_transform_tool.ui.views.configuration_view import ReformatConfigurationView
from data_transform_tool.ui.widgets.field_controls import ProfileCombo, bulk_buttons, fill_zones


def test_type_options_custom_input_and_separators(qtbot):
    combo = ProfileCombo(input_profile=True)
    qtbot.addWidget(combo)
    combo.load(None, "decimal")
    assert all(
        combo.findData(f"custom:{kind}") >= 0
        for kind in ("number", "datetime", "date", "time", "text", "boolean")
    )
    combo.decimal = ","
    assert decode(combo.profile()).decimal == ","
    output = ProfileCombo()
    qtbot.addWidget(output)
    output.load(None, "date")
    assert output.findText("0.00") == -1
    assert output.findData("custom:date") >= 0
    output.setEditText("dd/MM/yyyy")
    assert decode(output.profile()).pattern == "dd/MM/yyyy"


def test_editor_numeric_rounding_choice_and_resize(qtbot):
    view = ReformatConfigurationView()
    qtbot.addWidget(view)
    view.set_inspection(
        FileInspector.default().inspect(
            Path(__file__).parents[1] / "fixtures" / "monitoring_gap.csv"
        )
    )
    view.resize(1280, 720)
    view.show()
    source_index = view.mapping_model.index(2, 0)
    view._select_mapping_index(view.mapping_proxy.mapFromSource(source_index))
    assert view.draft.column(view._selected_source).is_numeric
    view.output_profile_combo.setCurrentIndex(view.output_profile_combo.findText("0.00"))
    column = view.draft.column(view._selected_source)
    assert decode(column.output_profile) == FieldFormat("number", "0.00")
    view.preserve_precision.setChecked(True)
    view.output_decimal.setCurrentText(",")
    column = view.draft.column(view._selected_source)
    assert decode(column.output_profile) == FieldFormat("number", "0.00", ",", True)
    view.output_type_combo.setCurrentIndex(view.output_type_combo.findData(SemanticType.DATE))
    assert view.transform_combo.count() == 1
    assert view.output_profile_combo.findText("0.00") == -1
    before = view.mapping_splitter.sizes()
    view.mapping_splitter.setSizes([140, 400])
    assert view.mapping_splitter.sizes() != before
    for table in (view.mapping_table, view.frozen_mapping_table):
        assert table.horizontalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAlwaysOn
        assert table.verticalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAlwaysOn


def test_bulk_scope_does_not_confirm_other_decisions(qtbot):
    widget = QWidget()
    qtbot.addWidget(widget)
    layout = QVBoxLayout(widget)
    options = (QCheckBox("CSV"), QCheckBox("Excel"))
    confirmation = QCheckBox("Confirmed timestamp")
    for check in (*options, confirmation):
        layout.addWidget(check)
    calls = []
    buttons = bulk_buttons(options, lambda: calls.append(True))
    layout.addLayout(buttons)
    buttons.itemAt(0).widget().click()
    assert all(check.isChecked() for check in options)
    assert not confirmation.isChecked()
    buttons.itemAt(1).widget().click()
    assert not any(check.isChecked() for check in options)
    assert len(calls) == 2


def test_wizard_type_change_clears_numeric_only_preferences(qtbot):
    inspection = FileInspector.default().inspect(
        Path(__file__).parents[1] / "fixtures" / "monitoring_gap.csv"
    )
    wizard = SequentialColumnWizard(inspection, create_reformat_draft(inspection))
    qtbot.addWidget(wizard)
    wizard._index = 2
    wizard._load_current()
    wizard.output_profile_combo.setCurrentIndex(wizard.output_profile_combo.findText("0.00"))
    wizard.output_decimal.setCurrentText(",")
    wizard.preserve_precision.setChecked(True)
    wizard.output_type_combo.setCurrentIndex(wizard.output_type_combo.findData(SemanticType.DATE))
    wizard._type_changed()
    assert wizard._save_current()
    assert wizard.result_draft.columns[2].output_profile is None
    assert not wizard.preserve_precision.isChecked()


def test_zone_priority_and_custom_offsets(qtbot):
    combo = QComboBox()
    qtbot.addWidget(combo)
    fill_zones(combo)
    assert [combo.itemText(i) for i in range(3)] == ["UTC", "Asia/Colombo", "Custom…"]
    assert combo.findText("+05:30") >= 0
    assert combo.findText("Asia/Kathmandu") >= 0
    combo.setEditText("+05:45")
    fill_zones(combo)
    assert combo.currentText() == "+05:45"


@pytest.mark.parametrize("dark", [False, True])
@pytest.mark.parametrize("color", ["teal", "blue", "graphite", "violet", "spectrum"])
def test_palette_text_contrast(dark, color):
    colors = theme_colors(dark, color)

    def luminance(hexcolor):
        channels = [int(hexcolor[i : i + 2], 16) / 255 for i in (1, 3, 5)]
        linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
        return sum(c * weight for c, weight in zip(linear, (0.2126, 0.7152, 0.0722), strict=True))

    for foreground, background in (
        (colors.text, colors.surface),
        (colors.muted, colors.canvas),
        (colors.primary_text, colors.primary),
    ):
        low, high = sorted((luminance(foreground), luminance(background)))
        assert (high + 0.05) / (low + 0.05) >= 4.5
