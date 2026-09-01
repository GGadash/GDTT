from PySide6.QtWidgets import QComboBox

from data_transform_tool.settings.models import AppSettings
from data_transform_tool.ui.main_window import MainWindow


def test_home_shell_contains_product_controls(qtbot) -> None:  # type: ignore[no-untyped-def]
    window = MainWindow(settings=AppSettings())
    qtbot.addWidget(window)

    assert window.windowTitle() == "GDTT"
    selector = window.findChild(QComboBox)
    assert selector is not None
    assert [selector.itemText(index) for index in range(selector.count())] == [
        "Dark",
        "Light",
        "Auto",
        "System",
    ]


def test_averaging_card_opens_working_inspection_route(qtbot) -> None:  # type: ignore[no-untyped-def]
    window = MainWindow(settings=AppSettings())
    qtbot.addWidget(window)

    window.home_view.averaging_requested.emit()

    assert window.stack.currentWidget() is window.averaging_inspection_view
    assert window.averaging_inspection_view.configure_button.text() == "Configure averaging  →"
