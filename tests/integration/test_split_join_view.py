from pathlib import Path

from data_transform_tool.io.inspector import FileInspector
from data_transform_tool.settings.models import AppSettings
from data_transform_tool.split_join.models import Action
from data_transform_tool.ui.main_window import MainWindow


def test_split_join_route_prepares_exports_and_invalidates(qtbot, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    path = tmp_path / "source.csv"
    path.write_text("Time,PM\n2025-12-31T23:00:00Z,1\n2026-01-01T00:00:00Z,2\n")
    window = MainWindow(settings=AppSettings())
    qtbot.addWidget(window)
    assert window.stack.currentWidget() is window.home_view
    window.home_view.split_join_requested.emit()
    view = window.split_join_view
    assert window.stack.currentWidget() is view
    view.add_paths([path])
    view.editors[0].apply_inspection(FileInspector.default().inspect(path))
    view.editors[0].timestamp.setCurrentText("Time")
    view._prepare()
    qtbot.waitUntil(lambda: not view.busy, timeout=15000)
    assert view.prepared is not None, view.status.text()
    assert len(view.prepared.outputs) == 2
    assert view.export_button.isEnabled()
    view.destination.setText(str(tmp_path / "out"))
    view._export()
    qtbot.waitUntil(lambda: not view.busy, timeout=15000)
    assert "Export complete" in view.status.text()
    assert len(list((tmp_path / "out").glob("*/SPLIT_JOIN_REPORT.json"))) == 1
    view.operation.setCurrentIndex(view.operation.findData(Action.SPLIT_FIELDS))
    assert view.prepared is None
    assert not view.export_button.isEnabled()
    window.close()


def test_hidden_calendar_settings_do_not_block_field_operations(qtbot) -> None:  # type: ignore[no-untyped-def]
    window = MainWindow(settings=AppSettings())
    qtbot.addWidget(window)
    view = window.split_join_view
    view.start_month.setValue(2)
    view.start_day.setValue(31)
    view.operation.setCurrentIndex(view.operation.findData(Action.SPLIT_FIELDS))
    spec = view.configuration()
    assert spec.action is Action.SPLIT_FIELDS
    assert spec.period.year_start_month == 1
    assert spec.period.year_start_day == 1
    window.close()
