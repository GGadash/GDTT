"""GUI integration coverage for the Phase 2 source-inspection flow."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QLabel, QTextBrowser

from data_transform_tool.app.batch_input import BatchInspection
from data_transform_tool.settings.models import AppSettings
from data_transform_tool.ui.dialogs.about_dialog import AboutDialog
from data_transform_tool.ui.main_window import MainWindow
from data_transform_tool.ui.views.inspection_view import FileInspectionView

FIXTURE = Path(__file__).parents[1] / "fixtures" / "monitoring_gap.csv"


def test_inspection_view_profiles_csv_in_background(qtbot) -> None:  # type: ignore[no-untyped-def]
    view = FileInspectionView()
    qtbot.addWidget(view)
    view.show()

    view.set_source_path(FIXTURE)
    view.start_inspection()
    qtbot.waitUntil(lambda: view._thread is None, timeout=5_000)

    assert view.results.isVisible()
    assert "10 rows" in view.status_label.text()
    assert view.column_table.model().rowCount() == 5
    assert view.preview_tabs.count() == 3
    assert view.configure_button.isVisible()

    with qtbot.waitSignal(view.configuration_requested) as signal:
        view.configure_button.click()
    assert signal.args[0].row_count == 10


def test_inspection_view_accepts_a_compatible_multi_file_batch(qtbot, tmp_path) -> None:  # type: ignore[no-untyped-def]
    first = tmp_path / "station-a.csv"
    second = tmp_path / "station-b.csv"
    content = FIXTURE.read_text(encoding="utf-8")
    first.write_text(content, encoding="utf-8")
    second.write_text(content.replace("Station-A", "Station-B"), encoding="utf-8")
    view = FileInspectionView()
    qtbot.addWidget(view)
    view.show()

    view.set_source_paths([first, second])
    view.start_inspection()
    qtbot.waitUntil(lambda: view._thread is None, timeout=8_000)

    assert view.configure_button.isVisible()
    assert "2 compatible files" in view.status_label.text()
    with qtbot.waitSignal(view.configuration_requested) as signal:
        view.configure_button.click()
    assert isinstance(signal.args[0], BatchInspection)
    assert len(signal.args[0].inspections) == 2


def test_credit_is_only_in_about_content(qtbot) -> None:  # type: ignore[no-untyped-def]
    window = MainWindow(settings=AppSettings())
    qtbot.addWidget(window)
    visible_shell_text = "\n".join(label.text() for label in window.findChildren(QLabel))

    assert "Created by" not in visible_shell_text
    assert "Akila DJ" not in visible_shell_text

    dialog = AboutDialog(window)
    qtbot.addWidget(dialog)
    about_text = "\n".join(label.text() for label in dialog.findChildren(QLabel))
    about_text += "\n" + "\n".join(
        browser.toPlainText() for browser in dialog.findChildren(QTextBrowser)
    )
    assert "Akila DJ" in about_text
    assert "OpenAI Codex" in about_text
    assert "PyInstaller" in about_text
    assert "NSIS" in about_text
