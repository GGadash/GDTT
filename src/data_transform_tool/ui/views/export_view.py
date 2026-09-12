"""Phase 8 pre-export review, output options, templates, and verified results.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import cast

from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTableView,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from data_transform_tool.app.averaging_preview import PreviewTable
from data_transform_tool.app.batch_export import BatchExportResult
from data_transform_tool.app.export_workflow import PreparedExport, WorkflowDraft
from data_transform_tool.export.models import ExportPlan, ExportResult, XlsxStyle
from data_transform_tool.io.cancellation import CancellationToken
from data_transform_tool.io.models import FileInspection, PreviewSlice
from data_transform_tool.templates import TemplateRecord, TemplateRepository
from data_transform_tool.transformation.recipe import (
    OutputFormat,
    OutputMissingPolicy,
    TransformationRecipe,
)
from data_transform_tool.ui.models import SimplePreviewTableModel
from data_transform_tool.ui.widgets.field_controls import bulk_buttons
from data_transform_tool.ui.workers.export_worker import (
    BatchExecutionWorker,
    ExecutionWorker,
    PreparationWorker,
)


class ExportView(QWidget):
    """Review complete-file evidence and make all export choices explicit."""

    back_requested = Signal(str)
    template_apply_requested = Signal(object, object)
    process_more_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._inspection: FileInspection | None = None
        self._inspections: tuple[FileInspection, ...] = ()
        self._draft: WorkflowDraft | None = None
        self._recipe: TransformationRecipe | None = None
        self._prepared: PreparedExport | None = None
        self._thread: QThread | None = None
        self._worker: PreparationWorker | ExecutionWorker | BatchExecutionWorker | None = None
        self._cancellation: CancellationToken | None = None
        self._template_repository = TemplateRepository()
        self._build_ui()

    def set_context(
        self,
        inspection: FileInspection,
        draft: WorkflowDraft,
        recipe: TransformationRecipe,
        inspections: tuple[FileInspection, ...] | None = None,
    ) -> None:
        if self._prepared is not None:
            self._prepared.close()
        self._inspection = inspection
        self._inspections = inspections or (inspection,)
        self._draft = draft
        self._recipe = recipe
        self._prepared = None
        self.tabs.setCurrentIndex(0)
        self.status_label.setText("Preparing complete-file review locally…")
        self.progress.setValue(0)
        self.progress.show()
        self.export_button.setEnabled(False)
        self.destination_edit.setText(str(inspection.path.parent))
        self.name_edit.clear()
        self.name_edit.setEnabled(len(self._inspections) == 1)
        self.name_edit.setToolTip(
            "Batch mode uses a collision-safe name derived from each source file."
            if len(self._inspections) > 1
            else "Choose the output base filename."
        )
        self.process_more_button.hide()
        self.missing_combo.setCurrentIndex(
            max(self.missing_combo.findData(recipe.output.missing_policy.value), 0)
        )
        self.custom_missing_edit.setText(
            ""
            if recipe.output.custom_missing_sentinel is None
            else str(recipe.output.custom_missing_sentinel)
        )
        self._populate_template_matches()
        QTimer.singleShot(0, self._start_preparation)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 22, 30, 22)
        layout.setSpacing(12)
        top = QHBoxLayout()
        back = QPushButton("← Back to configuration")
        back.setProperty("role", "ghost")
        back.clicked.connect(self._go_back)
        top.addWidget(back)
        top.addStretch()
        self.status_label = QLabel("Waiting for a confirmed configuration.")
        self.status_label.setProperty("role", "muted")
        top.addWidget(self.status_label)
        layout.addLayout(top)

        title = QLabel("Review and export")
        title.setProperty("role", "pageTitle")
        layout.addWidget(title)
        subtitle = QLabel(
            "Full-file execution is separate from bounded preview. Review the first, middle, "
            "and last records before writing any output."
        )
        subtitle.setWordWrap(True)
        subtitle.setProperty("role", "muted")
        layout.addWidget(subtitle)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.hide()
        layout.addWidget(self.progress)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._review_panel(), "1  Pre-export review")
        self.tabs.addTab(self._options_panel(), "2  Output & style")
        self.tabs.addTab(self._results_panel(), "3  Verification")
        layout.addWidget(self.tabs, 1)

    def _review_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        self.review_summary = QLabel(
            "Complete-file counts and transformation plan will appear here."
        )
        self.review_summary.setWordWrap(True)
        self.review_summary.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.review_summary)
        selectors = QHBoxLayout()
        selectors.addWidget(QLabel("Input slice"))
        self.input_slice_combo = QComboBox()
        self.input_slice_combo.currentIndexChanged.connect(self._refresh_input_slice)
        selectors.addWidget(self.input_slice_combo)
        selectors.addSpacing(18)
        selectors.addWidget(QLabel("Proposed output slice"))
        self.output_slice_combo = QComboBox()
        self.output_slice_combo.currentIndexChanged.connect(self._refresh_output_slice)
        selectors.addWidget(self.output_slice_combo)
        selectors.addStretch()
        layout.addLayout(selectors)
        self.input_model = SimplePreviewTableModel()
        self.input_table = self._table(self.input_model)
        layout.addWidget(QLabel("Input"))
        layout.addWidget(self.input_table, 1)
        self.output_model = SimplePreviewTableModel()
        self.output_table = self._table(self.output_model)
        layout.addWidget(QLabel("Proposed output"))
        layout.addWidget(self.output_table, 1)
        next_button = QPushButton("Choose outputs →")
        next_button.setProperty("role", "primary")
        next_button.clicked.connect(lambda: self.tabs.setCurrentIndex(1))
        layout.addWidget(next_button, alignment=Qt.AlignmentFlag.AlignRight)
        return panel

    def _options_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        destination_card = QFrame()
        destination_card.setProperty("role", "modeCard")
        form = QFormLayout(destination_card)
        destination_row = QHBoxLayout()
        self.destination_edit = QLineEdit()
        destination_row.addWidget(self.destination_edit, 1)
        browse = QPushButton("Browse…")
        browse.clicked.connect(self._browse_destination)
        destination_row.addWidget(browse)
        form.addRow("Output folder", destination_row)
        self.name_edit = QLineEdit()
        form.addRow("Base filename", self.name_edit)

        format_row = QHBoxLayout()
        self.csv_check = QCheckBox("CSV")
        self.csv_check.setChecked(True)
        self.plain_check = QCheckBox("XLSX plain")
        self.formatted_check = QCheckBox("XLSX formatted")
        self.formatted_check.toggled.connect(self._update_option_visibility)
        format_row.addWidget(self.csv_check)
        format_row.addWidget(self.plain_check)
        format_row.addWidget(self.formatted_check)
        format_row.addStretch()
        form.addRow("Data outputs", format_row)
        form.addRow(
            bulk_buttons(
                (self.csv_check, self.plain_check, self.formatted_check),
                self._update_option_visibility,
            )
        )

        self.missing_combo = QComboBox()
        self.missing_combo.addItem("True blank / null", OutputMissingPolicy.TRUE_NULL.value)
        self.missing_combo.addItem("N/A", OutputMissingPolicy.NA.value)
        self.missing_combo.addItem("-999", OutputMissingPolicy.MINUS_999.value)
        self.missing_combo.addItem("Custom sentinel", OutputMissingPolicy.CUSTOM.value)
        self.missing_combo.currentIndexChanged.connect(self._update_option_visibility)
        form.addRow("Missing output", self.missing_combo)
        self.custom_missing_edit = QLineEdit()
        self.custom_missing_edit.setPlaceholderText("Required only for Custom")
        form.addRow("Custom sentinel", self.custom_missing_edit)
        self.overwrite_check = QCheckBox("Allow replacing files with the same names")
        form.addRow("Overwrite", self.overwrite_check)
        layout.addWidget(destination_card)

        self.style_card = QFrame()
        self.style_card.setProperty("role", "modeCard")
        style_form = QFormLayout(self.style_card)
        self.style_preset = QComboBox()
        self.style_preset.addItems(("Environmental Technical", "Clean Laboratory", "Minimal"))
        self.style_preset.currentTextChanged.connect(self._apply_style_preset)
        style_form.addRow("Style preset", self.style_preset)
        self.font_edit = QLineEdit("Aptos")
        style_form.addRow("Font", self.font_edit)
        self.font_size = QSpinBox()
        self.font_size.setRange(6, 72)
        self.font_size.setValue(10)
        style_form.addRow("Font size", self.font_size)
        self.header_fill = QLineEdit("#0F766E")
        style_form.addRow("Header fill", self.header_fill)
        self.alternate_fill = QLineEdit("#ECFDF5")
        style_form.addRow("Alternating rows", self.alternate_fill)
        self.filter_check = QCheckBox("AutoFilter")
        self.filter_check.setChecked(True)
        self.freeze_check = QCheckBox("Freeze header")
        self.freeze_check.setChecked(True)
        style_flags = QHBoxLayout()
        style_flags.addWidget(self.filter_check)
        style_flags.addWidget(self.freeze_check)
        style_flags.addStretch()
        style_form.addRow("Worksheet", style_flags)
        style_form.addRow(bulk_buttons((self.filter_check, self.freeze_check)))
        layout.addWidget(self.style_card)

        sidecars = QFrame()
        sidecars.setProperty("role", "modeCard")
        sidecar_form = QFormLayout(sidecars)
        self.info_check = QCheckBox("Transformation information (.txt)")
        self.info_check.setChecked(True)
        self.recipe_check = QCheckBox("Reusable recipe (.json)")
        self.recipe_check.setChecked(True)
        self.summary_check = QCheckBox("Concise summary (.txt)")
        self.summary_check.setChecked(True)
        self.errors_check = QCheckBox("Warning / error report when needed")
        self.errors_check.setChecked(True)
        sidecar_row = QVBoxLayout()
        for control in (
            self.info_check,
            self.recipe_check,
            self.summary_check,
            self.errors_check,
        ):
            sidecar_row.addWidget(control)
        sidecar_form.addRow("Evidence sidecars", sidecar_row)
        sidecar_form.addRow(
            bulk_buttons(
                (self.info_check, self.recipe_check, self.summary_check, self.errors_check)
            )
        )
        layout.addWidget(sidecars)

        template_row = QHBoxLayout()
        self.template_combo = QComboBox()
        template_row.addWidget(QLabel("Matching templates"))
        template_row.addWidget(self.template_combo, 1)
        apply_template = QPushButton("Apply")
        apply_template.clicked.connect(self._apply_selected_template)
        template_row.addWidget(apply_template)
        review_template = QPushButton("Review")
        review_template.clicked.connect(self._review_selected_template)
        template_row.addWidget(review_template)
        ignore_template = QPushButton("Ignore")
        ignore_template.clicked.connect(self._ignore_selected_template)
        template_row.addWidget(ignore_template)
        save_template = QPushButton("Save current…")
        save_template.clicked.connect(self._save_template)
        template_row.addWidget(save_template)
        manage = QPushButton("Manage…")
        manage.clicked.connect(self._manage_templates)
        template_row.addWidget(manage)
        layout.addLayout(template_row)
        layout.addStretch()

        actions = QHBoxLayout()
        actions.addStretch()
        cancel = QPushButton("Cancel operation")
        cancel.clicked.connect(self._cancel)
        actions.addWidget(cancel)
        self.export_button = QPushButton("Export and verify")
        self.export_button.setProperty("role", "primary")
        self.export_button.setEnabled(False)
        self.export_button.clicked.connect(self._start_export)
        actions.addWidget(self.export_button)
        layout.addLayout(actions)
        self._update_option_visibility()
        return panel

    def _results_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        self.result_heading = QLabel("No export has run.")
        self.result_heading.setProperty("role", "sectionTitle")
        layout.addWidget(self.result_heading)
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        layout.addWidget(self.result_text, 1)
        result_actions = QHBoxLayout()
        result_actions.addStretch()
        self.process_more_button = QPushButton("Process more similar files")
        self.process_more_button.setProperty("role", "primary")
        self.process_more_button.clicked.connect(self._process_more)
        self.process_more_button.hide()
        result_actions.addWidget(self.process_more_button)
        layout.addLayout(result_actions)
        return panel

    @staticmethod
    def _table(model: SimplePreviewTableModel) -> QTableView:
        table = QTableView()
        table.setModel(model)
        table.setAlternatingRowColors(True)
        table.setSortingEnabled(False)
        return table

    def _start_preparation(self) -> None:
        if (
            self._inspection is None
            or self._draft is None
            or self._recipe is None
            or self._thread is not None
        ):
            return
        self._cancellation = CancellationToken()
        worker = PreparationWorker(
            self._inspection,
            self._draft,
            self._recipe,
            self._cancellation,
        )
        worker.completed.connect(self._on_prepared)
        self._launch(worker)

    def _start_export(self) -> None:
        if self._prepared is None or self._thread is not None:
            return
        try:
            plan = self._build_plan()
        except (ValueError, OSError) as error:
            QMessageBox.warning(self, "Export options", str(error))
            return
        self._cancellation = CancellationToken()
        worker: ExecutionWorker | BatchExecutionWorker
        if len(self._inspections) > 1 and self._draft is not None and self._recipe is not None:
            worker = BatchExecutionWorker(
                self._prepared,
                self._inspections,
                self._draft,
                self._recipe,
                plan,
                self._cancellation,
            )
        else:
            worker = ExecutionWorker(self._prepared, plan, self._cancellation)
        worker.completed.connect(self._on_exported)
        self.export_button.setEnabled(False)
        self.progress.setValue(0)
        self.progress.show()
        self.status_label.setText("Writing and verifying locally…")
        self._launch(worker)

    def _launch(self, worker: PreparationWorker | ExecutionWorker | BatchExecutionWorker) -> None:
        thread = QThread(self)
        self._thread = thread
        self._worker = worker
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress_changed.connect(self._on_progress)
        worker.failed.connect(self._on_failed)
        worker.cancelled.connect(self._on_cancelled)
        worker.completed.connect(thread.quit)
        worker.failed.connect(thread.quit)
        worker.cancelled.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(self._thread_finished)
        thread.start()

    def _on_progress(self, percent: int, message: str) -> None:
        self.progress.setValue(percent)
        self.status_label.setText(message)

    def _on_prepared(self, value: object) -> None:
        prepared = cast(PreparedExport, value)
        self._prepared = prepared
        self.name_edit.setText(prepared.suggested_base_name)
        self._set_slices(self.input_slice_combo, prepared.input_previews)
        self._set_slices(self.output_slice_combo, prepared.output_previews)
        self._refresh_input_slice()
        self._refresh_output_slice()
        evidence = prepared.evidence
        plan_lines = (
            f"Mode: {'Batch' if len(self._inspections) > 1 else 'Single file'} · "
            f"{len(self._inspections)} source file(s)",
            f"Reference preview: {prepared.inspection.path.name}",
            f"Input: {prepared.input_table.row_count:,} rows x "
            f"{prepared.input_table.column_count} columns",
            f"Expected output: {prepared.output_table.row_count:,} rows x "
            f"{prepared.output_table.column_count} columns",
            f"Output fields: {', '.join(prepared.output_table.columns)}",
            f"Generated gaps: {evidence.generated_gap_rows:,} • "
            f"Removed rows: {evidence.removed_rows:,} • "
            f"Rejected averages: {evidence.rejected_averages:,}",
            f"Execution: {evidence.execution_strategy}",
            *(f"Warning: {warning}" for warning in evidence.warnings),
        )
        self.review_summary.setText("\n".join(plan_lines))
        self.export_button.setEnabled(True)
        self.status_label.setText(
            "Reference-file review ready. The same confirmed plan will be independently "
            "verified for every compatible source."
            if len(self._inspections) > 1
            else "Complete-file review ready. Inspect slices, then choose outputs."
        )
        self.progress.hide()

    def _on_exported(self, value: object) -> None:
        if isinstance(value, BatchExportResult):
            self._on_batch_exported(value)
            return
        result = cast(ExportResult, value)
        failed = bool(result.errors)
        verification_lines = [
            f"{item.artifact.name}: {item.status.value.replace('_', ' ').title()}"
            for item in result.verifications
        ]
        artifact_lines = [f"• {artifact.kind}: {artifact.path}" for artifact in result.artifacts]
        self.result_heading.setText(
            "Export completed with failures" if failed else "Export completed and verified"
        )
        self.result_text.setPlainText(
            "\n".join(
                (
                    "OUTPUTS",
                    *artifact_lines,
                    "",
                    "VERIFICATION",
                    *verification_lines,
                    "",
                    "WARNINGS",
                    *(result.warnings or ("None",)),
                    "",
                    "ERRORS",
                    *(result.errors or ("None",)),
                    "",
                    "FULL REPORT",
                    result.report_text,
                )
            )
        )
        self.tabs.setCurrentIndex(2)
        self.status_label.setText(
            "Verification failures are shown and retained in the report."
            if failed
            else "Export complete. Every selected data output passed reopen verification."
        )
        self.progress.hide()
        self.process_more_button.show()

    def _on_batch_exported(self, result: BatchExportResult) -> None:
        lines = [
            "BATCH VERIFICATION",
            f"Passed: {result.passed_count} of {len(result.items)} files",
            f"Failed: {result.failed_count}",
            "",
        ]
        for item in result.items:
            lines.append(f"SOURCE: {item.source}")
            if item.error is not None:
                lines.extend(("Status: Failed", f"Error: {item.error}", ""))
                continue
            assert item.result is not None
            lines.append("Status: Passed" if item.passed else "Status: Failed")
            lines.extend(
                f"• {verification.artifact.name}: "
                f"{verification.status.value.replace('_', ' ').title()}"
                for verification in item.result.verifications
            )
            lines.extend(f"• output: {artifact.path}" for artifact in item.result.artifacts)
            if item.result.warnings:
                lines.extend(f"Warning: {warning}" for warning in item.result.warnings)
            if item.result.errors:
                lines.extend(f"Error: {error}" for error in item.result.errors)
            lines.append("")
        self.result_heading.setText(
            "Batch export completed and verified"
            if result.failed_count == 0
            else "Batch export completed with failures"
        )
        self.result_text.setPlainText("\n".join(lines))
        self.tabs.setCurrentIndex(2)
        self.status_label.setText(
            "Every batch source passed independent reopen verification."
            if result.failed_count == 0
            else "Batch failures are isolated and listed per source."
        )
        self.progress.hide()
        self.process_more_button.show()

    def _process_more(self) -> None:
        mode = self._recipe.mode if self._recipe is not None else "reformat"
        if self._prepared is not None:
            self._prepared.close()
            self._prepared = None
        self.process_more_requested.emit(mode)

    def _on_failed(self, message: str, details: str) -> None:
        self.progress.hide()
        self.status_label.setText(message)
        box = QMessageBox(QMessageBox.Icon.Critical, "Processing or export", message, parent=self)
        if details:
            box.setDetailedText(details)
        box.exec()

    def _on_cancelled(self) -> None:
        self.progress.hide()
        self.status_label.setText("Operation cancelled safely. No temporary output was retained.")

    def _thread_finished(self) -> None:
        self._thread = None
        self._worker = None
        self._cancellation = None
        self.export_button.setEnabled(self._prepared is not None)

    def _cancel(self) -> None:
        if self._cancellation is not None:
            self._cancellation.cancel()
            self.status_label.setText("Cancelling safely…")

    def _go_back(self) -> None:
        if self._thread is not None:
            self._cancel()
            self.status_label.setText("Wait for cancellation before returning.")
            return
        mode = self._recipe.mode if self._recipe is not None else "reformat"
        if self._prepared is not None:
            self._prepared.close()
            self._prepared = None
        self.back_requested.emit(mode)

    def _build_plan(self) -> ExportPlan:
        destination_text = self.destination_edit.text().strip()
        if not destination_text:
            raise ValueError("Choose an output folder.")
        destination = Path(destination_text)
        formats: list[OutputFormat] = []
        if self.csv_check.isChecked():
            formats.append(OutputFormat.CSV)
        if self.plain_check.isChecked():
            formats.append(OutputFormat.XLSX_PLAIN)
        if self.formatted_check.isChecked():
            formats.append(OutputFormat.XLSX_FORMATTED)
        missing = OutputMissingPolicy(str(self.missing_combo.currentData()))
        custom: str | None = None
        if missing is OutputMissingPolicy.CUSTOM:
            custom = self.custom_missing_edit.text().strip()
        style = XlsxStyle(
            name=self.style_preset.currentText(),
            font_name=self.font_edit.text().strip(),
            font_size=self.font_size.value(),
            header_fill=self.header_fill.text().strip(),
            alternating_fill=self.alternate_fill.text().strip(),
            autofilter=self.filter_check.isChecked(),
            freeze_header=self.freeze_check.isChecked(),
        )
        return ExportPlan(
            destination,
            self.name_edit.text().strip(),
            tuple(formats),
            missing,
            custom,
            style,
            self.overwrite_check.isChecked(),
            self.info_check.isChecked(),
            self.recipe_check.isChecked(),
            self.errors_check.isChecked(),
            self.summary_check.isChecked(),
        )

    def _refresh_input_slice(self) -> None:
        if self._prepared is not None:
            self.input_model.set_table(
                self._slice_table(
                    self._prepared.input_table.columns,
                    self._prepared.input_previews,
                    self.input_slice_combo.currentIndex(),
                )
            )

    def _refresh_output_slice(self) -> None:
        if self._prepared is not None:
            self.output_model.set_table(
                self._slice_table(
                    self._prepared.output_table.columns,
                    self._prepared.output_previews,
                    self.output_slice_combo.currentIndex(),
                )
            )

    @staticmethod
    def _slice_table(
        columns: tuple[str, ...],
        slices: tuple[PreviewSlice, ...],
        index: int,
    ) -> PreviewTable:
        if not slices:
            return PreviewTable(columns, ())
        selected = slices[max(0, min(index, len(slices) - 1))]
        return PreviewTable(columns, selected.rows)

    @staticmethod
    def _set_slices(combo: QComboBox, slices: tuple[PreviewSlice, ...]) -> None:
        combo.clear()
        for preview in slices:
            combo.addItem(
                f"{preview.label} • rows {preview.start_row}-"
                f"{preview.start_row + max(len(preview.rows) - 1, 0)}"
            )

    def _browse_destination(self) -> None:
        selected = QFileDialog.getExistingDirectory(
            self,
            "Choose output folder",
            self.destination_edit.text(),
        )
        if selected:
            self.destination_edit.setText(selected)

    def _update_option_visibility(self) -> None:
        custom = (
            hasattr(self, "missing_combo")
            and self.missing_combo.currentData() == OutputMissingPolicy.CUSTOM.value
        )
        if hasattr(self, "custom_missing_edit"):
            self.custom_missing_edit.setEnabled(custom)
        if hasattr(self, "style_card"):
            self.style_card.setVisible(self.formatted_check.isChecked())

    def _apply_style_preset(self, name: str) -> None:
        presets = {
            "Environmental Technical": ("Aptos", 10, "#0F766E", "#ECFDF5"),
            "Clean Laboratory": ("Arial", 10, "#155E75", "#ECFEFF"),
            "Minimal": ("Aptos", 10, "#334155", "#F8FAFC"),
        }
        font, size, header, alternate = presets[name]
        self.font_edit.setText(font)
        self.font_size.setValue(size)
        self.header_fill.setText(header)
        self.alternate_fill.setText(alternate)

    def _populate_template_matches(self) -> None:
        self.template_combo.clear()
        if self._inspection is None:
            return
        matches = self._template_repository.matches(self._inspection.column_names)
        if not matches:
            self.template_combo.addItem("No schema-count matches", None)
            return
        for match in matches:
            self.template_combo.addItem(
                f"{match.record.name} • {match.label}",
                match.record.identifier,
            )

    def _save_template(self) -> None:
        if self._recipe is None:
            return
        name, accepted = QInputDialog.getText(self, "Save recipe template", "Template name")
        if not accepted:
            return
        try:
            style = self._build_plan().xlsx_style
            self._template_repository.save(name, self._recipe, style)
        except (ValueError, OSError) as error:
            QMessageBox.warning(self, "Save template", str(error))
            return
        self._populate_template_matches()
        self.status_label.setText("Template saved locally without measurement data.")

    def _selected_template(self) -> TemplateRecord | None:
        identifier = self.template_combo.currentData()
        if identifier is None:
            return None
        try:
            return self._template_repository.get(str(identifier))
        except (ValueError, OSError):
            return None

    def _review_selected_template(self) -> None:
        selected = self._selected_template()
        if selected is None:
            return
        box = QMessageBox(
            QMessageBox.Icon.Information,
            "Review recipe template",
            (
                f"{selected.name}\n\n"
                f"Mode: {selected.recipe.mode}\n"
                f"Expected columns: {len(selected.recipe.source.expected_columns)}\n"
                "No measurement records are stored."
            ),
            parent=self,
        )
        box.setDetailedText(selected.recipe.to_json())
        box.exec()

    def _ignore_selected_template(self) -> None:
        index = self.template_combo.currentIndex()
        if index >= 0 and self.template_combo.currentData() is not None:
            self.template_combo.removeItem(index)
            self.status_label.setText("Template ignored for this review session.")

    def _apply_selected_template(self) -> None:
        selected = self._selected_template()
        if selected is None:
            return
        if self._thread is not None:
            self.status_label.setText("Wait for the current operation before applying a template.")
            return
        self._apply_template_output_choices(selected)
        self.template_apply_requested.emit(selected.recipe, selected.style)

    def _apply_template_output_choices(self, selected: TemplateRecord) -> None:
        formats = set(selected.recipe.output.formats)
        self.csv_check.setChecked(OutputFormat.CSV in formats)
        self.plain_check.setChecked(OutputFormat.XLSX_PLAIN in formats)
        self.formatted_check.setChecked(OutputFormat.XLSX_FORMATTED in formats)
        self.missing_combo.setCurrentIndex(
            max(
                self.missing_combo.findData(selected.recipe.output.missing_policy.value),
                0,
            )
        )
        self.custom_missing_edit.setText(
            ""
            if selected.recipe.output.custom_missing_sentinel is None
            else str(selected.recipe.output.custom_missing_sentinel)
        )
        style = selected.style
        if self.style_preset.findText(style.name) < 0:
            self.style_preset.addItem(style.name)
        self.style_preset.setCurrentText(style.name)
        self.font_edit.setText(style.font_name)
        self.font_size.setValue(style.font_size)
        self.header_fill.setText(style.header_fill)
        self.alternate_fill.setText(style.alternating_fill)
        self.filter_check.setChecked(style.autofilter)
        self.freeze_check.setChecked(style.freeze_header)

    def _manage_templates(self) -> None:
        TemplateManagerDialog(self._template_repository, self).exec()
        self._populate_template_matches()


class TemplateManagerDialog(QDialog):
    """Explicit local template CRUD with confirmation before deletion."""

    def __init__(self, repository: TemplateRepository, parent: QWidget) -> None:
        super().__init__(parent)
        self._repository = repository
        self._records: tuple[TemplateRecord, ...] = ()
        self.setWindowTitle("Recipe templates")
        self.resize(760, 480)
        layout = QVBoxLayout(self)
        note = QLabel(
            "Templates contain schema and processing choices only—never measurement records. "
            "Review a recipe before applying its choices to another file."
        )
        note.setWordWrap(True)
        note.setProperty("role", "muted")
        layout.addWidget(note)
        content = QHBoxLayout()
        self.template_list = QListWidget()
        self.template_list.currentRowChanged.connect(self._review)
        content.addWidget(self.template_list, 1)
        self.review_text = QTextEdit()
        self.review_text.setReadOnly(True)
        content.addWidget(self.review_text, 2)
        layout.addLayout(content, 1)
        actions = QHBoxLayout()
        for label, handler in (
            ("Import…", self._import),
            ("Export…", self._export),
            ("Duplicate…", self._duplicate),
            ("Rename…", self._rename),
            ("Delete…", self._delete),
        ):
            button = QPushButton(label)
            button.clicked.connect(handler)
            actions.addWidget(button)
        actions.addStretch()
        close = QPushButton("Close")
        close.clicked.connect(self.accept)
        actions.addWidget(close)
        layout.addLayout(actions)
        self._refresh()

    def _refresh(self) -> None:
        try:
            self._records = self._repository.list()
        except (ValueError, OSError) as error:
            QMessageBox.warning(self, "Recipe templates", str(error))
            self._records = ()
        self.template_list.clear()
        self.template_list.addItems(tuple(record.name for record in self._records))
        if self._records:
            self.template_list.setCurrentRow(0)
        else:
            self.review_text.setPlainText("No local templates.")

    def _selected(self) -> TemplateRecord | None:
        row = self.template_list.currentRow()
        return self._records[row] if 0 <= row < len(self._records) else None

    def _review(self) -> None:
        selected = self._selected()
        self.review_text.setPlainText(selected.recipe.to_json() if selected else "")

    def _duplicate(self) -> None:
        selected = self._selected()
        if selected is None:
            return
        name, accepted = QInputDialog.getText(
            self,
            "Duplicate template",
            "New name",
            text=f"{selected.name} copy",
        )
        if accepted:
            self._perform(lambda: self._repository.duplicate(selected.identifier, name))

    def _rename(self) -> None:
        selected = self._selected()
        if selected is None:
            return
        name, accepted = QInputDialog.getText(
            self,
            "Rename template",
            "New name",
            text=selected.name,
        )
        if accepted:
            self._perform(lambda: self._repository.rename(selected.identifier, name))

    def _delete(self) -> None:
        selected = self._selected()
        if selected is None:
            return
        answer = QMessageBox.question(
            self,
            "Delete template",
            f"Delete '{selected.name}'? This local template file cannot be restored here.",
        )
        if answer is QMessageBox.StandardButton.Yes:
            self._perform(lambda: self._repository.delete(selected.identifier))

    def _import(self) -> None:
        selected, _ = QFileDialog.getOpenFileName(
            self,
            "Import GDTT template",
            "",
            "DTT template (*.json);;All files (*)",
        )
        if selected:
            self._perform(lambda: self._repository.import_file(Path(selected)))

    def _export(self) -> None:
        selected = self._selected()
        if selected is None:
            return
        destination = QFileDialog.getExistingDirectory(self, "Export template to folder")
        if destination:
            self._perform(
                lambda: self._repository.export_file(selected.identifier, Path(destination))
            )

    def _perform(self, operation: Callable[[], object]) -> None:
        try:
            operation()
        except (ValueError, OSError) as error:
            QMessageBox.warning(self, "Recipe templates", str(error))
        self._refresh()
