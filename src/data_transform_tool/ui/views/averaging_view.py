"""Phase 7 averaging configuration and bounded previews.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, time, timedelta
from typing import cast
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from PySide6.QtCore import QDate, QDateTime, QModelIndex, Qt, QTime, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDateTimeEdit,
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
    QSpinBox,
    QSplitter,
    QTableView,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from data_transform_tool.aggregation import (
    AggregationApproach,
    AggregationStatistic,
    PeriodKind,
    PeriodSpec,
    SeasonBoundary,
)
from data_transform_tool.app.averaging_configuration import (
    DEFAULT_SEASONS,
    AveragingConfigurationSession,
    AveragingDraft,
    AveragingStageDraft,
    averaging_summary,
    build_averaging_recipe,
    create_averaging_draft,
    period_from_choice,
    stage_label,
    validate_averaging_draft,
)
from data_transform_tool.app.averaging_preview import (
    AveragingPreview,
    PreviewTable,
    build_averaging_preview,
)
from data_transform_tool.io.models import FileInspection
from data_transform_tool.transformation.recipe import OutputMissingPolicy
from data_transform_tool.ui.models import AveragingFieldTableModel, SimplePreviewTableModel


class AveragingConfigurationView(QWidget):
    """Compose a typed averaging recipe with progressive disclosure."""

    back_requested = Signal()
    configuration_ready = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self._inspection: FileInspection | None = None
        self._session: AveragingConfigurationSession | None = None
        self._selected_field: str | None = None
        self._selected_stage = 0
        self._preview = AveragingPreview(PreviewTable((), ()), ())
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
    def draft(self) -> AveragingDraft | None:
        return self._session.current if self._session is not None else None

    def set_inspection(self, inspection: FileInspection) -> None:
        self._inspection = inspection
        self._session = AveragingConfigurationSession(create_averaging_draft(inspection))
        self._selected_field = (
            self._session.current.fields[0].source_name if self._session.current.fields else None
        )
        self._selected_stage = 0
        self.setEnabled(True)
        self._refresh_from_session()

    def apply_template(self, draft: AveragingDraft) -> None:
        """Apply one reviewed template as a reversible draft change."""
        if self._session is None:
            raise ValueError("Load a source inspection before applying a template.")
        self._session.apply(draft)
        self._selected_field = draft.fields[0].source_name if draft.fields else None
        self._selected_stage = 0
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
        eyebrow = QLabel("AVERAGE / AGGREGATE  •  PHASE 7")
        eyebrow.setProperty("role", "eyebrow")
        title = QLabel("Configure reporting periods and inspect proposed aggregates")
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
                layout.addWidget(QLabel("→"))
        layout.addStretch()
        return stepper

    def _create_toolbar(self) -> QHBoxLayout:
        row = QHBoxLayout()
        confirm = QPushButton("Confirm selected suggestions")
        confirm.clicked.connect(self._confirm_selected_fields)
        row.addWidget(confirm)
        select_numeric = QPushButton("Select numeric")
        select_numeric.clicked.connect(lambda: self._set_numeric_selection(True))
        row.addWidget(select_numeric)
        deselect = QPushButton("Deselect all")
        deselect.clicked.connect(lambda: self._set_numeric_selection(False))
        row.addWidget(deselect)
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
        self.main_tabs = QTabWidget()
        self.main_tabs.addTab(self._create_field_panel(), "Field rules")
        self.main_tabs.addTab(self._create_final_preview_panel(), "Proposed output")
        self.main_tabs.addTab(self._create_stage_evidence_panel(), "Stage completeness")
        splitter.addWidget(self.main_tabs)
        splitter.addWidget(self._create_editor_scroll())
        splitter.setStretchFactor(0, 1)
        splitter.setSizes([900, 540])
        return splitter

    def _create_field_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        notice = QLabel(
            "Leq, rainfall, and rain-rate rules are advisory name-based suggestions. "
            "Confirm or override every selected field."
        )
        notice.setWordWrap(True)
        notice.setProperty("role", "muted")
        layout.addWidget(notice)
        self.field_model = AveragingFieldTableModel()
        self.field_model.edit_requested.connect(self._on_field_table_edit)
        self.field_table = QTableView()
        self.field_table.setModel(self.field_model)
        self.field_table.setAlternatingRowColors(True)
        self.field_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.field_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.field_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.field_table.horizontalHeader().setStretchLastSection(True)
        self.field_table.clicked.connect(self._select_field)
        layout.addWidget(self.field_table, 1)
        return panel

    def _create_final_preview_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        self.preview_notice = QLabel("Complete required confirmations to calculate a preview.")
        self.preview_notice.setWordWrap(True)
        self.preview_notice.setProperty("role", "muted")
        layout.addWidget(self.preview_notice)
        self.final_preview_model = SimplePreviewTableModel()
        table = QTableView()
        table.setModel(self.final_preview_model)
        table.setAlternatingRowColors(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(table, 1)
        return panel

    def _create_stage_evidence_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        row = QHBoxLayout()
        row.addWidget(QLabel("Preview stage"))
        self.preview_stage_combo = QComboBox()
        self.preview_stage_combo.currentIndexChanged.connect(self._refresh_stage_preview)
        row.addWidget(self.preview_stage_combo)
        self.stage_result_label = QLabel()
        self.stage_result_label.setProperty("role", "muted")
        row.addWidget(self.stage_result_label, 1)
        layout.addLayout(row)
        split = QSplitter(Qt.Orientation.Vertical)
        self.stage_table_model = SimplePreviewTableModel()
        stage_table = QTableView()
        stage_table.setModel(self.stage_table_model)
        stage_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        split.addWidget(stage_table)
        self.completeness_model = SimplePreviewTableModel()
        completeness_table = QTableView()
        completeness_table.setModel(self.completeness_model)
        completeness_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        split.addWidget(completeness_table)
        layout.addWidget(split, 1)
        return panel

    def _create_editor_scroll(self) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(460)
        editor = QWidget()
        layout = QVBoxLayout(editor)
        layout.addWidget(self._create_source_time_group())
        layout.addWidget(self._create_plan_group())
        layout.addWidget(self._create_selected_field_group())
        layout.addWidget(self._create_missing_group())
        layout.addWidget(self._create_summary_group())
        layout.addStretch()
        scroll.setWidget(editor)
        return scroll

    def _create_source_time_group(self) -> QGroupBox:
        group = QGroupBox("1. Source time and grid")
        form = QFormLayout(group)
        self.timestamp_combo = QComboBox()
        form.addRow("Timestamp field", self.timestamp_combo)
        self.timestamp_confirm_check = QCheckBox("Confirmed")
        form.addRow("Timestamp decision", self.timestamp_confirm_check)
        self.profile_combo = QComboBox()
        for label, value in (
            ("ISO date + hour:minute", "iso_minute"),
            ("ISO date + seconds", "iso_second"),
            ("ISO timestamp with offset", "iso_offset"),
            ("Day-first date + hour:minute", "dmy_slash_minute"),
            ("Month-first date + hour:minute", "mdy_slash_minute"),
        ):
            self.profile_combo.addItem(label, value)
        form.addRow("Input profile", self.profile_combo)
        timezone_choices = (
            "UTC",
            "Asia/Colombo",
            "Asia/Kolkata",
            "Europe/London",
            "America/New_York",
        )
        self.timezone_combo = QComboBox()
        self.timezone_combo.setEditable(True)
        self.timezone_combo.addItems(timezone_choices)
        form.addRow("Source timestamp zone", self.timezone_combo)
        self.timezone_confirm_check = QCheckBox("Confirmed")
        form.addRow("Source-zone decision", self.timezone_confirm_check)
        self.reporting_timezone_combo = QComboBox()
        self.reporting_timezone_combo.setEditable(True)
        self.reporting_timezone_combo.addItems(timezone_choices)
        for control in (self.timezone_combo, self.reporting_timezone_combo):
            control.setToolTip(
                "UTC; Asia/Colombo = UTC+05:30 (+5.5 hours). Type a custom IANA timezone here."
            )
        form.addRow("Reporting boundary zone", self.reporting_timezone_combo)
        zone_help = QLabel(
            "UTC · Asia/Colombo (UTC+05:30 / +5.5 hours) · Custom: type an IANA zone"
        )
        zone_help.setWordWrap(True)
        form.addRow(zone_help)
        self.reporting_timezone_confirm_check = QCheckBox("Confirmed")
        form.addRow("Reporting-zone decision", self.reporting_timezone_confirm_check)
        self.interval_combo = QComboBox()
        interval_options: tuple[tuple[str, float | None], ...] = (
            ("1 minute", 60.0),
            ("5 minutes", 300.0),
            ("15 minutes", 900.0),
            ("1 hour", 3600.0),
            ("Custom", None),
        )
        for interval_label, interval_value in interval_options:
            self.interval_combo.addItem(interval_label, interval_value)
        form.addRow("Input interval", self.interval_combo)
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
        for control in (
            self.timestamp_combo,
            self.profile_combo,
            self.timezone_combo,
            self.reporting_timezone_combo,
            self.interval_combo,
        ):
            control.currentIndexChanged.connect(self._commit_global_controls)
        self.timezone_combo.editTextChanged.connect(self._commit_global_controls)
        self.reporting_timezone_combo.editTextChanged.connect(self._commit_global_controls)
        self.custom_interval_spin.valueChanged.connect(self._commit_global_controls)
        for check in (
            self.timestamp_confirm_check,
            self.timezone_confirm_check,
            self.reporting_timezone_confirm_check,
            self.interval_confirm_check,
            self.allow_reorder_check,
        ):
            check.toggled.connect(self._commit_global_controls)
        return group

    def _create_plan_group(self) -> QGroupBox:
        group = QGroupBox("2. Aggregation plan")
        layout = QVBoxLayout(group)
        approach_form = QFormLayout()
        self.approach_combo = QComboBox()
        self.approach_combo.addItem("Direct — source rows to target", AggregationApproach.DIRECT)
        self.approach_combo.addItem(
            "Incremental — visible staged chain", AggregationApproach.INCREMENTAL
        )
        approach_form.addRow("Approach", self.approach_combo)
        layout.addLayout(approach_form)
        chain_row = QHBoxLayout()
        self.stage_list = QListWidget()
        self.stage_list.setMaximumHeight(112)
        self.stage_list.currentRowChanged.connect(self._select_stage)
        chain_row.addWidget(self.stage_list, 1)
        buttons = QVBoxLayout()
        add = QPushButton("Add stage")
        add.clicked.connect(self._add_stage)
        buttons.addWidget(add)
        remove = QPushButton("Remove stage")
        remove.clicked.connect(self._remove_stage)
        buttons.addWidget(remove)
        buttons.addStretch()
        chain_row.addLayout(buttons)
        layout.addLayout(chain_row)

        form = QFormLayout()
        self.period_combo = QComboBox()
        for label, value in (
            ("5 minutes", "5m"),
            ("15 minutes", "15m"),
            ("1 hour", "1h"),
            ("8 hours", "8h"),
            ("Custom clock interval", "custom_clock"),
            ("Reporting day", "day"),
            ("Week", "week"),
            ("Calendar month", "month"),
            ("Fixed 30 days", "fixed30"),
            ("Quarter", "quarter"),
            ("Configured season", "season"),
            ("Calendar / reporting year", "year"),
            ("Fixed one year", "fixedyear"),
        ):
            self.period_combo.addItem(label, value)
        form.addRow("Target period", self.period_combo)
        self.custom_period_spin = QDoubleSpinBox()
        self.custom_period_spin.setRange(0.001, 86_400)
        self.custom_period_spin.setDecimals(3)
        self.custom_period_spin.setSuffix(" seconds")
        form.addRow("Clock duration", self.custom_period_spin)
        self.custom_period_label = cast(QLabel, form.labelForField(self.custom_period_spin))
        self.day_start_edit = QTimeEdit(QTime(0, 0))
        self.day_start_edit.setDisplayFormat("HH:mm")
        form.addRow("Start of day", self.day_start_edit)
        self.week_start_combo = QComboBox()
        weekdays = (
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        )
        for index, name in enumerate(weekdays):
            self.week_start_combo.addItem(name, index)
        form.addRow("Week starts", self.week_start_combo)
        self.quarter_start_combo = QComboBox()
        for month in range(1, 13):
            self.quarter_start_combo.addItem(datetime(2001, month, 1).strftime("%B"), month)
        form.addRow("Q1 starts", self.quarter_start_combo)
        self.year_start_edit = QDateEdit(QDate(2001, 1, 1))
        self.year_start_edit.setDisplayFormat("MMMM d")
        form.addRow("Reporting year starts", self.year_start_edit)
        self.anchor_edit = QDateTimeEdit(QDateTime(QDate(2025, 1, 1), QTime(0, 0)))
        self.anchor_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        form.addRow("Fixed-period anchor", self.anchor_edit)
        self.threshold_spin = QSpinBox()
        self.threshold_spin.setRange(1, 100)
        self.threshold_spin.setSuffix(" %")
        self.threshold_spin.setValue(75)
        form.addRow("Completeness", self.threshold_spin)
        self.two_of_three_check = QCheckBox("Allow 2 of 3 when exactly three components exist")
        form.addRow("Special rule", self.two_of_three_check)
        layout.addLayout(form)

        self.season_group = QGroupBox("Season boundaries")
        season_layout = QVBoxLayout(self.season_group)
        self.season_table = QTableWidget(0, 3)
        self.season_table.setHorizontalHeaderLabels(("Season name", "Start month", "Start day"))
        self.season_table.horizontalHeader().setStretchLastSection(True)
        self.season_table.setMaximumHeight(142)
        season_layout.addWidget(self.season_table)
        season_buttons = QHBoxLayout()
        add_season = QPushButton("Add boundary")
        add_season.clicked.connect(self._add_season)
        season_buttons.addWidget(add_season)
        remove_season = QPushButton("Remove boundary")
        remove_season.clicked.connect(self._remove_season)
        season_buttons.addWidget(remove_season)
        season_buttons.addStretch()
        season_layout.addLayout(season_buttons)
        layout.addWidget(self.season_group)

        self.approach_combo.currentIndexChanged.connect(self._change_approach)
        for control in (
            self.period_combo,
            self.week_start_combo,
            self.quarter_start_combo,
        ):
            control.currentIndexChanged.connect(self._commit_stage_controls)
        self.custom_period_spin.valueChanged.connect(self._commit_stage_controls)
        self.day_start_edit.timeChanged.connect(self._commit_stage_controls)
        self.year_start_edit.dateChanged.connect(self._commit_stage_controls)
        self.anchor_edit.dateTimeChanged.connect(self._commit_stage_controls)
        self.threshold_spin.valueChanged.connect(self._commit_stage_controls)
        self.two_of_three_check.toggled.connect(self._commit_stage_controls)
        self.season_table.itemChanged.connect(self._commit_stage_controls)
        return group

    def _create_selected_field_group(self) -> QGroupBox:
        group = QGroupBox("3. Selected field")
        form = QFormLayout(group)
        self.selected_field_label = QLabel("Select a field")
        self.selected_field_label.setProperty("role", "sectionTitle")
        form.addRow(self.selected_field_label)
        self.field_detection_label = QLabel()
        self.field_detection_label.setWordWrap(True)
        self.field_detection_label.setProperty("role", "muted")
        form.addRow(self.field_detection_label)
        self.include_check = QCheckBox("Aggregate this field")
        form.addRow("Selection", self.include_check)
        self.statistic_combo = QComboBox()
        labels = {
            AggregationStatistic.ARITHMETIC_MEAN: "Arithmetic mean",
            AggregationStatistic.MINIMUM: "Minimum",
            AggregationStatistic.MAXIMUM: "Maximum",
            AggregationStatistic.SUM: "Sum",
            AggregationStatistic.MEDIAN: "Median",
            AggregationStatistic.STANDARD_DEVIATION: "Population standard deviation",
            AggregationStatistic.COUNT: "Count",
            AggregationStatistic.ENERGY_AVERAGE_LEQ: "Energy average / Leq",
            AggregationStatistic.RAINFALL_ACCUMULATION: "Rainfall accumulation",
            AggregationStatistic.RAIN_RATE_MEAN: "Rain-rate mean",
        }
        for value in AggregationStatistic:
            self.statistic_combo.addItem(labels[value], value)
        form.addRow("Statistic", self.statistic_combo)
        self.statistic_confirm_check = QCheckBox("Confirmed — suggestion reviewed")
        form.addRow("Rule decision", self.statistic_confirm_check)
        self.output_name_edit = QLineEdit()
        form.addRow("Output name", self.output_name_edit)
        self.duration_combo = QComboBox()
        form.addRow("Leq duration field", self.duration_combo)
        self.sample_label = QLabel()
        self.sample_label.setWordWrap(True)
        self.sample_label.setProperty("role", "muted")
        form.addRow("Samples", self.sample_label)
        self.include_check.toggled.connect(self._commit_field_controls)
        self.statistic_combo.currentIndexChanged.connect(self._commit_field_controls)
        self.statistic_confirm_check.toggled.connect(self._commit_field_controls)
        self.output_name_edit.editingFinished.connect(self._commit_field_controls)
        self.duration_combo.currentIndexChanged.connect(self._commit_field_controls)
        return group

    def _create_missing_group(self) -> QGroupBox:
        group = QGroupBox("4. Missing values")
        layout = QVBoxLayout(group)
        form = QFormLayout()
        self.missing_policy_combo = QComboBox()
        for label, value in (
            ("True Null / blank (recommended)", OutputMissingPolicy.TRUE_NULL),
            ("N/A", OutputMissingPolicy.NA),
            ("-999", OutputMissingPolicy.MINUS_999),
            ("Custom sentinel", OutputMissingPolicy.CUSTOM),
        ):
            self.missing_policy_combo.addItem(label, value)
        form.addRow("Rejected / missing result", self.missing_policy_combo)
        self.custom_sentinel_edit = QLineEdit()
        form.addRow("Custom sentinel", self.custom_sentinel_edit)
        self.custom_sentinel_label = cast(QLabel, form.labelForField(self.custom_sentinel_edit))
        layout.addLayout(form)
        layout.addWidget(QLabel("Detected input markers — confirm each explicitly"))
        self.missing_marker_list = QListWidget()
        self.missing_marker_list.setMaximumHeight(90)
        layout.addWidget(self.missing_marker_list)
        self.missing_markers_reviewed_check = QCheckBox(
            "Marker decisions reviewed — checked values become null"
        )
        layout.addWidget(self.missing_markers_reviewed_check)
        self.missing_policy_combo.currentIndexChanged.connect(self._commit_missing_controls)
        self.custom_sentinel_edit.editingFinished.connect(self._commit_missing_controls)
        self.missing_marker_list.itemChanged.connect(self._commit_missing_controls)
        self.missing_markers_reviewed_check.toggled.connect(self._commit_missing_controls)
        return group

    def _create_summary_group(self) -> QGroupBox:
        group = QGroupBox("Readable plan and warnings")
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
        self.status_label = QLabel("Load an inspection to configure averaging.")
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
        review = QPushButton("Review averaging plan →")
        review.setProperty("role", "primary")
        review.clicked.connect(self._review_configuration)
        row.addWidget(review)
        return row

    def _apply(self, draft: AveragingDraft) -> None:
        if self._session is not None and self._session.apply(draft):
            self._refresh_from_session()

    def _refresh_from_session(self) -> None:
        if self._session is None or self._inspection is None:
            return
        self._refreshing = True
        draft = self._session.current
        self.field_model.set_draft(draft)
        self.undo_button.setEnabled(self._session.can_undo)
        self.redo_button.setEnabled(self._session.can_redo)
        self.timestamp_combo.clear()
        self.timestamp_combo.addItem("Choose timestamp…", None)
        for name in draft.expected_columns:
            self.timestamp_combo.addItem(name, name)
        self.timestamp_combo.setCurrentIndex(
            max(self.timestamp_combo.findData(draft.timestamp_column), 0)
        )
        self.timestamp_confirm_check.setChecked(draft.timestamp_confirmed)
        self.profile_combo.setCurrentIndex(
            max(self.profile_combo.findData(draft.timestamp_profile), 0)
        )
        self.timezone_combo.setCurrentText(draft.source_timezone)
        self.timezone_confirm_check.setChecked(draft.source_timezone_confirmed)
        self.reporting_timezone_combo.setCurrentText(draft.reporting_timezone)
        self.reporting_timezone_confirm_check.setChecked(draft.reporting_timezone_confirmed)
        interval_index = self.interval_combo.findData(draft.interval_seconds)
        self.interval_combo.setCurrentIndex(
            interval_index if interval_index >= 0 else self.interval_combo.count() - 1
        )
        if draft.interval_seconds is not None:
            self.custom_interval_spin.setValue(draft.interval_seconds)
        custom_interval = self.interval_combo.currentData() is None
        self.custom_interval_spin.setVisible(custom_interval)
        self.custom_interval_label.setVisible(custom_interval)
        self.interval_confirm_check.setChecked(draft.interval_confirmed)
        self.allow_reorder_check.setChecked(draft.allow_reorder)
        self.approach_combo.setCurrentIndex(self.approach_combo.findData(draft.approach))
        self._refresh_stage_list(draft)
        self._refresh_field_editor(draft)
        self.missing_policy_combo.setCurrentIndex(
            self.missing_policy_combo.findData(draft.output_missing_policy)
        )
        self.custom_sentinel_edit.setText(
            "" if draft.custom_missing_sentinel is None else str(draft.custom_missing_sentinel)
        )
        custom_missing = draft.output_missing_policy is OutputMissingPolicy.CUSTOM
        self.custom_sentinel_edit.setVisible(custom_missing)
        self.custom_sentinel_label.setVisible(custom_missing)
        self._refresh_markers(draft)
        self.missing_markers_reviewed_check.setChecked(draft.missing_marker_decisions_confirmed)
        self.missing_markers_reviewed_check.setEnabled(bool(draft.detected_missing_markers))
        self._refresh_preview_and_summary(draft)
        self._refreshing = False
        self._refresh_stage_preview()

    def _refresh_stage_list(self, draft: AveragingDraft) -> None:
        self.stage_list.clear()
        for index, stage in enumerate(draft.stages, start=1):
            special = " • 2/3 allowed" if stage.allow_two_of_three else ""
            self.stage_list.addItem(
                f"{index}. {stage_label(stage)} • {stage.threshold:.0%}{special}"
            )
        self._selected_stage = min(self._selected_stage, max(len(draft.stages) - 1, 0))
        self.stage_list.setCurrentRow(self._selected_stage)
        self._refresh_stage_editor()

    def _refresh_stage_editor(self) -> None:
        if self._session is None or not self._session.current.stages:
            return
        stage = self._session.current.stages[self._selected_stage]
        period = stage.period
        choice = _choice_for_period(period)
        self.period_combo.setCurrentIndex(max(self.period_combo.findData(choice), 0))
        if period.duration is not None:
            self.custom_period_spin.setValue(period.duration.total_seconds())
        self.day_start_edit.setTime(QTime(period.day_start.hour, period.day_start.minute))
        self.week_start_combo.setCurrentIndex(self.week_start_combo.findData(period.week_start))
        self.quarter_start_combo.setCurrentIndex(
            self.quarter_start_combo.findData(period.quarter_start_month)
        )
        self.year_start_edit.setDate(QDate(2001, period.year_start_month, period.year_start_day))
        if period.anchor is not None:
            anchor = period.anchor
            self.anchor_edit.setDateTime(
                QDateTime(
                    QDate(anchor.year, anchor.month, anchor.day),
                    QTime(anchor.hour, anchor.minute, anchor.second),
                )
            )
        self.threshold_spin.setValue(round(stage.threshold * 100))
        self.two_of_three_check.setChecked(stage.allow_two_of_three)
        self.two_of_three_check.setEnabled(
            self._session.current.approach is AggregationApproach.INCREMENTAL
        )
        self._populate_seasons(period.seasons or DEFAULT_SEASONS)
        self._update_period_visibility(choice)

    def _refresh_field_editor(self, draft: AveragingDraft) -> None:
        if self._selected_field is None or not draft.fields:
            return
        field = draft.field(self._selected_field)
        self.selected_field_label.setText(field.source_name)
        self.field_detection_label.setText(
            f"Detected {field.detected_type.value} at {field.confidence:.0%} confidence • "
            f"{field.missing_percent:.2f}% missing"
        )
        self.include_check.setChecked(field.include)
        self.statistic_combo.setCurrentIndex(self.statistic_combo.findData(field.statistic))
        self.statistic_confirm_check.setChecked(field.statistic_confirmed)
        self.output_name_edit.setText(field.output_name)
        self.duration_combo.clear()
        self.duration_combo.addItem("Equal duration / none", None)
        for name in draft.expected_columns:
            self.duration_combo.addItem(name, name)
        self.duration_combo.setCurrentIndex(
            max(self.duration_combo.findData(field.duration_column), 0)
        )
        self.duration_combo.setEnabled(field.statistic is AggregationStatistic.ENERGY_AVERAGE_LEQ)
        self.sample_label.setText(" • ".join(field.samples) or "No non-null samples available")

    def _refresh_markers(self, draft: AveragingDraft) -> None:
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

    def _refresh_preview_and_summary(self, draft: AveragingDraft) -> None:
        if self._inspection is None:
            return
        preview = build_averaging_preview(self._inspection, draft)
        self._preview = preview
        self.final_preview_model.set_table(preview.final_table)
        self.preview_stage_combo.clear()
        for index, stage in enumerate(preview.stages):
            self.preview_stage_combo.addItem(f"{index + 1}. {stage.label}", index)
        self._refresh_stage_preview()
        validation = validate_averaging_draft(draft)
        self.readiness_badge.setText("Ready" if validation.ready else "Needs confirmation")
        self.summary_label.setText("\n".join(f"• {line}" for line in averaging_summary(draft)))
        messages = validation.errors + validation.warnings
        self.validation_label.setText(
            "\n".join(f"• {message}" for message in messages) or "No configuration warnings."
        )
        if preview.error:
            self.preview_notice.setText(f"Preview waiting: {preview.error}")
        else:
            self.preview_notice.setText(
                f"Bounded sample • {preview.source_row_count} source rows • "
                f"{len(preview.final_table.rows)} proposed periods • "
                f"{len(preview.stages)} stage(s). Complete-file execution follows review."
            )
        self.status_label.setText(
            "Averaging configuration is ready for review."
            if validation.ready
            else f"{len(validation.errors)} required decision(s) remain. Changes are reversible."
        )

    def _refresh_stage_preview(self) -> None:
        if self._refreshing:
            return
        index = self.preview_stage_combo.currentIndex()
        if index < 0 or index >= len(self._preview.stages):
            self.stage_table_model.set_table(PreviewTable((), ()))
            self.completeness_model.set_table(PreviewTable((), ()))
            self.stage_result_label.clear()
            return
        stage = self._preview.stages[index]
        self.stage_table_model.set_table(stage.table)
        self.completeness_model.set_table(
            PreviewTable(stage.completeness_headers, stage.completeness_rows)
        )
        self.stage_result_label.setText(f"{stage.accepted} accepted • {stage.rejected} missing")

    def _commit_global_controls(self) -> None:
        if self._refreshing or self._session is None:
            return
        interval_data = cast(float | None, self.interval_combo.currentData())
        interval = interval_data if interval_data is not None else self.custom_interval_spin.value()
        self._apply(
            replace(
                self._session.current,
                timestamp_column=cast(str | None, self.timestamp_combo.currentData()),
                timestamp_profile=str(self.profile_combo.currentData()),
                timestamp_confirmed=self.timestamp_confirm_check.isChecked(),
                source_timezone=self.timezone_combo.currentText().strip(),
                source_timezone_confirmed=self.timezone_confirm_check.isChecked(),
                reporting_timezone=self.reporting_timezone_combo.currentText().strip(),
                reporting_timezone_confirmed=(self.reporting_timezone_confirm_check.isChecked()),
                interval_seconds=interval,
                interval_confirmed=self.interval_confirm_check.isChecked(),
                allow_reorder=self.allow_reorder_check.isChecked(),
            )
        )

    def _commit_field_controls(self) -> None:
        if self._refreshing or self._session is None or self._selected_field is None:
            return
        current = self._session.current.field(self._selected_field)
        statistic = AggregationStatistic(str(self.statistic_combo.currentData()))
        updated = replace(
            current,
            include=self.include_check.isChecked(),
            statistic=statistic,
            statistic_confirmed=self.statistic_confirm_check.isChecked(),
            output_name=self.output_name_edit.text().strip() or current.output_name,
            duration_column=(
                cast(str | None, self.duration_combo.currentData())
                if statistic is AggregationStatistic.ENERGY_AVERAGE_LEQ
                else None
            ),
        )
        self._apply(self._session.current.update_field(updated))

    def _commit_missing_controls(self) -> None:
        if self._refreshing or self._session is None:
            return
        markers = tuple(
            self.missing_marker_list.item(index).text()
            for index in range(self.missing_marker_list.count())
            if self.missing_marker_list.item(index).checkState() == Qt.CheckState.Checked
        )
        self._apply(
            replace(
                self._session.current,
                confirmed_missing_markers=markers,
                missing_marker_decisions_confirmed=(
                    self.missing_markers_reviewed_check.isChecked()
                    or not self._session.current.detected_missing_markers
                ),
                output_missing_policy=OutputMissingPolicy(
                    str(self.missing_policy_combo.currentData())
                ),
                custom_missing_sentinel=self.custom_sentinel_edit.text().strip() or None,
            )
        )

    def _commit_stage_controls(self) -> None:
        if self._refreshing or self._session is None or not self._session.current.stages:
            return
        try:
            anchor = cast(datetime, self.anchor_edit.dateTime().toPython()).replace(
                tzinfo=ZoneInfo(self._session.current.reporting_timezone)
            )
            period = period_from_choice(
                str(self.period_combo.currentData()),
                day_start=cast(time, self.day_start_edit.time().toPython()),
                week_start=int(self.week_start_combo.currentData()),
                quarter_start_month=int(self.quarter_start_combo.currentData()),
                year_start_month=self.year_start_edit.date().month(),
                year_start_day=self.year_start_edit.date().day(),
                anchor=anchor,
                custom_duration_seconds=self.custom_period_spin.value(),
                seasons=self._read_seasons(),
            )
            current = self._session.current.stages[self._selected_stage]
            updated = replace(
                current,
                period=period,
                threshold=self.threshold_spin.value() / 100,
                allow_two_of_three=(
                    self.two_of_three_check.isChecked()
                    and self._session.current.approach is AggregationApproach.INCREMENTAL
                ),
                label=None,
            )
        except (ValueError, ZoneInfoNotFoundError) as error:
            self.status_label.setText(str(error))
            self._update_period_visibility(str(self.period_combo.currentData()))
            return
        stages = list(self._session.current.stages)
        stages[self._selected_stage] = updated
        self._apply(replace(self._session.current, stages=tuple(stages)))

    def _change_approach(self) -> None:
        if self._refreshing or self._session is None:
            return
        approach = AggregationApproach(str(self.approach_combo.currentData()))
        stages = self._session.current.stages
        if approach is AggregationApproach.DIRECT:
            stages = (stages[-1],)
            self._selected_stage = 0
        elif len(stages) == 1:
            stages = (
                stages[0],
                AveragingStageDraft(PeriodSpec.clock(timedelta(hours=8)), label="8 hours"),
            )
            self._selected_stage = 1
        self._apply(replace(self._session.current, approach=approach, stages=stages))

    def _add_stage(self) -> None:
        if self._session is None:
            return
        stages = (
            *self._session.current.stages,
            AveragingStageDraft(PeriodSpec.day(), label="Day"),
        )
        self._selected_stage = len(stages) - 1
        self._apply(
            replace(
                self._session.current,
                approach=AggregationApproach.INCREMENTAL,
                stages=stages,
            )
        )

    def _remove_stage(self) -> None:
        if self._session is None or len(self._session.current.stages) <= 1:
            self.status_label.setText("At least one target stage is required.")
            return
        stages = list(self._session.current.stages)
        stages.pop(self._selected_stage)
        self._selected_stage = min(self._selected_stage, len(stages) - 1)
        approach = (
            AggregationApproach.INCREMENTAL if len(stages) > 1 else AggregationApproach.DIRECT
        )
        self._apply(replace(self._session.current, approach=approach, stages=tuple(stages)))

    def _select_stage(self, row: int) -> None:
        if self._refreshing or row < 0:
            return
        self._selected_stage = row
        self._refreshing = True
        self._refresh_stage_editor()
        self._refreshing = False

    def _populate_seasons(self, seasons: tuple[SeasonBoundary, ...]) -> None:
        self.season_table.setRowCount(0)
        for boundary in seasons:
            row = self.season_table.rowCount()
            self.season_table.insertRow(row)
            values = (boundary.name, str(boundary.month), str(boundary.day))
            for column, value in enumerate(values):
                self.season_table.setItem(row, column, QTableWidgetItem(value))

    def _read_seasons(self) -> tuple[SeasonBoundary, ...]:
        boundaries: list[SeasonBoundary] = []
        for row in range(self.season_table.rowCount()):
            cells = tuple(self.season_table.item(row, column) for column in range(3))
            values = tuple(cell.text().strip() if cell is not None else "" for cell in cells)
            if not any(values):
                continue
            boundaries.append(SeasonBoundary(values[0], int(values[1]), int(values[2])))
        return tuple(boundaries)

    def _add_season(self) -> None:
        self._refreshing = True
        row = self.season_table.rowCount()
        self.season_table.insertRow(row)
        for column, value in enumerate((f"Season {row + 1}", "1", "1")):
            self.season_table.setItem(row, column, QTableWidgetItem(value))
        self._refreshing = False
        self._commit_stage_controls()

    def _remove_season(self) -> None:
        row = self.season_table.currentRow()
        if row >= 0:
            self.season_table.removeRow(row)
            self._commit_stage_controls()

    def _update_period_visibility(self, choice: str) -> None:
        custom = choice == "custom_clock"
        self.custom_period_spin.setVisible(custom)
        self.custom_period_label.setVisible(custom)
        self.week_start_combo.setEnabled(choice == "week")
        self.quarter_start_combo.setEnabled(choice == "quarter")
        self.year_start_edit.setEnabled(choice == "year")
        self.anchor_edit.setEnabled(choice in {"fixed30", "fixedyear"})
        self.season_group.setVisible(choice == "season")

    def _select_field(self, index: QModelIndex) -> None:
        if not index.isValid():
            return
        self._selected_field = self.field_model.field_draft(index.row()).source_name
        self._refreshing = True
        if self._session is not None:
            self._refresh_field_editor(self._session.current)
        self._refreshing = False

    def _on_field_table_edit(self, row: int, field_name: str, value: object) -> None:
        if self._session is None:
            return
        field = self._session.current.fields[row]
        updated = (
            replace(field, include=bool(value))
            if field_name == "include"
            else replace(field, output_name=str(value))
        )
        self._selected_field = field.source_name
        self._apply(self._session.current.update_field(updated))

    def _confirm_selected_fields(self) -> None:
        if self._session is None:
            return
        fields = tuple(
            replace(field, statistic_confirmed=True) if field.include else field
            for field in self._session.current.fields
        )
        self._apply(replace(self._session.current, fields=fields))

    def _set_numeric_selection(self, selected: bool) -> None:
        if self._session is None:
            return
        fields = tuple(
            replace(field, include=selected and field.is_numeric)
            for field in self._session.current.fields
        )
        self._apply(replace(self._session.current, fields=fields))

    def _undo(self) -> None:
        if self._session is not None and self._session.undo():
            self._refresh_from_session()

    def _redo(self) -> None:
        if self._session is not None and self._session.redo():
            self._refresh_from_session()

    def _reset(self) -> None:
        if self._session is not None and self._session.reset():
            self._selected_stage = 0
            self._refresh_from_session()
            self.status_label.setText("Reset to inspected suggestions. You can undo this change.")

    def _review_configuration(self) -> None:
        if self._session is None:
            return
        validation = validate_averaging_draft(self._session.current)
        self.main_tabs.setCurrentIndex(1)
        if not validation.ready:
            self.status_label.setText("Review is available, but required confirmations remain.")
            return
        recipe = build_averaging_recipe(self._session.current)
        self.configuration_ready.emit(recipe)
        self.status_label.setText("Averaging plan is valid. Preparing the complete-file review.")


def _choice_for_period(period: PeriodSpec) -> str:
    if period.kind is PeriodKind.FIXED_CLOCK and period.duration is not None:
        choices = {
            300.0: "5m",
            900.0: "15m",
            3600.0: "1h",
            28800.0: "8h",
        }
        return choices.get(period.duration.total_seconds(), "custom_clock")
    return {
        PeriodKind.DAY: "day",
        PeriodKind.WEEK: "week",
        PeriodKind.CALENDAR_MONTH: "month",
        PeriodKind.FIXED_DAYS: "fixed30",
        PeriodKind.QUARTER: "quarter",
        PeriodKind.SEASON: "season",
        PeriodKind.CALENDAR_YEAR: "year",
        PeriodKind.FIXED_YEAR: "fixedyear",
    }[period.kind]
