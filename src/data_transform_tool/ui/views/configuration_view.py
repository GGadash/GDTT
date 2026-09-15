"""Phase 5 mapping grid, detailed controls, live preview, and summary UI.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from dataclasses import replace
from typing import cast

from PySide6.QtCore import QModelIndex, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QTableView,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from data_transform_tool.app.reformat_configuration import (
    ConfigurationSession,
    GapBehaviorChoice,
    ReformatDraft,
    TimezoneSourceMode,
    TransformChoice,
    build_transformation_recipe,
    configuration_summary,
    create_reformat_draft,
    validate_reformat_draft,
)
from data_transform_tool.app.reformat_preview import (
    build_proposed_preview,
    proposed_column_samples,
)
from data_transform_tool.datetime.models import TimestampRole
from data_transform_tool.io.models import FileInspection, SemanticType
from data_transform_tool.transformation.recipe import OutputMissingPolicy
from data_transform_tool.ui.dialogs.column_wizard import SequentialColumnWizard
from data_transform_tool.ui.models import (
    ConfigurationFilterProxyModel,
    MappingTableModel,
    ProposedPreviewTableModel,
)
from data_transform_tool.ui.widgets.field_controls import ProfileCombo, bulk_buttons, fill_zones
from data_transform_tool.validation.numeric import InvalidNumericPolicy
from data_transform_tool.validation.rows import RemoveNullMode


class ReformatConfigurationView(QWidget):
    """Edit one versioned recipe draft with progressive disclosure."""

    back_requested = Signal()
    configuration_ready = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self._inspection: FileInspection | None = None
        self._session: ConfigurationSession | None = None
        self._selected_source: str | None = None
        self._refreshing = False

        root = QVBoxLayout(self)
        root.setContentsMargins(30, 22, 30, 22)
        root.setSpacing(12)
        root.addLayout(self._create_title_row())
        root.addWidget(self._create_stepper())
        root.addLayout(self._create_toolbar())
        root.addWidget(self._create_workspace(), 1)
        root.addLayout(self._create_action_row())
        self.setEnabled(False)

    @property
    def draft(self) -> ReformatDraft | None:
        return self._session.current if self._session is not None else None

    def set_inspection(self, inspection: FileInspection) -> None:
        self._inspection = inspection
        self._session = ConfigurationSession(create_reformat_draft(inspection))
        self._selected_source = inspection.column_names[0] if inspection.column_names else None
        self.setEnabled(True)
        self._refresh_from_session()

    def apply_template(self, draft: ReformatDraft) -> None:
        """Apply one reviewed template as a reversible draft change."""
        if self._session is None:
            raise ValueError("Load a source inspection before applying a template.")
        self._session.apply(draft)
        self._selected_source = draft.columns[0].source_name if draft.columns else None
        self._refresh_from_session()
        self.status_label.setText(
            "Template choices applied. Review every confirmation before continuing."
        )

    def _create_title_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        back = QPushButton("←  Back to inspection")
        back.setProperty("role", "ghost")
        back.clicked.connect(self.back_requested)
        row.addWidget(back)
        titles = QVBoxLayout()
        eyebrow = QLabel("REFORMAT / TRANSFORM  •  PHASE 5")
        eyebrow.setProperty("role", "eyebrow")
        title = QLabel("Configure fields and inspect the proposed output")
        title.setProperty("role", "sectionTitle")
        titles.addWidget(eyebrow)
        titles.addWidget(title)
        row.addLayout(titles)
        row.addStretch()
        self.readiness_badge = QLabel("Configuration not loaded")
        self.readiness_badge.setProperty("role", "badge")
        row.addWidget(self.readiness_badge)
        return row

    def _create_stepper(self) -> QFrame:
        stepper = QFrame()
        stepper.setProperty("role", "modeCard")
        layout = QHBoxLayout(stepper)
        layout.setContentsMargins(18, 10, 18, 10)
        names = ("1  Mode", "2  File", "3  Inspect", "4  Configure", "5  Preview", "6  Export")
        for index, name in enumerate(names):
            label = QLabel(name)
            label.setProperty("role", "badge" if index in {3, 4} else "muted")
            layout.addWidget(label)
            if index < len(names) - 1:
                separator = QLabel("→")
                separator.setProperty("role", "muted")
                layout.addWidget(separator)
        layout.addStretch()
        return stepper

    def _create_toolbar(self) -> QHBoxLayout:
        row = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search any field, type, profile, or warning…")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.setMinimumWidth(290)
        row.addWidget(self.search_edit)
        self.group_combo = QComboBox()
        for label, group_value in (
            ("All fields", "all"),
            ("Exported", "exported"),
            ("Needs review", "warnings"),
            ("Date / time", "temporal"),
            ("Numeric", "numeric"),
        ):
            self.group_combo.addItem(label, group_value)
        row.addWidget(self.group_combo)
        for label, selected in (("Select all", True), ("Deselect all", False)):
            button = QPushButton(label)
            button.clicked.connect(
                lambda _checked=False, value=selected: self._set_all_export(value)
            )
            row.addWidget(button)
        wizard = QPushButton("Sequential wizard…")
        wizard.clicked.connect(self._open_wizard)
        row.addWidget(wizard)
        row.addStretch()
        self.undo_button = QPushButton("Undo")
        self.undo_button.clicked.connect(self._undo)
        row.addWidget(self.undo_button)
        self.redo_button = QPushButton("Redo")
        self.redo_button.clicked.connect(self._redo)
        row.addWidget(self.redo_button)
        return row

    def _create_workspace(self) -> QSplitter:
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.workspace_splitter = splitter
        splitter.setChildrenCollapsible(False)
        self.main_tabs = QTabWidget()
        self.main_tabs.addTab(self._create_mapping_panel(), "Field mapping")
        self.main_tabs.addTab(self._create_preview_panel(), "Proposed output preview")
        splitter.addWidget(self.main_tabs)
        splitter.addWidget(self._create_editor_scroll())
        splitter.setStretchFactor(0, 1)
        splitter.setSizes([900, 520])
        return splitter

    def _create_mapping_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        hint = QLabel(
            "Export, Input, and Status stay frozen on the left. Double-click a row for "
            "detailed configuration; Export and output names are editable in place."
        )
        hint.setProperty("role", "muted")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        self.mapping_model = MappingTableModel()
        self.mapping_proxy = ConfigurationFilterProxyModel()
        self.mapping_proxy.setSourceModel(self.mapping_model)
        self.search_edit.textChanged.connect(self.mapping_proxy.setFilterFixedString)
        self.group_combo.currentIndexChanged.connect(
            lambda: self.mapping_proxy.set_group(str(self.group_combo.currentData()))
        )
        self.mapping_model.edit_requested.connect(self._on_mapping_edit)

        tables = QSplitter(Qt.Orientation.Horizontal)
        self.mapping_splitter = tables
        tables.setChildrenCollapsible(False)
        self.frozen_mapping_table = self._mapping_table()
        self.mapping_table = self._mapping_table()
        for table in (self.frozen_mapping_table, self.mapping_table):
            table.setModel(self.mapping_proxy)
            table.clicked.connect(self._select_mapping_index)
            table.doubleClicked.connect(self._select_mapping_index)
        for column in range(len(MappingTableModel.HEADERS)):
            self.frozen_mapping_table.setColumnHidden(column, column > 2)
            self.mapping_table.setColumnHidden(column, column <= 2)
        self.frozen_mapping_table.setMinimumWidth(140)
        self.mapping_table.verticalHeader().hide()
        self.frozen_mapping_table.verticalScrollBar().valueChanged.connect(
            self.mapping_table.verticalScrollBar().setValue
        )
        self.mapping_table.verticalScrollBar().valueChanged.connect(
            self.frozen_mapping_table.verticalScrollBar().setValue
        )
        tables.addWidget(self.frozen_mapping_table)
        tables.addWidget(self.mapping_table)
        tables.setSizes([300, 600])
        layout.addWidget(tables, 1)
        return panel

    def _mapping_table(self) -> QTableView:
        table = QTableView()
        table.setAlternatingRowColors(True)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        table.setSortingEnabled(True)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        return table

    def _create_preview_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        self.preview_notice = QLabel()
        self.preview_notice.setWordWrap(True)
        self.preview_notice.setProperty("role", "muted")
        layout.addWidget(self.preview_notice)
        self.preview_table = QTableView()
        self.preview_model = ProposedPreviewTableModel()
        self.preview_table.setModel(self.preview_model)
        self.preview_table.setAlternatingRowColors(True)
        self.preview_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        layout.addWidget(self.preview_table, 1)
        return panel

    def _create_editor_scroll(self) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setMinimumWidth(280)
        content = QWidget()
        layout = QVBoxLayout(content)
        self.editor_tabs = QTabWidget()
        self.editor_tabs.addTab(self._create_column_editor(), "Selected field")
        self.editor_tabs.addTab(self._create_gap_editor(), "Gaps && missing")
        self.editor_tabs.addTab(self._create_summary_panel(), "Summary")
        for combo in content.findChildren(QComboBox):
            combo.setSizeAdjustPolicy(
                QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
            )
            combo.setMinimumContentsLength(12)
            combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.editor_tabs)
        for form in content.findChildren(QFormLayout):
            form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        scroll.setWidget(content)
        return scroll

    def _create_column_editor(self) -> QGroupBox:
        group = QGroupBox("Selected field")
        layout = QVBoxLayout(group)
        self.selected_column_label = QLabel("Select a field")
        self.selected_column_label.setProperty("role", "cardTitle")
        layout.addWidget(self.selected_column_label)
        self.column_detection_label = QLabel()
        self.column_detection_label.setProperty("role", "muted")
        self.column_detection_label.setWordWrap(True)
        layout.addWidget(self.column_detection_label)
        form = QFormLayout()
        self.export_check = QCheckBox("Include in output")
        form.addRow("Export", self.export_check)
        self.output_name_edit = QLineEdit()
        self.output_type_combo = QComboBox()
        for item in SemanticType:
            self.output_type_combo.addItem(item.value, item)
        self.transform_combo = QComboBox()
        for label, transform_value in (
            ("Keep as is", TransformChoice.KEEP),
            ("Round to 2 decimals", TransformChoice.ROUND_2),
            ("ppm → ppb", TransformChoice.PPM_TO_PPB),
            ("ppb → ppm", TransformChoice.PPB_TO_PPM),
        ):
            self.transform_combo.addItem(label, transform_value)
        self.input_profile_combo = ProfileCombo(input_profile=True)
        self.output_profile_combo = ProfileCombo()
        self.input_profile_combo.load(None, "text")
        self.output_profile_combo.load(None, "text")
        form.addRow(QLabel("Input · interpreting source values"))
        form.addRow("Input profile", self.input_profile_combo)
        self.input_decimal = QComboBox()
        self.input_decimal.addItems([".", ","])
        self.input_decimal.setToolTip(
            "Decimal separator in source numbers. Select a grouped profile for thousands "
            "separators; no automatic locale guessing."
        )
        form.addRow("Input decimal separator", self.input_decimal)
        form.addRow(QLabel("Output · formatting exported values"))
        form.addRow("Output name", self.output_name_edit)
        form.addRow("Output type", self.output_type_combo)
        form.addRow("Transformation", self.transform_combo)
        form.addRow("Output format", self.output_profile_combo)
        self.output_decimal = QComboBox()
        self.output_decimal.addItems([".", ","])
        self.output_decimal.setToolTip(
            "Separator for preview and CSV. Numeric Excel cells follow Excel/OS regional settings."
        )
        form.addRow("Output decimal separator", self.output_decimal)
        self.preserve_precision = QCheckBox("Keep full numeric precision")
        self.preserve_precision.setToolTip(
            "Off: round exported values to the mask. On: retain full CSV/Excel values; "
            "Excel displays the selected precision. Excel's native numeric precision limit "
            "still applies."
        )
        form.addRow("Numeric export", self.preserve_precision)
        form.addRow(QLabel("Time zones and gap-row values"))
        self.timestamp_role_combo = QComboBox()
        for role in TimestampRole:
            self.timestamp_role_combo.addItem(role.value.title(), role)
        form.addRow("Timestamp role", self.timestamp_role_combo)
        self.timezone_mode_combo = QComboBox()
        for label, timezone_value in (
            ("No conversion", TimezoneSourceMode.NONE),
            ("Embedded offset", TimezoneSourceMode.EMBEDDED),
            ("Fixed zone / offset", TimezoneSourceMode.FIXED_IANA),
            ("IANA zone from field", TimezoneSourceMode.IANA_COLUMN),
            ("Manual UTC offset", TimezoneSourceMode.MANUAL_OFFSET),
        ):
            self.timezone_mode_combo.addItem(label, timezone_value)
        form.addRow("Source timezone", self.timezone_mode_combo)
        self.timezone_source_combo = QComboBox()
        self.timezone_source_combo.setEditable(True)
        form.addRow("Source value", self.timezone_source_combo)
        self.target_timezone_combo = QComboBox()
        self.target_timezone_combo.setEditable(True)
        self.target_timezone_combo.addItem("No target conversion", "")
        for zone in ("UTC", "Asia/Colombo", "Asia/Kolkata", "Europe/London", "America/New_York"):
            self.target_timezone_combo.addItem(zone, zone)
        fill_zones(self.target_timezone_combo)
        self.target_timezone_combo.setEditText("")
        target_editor = self.target_timezone_combo.lineEdit()
        assert target_editor is not None
        target_editor.setPlaceholderText("No conversion")
        form.addRow("Target timezone", self.target_timezone_combo)
        zone_help = QLabel(
            "UTC · Asia/Colombo (UTC+05:30 / +5.5 hours) · Custom IANA zone; "
            "manual source offset is also available."
        )
        zone_help.setWordWrap(True)
        form.addRow(zone_help)
        self.gap_behavior_combo = QComboBox()
        for label, gap_value in (
            ("Null", GapBehaviorChoice.NULL),
            ("Carry Stable Metadata", GapBehaviorChoice.CARRY_STABLE),
            ("Fixed Value", GapBehaviorChoice.FIXED_VALUE),
            ("Derived from Timestamp", GapBehaviorChoice.DERIVED_FROM_TIMESTAMP),
        ):
            self.gap_behavior_combo.addItem(label, gap_value)
        form.addRow("Generated gap row", self.gap_behavior_combo)
        self.gap_fixed_edit = QLineEdit()
        form.addRow("Fixed value", self.gap_fixed_edit)
        layout.addLayout(form)
        layout.addWidget(QLabel("Derive interval fields"))
        derived = QHBoxLayout()
        self.derive_start_check = QCheckBox("Start")
        self.derive_mid_check = QCheckBox("Mid")
        self.derive_end_check = QCheckBox("End")
        for check in (self.derive_start_check, self.derive_mid_check, self.derive_end_check):
            derived.addWidget(check)
        layout.addLayout(derived)
        layout.addLayout(
            bulk_buttons(
                (self.derive_start_check, self.derive_mid_check, self.derive_end_check),
                self._commit_column_controls,
            )
        )
        layout.addWidget(QLabel("Live samples"))
        self.live_samples_label = QLabel()
        self.live_samples_label.setWordWrap(True)
        self.live_samples_label.setProperty("role", "samplePanel")
        layout.addWidget(self.live_samples_label)
        self._connect_column_controls()
        return group

    def _create_gap_editor(self) -> QGroupBox:
        group = QGroupBox("Gap and missing-value options")
        layout = QVBoxLayout(group)
        self.gap_fill_check = QCheckBox("Insert Missing Time Rows")
        self.gap_fill_check.setChecked(True)
        layout.addWidget(self.gap_fill_check)
        scope = QLabel(
            "Enabled by default. Generated measurements remain internally null; the output "
            "representation below applies to every missing measurement."
        )
        scope.setProperty("role", "muted")
        scope.setWordWrap(True)
        scope.setMaximumWidth(420)
        layout.addWidget(scope)
        form = QFormLayout()
        self.timestamp_combo = QComboBox()
        form.addRow("Primary timestamp", self.timestamp_combo)
        self.timestamp_confirm_check = QCheckBox("Confirmed")
        form.addRow("Timestamp decision", self.timestamp_confirm_check)
        self.interval_combo = QComboBox()
        for label, seconds in (
            ("1 minute", 60.0),
            ("5 minutes", 300.0),
            ("15 minutes", 900.0),
            ("1 hour", 3600.0),
            ("Custom", None),
        ):
            self.interval_combo.addItem(label, seconds)
        form.addRow("Expected interval", self.interval_combo)
        self.custom_interval_spin = QDoubleSpinBox()
        self.custom_interval_spin.setRange(0.001, 31_536_000)
        self.custom_interval_spin.setDecimals(3)
        self.custom_interval_spin.setSuffix(" seconds")
        form.addRow("Custom interval", self.custom_interval_spin)
        self.custom_interval_label = cast(QLabel, form.labelForField(self.custom_interval_spin))
        self.interval_confirm_check = QCheckBox("Confirmed")
        form.addRow("Interval decision", self.interval_confirm_check)
        self.allow_reorder_check = QCheckBox("Allow explicit chronological reordering")
        form.addRow("Ordering", self.allow_reorder_check)
        self.missing_policy_combo = QComboBox()
        for label, missing_value in (
            ("True Null / blank (recommended)", OutputMissingPolicy.TRUE_NULL),
            ("N/A", OutputMissingPolicy.NA),
            ("-999", OutputMissingPolicy.MINUS_999),
            ("Custom sentinel", OutputMissingPolicy.CUSTOM),
        ):
            self.missing_policy_combo.addItem(label, missing_value)
        form.addRow("Missing output", self.missing_policy_combo)
        self.custom_sentinel_edit = QLineEdit()
        form.addRow("Custom sentinel", self.custom_sentinel_edit)
        self.custom_sentinel_label = cast(QLabel, form.labelForField(self.custom_sentinel_edit))
        self.invalid_numeric_combo = QComboBox()
        for label, invalid_value in (
            ("Null and continue (recommended)", InvalidNumericPolicy.NULL_AND_CONTINUE),
            ("Inspect affected rows", InvalidNumericPolicy.INSPECT),
            ("Stop processing", InvalidNumericPolicy.STOP),
            ("Preserve source text separately", InvalidNumericPolicy.PRESERVE_SOURCE),
        ):
            self.invalid_numeric_combo.addItem(label, invalid_value)
        form.addRow("Invalid numerics", self.invalid_numeric_combo)
        self.remove_empty_check = QCheckBox("Remove matching empty rows")
        form.addRow("Remove rows", self.remove_empty_check)
        self.remove_mode_combo = QComboBox()
        for label, remove_value in (
            ("All measurement fields missing", RemoveNullMode.ALL_MEASUREMENTS_MISSING),
            ("All selected fields missing", RemoveNullMode.ALL_SELECTED_MISSING),
            ("Any required field missing", RemoveNullMode.ANY_REQUIRED_MISSING),
            ("Selected subset missing", RemoveNullMode.SELECTED_SUBSET_MISSING),
            ("Below present-value threshold", RemoveNullMode.BELOW_PRESENT_THRESHOLD),
        ):
            self.remove_mode_combo.addItem(label, remove_value)
        form.addRow("Removal rule", self.remove_mode_combo)
        layout.addLayout(form)
        layout.addWidget(QLabel("Detected input missing markers — confirm each explicitly"))
        self.missing_marker_list = QListWidget()
        self.missing_marker_list.setMaximumHeight(104)
        layout.addWidget(self.missing_marker_list)
        layout.addLayout(bulk_buttons(self.missing_marker_list, self._commit_global_controls))
        self._connect_global_controls()
        return group

    def _create_summary_panel(self) -> QGroupBox:
        group = QGroupBox("Transformation summary")
        layout = QVBoxLayout(group)
        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)
        self.validation_label = QLabel()
        self.validation_label.setWordWrap(True)
        self.validation_label.setProperty("role", "muted")
        layout.addWidget(self.validation_label)
        return group

    def _create_action_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        self.status_label = QLabel("Load an inspection to configure it.")
        self.status_label.setWordWrap(True)
        self.status_label.setProperty("role", "muted")
        row.addWidget(self.status_label, 1)
        reset = QPushButton("Reset")
        reset.clicked.connect(self._reset)
        row.addWidget(reset)
        back = QPushButton("Back")
        back.setProperty("role", "ghost")
        back.clicked.connect(self.back_requested)
        row.addWidget(back)
        review = QPushButton("Review configuration →")
        review.setProperty("role", "primary")
        review.clicked.connect(self._review_configuration)
        row.addWidget(review)
        return row

    def _connect_column_controls(self) -> None:
        self.input_decimal.currentIndexChanged.connect(self._commit_column_controls)
        self.output_decimal.currentIndexChanged.connect(self._commit_column_controls)
        self.preserve_precision.toggled.connect(self._commit_column_controls)
        for profile_control in (self.input_profile_combo, self.output_profile_combo):
            editor = profile_control.lineEdit()
            assert editor is not None
            editor.editingFinished.connect(self._commit_column_controls)
        self.export_check.toggled.connect(self._commit_column_controls)
        self.output_name_edit.editingFinished.connect(self._commit_column_controls)
        combos = (
            self.output_type_combo,
            self.transform_combo,
            self.input_profile_combo,
            self.output_profile_combo,
            self.timestamp_role_combo,
            self.timezone_mode_combo,
            self.timezone_source_combo,
            self.target_timezone_combo,
            self.gap_behavior_combo,
        )
        for combo in combos:
            combo.currentIndexChanged.connect(self._commit_column_controls)
        self.timezone_source_combo.editTextChanged.connect(self._commit_column_controls)
        self.target_timezone_combo.editTextChanged.connect(self._commit_column_controls)
        self.gap_fixed_edit.editingFinished.connect(self._commit_column_controls)
        for check in (self.derive_start_check, self.derive_mid_check, self.derive_end_check):
            check.toggled.connect(self._commit_column_controls)

    def _connect_global_controls(self) -> None:
        checks = (
            self.gap_fill_check,
            self.timestamp_confirm_check,
            self.interval_confirm_check,
            self.allow_reorder_check,
            self.remove_empty_check,
        )
        for check in checks:
            check.toggled.connect(self._commit_global_controls)
        combos = (
            self.timestamp_combo,
            self.interval_combo,
            self.missing_policy_combo,
            self.invalid_numeric_combo,
            self.remove_mode_combo,
        )
        for combo in combos:
            combo.currentIndexChanged.connect(self._commit_global_controls)
        self.custom_interval_spin.valueChanged.connect(self._commit_global_controls)
        self.custom_sentinel_edit.editingFinished.connect(self._commit_global_controls)
        self.missing_marker_list.itemChanged.connect(self._commit_global_controls)

    def _commit_column_controls(self) -> None:
        if self._refreshing or self._session is None or self._selected_source is None:
            return
        current = self._session.current.column(self._selected_source)
        self.input_profile_combo.decimal = self.input_decimal.currentText()
        self.output_profile_combo.decimal = self.output_decimal.currentText()
        self.output_profile_combo.preserve = self.preserve_precision.isChecked()
        try:
            input_profile = self.input_profile_combo.profile()
            output_profile = self.output_profile_combo.profile()
        except ValueError as error:
            self.status_label.setText(str(error))
            return
        output_type = SemanticType(str(self.output_type_combo.currentData()))
        transform = TransformChoice(str(self.transform_combo.currentData()))
        if output_type != current.output_type:
            numeric = output_type in {SemanticType.INTEGER, SemanticType.DECIMAL}
            input_profile = None
            output_profile = None
            if not numeric:
                transform = TransformChoice.KEEP
        updated = replace(
            current,
            export=self.export_check.isChecked(),
            output_name=self.output_name_edit.text().strip() or current.output_name,
            output_type=output_type,
            input_profile=input_profile,
            output_profile=output_profile,
            transform=transform,
            timestamp_role=TimestampRole(str(self.timestamp_role_combo.currentData())),
            timezone_source_mode=TimezoneSourceMode(str(self.timezone_mode_combo.currentData())),
            timezone_source_value=self.timezone_source_combo.currentText().strip() or None,
            target_timezone=self.target_timezone_combo.currentText().strip() or None,
            derive_start=self.derive_start_check.isChecked(),
            derive_midpoint=self.derive_mid_check.isChecked(),
            derive_end=self.derive_end_check.isChecked(),
            gap_behavior=GapBehaviorChoice(str(self.gap_behavior_combo.currentData())),
            gap_fixed_value=self.gap_fixed_edit.text() or None,
        )
        self._apply(self._session.current.update_column(updated))

    def _commit_global_controls(self) -> None:
        if self._refreshing or self._session is None:
            return
        interval_data = cast(float | None, self.interval_combo.currentData())
        interval = interval_data if interval_data is not None else self.custom_interval_spin.value()
        confirmed_markers = tuple(
            self.missing_marker_list.item(index).text()
            for index in range(self.missing_marker_list.count())
            if self.missing_marker_list.item(index).checkState() == Qt.CheckState.Checked
        )
        draft = replace(
            self._session.current,
            confirmed_missing_markers=confirmed_markers,
            gap_fill_enabled=self.gap_fill_check.isChecked(),
            timestamp_column=cast(str | None, self.timestamp_combo.currentData()),
            timestamp_confirmed=self.timestamp_confirm_check.isChecked(),
            interval_seconds=interval,
            interval_confirmed=self.interval_confirm_check.isChecked(),
            allow_reorder=self.allow_reorder_check.isChecked(),
            output_missing_policy=OutputMissingPolicy(str(self.missing_policy_combo.currentData())),
            custom_missing_sentinel=self.custom_sentinel_edit.text().strip() or None,
            invalid_numeric_policy=InvalidNumericPolicy(
                str(self.invalid_numeric_combo.currentData())
            ),
            remove_empty_enabled=self.remove_empty_check.isChecked(),
            remove_empty_mode=RemoveNullMode(str(self.remove_mode_combo.currentData())),
        )
        self._apply(draft)

    def _apply(self, draft: ReformatDraft) -> None:
        if self._session is not None and self._session.apply(draft):
            self._refresh_from_session()

    def _refresh_from_session(self) -> None:
        if self._session is None or self._inspection is None:
            return
        self._refreshing = True
        draft = self._session.current
        self.mapping_model.set_draft(draft)
        self.undo_button.setEnabled(self._session.can_undo)
        self.redo_button.setEnabled(self._session.can_redo)
        self.timestamp_combo.clear()
        self.timestamp_combo.addItem("Choose timestamp…", None)
        for column in draft.columns:
            self.timestamp_combo.addItem(column.output_name, column.source_name)
        self.timestamp_combo.setCurrentIndex(
            max(self.timestamp_combo.findData(draft.timestamp_column), 0)
        )
        self.timestamp_confirm_check.setChecked(draft.timestamp_confirmed)
        self.gap_fill_check.setChecked(draft.gap_fill_enabled)
        interval_index = self.interval_combo.findData(draft.interval_seconds)
        self.interval_combo.setCurrentIndex(
            interval_index if interval_index >= 0 else self.interval_combo.count() - 1
        )
        if draft.interval_seconds is not None:
            self.custom_interval_spin.setValue(draft.interval_seconds)
        custom_interval_visible = self.interval_combo.currentData() is None
        self.custom_interval_spin.setVisible(custom_interval_visible)
        self.custom_interval_label.setVisible(custom_interval_visible)
        self.interval_confirm_check.setChecked(draft.interval_confirmed)
        self.allow_reorder_check.setChecked(draft.allow_reorder)
        self.missing_policy_combo.setCurrentIndex(
            self.missing_policy_combo.findData(draft.output_missing_policy)
        )
        self.custom_sentinel_edit.setText(
            "" if draft.custom_missing_sentinel is None else str(draft.custom_missing_sentinel)
        )
        custom_sentinel_visible = draft.output_missing_policy is OutputMissingPolicy.CUSTOM
        self.custom_sentinel_edit.setVisible(custom_sentinel_visible)
        self.custom_sentinel_label.setVisible(custom_sentinel_visible)
        self.invalid_numeric_combo.setCurrentIndex(
            self.invalid_numeric_combo.findData(draft.invalid_numeric_policy)
        )
        self.remove_empty_check.setChecked(draft.remove_empty_enabled)
        self.remove_mode_combo.setCurrentIndex(
            self.remove_mode_combo.findData(draft.remove_empty_mode)
        )
        self.remove_mode_combo.setEnabled(draft.remove_empty_enabled)
        self._refresh_missing_markers(draft)
        if self._selected_source is None and draft.columns:
            self._selected_source = draft.columns[0].source_name
        self._refresh_column_editor()
        self._refresh_preview_and_summary(draft)
        self._refreshing = False

    def _refresh_missing_markers(self, draft: ReformatDraft) -> None:
        self.missing_marker_list.clear()
        for marker in draft.detected_missing_markers:
            item = QListWidgetItem(marker)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            state = (
                Qt.CheckState.Checked
                if marker in draft.confirmed_missing_markers
                else Qt.CheckState.Unchecked
            )
            item.setCheckState(state)
            self.missing_marker_list.addItem(item)
        if not draft.detected_missing_markers:
            item = QListWidgetItem("No likely markers detected")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.missing_marker_list.addItem(item)

    def _refresh_column_editor(self) -> None:
        if self._session is None or self._inspection is None or self._selected_source is None:
            return
        column = self._session.current.column(self._selected_source)
        self.selected_column_label.setText(column.source_name)
        self.column_detection_label.setText(
            f"Detected {column.detected_type.value} at {column.confidence:.0%} confidence  •  "
            f"{column.missing_percent:.2f}% missing"
        )
        self.export_check.setChecked(column.export)
        self.output_name_edit.setText(column.output_name)
        self.output_type_combo.setCurrentIndex(self.output_type_combo.findData(column.output_type))
        self.transform_combo.setCurrentIndex(self.transform_combo.findData(column.transform))
        self.input_profile_combo.load(column.input_profile, column.output_type.value)
        self.output_profile_combo.load(column.output_profile, column.output_type.value)
        self.input_decimal.setCurrentText(self.input_profile_combo.decimal)
        self.output_decimal.setCurrentText(self.output_profile_combo.decimal)
        self.preserve_precision.setChecked(self.output_profile_combo.preserve)
        for control in (self.output_decimal, self.preserve_precision):
            control.setEnabled(column.is_numeric)
        self.transform_combo.clear()
        self.transform_combo.addItem("Keep as is", TransformChoice.KEEP)
        if column.is_numeric:
            for label, transform in (
                ("Round to 2 decimals", TransformChoice.ROUND_2),
                ("ppm → ppb", TransformChoice.PPM_TO_PPB),
                ("ppb → ppm", TransformChoice.PPB_TO_PPM),
            ):
                self.transform_combo.addItem(label, transform)
        self.transform_combo.setCurrentIndex(
            max(0, self.transform_combo.findData(column.transform))
        )
        self.timestamp_role_combo.setCurrentIndex(
            self.timestamp_role_combo.findData(column.timestamp_role)
        )
        self.timezone_mode_combo.setCurrentIndex(
            self.timezone_mode_combo.findData(column.timezone_source_mode)
        )
        if column.timezone_source_mode is TimezoneSourceMode.IANA_COLUMN:
            self.timezone_source_combo.clear()
            self.timezone_source_combo.addItems(list(self._inspection.column_names))
        else:
            fill_zones(self.timezone_source_combo)
        self.timezone_source_combo.setCurrentText(column.timezone_source_value or "")
        self.target_timezone_combo.setCurrentText(column.target_timezone or "")
        self.derive_start_check.setChecked(column.derive_start)
        self.derive_mid_check.setChecked(column.derive_midpoint)
        self.derive_end_check.setChecked(column.derive_end)
        self.gap_behavior_combo.setCurrentIndex(
            self.gap_behavior_combo.findData(column.gap_behavior)
        )
        self.gap_fixed_edit.setText(
            "" if column.gap_fixed_value is None else str(column.gap_fixed_value)
        )
        self.gap_fixed_edit.setVisible(column.gap_behavior is GapBehaviorChoice.FIXED_VALUE)
        samples = proposed_column_samples(
            self._inspection, self._session.current, column.source_name
        )
        self.live_samples_label.setText("\n".join(samples) or "No non-null samples are available.")

    def _refresh_preview_and_summary(self, draft: ReformatDraft) -> None:
        if self._inspection is None:
            return
        preview = build_proposed_preview(self._inspection, draft)
        self.preview_model.set_preview(preview)
        if preview.error:
            self.preview_notice.setText(
                f"Preview warning: {preview.error} Raw mapped values are shown instead."
            )
        else:
            self.preview_notice.setText(
                f"Bounded sample • {len(preview.rows)} rows • {len(preview.headers)} fields • "
                f"{len(preview.diagnostics)} diagnostic(s). Full-file gap counts are checked "
                "during processing."
            )
        validation = validate_reformat_draft(draft)
        self.readiness_badge.setText("Ready" if validation.ready else "Needs confirmation")
        self.summary_label.setText("\n".join(f"• {line}" for line in configuration_summary(draft)))
        messages = validation.errors + validation.warnings
        self.validation_label.setText(
            "\n".join(f"• {message}" for message in messages) or "No configuration warnings."
        )
        self.status_label.setText(
            "Configuration is ready for review."
            if validation.ready
            else f"{len(validation.errors)} required decision(s) remain. Changes are reversible."
        )

    def _select_mapping_index(self, index: QModelIndex) -> None:
        source_index = self.mapping_proxy.mapToSource(index)
        if not source_index.isValid():
            return
        self._selected_source = self.mapping_model.column_draft(source_index.row()).source_name
        self._refreshing = True
        self._refresh_column_editor()
        self._refreshing = False

    def _on_mapping_edit(self, row: int, field: str, value: object) -> None:
        if self._session is None:
            return
        column = self._session.current.columns[row]
        updated = (
            replace(column, export=bool(value))
            if field == "export"
            else replace(column, output_name=str(value))
        )
        self._selected_source = column.source_name
        self._apply(self._session.current.update_column(updated))

    def _set_all_export(self, selected: bool) -> None:
        if self._session is None:
            return
        columns = tuple(
            replace(column, export=selected) for column in self._session.current.columns
        )
        self._apply(replace(self._session.current, columns=columns))

    def _open_wizard(self) -> None:
        if self._session is None or self._inspection is None:
            return
        dialog = SequentialColumnWizard(self._inspection, self._session.current, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._apply(dialog.result_draft)
            self.status_label.setText("Wizard changes applied as one undoable edit.")

    def _undo(self) -> None:
        if self._session is not None and self._session.undo():
            self._refresh_from_session()

    def _redo(self) -> None:
        if self._session is not None and self._session.redo():
            self._refresh_from_session()

    def _reset(self) -> None:
        if self._session is not None and self._session.reset():
            self._refresh_from_session()
            self.status_label.setText("Reset to inspected defaults. You can undo this change.")

    def _review_configuration(self) -> None:
        if self._session is None:
            return
        validation = validate_reformat_draft(self._session.current)
        self.main_tabs.setCurrentIndex(1)
        if not validation.ready:
            self.status_label.setText(
                "Review is available, but required confirmations remain in the summary."
            )
            return
        recipe = build_transformation_recipe(self._session.current)
        self.configuration_ready.emit(recipe)
        self.status_label.setText("Configuration is valid. Preparing the complete-file review.")
