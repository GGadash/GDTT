"""Desktop application composition and process-level error handling.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

import logging
import sys
from collections.abc import Sequence
from types import TracebackType
from typing import cast

from PySide6.QtWidgets import QApplication, QMessageBox

from data_transform_tool import __version__
from data_transform_tool.app.metadata import PRODUCT_NAME
from data_transform_tool.reporting.logging_setup import configure_logging
from data_transform_tool.resources import application_icon
from data_transform_tool.settings.repository import SettingsRepository
from data_transform_tool.ui.main_window import MainWindow
from data_transform_tool.ui.theme import apply_theme

LOGGER = logging.getLogger(__name__)


def build_application(arguments: Sequence[str] | None = None) -> tuple[QApplication, MainWindow]:
    """Compose the Qt application without starting the event loop.

    Keeping construction separate from ``run`` makes launch behavior testable.
    """
    existing_application = QApplication.instance()
    app = (
        cast(QApplication, existing_application)
        if existing_application is not None
        else QApplication(list(arguments or sys.argv))
    )
    app.setApplicationName(PRODUCT_NAME)
    app.setApplicationDisplayName(PRODUCT_NAME)
    app.setApplicationVersion(__version__)
    app.setOrganizationName("Gadash (Akila DJ)")
    app.setWindowIcon(application_icon())
    app.setStyle("Fusion")

    settings_repository = SettingsRepository.default()
    settings = settings_repository.load()
    configure_logging()
    apply_theme(app, settings.theme, settings.color_theme, settings.font_size)

    window = MainWindow(settings=settings)
    window.theme_changed.connect(lambda theme: _persist_theme(settings_repository, theme))
    window.appearance_changed.connect(
        lambda color, size: settings_repository.save(
            settings_repository.load().model_copy(update={"color_theme": color, "font_size": size})
        )
    )
    return app, window


def _persist_theme(repository: SettingsRepository, theme: str) -> None:
    settings = repository.load().model_copy(update={"theme": theme})
    repository.save(settings)


def _show_unhandled_error(
    error_type: type[BaseException],
    error: BaseException,
    traceback: TracebackType | None,
) -> None:
    LOGGER.critical("Unhandled application error", exc_info=(error_type, error, traceback))
    QMessageBox.critical(
        None,
        PRODUCT_NAME,
        "An unexpected error occurred. The technical details were written to the local log.",
    )


def run(arguments: Sequence[str] | None = None) -> int:
    """Launch the main window and run the Qt event loop."""
    sys.excepthook = _show_unhandled_error
    app, window = build_application(arguments)
    window.show()
    return app.exec()
