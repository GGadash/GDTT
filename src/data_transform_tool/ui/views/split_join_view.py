"""Separate Split & Join workspace with explicit configuration and verified export.

Copyright (c) 2026 Akila DJ +. Gadash (Akila DJ); OpenAI Codex.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import time
from pathlib import Path
from typing import cast

from PySide6.QtCore import Qt, QThread, QTime, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QResizeEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
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
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from data_transform_tool.aggregation.models import PeriodKind, PeriodSpec, SeasonBoundary
from data_transform_tool.app.split_join_workflow import (
    PreparedSplitJoin,
    export_split_join,
    prepare_split_join,
)
from data_transform_tool.export.models import ExportPlan
from data_transform_tool.export.naming import data_output_path
from data_transform_tool.io.cancellation import CancellationToken
from data_transform_tool.io.inspector import FileInspector
from data_transform_tool.io.models import FileInspection
from data_transform_tool.io.options import InspectionOptions
from data_transform_tool.split_join.models import (
    Action,
    DuplicatePolicy,
    FieldGroup,
    MatchPolicy,
    SourceSpec,
    SplitJoinSpec,
)
from data_transform_tool.timezone.converter import list_iana_timezones
from data_transform_tool.transformation.recipe import OutputFormat, OutputMissingPolicy
from data_transform_tool.ui.widgets.field_controls import bulk_buttons, fill_zones
from data_transform_tool.ui.workers.split_join_worker import SplitJoinWorker


def zone_combo() -> QComboBox:
    combo = QComboBox()
    combo.setEditable(True)
    combo.addItems(["UTC", "Asia/Colombo", "+05:30"])
    combo.addItems([zone for zone in list_iana_timezones() if zone not in {"UTC", "Asia/Colombo"}])
    combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
    combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
    combo.setMinimumContentsLength(20)
    combo.setToolTip(
        "UTC; Asia/Colombo = UTC+05:30 (+5.5 hours). Type any IANA zone or ±HH:MM offset."
    )
    combo.setAccessibleName("Timezone: select or type a custom IANA zone or UTC offset")
    fill_zones(combo)
    return combo


def table_widget(headers: list[str]) -> QTableWidget:
    table = QTableWidget(0, len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
    table.horizontalHeader().setStretchLastSection(True)
    return table


def readonly_item(value: object) -> QTableWidgetItem:
    item = QTableWidgetItem(str(value))
    item.setToolTip(str(value))
    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
    return item


class SourceEditor(QWidget):
    changed = Signal()
    inspect_requested = Signal()

    def __init__(self, path: Path) -> None:
        super().__init__()
        self.path = path
        self.inspection: FileInspection | None = None
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.sheet = QComboBox()
        self.sheet.setEditable(True)
        form.addRow("Excel worksheet (blank = first)", self.sheet)
        self.delimiter = QComboBox()
        for label, value in [
            ("Detect", None),
            ("Comma", ","),
            ("Tab", "\t"),
            ("Semicolon", ";"),
            ("Pipe", "|"),
        ]:
            self.delimiter.addItem(label, value)
        form.addRow("Text delimiter", self.delimiter)
        self.header = QComboBox()
        for label, header_value in [
            ("Detect", None),
            ("First row is header", True),
            ("No header", False),
        ]:
            self.header.addItem(label, header_value)
        form.addRow("Header", self.header)
        self.encoding = QLineEdit()
        self.encoding.setPlaceholderText("Detect, or enter utf-8 / cp1252 / …")
        form.addRow("Text encoding", self.encoding)
        form.setRowVisible(self.sheet, path.suffix.lower() == ".xlsx")
        form.setRowVisible(self.delimiter, path.suffix.lower() != ".xlsx")
        form.setRowVisible(self.encoding, path.suffix.lower() != ".xlsx")
        self.inspect_button = QPushButton("Inspect / refresh columns")
        self.inspect_button.clicked.connect(self.inspect_requested)
        form.addRow(self.inspect_button)
        self.timestamp = QComboBox()
        form.addRow("Timestamp column", self.timestamp)
        self.pattern = QComboBox()
        self.pattern.setEditable(True)
        self.pattern.addItems(
            ["ISO", "%d/%m/%Y %H:%M", "%d/%m/%Y %H:%M:%S", "%m/%d/%Y %H:%M", "%Y-%m-%d %H:%M:%S%z"]
        )
        self.pattern.setToolTip(
            "ISO accepts date, seconds, fractional seconds and embedded offsets. "
            "Custom uses Python strptime syntax."
        )
        form.addRow("Timestamp format (or type custom)", self.pattern)
        self.zone = zone_combo()
        form.addRow("Source timezone (naive timestamps)", self.zone)
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        layout.addLayout(form)
        info = QLabel(
            "Embedded offsets are honored. Colombo = UTC+05:30. "
            "Select fields below; the timestamp is always retained."
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        self.fields = QListWidget()
        self.fields.setMaximumHeight(140)
        layout.addWidget(self.fields)
        layout.addLayout(bulk_buttons(self.fields, self.changed.emit))
        self.details = QLabel("Inspect the file to review its columns and detected structure.")
        self.details.setWordWrap(True)
        layout.addWidget(self.details)
        self.sample = table_widget([])
        self.sample.setMaximumHeight(165)
        layout.addWidget(self.sample)
        for combo in (
            self.sheet,
            self.delimiter,
            self.header,
            self.timestamp,
            self.pattern,
            self.zone,
        ):
            combo.currentTextChanged.connect(self.changed)
        self.encoding.textChanged.connect(self.changed)
        self.fields.itemChanged.connect(self.changed)
        self.timestamp.currentTextChanged.connect(self._timestamp_changed)

    def options(self) -> InspectionOptions:
        return InspectionOptions(
            worksheet=self.sheet.currentText().strip() or None,
            delimiter=self.delimiter.currentData(),
            has_header=self.header.currentData(),
            encoding=self.encoding.text().strip() or None,
        )

    def apply_inspection(self, inspection: FileInspection) -> None:
        previous = self.timestamp.currentText()
        self.inspection = inspection
        self.sheet.clear()
        self.sheet.addItems(inspection.available_worksheets)
        self.sheet.setCurrentText(inspection.worksheet or "")
        self.timestamp.clear()
        self.timestamp.addItems(inspection.column_names)
        self.timestamp.setCurrentText(
            previous
            if previous in inspection.column_names
            else (inspection.likely_datetime_column or inspection.column_names[0])
        )
        self._timestamp_changed()
        self.details.setText(
            f"{inspection.row_count:,} rows · {inspection.column_count} columns · "
            f"header: {inspection.header_detected} · delimiter: {inspection.delimiter!r} · "
            f"encoding: {inspection.encoding or 'Excel'}\n" + "\n".join(inspection.warnings)
        )
        rows = inspection.previews[0].rows[:5] if inspection.previews else ()
        self.sample.setColumnCount(inspection.column_count)
        self.sample.setHorizontalHeaderLabels(inspection.column_names)
        self.sample.setColumnWidth(0, 260)
        self.sample.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, value in enumerate(row):
                self.sample.setItem(r, c, readonly_item("" if value is None else value))

    def _timestamp_changed(self) -> None:
        if self.inspection is None:
            return
        self.fields.clear()
        for name in self.inspection.column_names:
            if name != self.timestamp.currentText():
                item = QListWidgetItem(name)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Checked)
                self.fields.addItem(item)

    def source(self) -> SourceSpec:
        if self.inspection is None:
            raise ValueError(f"Inspect {self.path.name} before preparing.")
        fields = tuple(
            self.fields.item(i).text()
            for i in range(self.fields.count())
            if self.fields.item(i).checkState() == Qt.CheckState.Checked
        )
        if not fields:
            raise ValueError("Select at least one non-timestamp field per source.")
        return SourceSpec(
            self.path,
            self.timestamp.currentText(),
            self.zone.currentText().strip(),
            self.pattern.currentText().strip(),
            self.options(),
            fields,
        )


class SplitJoinView(QWidget):
    back_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setAcceptDrops(True)
        self.editors: list[SourceEditor] = []
        self.prepared: PreparedSplitJoin | None = None
        self._thread: QThread | None = None
        self.worker: SplitJoinWorker | None = None
        self.token = CancellationToken()
        self._complete: Callable[[object], None] = lambda _: None
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 16, 24, 16)
        title = QLabel("Data Splitter & Joiner")
        title.setProperty("role", "sectionTitle")
        root.addWidget(title)
        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)
        self._inputs_tab()
        self._operation_tab()
        self._review_tab()
        self.status = QLabel(
            "Add files by browsing or dropping them here. Configure and inspect each source."
        )
        self.status.setWordWrap(True)
        root.addWidget(self.status)
        actions = QHBoxLayout()
        self.back = QPushButton("← Home")
        self.back.clicked.connect(self.back_requested)
        actions.addWidget(self.back)
        actions.addStretch()
        self.prepare_button = QPushButton("Prepare preview")
        self.prepare_button.setToolTip("Validate sources and prepare the Split / Join preview.")
        self.prepare_button.setProperty("role", "primary")
        self.prepare_button.clicked.connect(self._prepare)
        actions.addWidget(self.prepare_button)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(lambda: self.token.cancel())
        actions.addWidget(self.cancel_button)
        root.addLayout(actions)

    @property
    def busy(self) -> bool:
        return self._thread is not None

    def _inputs_tab(self) -> None:
        page = QWidget()
        layout = QHBoxLayout(page)
        sidebar = QVBoxLayout()
        self.files = QListWidget()
        self.files.setMaximumWidth(270)
        self.source_stack = QStackedWidget()
        self.files.currentRowChanged.connect(self.source_stack.setCurrentIndex)
        sidebar.addWidget(self.files)
        browse = QPushButton("Add files…")
        browse.clicked.connect(self._browse)
        sidebar.addWidget(browse)
        remove = QPushButton("Remove selected")
        remove.clicked.connect(self._remove)
        sidebar.addWidget(remove)
        layout.addLayout(sidebar)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.source_stack)
        layout.addWidget(scroll, 1)
        self.tabs.addTab(page, "1 · Input files")

    def _operation_tab(self) -> None:
        page = QWidget()
        grid = QGridLayout(page)
        self.operation = QComboBox()
        for label, action in [
            ("Split by time period", Action.SPLIT_TIME),
            ("Split parameters / field groups", Action.SPLIT_FIELDS),
            ("Join time-series files", Action.JOIN_TIME),
            ("Join parameters by timestamp", Action.JOIN_FIELDS),
        ]:
            self.operation.addItem(label, action)
        grid.addWidget(self.operation, 0, 0, 1, 2)
        general = QGroupBox("Matching & timestamps")
        self._general_box = general
        self._options_grid = grid
        form = QFormLayout(general)
        self._general_form = form
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self.output_zone = zone_combo()
        form.addRow("Boundary / output timezone", self.output_zone)
        hint = QLabel(
            "UTC or Colombo (+05:30 / +5.5 hours); type a custom IANA zone or ±HH:MM.\n"
            "Outputs use ISO timestamps with offsets, sorted by instant. "
            "Periods include the start and exclude the end."
        )
        hint.setWordWrap(True)
        form.addRow(hint)
        self.match = QComboBox()
        for label, value in [
            ("All timestamps (outer)", MatchPolicy.OUTER),
            ("Only common timestamps (inner)", MatchPolicy.INNER),
            ("First file's timestamps (left)", MatchPolicy.LEFT),
        ]:
            self.match.addItem(label, value)
        form.addRow("Field-join matching", self.match)
        self.duplicates = QComboBox()
        for label, duplicate_value in [
            ("Stop and report duplicates", DuplicatePolicy.ERROR),
            ("Keep first (input-file then row order)", DuplicatePolicy.FIRST),
            ("Keep last (input-file then row order)", DuplicatePolicy.LAST),
            ("Keep all (time join only)", DuplicatePolicy.KEEP),
        ]:
            self.duplicates.addItem(label, duplicate_value)
        form.addRow("Duplicate / overlap policy", self.duplicates)
        self.regroup = QCheckBox("Split the joined result into the chosen time periods")
        form.addRow(self.regroup)
        grid.addWidget(general, 1, 0)
        self.period_box = QGroupBox("Time-period boundaries")
        form = QFormLayout(self.period_box)
        self._period_form = form
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self.period = QComboBox()
        for label, kind in [
            ("Calendar year", PeriodKind.CALENDAR_YEAR),
            ("Month", PeriodKind.CALENDAR_MONTH),
            ("Week", PeriodKind.WEEK),
            ("Quarter", PeriodKind.QUARTER),
            ("Custom seasons", PeriodKind.SEASON),
            ("Day", PeriodKind.DAY),
        ]:
            self.period.addItem(label, kind)
        form.addRow("Period", self.period)
        self.start_time = QTimeEdit(QTime(0, 0))
        self.start_time.setDisplayFormat("HH:mm:ss")
        form.addRow("Start time in boundary timezone", self.start_time)
        self.week_start = QComboBox()
        self.week_start.addItems(
            ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        )
        form.addRow("Week starts on", self.week_start)
        self.start_month = QSpinBox()
        self.start_month.setRange(1, 12)
        form.addRow("Year / first quarter starts in month", self.start_month)
        self.start_day = QSpinBox()
        self.start_day.setRange(1, 28)
        form.addRow("Start day (month/quarter: 1-28)", self.start_day)
        self.start_day.setToolTip(
            "Annual starts also allow 29, 30 or 31 when valid in the chosen month."
        )
        self.seasons = table_widget(["Season name", "Start month", "Start day"])
        self.seasons.setRowCount(2)
        for r, values in enumerate([("Season 1", "1", "1"), ("Season 2", "7", "1")]):
            for c, season_value in enumerate(values):
                self.seasons.setItem(r, c, QTableWidgetItem(season_value))
        self.seasons.setMaximumHeight(150)
        form.addRow("Each season ends at the next start", self.seasons)
        season_buttons = QHBoxLayout()
        self._season_buttons = season_buttons
        add = QPushButton("Add season")
        add.clicked.connect(lambda: self.seasons.insertRow(self.seasons.rowCount()))
        remove = QPushButton("Remove last season")
        remove.clicked.connect(lambda: self.seasons.removeRow(self.seasons.rowCount() - 1))
        season_buttons.addWidget(add)
        season_buttons.addWidget(remove)
        form.addRow(season_buttons)
        grid.addWidget(self.period_box, 1, 1)
        self.group_box = QGroupBox("Field splitting")
        group_layout = QVBoxLayout(self.group_box)
        self.custom_groups = QCheckBox(
            "Use named groups (otherwise one output per selected parameter)"
        )
        group_layout.addWidget(self.custom_groups)
        self.groups = table_widget(["Parameter", "Output group (blank = exclude)"])
        self.groups.setMaximumHeight(180)
        group_layout.addWidget(self.groups)
        load = QPushButton("Load selected parameters into groups")
        load.clicked.connect(self._load_groups)
        group_layout.addWidget(load)
        self.shared = QListWidget()
        self.shared.setMaximumHeight(110)
        group_layout.addWidget(
            QLabel("Optional shared metadata in every field split (timestamp is automatic)")
        )
        group_layout.addWidget(self.shared)
        group_layout.addLayout(bulk_buttons(self.shared, self._invalidate))
        grid.addWidget(self.group_box, 2, 0, 1, 2)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)
        self.tabs.addTab(scroll, "2 · Split / Join options")
        for combo in (
            self.operation,
            self.output_zone,
            self.match,
            self.duplicates,
            self.period,
            self.week_start,
        ):
            combo.currentTextChanged.connect(self._invalidate)
        for control in (self.start_month, self.start_day):
            control.valueChanged.connect(self._invalidate)
        self.start_time.timeChanged.connect(self._invalidate)
        for check in (self.regroup, self.custom_groups):
            check.toggled.connect(self._invalidate)
        self.groups.itemChanged.connect(self._invalidate)
        self.seasons.itemChanged.connect(self._invalidate)
        self.shared.itemChanged.connect(self._invalidate)
        self.operation.currentIndexChanged.connect(self._mode_changed)
        self.period.currentIndexChanged.connect(self._mode_changed)
        self.regroup.toggled.connect(self._mode_changed)
        self._mode_changed()

    def _review_tab(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        self.summary = QLabel(
            "Prepare a plan to review full-source row counts and bounded samples."
        )
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)
        self.outputs = table_widget(
            ["Output name", "Rows", "Columns", "Period start", "End (exclusive)"]
        )
        self.outputs.setMaximumHeight(200)
        self.outputs.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.outputs.itemSelectionChanged.connect(self._preview)
        layout.addWidget(self.outputs)
        self.preview = table_widget([])
        layout.addWidget(self.preview, 1)
        self.planned_files = QLabel()
        self.planned_files.setWordWrap(True)
        layout.addWidget(self.planned_files)
        form = QFormLayout()
        self.destination = QLineEdit()
        folder = QPushButton("Choose folder…")
        folder.clicked.connect(self._destination)
        row = QHBoxLayout()
        row.addWidget(self.destination, 1)
        row.addWidget(folder)
        form.addRow("Export into a new run subfolder", row)
        formats = QHBoxLayout()
        self.csv = QCheckBox("CSV")
        self.csv.setChecked(True)
        self.xlsx = QCheckBox("Plain Excel")
        self.styled = QCheckBox("Formatted Excel")
        for check in (self.csv, self.xlsx, self.styled):
            formats.addWidget(check)
            check.toggled.connect(self._planned_filenames)
        form.addRow("Output formats", formats)
        form.addRow(bulk_buttons((self.csv, self.xlsx, self.styled), self._planned_filenames))
        self.null_policy = QComboBox()
        for label, value in [
            ("True null", OutputMissingPolicy.TRUE_NULL),
            ("N/A", OutputMissingPolicy.NA),
            ("-999", OutputMissingPolicy.MINUS_999),
            ("Custom", OutputMissingPolicy.CUSTOM),
        ]:
            self.null_policy.addItem(label, value)
        form.addRow("Unmatched-field output value", self.null_policy)
        self.sentinel = QLineEdit()
        form.addRow("Custom missing value", self.sentinel)
        layout.addLayout(form)
        self.export_button = QPushButton("Export & verify all outputs")
        self.export_button.setProperty("role", "primary")
        self.export_button.setEnabled(False)
        self.export_button.clicked.connect(self._export)
        layout.addWidget(self.export_button)
        self.tabs.addTab(page, "3 · Review & export")

    def _mode_changed(self) -> None:
        action = Action(self.operation.currentData())
        join = action in {Action.JOIN_FIELDS, Action.JOIN_TIME}
        self.match.setEnabled(action is Action.JOIN_FIELDS)
        self.duplicates.setEnabled(join)
        self.regroup.setEnabled(join)
        self.group_box.setVisible(action is Action.SPLIT_FIELDS)
        self.period_box.setEnabled(
            action is Action.SPLIT_TIME or (join and self.regroup.isChecked())
        )
        self.period_box.setVisible(action is not Action.SPLIT_FIELDS)
        kind = PeriodKind(self.period.currentData())
        self.start_day.setMaximum(31 if kind is PeriodKind.CALENDAR_YEAR else 28)
        self.week_start.setEnabled(kind is PeriodKind.WEEK)
        self.start_month.setEnabled(kind in {PeriodKind.QUARTER, PeriodKind.CALENDAR_YEAR})
        self.start_day.setEnabled(
            kind in {PeriodKind.QUARTER, PeriodKind.CALENDAR_YEAR, PeriodKind.CALENDAR_MONTH}
        )
        self.seasons.setEnabled(kind is PeriodKind.SEASON)
        self._general_form.setRowVisible(self.match, action is Action.JOIN_FIELDS)
        self._general_form.setRowVisible(self.duplicates, join)
        self._general_form.setRowVisible(self.regroup, join)
        self._period_form.setRowVisible(self.week_start, kind is PeriodKind.WEEK)
        self._period_form.setRowVisible(
            self.start_month, kind in {PeriodKind.QUARTER, PeriodKind.CALENDAR_YEAR}
        )
        self._period_form.setRowVisible(
            self.start_day,
            kind in {PeriodKind.QUARTER, PeriodKind.CALENDAR_YEAR, PeriodKind.CALENDAR_MONTH},
        )
        self._period_form.setRowVisible(self.seasons, kind is PeriodKind.SEASON)
        self._period_form.setRowVisible(self._season_buttons, kind is PeriodKind.SEASON)

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        if not hasattr(self, "_options_grid"):
            return
        wide = self.width() >= 1150
        self._options_grid.removeWidget(self._general_box)
        self._options_grid.removeWidget(self.period_box)
        self._options_grid.removeWidget(self.group_box)
        self._options_grid.addWidget(self._general_box, 1, 0, 1, 1 if wide else 2)
        self._options_grid.addWidget(
            self.period_box, 1 if wide else 2, 1 if wide else 0, 1, 1 if wide else 2
        )
        self._options_grid.addWidget(self.group_box, 3, 0, 1, 2)

    def _browse(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Add local data files", "", "Data (*.csv *.tsv *.txt *.xlsx)"
        )
        self.add_paths([Path(path) for path in paths])

    def add_paths(self, paths: list[Path]) -> None:
        if self.busy:
            return
        for path in paths:
            path = path.resolve()
            if any(editor.path == path for editor in self.editors):
                continue
            if path.suffix.lower() not in {".csv", ".tsv", ".txt", ".xlsx"} or not path.is_file():
                self.status.setText("Only local CSV, TSV, TXT and XLSX files are supported.")
                continue
            editor = SourceEditor(path)
            editor.changed.connect(self._invalidate)
            editor.inspect_requested.connect(lambda e=editor: self._inspect(e))
            self.editors.append(editor)
            self.source_stack.addWidget(editor)
            item = QListWidgetItem(f"S{len(self.editors)} · {path.name}")
            item.setToolTip(str(path))
            self.files.addItem(item)
        if self.editors:
            self.files.setCurrentRow(len(self.editors) - 1)
        self._invalidate()

    def _remove(self) -> None:
        index = self.files.currentRow()
        if index < 0 or self.busy:
            return
        editor = self.editors.pop(index)
        self.source_stack.removeWidget(editor)
        editor.deleteLater()
        self.files.takeItem(index)
        for i, source in enumerate(self.editors):
            self.files.item(i).setText(f"S{i + 1} · {source.path.name}")
        self._invalidate()

    def _inspect(self, editor: SourceEditor) -> None:
        self._invalidate()
        options = editor.options()
        self._start(
            lambda token, progress: FileInspector.default().inspect(
                editor.path, options, cancellation=token
            ),
            lambda value: editor.apply_inspection(cast(FileInspection, value)),
        )

    def _load_groups(self) -> None:
        try:
            fields = tuple(
                dict.fromkeys(field for editor in self.editors for field in editor.source().fields)
            )
            self.groups.setRowCount(len(fields))
            self.shared.clear()
            for index, field in enumerate(fields):
                self.groups.setItem(index, 0, readonly_item(field))
                self.groups.setItem(index, 1, QTableWidgetItem(field))
                item = QListWidgetItem(field)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked)
                self.shared.addItem(item)
        except ValueError as error:
            self.status.setText(str(error))

    def configuration(self) -> SplitJoinSpec:
        kind = PeriodKind(self.period.currentData())
        action = Action(self.operation.currentData())
        use_period = action is Action.SPLIT_TIME or (
            action in {Action.JOIN_TIME, Action.JOIN_FIELDS} and self.regroup.isChecked()
        )
        seasons: tuple[SeasonBoundary, ...] = ()
        if use_period and kind is PeriodKind.SEASON:
            seasons = tuple(
                SeasonBoundary(
                    self._text(self.seasons, r, 0),
                    int(self._text(self.seasons, r, 1)),
                    int(self._text(self.seasons, r, 2)),
                )
                for r in range(self.seasons.rowCount())
            )
        selected_time = self.start_time.time()
        period = PeriodSpec(
            kind if use_period else PeriodKind.CALENDAR_YEAR,
            day_start=time(selected_time.hour(), selected_time.minute(), selected_time.second()),
            week_start=self.week_start.currentIndex(),
            quarter_start_month=self.start_month.value(),
            year_start_month=(
                self.start_month.value() if use_period and kind is PeriodKind.CALENDAR_YEAR else 1
            ),
            year_start_day=(
                self.start_day.value() if use_period and kind is PeriodKind.CALENDAR_YEAR else 1
            ),
            seasons=seasons,
        )
        groups: dict[str, list[str]] = {}
        shared = (
            tuple(
                self.shared.item(i).text()
                for i in range(self.shared.count())
                if self.shared.item(i).checkState() == Qt.CheckState.Checked
            )
            if action is Action.SPLIT_FIELDS
            else ()
        )
        if action is Action.SPLIT_FIELDS and self.custom_groups.isChecked():
            for row in range(self.groups.rowCount()):
                name = self._text(self.groups, row, 1)
                field = self._text(self.groups, row, 0)
                if name and field not in shared:
                    groups.setdefault(name, []).append(field)
            if not groups:
                raise ValueError("Load parameters and assign at least one non-empty output group.")
        return SplitJoinSpec(
            action=action,
            boundary_timezone=self.output_zone.currentText().strip(),
            period=period,
            month_start_day=(
                self.start_day.value()
                if kind in {PeriodKind.CALENDAR_MONTH, PeriodKind.QUARTER}
                else 1
            ),
            groups=tuple(FieldGroup(name, tuple(fields)) for name, fields in groups.items()),
            shared_fields=shared,
            duplicates=DuplicatePolicy(self.duplicates.currentData()),
            match=MatchPolicy(self.match.currentData()),
            regroup_join=use_period and action in {Action.JOIN_TIME, Action.JOIN_FIELDS},
        )

    @staticmethod
    def _text(table: QTableWidget, row: int, column: int) -> str:
        item = table.item(row, column)
        return item.text().strip() if item is not None else ""

    def _prepare(self) -> None:
        try:
            sources = tuple(editor.source() for editor in self.editors)
            spec = self.configuration()
        except (ValueError, TypeError) as error:
            self.status.setText(str(error))
            return
        self._invalidate()
        self._start(
            lambda token, progress: prepare_split_join(sources, spec, token, progress),
            self._prepared,
        )

    def _prepared(self, value: object) -> None:
        self.prepared = cast(PreparedSplitJoin, value)
        outputs = self.prepared.outputs
        self.summary.setText(
            f"{len(outputs):,} output tables · {sum(self.prepared.input_rows):,} source rows · "
            f"{sum(output.table.row_count for output in outputs):,} output rows across all tables. "
            "Select an output for first/middle/last samples (up to 15 rows). "
            "Field joins label parameters S1_, S2_, etc. "
            "Review matching and duplicate choices before export."
        )
        self.outputs.setRowCount(len(outputs))
        for column, width in enumerate((380, 75, 80, 255, 255)):
            self.outputs.setColumnWidth(column, width)
        for r, output in enumerate(outputs):
            for c, item in enumerate(
                (
                    output.name,
                    output.table.row_count,
                    output.table.column_count,
                    output.period_start or "—",
                    output.period_end or "—",
                )
            ):
                self.outputs.setItem(r, c, readonly_item(item))
        self.outputs.selectRow(0)
        self.tabs.setCurrentIndex(2)
        self.status.setText(
            "Full-source plan prepared. Review samples, choose output formats, then export."
        )

    def _preview(self) -> None:
        index = self.outputs.currentRow()
        if self.prepared is None or not 0 <= index < len(self.prepared.outputs):
            return
        table = self.prepared.outputs[index].table
        positions = sorted(
            {
                r
                for start in (0, max(0, table.row_count // 2 - 2), max(0, table.row_count - 5))
                for r in range(start, min(start + 5, table.row_count))
            }
        )
        self.preview.setColumnCount(table.column_count)
        self.preview.setHorizontalHeaderLabels(table.columns)
        self.preview.setColumnWidth(0, 275)
        self.preview.setRowCount(len(positions))
        self.preview.setVerticalHeaderLabels([str(position + 1) for position in positions])
        for r, position in enumerate(positions):
            row = table.read_rows(position, 1)[0]
            for c, value in enumerate(row):
                self.preview.setItem(r, c, readonly_item("<null>" if value is None else value))
        self._planned_filenames()

    def _planned_filenames(self) -> None:
        index = self.outputs.currentRow()
        if self.prepared is None or not 0 <= index < len(self.prepared.outputs):
            self.planned_files.clear()
            return
        name = self.prepared.outputs[index].name
        names = [
            data_output_path(Path(), name, fmt).name
            for check, fmt in (
                (self.csv, OutputFormat.CSV),
                (self.xlsx, OutputFormat.XLSX_PLAIN),
                (self.styled, OutputFormat.XLSX_FORMATTED),
            )
            if check.isChecked()
        ]
        self.planned_files.setText("Automatic filenames: " + " · ".join(names))

    def _destination(self) -> None:
        selected = QFileDialog.getExistingDirectory(
            self, "Choose output parent folder", self.destination.text()
        )
        if selected:
            self.destination.setText(selected)

    def _export(self) -> None:
        if self.prepared is None:
            return
        try:
            if not self.destination.text().strip():
                raise ValueError("Choose an output folder.")
            formats = tuple(
                fmt
                for check, fmt in [
                    (self.csv, OutputFormat.CSV),
                    (self.xlsx, OutputFormat.XLSX_PLAIN),
                    (self.styled, OutputFormat.XLSX_FORMATTED),
                ]
                if check.isChecked()
            )
            plan = ExportPlan(
                Path(self.destination.text().strip()),
                "SplitJoin",
                formats,
                missing_policy=OutputMissingPolicy(self.null_policy.currentData()),
                custom_missing_sentinel=self.sentinel.text().strip() or None,
            )
        except ValueError as error:
            self.status.setText(str(error))
            return
        prepared = self.prepared
        self._start(
            lambda token, progress: export_split_join(prepared, plan, token, progress),
            self._exported,
        )

    def _exported(self, value: object) -> None:
        target = cast(Path, value)
        self.status.setText(
            "Export complete. All files reopened and verified. "
            f"Report: {target / 'SPLIT_JOIN_REPORT.json'}"
        )
        if self.prepared is not None:
            self.summary.setText(
                f"Verified export saved in {target}. "
                f"All {len(self.prepared.outputs)} output tables passed. "
                "You can change options or add files for another run."
            )

    def _invalidate(self) -> None:
        if self.busy:
            return
        if self.prepared is not None:
            self.prepared.close()
            self.prepared = None
        if hasattr(self, "export_button"):
            self.export_button.setEnabled(False)
            self.outputs.setRowCount(0)
            self.preview.setRowCount(0)
            self.planned_files.clear()
            self.summary.setText(
                "Configuration changed. Prepare again to refresh the full-source preview."
            )

    def _start(
        self,
        task: Callable[[CancellationToken, Callable[[str], None]], object],
        complete: Callable[[object], None],
    ) -> None:
        if self.busy:
            return
        self.token = CancellationToken()
        self._complete = complete
        self._thread = QThread(self)
        self.worker = SplitJoinWorker(task, self.token)
        self.worker.moveToThread(self._thread)
        self._thread.started.connect(self.worker.run)
        self.worker.completed.connect(self._completed)
        self.worker.failed.connect(self.status.setText)
        self.worker.progress.connect(self.status.setText)
        self.worker.finished.connect(self._thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self._thread.finished.connect(self._finished)
        self.tabs.setEnabled(False)
        self.prepare_button.setEnabled(False)
        self.back.setEnabled(False)
        self.export_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.status.setText("Working…")
        self._thread.start()

    def _completed(self, value: object) -> None:
        self._complete(value)

    def _finished(self) -> None:
        if self._thread is not None:
            self._thread.deleteLater()
        self._thread = None
        self.worker = None
        self.tabs.setEnabled(True)
        self.prepare_button.setEnabled(True)
        self.back.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.export_button.setEnabled(self.prepared is not None)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if (
            not self.busy
            and event.mimeData().hasUrls()
            and all(url.isLocalFile() for url in event.mimeData().urls())
        ):
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        if not self.busy and all(url.isLocalFile() for url in event.mimeData().urls()):
            self.add_paths([Path(url.toLocalFile()) for url in event.mimeData().urls()])
            event.acceptProposedAction()
