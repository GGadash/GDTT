"""Phase 2 file selection, detection overrides, profiling, and previews.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Literal, cast

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableView,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from data_transform_tool.app.batch_input import BatchInspection
from data_transform_tool.domain.errors import AppError
from data_transform_tool.io.cancellation import CancellationToken
from data_transform_tool.io.inspector import FileInspector
from data_transform_tool.io.models import FileInspection
from data_transform_tool.io.options import InspectionOptions
from data_transform_tool.ui.models import ColumnProfileTableModel, PreviewTableModel
from data_transform_tool.ui.workers.inspection_worker import BatchInspectionWorker


class FileInspectionView(QWidget):
    """Guide the user from local file selection to a transparent source profile."""

    back_requested = Signal()
    configuration_requested = Signal(object)

    def __init__(
        self,
        inspector: FileInspector | None = None,
        *,
        workflow: Literal["reformat", "average"] = "reformat",
    ) -> None:
        super().__init__()
        self._workflow = workflow
        self._inspector = inspector or FileInspector.default()
        self._source_paths: tuple[Path, ...] = ()
        self._source_path: Path | None = None
        self._inspection: FileInspection | None = None
        self._batch_inspection: BatchInspection | None = None
        self._thread: QThread | None = None
        self._worker: BatchInspectionWorker | None = None
        self._cancellation: CancellationToken | None = None
        self._table_models: list[object] = []
        self.setAcceptDrops(True)

        root = QVBoxLayout(self)
        root.setContentsMargins(38, 28, 38, 28)
        root.setSpacing(16)
        root.addLayout(self._create_title_row())
        root.addWidget(self._create_stepper())
        root.addWidget(self._create_source_panel())
        root.addLayout(self._create_progress_row())
        root.addWidget(self._create_results(), 1)

    def _create_title_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        back = QPushButton("←  Back")
        back.setProperty("role", "ghost")
        back.clicked.connect(self.back_requested)
        row.addWidget(back)
        titles = QVBoxLayout()
        eyebrow_text = (
            "AVERAGE / AGGREGATE  •  SOURCE INSPECTION"
            if self._workflow == "average"
            else "REFORMAT / TRANSFORM  •  PHASE 2"
        )
        eyebrow = QLabel(eyebrow_text)
        eyebrow.setProperty("role", "eyebrow")
        title = QLabel("Inspect the source before changing it")
        title.setProperty("role", "sectionTitle")
        titles.addWidget(eyebrow)
        titles.addWidget(title)
        row.addLayout(titles)
        row.addStretch()
        return row

    def _create_stepper(self) -> QFrame:
        stepper = QFrame()
        stepper.setProperty("role", "modeCard")
        layout = QHBoxLayout(stepper)
        layout.setContentsMargins(18, 12, 18, 12)
        for index, name in enumerate(
            ("1  Mode", "2  File", "3  Inspect", "4  Configure", "5  Preview", "6  Export")
        ):
            label = QLabel(name)
            label.setProperty("role", "badge" if index in {1, 2} else "muted")
            layout.addWidget(label)
            if index < 5:
                separator = QLabel("→")
                separator.setProperty("role", "muted")
                layout.addWidget(separator)
        layout.addStretch()
        return stepper

    def _create_source_panel(self) -> QFrame:
        panel = QFrame()
        panel.setProperty("role", "modeCard")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        file_row = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        self.path_edit.setPlaceholderText("Choose or drop one or more CSV, TSV, TXT, or XLSX files")
        file_row.addWidget(self.path_edit, 1)
        browse = QPushButton("Choose files")
        browse.setProperty("role", "primary")
        browse.clicked.connect(self._browse)
        file_row.addWidget(browse)
        layout.addLayout(file_row)

        drop_hint = QLabel(
            "You can also drag files here. In batch mode, the first file is the reference and "
            "every other file must match its type, ordered columns, header, and format."
        )
        drop_hint.setWordWrap(True)
        drop_hint.setProperty("role", "muted")
        layout.addWidget(drop_hint)
        self.selected_files = QListWidget()
        self.selected_files.setMaximumHeight(100)
        self.selected_files.hide()
        layout.addWidget(self.selected_files)

        self.worksheet_row = QWidget()
        worksheet_layout = QHBoxLayout(self.worksheet_row)
        worksheet_layout.setContentsMargins(0, 0, 0, 0)
        worksheet_layout.addWidget(QLabel("Worksheet"))
        self.worksheet_selector = QComboBox()
        self.worksheet_selector.setMinimumWidth(260)
        worksheet_layout.addWidget(self.worksheet_selector)
        worksheet_layout.addStretch()
        self.worksheet_row.hide()
        layout.addWidget(self.worksheet_row)

        overrides = QGroupBox("Detection overrides")
        overrides.setCheckable(True)
        overrides.setChecked(False)
        overrides_layout = QVBoxLayout(overrides)
        overrides_layout.setContentsMargins(10, 4, 10, 10)
        self.override_fields = QWidget()
        override_layout = QGridLayout(self.override_fields)
        override_layout.setContentsMargins(0, 0, 0, 0)
        self.encoding_selector = QComboBox()
        self.encoding_selector.addItem("Auto-detect", None)
        for encoding in ("utf-8", "utf-8-sig", "cp1252", "utf-16"):
            self.encoding_selector.addItem(encoding, encoding)
        self.delimiter_selector = QComboBox()
        self.delimiter_selector.addItem("Auto-detect", None)
        self.delimiter_selector.addItem("Comma  ,", ",")
        self.delimiter_selector.addItem("Tab  ↹", "\t")
        self.delimiter_selector.addItem("Semicolon  ;", ";")
        self.delimiter_selector.addItem("Pipe  |", "|")
        self.header_selector = QComboBox()
        self.header_selector.addItem("Auto-detect", None)
        self.header_selector.addItem("First row is a header", True)
        self.header_selector.addItem("No header row", False)
        override_layout.addWidget(QLabel("Encoding"), 0, 0)
        override_layout.addWidget(self.encoding_selector, 0, 1)
        override_layout.addWidget(QLabel("Delimiter"), 0, 2)
        override_layout.addWidget(self.delimiter_selector, 0, 3)
        override_layout.addWidget(QLabel("Header"), 0, 4)
        override_layout.addWidget(self.header_selector, 0, 5)
        overrides_layout.addWidget(self.override_fields)
        overrides.toggled.connect(self.override_fields.setVisible)
        self.override_fields.hide()
        layout.addWidget(overrides)
        return panel

    def _create_progress_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        self.status_label = QLabel("Choose a local file to begin.")
        self.status_label.setProperty("role", "muted")
        row.addWidget(self.status_label, 1)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedWidth(190)
        self.progress_bar.hide()
        row.addWidget(self.progress_bar)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_inspection)
        self.cancel_button.hide()
        row.addWidget(self.cancel_button)
        self.inspect_button = QPushButton("Inspect file")
        self.inspect_button.setProperty("role", "primary")
        self.inspect_button.setEnabled(False)
        self.inspect_button.clicked.connect(self.start_inspection)
        row.addWidget(self.inspect_button)
        configure_label = (
            "Configure averaging  →" if self._workflow == "average" else "Configure fields  →"
        )
        self.configure_button = QPushButton(configure_label)
        self.configure_button.setProperty("role", "primary")
        self.configure_button.clicked.connect(self._request_configuration)
        self.configure_button.hide()
        row.addWidget(self.configure_button)
        return row

    def _create_results(self) -> QTabWidget:
        self.results = QTabWidget()
        self.results.setVisible(False)

        overview = QWidget()
        overview_layout = QVBoxLayout(overview)
        self.summary_grid = QGridLayout()
        overview_layout.addLayout(self.summary_grid)
        self.strategy_label = QLabel()
        self.strategy_label.setProperty("role", "muted")
        self.strategy_label.setWordWrap(True)
        overview_layout.addWidget(self.strategy_label)
        overview_layout.addWidget(QLabel("Warnings and confirmation points"))
        self.warning_list = QListWidget()
        self.warning_list.setMinimumHeight(76)
        overview_layout.addWidget(self.warning_list)
        self.results.addTab(overview, "Overview")

        self.column_table = QTableView()
        self.column_table.setAlternatingRowColors(True)
        self.column_table.setSortingEnabled(False)
        self.column_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.column_table.horizontalHeader().setStretchLastSection(True)
        self.results.addTab(self.column_table, "Columns")

        self.preview_tabs = QTabWidget()
        self.results.addTab(self.preview_tabs, "First / middle / last preview")
        return self.results

    def _browse(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Choose input data files",
            "",
            "Supported data (*.csv *.tsv *.txt *.xlsx);;"
            "Delimited text (*.csv *.tsv *.txt);;Excel workbook (*.xlsx)",
        )
        if paths:
            self.set_source_paths(paths)

    def set_source_path(self, path: str | Path) -> None:
        """Set a source path from a file dialog or an integration test."""
        self.set_source_paths((path,))

    def set_source_paths(self, paths: Sequence[str | Path]) -> None:
        """Set one or more source paths; the first becomes the batch reference."""
        resolved = tuple(dict.fromkeys(Path(path).resolve() for path in paths))
        unsupported = tuple(
            path
            for path in resolved
            if path.suffix.casefold() not in self._inspector.supported_extensions
        )
        if unsupported:
            self.status_label.setText(
                "Unsupported files were not selected: "
                + ", ".join(path.name for path in unsupported)
            )
            self.inspect_button.setEnabled(False)
            return
        self._source_paths = resolved
        self._source_path = resolved[0] if resolved else None
        self._inspection = None
        self._batch_inspection = None
        if len(resolved) == 1:
            self.path_edit.setText(str(self._source_path))
        elif self._source_path is not None:
            self.path_edit.setText(
                f"{len(resolved)} files selected · reference: {self._source_path.name}"
            )
        else:
            self.path_edit.clear()
        self.selected_files.clear()
        self.selected_files.addItems([path.name for path in resolved])
        self.selected_files.setVisible(len(resolved) > 1)
        self.results.hide()
        self.configure_button.hide()
        self.worksheet_selector.clear()
        if self._source_path is not None and self._source_path.suffix.casefold() == ".xlsx":
            try:
                worksheets = self._inspector.available_worksheets(self._source_path)
            except AppError as error:
                self._show_error(error.user_message, error.detail or "")
                self.inspect_button.setEnabled(False)
                return
            self.worksheet_selector.addItems(worksheets)
            self.worksheet_row.show()
        else:
            self.worksheet_row.hide()
        self.inspect_button.setEnabled(bool(resolved))
        if not resolved:
            self.status_label.setText("Choose or drop one or more local files to begin.")
        elif len(resolved) > 1:
            self.status_label.setText(
                "Ready to inspect locally. Batch compatibility will be checked "
                "against the first file."
            )
        else:
            self.status_label.setText(
                "Ready to inspect. Detection remains reviewable and overridable."
            )

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        paths = tuple(
            Path(url.toLocalFile()) for url in event.mimeData().urls() if url.isLocalFile()
        )
        if paths and all(
            path.suffix.casefold() in self._inspector.supported_extensions for path in paths
        ):
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        paths = tuple(
            Path(url.toLocalFile()) for url in event.mimeData().urls() if url.isLocalFile()
        )
        if paths:
            self.set_source_paths(list(paths))
            event.acceptProposedAction()

    def start_inspection(self) -> None:
        if self._source_path is None or self._thread is not None:
            return
        options = InspectionOptions(
            worksheet=(
                self.worksheet_selector.currentText()
                if self._source_path.suffix.casefold() == ".xlsx"
                else None
            ),
            encoding=cast(str | None, self.encoding_selector.currentData()),
            delimiter=cast(str | None, self.delimiter_selector.currentData()),
            has_header=cast(bool | None, self.header_selector.currentData()),
        )
        self._cancellation = CancellationToken()
        self._thread = QThread(self)
        self._worker = BatchInspectionWorker(
            inspector=self._inspector,
            paths=self._source_paths,
            options=options,
            cancellation=self._cancellation,
        )
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress_changed.connect(self._on_progress)
        self._worker.completed.connect(self._on_completed)
        self._worker.failed.connect(self._show_error)
        self._worker.cancelled.connect(self._on_cancelled)
        self._worker.completed.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._worker.cancelled.connect(self._thread.quit)
        self._thread.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread_finished)
        self.inspect_button.setEnabled(False)
        self.progress_bar.show()
        self.cancel_button.show()
        self.status_label.setText("Inspecting locally…")
        self._thread.start()

    def cancel_inspection(self) -> None:
        if self._cancellation is not None:
            self._cancellation.cancel()
            self.status_label.setText("Cancelling safely…")

    def _on_progress(self, phase: str, rows: object) -> None:
        row_count = cast(int | None, rows)
        suffix = f" • {row_count:,} rows" if row_count is not None else ""
        self.status_label.setText(f"{phase}{suffix}")

    def _on_completed(self, result: object) -> None:
        batch = cast(BatchInspection, result)
        inspection = batch.reference
        self._batch_inspection = batch
        self._inspection = inspection
        self._populate_result(inspection)
        self._populate_batch_status(batch)
        self.configure_button.setVisible(batch.is_compatible)
        if batch.is_compatible:
            suffix = (
                f" • {len(batch.inspections)} compatible files"
                if len(batch.inspections) > 1
                else ""
            )
            self.status_label.setText(
                f"Inspection complete • {inspection.row_count:,} rows • "
                f"{inspection.column_count:,} columns{suffix}"
            )
        else:
            self.status_label.setText(
                f"{len(batch.incompatible)} file(s) do not match the reference. "
                "Remove or correct them before configuring."
            )

    def _on_cancelled(self) -> None:
        self.status_label.setText("Inspection cancelled. The input file was not changed.")

    def _show_error(self, message: str, details: str) -> None:
        self.status_label.setText(message)
        box = QMessageBox(QMessageBox.Icon.Critical, "File inspection", message, parent=self)
        if details:
            box.setDetailedText(details)
        box.exec()

    def _thread_finished(self) -> None:
        self.progress_bar.hide()
        self.cancel_button.hide()
        self.inspect_button.setEnabled(bool(self._source_paths))
        self._thread = None
        self._worker = None
        self._cancellation = None

    def _request_configuration(self) -> None:
        if self._inspection is not None and self._batch_inspection is not None:
            value: FileInspection | BatchInspection = (
                self._inspection
                if len(self._batch_inspection.inspections) == 1
                else self._batch_inspection
            )
            self.configuration_requested.emit(value)

    def _populate_batch_status(self, batch: BatchInspection) -> None:
        self.selected_files.clear()
        for index, (inspection, status) in enumerate(
            zip(batch.inspections, batch.compatibility, strict=True)
        ):
            if index == 0:
                label = f"Reference · {inspection.path.name}"
            elif status.compatible:
                label = f"Compatible · {inspection.path.name}"
            else:
                label = f"Incompatible · {inspection.path.name} — {'; '.join(status.reasons)}"
            self.selected_files.addItem(label)
        self.selected_files.setVisible(len(batch.inspections) > 1)

    def _populate_result(self, inspection: FileInspection) -> None:
        self._clear_layout(self.summary_grid)
        summary = (
            (
                "Shape",
                f"{inspection.row_count:,} rows · {inspection.column_count:,} columns",
            ),
            (
                "Source",
                f"{inspection.file_kind.value} · {inspection.worksheet or inspection.path.name}",
            ),
            (
                "Text format",
                f"{inspection.encoding or 'Native XLSX'} · "
                f"{_delimiter_label(inspection.delimiter)}",
            ),
            (
                "Header",
                f"{'Detected' if inspection.header_detected else 'Not detected'} "
                f"({inspection.header_confidence:.0%})",
            ),
            (
                "Time structure",
                f"{inspection.likely_datetime_column or 'Timestamp not detected'} · "
                f"{inspection.likely_interval_label or 'Interval not detected'}",
            ),
            ("Empty columns", ", ".join(inspection.empty_columns) or "None"),
        )
        for index, (label, value) in enumerate(summary):
            row, column = divmod(index, 3)
            card = QFrame()
            card.setProperty("role", "modeCard")
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(10, 5, 10, 5)
            name = QLabel(f"{label}:")
            name.setProperty("role", "muted")
            content = QLabel(value)
            content.setWordWrap(True)
            content.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            card_layout.addWidget(name)
            card_layout.addWidget(content, 1)
            self.summary_grid.addWidget(card, row, column)

        self.strategy_label.setText(
            f"Read strategy: {inspection.processing_strategy}  •  "
            f"File {_format_bytes(inspection.file_size_bytes)}  •  "
            f"Estimated in-memory equivalent {_format_bytes(inspection.estimated_memory_bytes)}"
        )

        self.warning_list.clear()
        warnings = list(inspection.warnings)
        warnings.extend(
            f"Potential missing marker {marker.value!r}: {marker.count:,} occurrences — "
            "confirm before normalization."
            for marker in inspection.potential_missing_markers
        )
        if not warnings:
            warnings.append(
                "No blocking structural warnings were detected. Review all inferences "
                "before processing."
            )
        self.warning_list.addItems(warnings)

        profile_model = ColumnProfileTableModel(inspection.columns)
        self.column_table.setModel(profile_model)
        self._table_models = [profile_model]

        while self.preview_tabs.count():
            widget = self.preview_tabs.widget(0)
            self.preview_tabs.removeTab(0)
            if widget is not None:
                widget.deleteLater()
        for preview in inspection.previews:
            table = QTableView()
            table.setAlternatingRowColors(True)
            table.setWordWrap(False)
            model = PreviewTableModel(inspection.column_names, preview)
            table.setModel(model)
            table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            self._table_models.append(model)
            self.preview_tabs.addTab(table, preview.label)
        self.results.show()
        self.results.setCurrentIndex(0)

    @staticmethod
    def _clear_layout(layout: QGridLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()


def _delimiter_label(delimiter: str | None) -> str:
    if delimiter is None:
        return "Native XLSX"
    labels = {",": "Comma ( , )", "\t": "Tab", ";": "Semicolon ( ; )", "|": "Pipe ( | )"}
    return labels.get(delimiter, repr(delimiter))


def _format_bytes(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"
