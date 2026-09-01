"""Optional sequential editor for one immutable Phase 5 column draft at a time.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from dataclasses import replace
from typing import cast

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from data_transform_tool.app.reformat_configuration import (
    ReformatDraft,
    TransformChoice,
)
from data_transform_tool.app.reformat_preview import proposed_column_samples
from data_transform_tool.datetime.profiles import DateTimeProfileRegistry
from data_transform_tool.io.models import FileInspection, SemanticType


class SequentialColumnWizard(QDialog):
    """Edit all source columns sequentially and return one updated draft."""

    def __init__(
        self,
        inspection: FileInspection,
        draft: ReformatDraft,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Sequential column wizard")
        self.resize(640, 520)
        self._inspection = inspection
        self.result_draft = draft
        self._index = 0

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 22)
        eyebrow = QLabel("OPTIONAL SEQUENTIAL WIZARD")
        eyebrow.setProperty("role", "eyebrow")
        root.addWidget(eyebrow)
        self.title_label = QLabel()
        self.title_label.setProperty("role", "dialogTitle")
        root.addWidget(self.title_label)
        self.progress_label = QLabel()
        self.progress_label.setProperty("role", "muted")
        root.addWidget(self.progress_label)

        form = QFormLayout()
        self.export_check = QCheckBox("Include this field in output")
        form.addRow("Export", self.export_check)
        self.output_name_edit = QLineEdit()
        form.addRow("Output name", self.output_name_edit)
        self.output_type_combo = QComboBox()
        for item in SemanticType:
            self.output_type_combo.addItem(item.value, item)
        form.addRow("Output type", self.output_type_combo)
        self.input_profile_combo = QComboBox()
        self.output_profile_combo = QComboBox()
        _populate_profiles(self.input_profile_combo, "Auto / unchanged")
        _populate_profiles(self.output_profile_combo, "As source")
        form.addRow("Input profile", self.input_profile_combo)
        form.addRow("Output format", self.output_profile_combo)
        self.transform_combo = QComboBox()
        for label, value in (
            ("Keep as is", TransformChoice.KEEP),
            ("Round numeric to 2 decimals", TransformChoice.ROUND_2),
            ("Convert ppm to ppb", TransformChoice.PPM_TO_PPB),
            ("Convert ppb to ppm", TransformChoice.PPB_TO_PPM),
        ):
            self.transform_combo.addItem(label, value)
        form.addRow("Transformation", self.transform_combo)
        root.addLayout(form)

        root.addWidget(QLabel("Live samples"))
        self.samples_label = QLabel()
        self.samples_label.setWordWrap(True)
        self.samples_label.setProperty("role", "samplePanel")
        root.addWidget(self.samples_label, 1)
        self.status_label = QLabel()
        self.status_label.setProperty("role", "muted")
        root.addWidget(self.status_label)

        actions = QHBoxLayout()
        self.previous_button = QPushButton("← Previous field")
        self.previous_button.clicked.connect(self._previous)
        actions.addWidget(self.previous_button)
        self.next_button = QPushButton("Next field →")
        self.next_button.clicked.connect(self._next)
        actions.addWidget(self.next_button)
        actions.addStretch()
        cancel = QPushButton("Cancel")
        cancel.setProperty("role", "ghost")
        cancel.clicked.connect(self.reject)
        actions.addWidget(cancel)
        self.finish_button = QPushButton("Apply wizard changes")
        self.finish_button.setProperty("role", "primary")
        self.finish_button.clicked.connect(self._finish)
        actions.addWidget(self.finish_button)
        root.addLayout(actions)
        self._load_current()

    def _save_current(self) -> bool:
        output_name = self.output_name_edit.text().strip()
        if not output_name:
            self.status_label.setText("Output name cannot be blank.")
            return False
        column = self.result_draft.columns[self._index]
        updated = replace(
            column,
            export=self.export_check.isChecked(),
            output_name=output_name,
            output_type=SemanticType(str(self.output_type_combo.currentData())),
            input_profile=cast(str | None, self.input_profile_combo.currentData()),
            output_profile=cast(str | None, self.output_profile_combo.currentData()),
            transform=TransformChoice(str(self.transform_combo.currentData())),
        )
        self.result_draft = self.result_draft.update_column(updated)
        self.status_label.clear()
        return True

    def _load_current(self) -> None:
        column = self.result_draft.columns[self._index]
        self.title_label.setText(column.source_name)
        self.progress_label.setText(
            f"Field {self._index + 1} of {len(self.result_draft.columns)}  •  "
            f"Detected {column.detected_type.value} at {column.confidence:.0%} confidence"
        )
        self.export_check.setChecked(column.export)
        self.output_name_edit.setText(column.output_name)
        self.output_type_combo.setCurrentIndex(self.output_type_combo.findData(column.output_type))
        self.input_profile_combo.setCurrentIndex(
            max(self.input_profile_combo.findData(column.input_profile), 0)
        )
        self.output_profile_combo.setCurrentIndex(
            max(self.output_profile_combo.findData(column.output_profile), 0)
        )
        self.transform_combo.setCurrentIndex(self.transform_combo.findData(column.transform))
        samples = proposed_column_samples(self._inspection, self.result_draft, column.source_name)
        self.samples_label.setText("\n".join(samples) or "No non-null samples are available.")
        self.previous_button.setEnabled(self._index > 0)
        self.next_button.setEnabled(self._index + 1 < len(self.result_draft.columns))

    def _previous(self) -> None:
        if self._save_current() and self._index > 0:
            self._index -= 1
            self._load_current()

    def _next(self) -> None:
        if self._save_current() and self._index + 1 < len(self.result_draft.columns):
            self._index += 1
            self._load_current()

    def _finish(self) -> None:
        if self._save_current():
            self.accept()


def _populate_profiles(combo: QComboBox, default_label: str) -> None:
    combo.addItem(default_label, None)
    for profile in DateTimeProfileRegistry.default().all():
        combo.addItem(
            f"{profile.group}  •  {profile.name}  ({profile.display_pattern})",
            profile.profile_id,
        )
