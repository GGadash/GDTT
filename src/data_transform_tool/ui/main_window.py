"""Primary desktop window and global navigation chrome.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from typing import cast

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from data_transform_tool import __version__
from data_transform_tool.app.batch_input import BatchInspection
from data_transform_tool.app.metadata import PRODUCT_NAME
from data_transform_tool.app.template_application import (
    apply_averaging_template,
    apply_reformat_template,
)
from data_transform_tool.io.models import FileInspection
from data_transform_tool.resources import application_icon
from data_transform_tool.settings.models import AppSettings, ThemePreference
from data_transform_tool.transformation.recipe import TransformationRecipe
from data_transform_tool.ui.dialogs.about_dialog import AboutDialog
from data_transform_tool.ui.theme import apply_theme
from data_transform_tool.ui.views.averaging_view import AveragingConfigurationView
from data_transform_tool.ui.views.configuration_view import ReformatConfigurationView
from data_transform_tool.ui.views.export_view import ExportView
from data_transform_tool.ui.views.home_view import HomeView
from data_transform_tool.ui.views.inspection_view import FileInspectionView
from data_transform_tool.ui.views.split_join_view import SplitJoinView


class MainWindow(QMainWindow):
    """Host global controls and the active workflow view."""

    theme_changed = Signal(str)

    def __init__(self, *, settings: AppSettings) -> None:
        super().__init__()
        self.setWindowTitle(PRODUCT_NAME)
        self.resize(settings.window_width, settings.window_height)
        self.setMinimumSize(900, 620)

        root = QWidget()
        root.setObjectName("AppRoot")
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root_layout.addWidget(self._create_header(settings.theme))

        self.stack = QStackedWidget()
        self.home_view = HomeView()
        self.inspection_view = FileInspectionView()
        self.averaging_inspection_view = FileInspectionView(workflow="average")
        self.configuration_view = ReformatConfigurationView()
        self.averaging_view = AveragingConfigurationView()
        self.export_view = ExportView()
        self.split_join_view = SplitJoinView()
        self.home_view.split_join_requested.connect(
            lambda: self.stack.setCurrentWidget(self.split_join_view)
        )
        self.split_join_view.back_requested.connect(
            lambda: self.stack.setCurrentWidget(self.home_view)
        )
        self.stack.addWidget(self.split_join_view)
        self._reformat_inspection: FileInspection | None = None
        self._averaging_inspection: FileInspection | None = None
        self._reformat_inspections: tuple[FileInspection, ...] = ()
        self._averaging_inspections: tuple[FileInspection, ...] = ()
        self.home_view.reformat_requested.connect(
            lambda: self.stack.setCurrentWidget(self.inspection_view)
        )
        self.home_view.averaging_requested.connect(
            lambda: self.stack.setCurrentWidget(self.averaging_inspection_view)
        )
        self.stack.addWidget(self.home_view)
        self.stack.setCurrentWidget(self.home_view)
        self.inspection_view.back_requested.connect(
            lambda: self.stack.setCurrentWidget(self.home_view)
        )
        self.inspection_view.configuration_requested.connect(self._open_configuration)
        self.stack.addWidget(self.inspection_view)
        self.averaging_inspection_view.back_requested.connect(
            lambda: self.stack.setCurrentWidget(self.home_view)
        )
        self.averaging_inspection_view.configuration_requested.connect(
            self._open_averaging_configuration
        )
        self.stack.addWidget(self.averaging_inspection_view)
        self.configuration_view.back_requested.connect(
            lambda: self.stack.setCurrentWidget(self.inspection_view)
        )
        self.stack.addWidget(self.configuration_view)
        self.configuration_view.configuration_ready.connect(self._open_reformat_export)
        self.averaging_view.back_requested.connect(
            lambda: self.stack.setCurrentWidget(self.averaging_inspection_view)
        )
        self.stack.addWidget(self.averaging_view)
        self.averaging_view.configuration_ready.connect(self._open_averaging_export)
        self.export_view.back_requested.connect(self._return_from_export)
        self.export_view.process_more_requested.connect(self._process_more_files)
        self.export_view.template_apply_requested.connect(self._apply_template)
        self.stack.addWidget(self.export_view)
        root_layout.addWidget(self.stack, 1)
        root_layout.addWidget(self._create_footer())
        self.setCentralWidget(root)

    def _create_header(self, current_theme: ThemePreference) -> QFrame:
        header = QFrame()
        header.setProperty("role", "header")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(30, 15, 30, 15)
        layout.setSpacing(12)

        mark = QLabel()
        mark.setProperty("role", "cardIcon")
        mark.setFixedSize(48, 48)
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mark.setAccessibleName(PRODUCT_NAME)
        mark.setPixmap(application_icon().pixmap(42, 42))
        layout.addWidget(mark)

        names = QVBoxLayout()
        names.setSpacing(1)
        product = QLabel(PRODUCT_NAME)
        product.setProperty("role", "sectionTitle")
        caption = QLabel("Environmental time-series workspace")
        caption.setProperty("role", "muted")
        names.addWidget(product)
        names.addWidget(caption)
        layout.addLayout(names)
        layout.addStretch()

        offline = QLabel("● Offline processing")
        offline.setProperty("role", "badge")
        layout.addWidget(offline)

        about_button = QPushButton("About")
        about_button.setProperty("role", "ghost")
        about_button.clicked.connect(self._show_about)
        layout.addWidget(about_button)

        theme_label = QLabel("Theme")
        theme_label.setProperty("role", "muted")
        layout.addWidget(theme_label)
        self.theme_selector = QComboBox()
        self.theme_selector.setAccessibleName("Application theme")
        self.theme_selector.addItem("Dark", "dark")
        self.theme_selector.addItem("Light", "light")
        self.theme_selector.addItem("Auto", "auto")
        self.theme_selector.addItem("System", "system")
        selected_index = self.theme_selector.findData(current_theme)
        self.theme_selector.setCurrentIndex(max(selected_index, 0))
        self.theme_selector.currentIndexChanged.connect(self._on_theme_selected)
        layout.addWidget(self.theme_selector)
        return header

    def _create_footer(self) -> QFrame:
        footer = QFrame()
        footer.setProperty("role", "footer")
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(30, 10, 30, 10)
        left = QLabel(f"Version {__version__} • Verified data workspace")
        left.setProperty("role", "muted")
        layout.addWidget(left)
        layout.addStretch()
        privacy = QLabel("Private by design • No dataset upload")
        privacy.setProperty("role", "muted")
        layout.addWidget(privacy)
        return footer

    def _show_about(self) -> None:
        AboutDialog(self).exec()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.split_join_view.busy:
            self.split_join_view.token.cancel()
            self.split_join_view.status.setText(
                "Cancelling the active operation. Close again after it stops."
            )
            event.ignore()
            return
        self.split_join_view._invalidate()
        super().closeEvent(event)

    def _on_theme_selected(self) -> None:
        selected = cast(ThemePreference, self.theme_selector.currentData())
        application = QApplication.instance()
        if application is not None:
            apply_theme(cast(QApplication, application), selected)
        self.theme_changed.emit(selected)

    def _show_phase_message(self, mode: str, target_phase: str) -> None:
        QMessageBox.information(
            self,
            mode,
            f"{mode} is represented in the Phase 1 shell. "
            f"Its working flow begins in {target_phase}.",
        )

    def _open_configuration(self, inspection: object) -> None:
        if isinstance(inspection, BatchInspection):
            resolved = inspection.reference
            self._reformat_inspections = inspection.inspections
        else:
            resolved = cast(FileInspection, inspection)
            self._reformat_inspections = (resolved,)
        self._reformat_inspection = resolved
        self.configuration_view.set_inspection(resolved)
        self.stack.setCurrentWidget(self.configuration_view)

    def _open_averaging_configuration(self, inspection: object) -> None:
        if isinstance(inspection, BatchInspection):
            resolved = inspection.reference
            self._averaging_inspections = inspection.inspections
        else:
            resolved = cast(FileInspection, inspection)
            self._averaging_inspections = (resolved,)
        self._averaging_inspection = resolved
        self.averaging_view.set_inspection(resolved)
        self.stack.setCurrentWidget(self.averaging_view)

    def _open_reformat_export(self, recipe: object) -> None:
        draft = self.configuration_view.draft
        if self._reformat_inspection is None or draft is None:
            return
        self.export_view.set_context(
            self._reformat_inspection,
            draft,
            cast(TransformationRecipe, recipe),
            self._reformat_inspections,
        )
        self.stack.setCurrentWidget(self.export_view)

    def _open_averaging_export(self, recipe: object) -> None:
        draft = self.averaging_view.draft
        if self._averaging_inspection is None or draft is None:
            return
        self.export_view.set_context(
            self._averaging_inspection,
            draft,
            cast(TransformationRecipe, recipe),
            self._averaging_inspections,
        )
        self.stack.setCurrentWidget(self.export_view)

    def _return_from_export(self, mode: str) -> None:
        self.stack.setCurrentWidget(
            self.averaging_view if mode == "average" else self.configuration_view
        )

    def _process_more_files(self, mode: str) -> None:
        view = self.averaging_inspection_view if mode == "average" else self.inspection_view
        view.set_source_paths([])
        self.stack.setCurrentWidget(view)

    def _apply_template(self, recipe_value: object, _style_value: object) -> None:
        recipe = cast(TransformationRecipe, recipe_value)
        try:
            if recipe.mode == "average":
                averaging_draft = self.averaging_view.draft
                if averaging_draft is None:
                    raise ValueError("Load an Averaging source before applying a template.")
                self.averaging_view.apply_template(
                    apply_averaging_template(averaging_draft, recipe)
                )
                self.stack.setCurrentWidget(self.averaging_view)
            else:
                reformat_draft = self.configuration_view.draft
                if reformat_draft is None:
                    raise ValueError("Load a Reformat source before applying a template.")
                self.configuration_view.apply_template(
                    apply_reformat_template(reformat_draft, recipe)
                )
                self.stack.setCurrentWidget(self.configuration_view)
        except ValueError as error:
            QMessageBox.warning(self, "Apply recipe template", str(error))
