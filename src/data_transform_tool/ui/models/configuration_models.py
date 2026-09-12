"""Virtualized Qt models for Phase 5 mapping and proposed-output previews.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from datetime import date, datetime, time

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QPersistentModelIndex,
    QSortFilterProxyModel,
    Qt,
    Signal,
)

from data_transform_tool.app.reformat_configuration import (
    ColumnDraft,
    ReformatDraft,
    TransformChoice,
)
from data_transform_tool.app.reformat_preview import ProposedPreview
from data_transform_tool.datetime.custom_formats import profile_label
from data_transform_tool.io.models import SemanticType

_ROOT_INDEX = QModelIndex()


class MappingTableModel(QAbstractTableModel):
    """Editable mapping rows backed by an immutable draft owned by the view."""

    edit_requested = Signal(int, str, object)

    HEADERS = (
        "Export",
        "Input column",
        "Status",
        "Detected type",
        "Input profile",
        "Missing %",
        "Output column",
        "Output type",
        "Output format",
        "Transformations",
        "Gap behavior",
    )

    def __init__(self, draft: ReformatDraft | None = None) -> None:
        super().__init__()
        self._draft = draft

    def set_draft(self, draft: ReformatDraft) -> None:
        self.beginResetModel()
        self._draft = draft
        self.endResetModel()

    def column_draft(self, row: int) -> ColumnDraft:
        if self._draft is None:
            raise IndexError("No configuration draft is loaded.")
        return self._draft.columns[row]

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex = _ROOT_INDEX) -> int:
        return 0 if parent.isValid() or self._draft is None else len(self._draft.columns)

    def columnCount(self, parent: QModelIndex | QPersistentModelIndex = _ROOT_INDEX) -> int:
        return 0 if parent.isValid() else len(self.HEADERS)

    def data(
        self,
        index: QModelIndex | QPersistentModelIndex,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> object:
        if not index.isValid() or self._draft is None:
            return None
        column = self._draft.columns[index.row()]
        if index.column() == 0 and role == Qt.ItemDataRole.CheckStateRole:
            return Qt.CheckState.Checked if column.export else Qt.CheckState.Unchecked
        if role not in {Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.ToolTipRole}:
            return None
        values = (
            "",
            column.source_name,
            _status(column),
            f"{column.detected_type.value} · {column.confidence:.0%}",
            profile_label(column.input_profile, "Auto / unchanged"),
            f"{column.missing_percent:.2f}%",
            column.output_name,
            column.output_type.value,
            profile_label(column.output_profile, "As source"),
            _transformation_label(column),
            column.gap_behavior.value.replace("_", " ").title(),
        )
        return values[index.column()]

    def setData(
        self,
        index: QModelIndex | QPersistentModelIndex,
        value: object,
        role: int = Qt.ItemDataRole.EditRole,
    ) -> bool:
        if not index.isValid() or self._draft is None:
            return False
        if index.column() == 0 and role == Qt.ItemDataRole.CheckStateRole:
            self.edit_requested.emit(index.row(), "export", value == Qt.CheckState.Checked.value)
            return True
        if index.column() == 6 and role == Qt.ItemDataRole.EditRole:
            text = str(value).strip()
            if text:
                self.edit_requested.emit(index.row(), "output_name", text)
                return True
        return False

    def flags(self, index: QModelIndex | QPersistentModelIndex) -> Qt.ItemFlag:
        flags = super().flags(index)
        if not index.isValid():
            return flags
        if index.column() == 0:
            return flags | Qt.ItemFlag.ItemIsUserCheckable
        if index.column() == 6:
            return flags | Qt.ItemFlag.ItemIsEditable
        return flags

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> object:
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return self.HEADERS[section]
        return section + 1


class ConfigurationFilterProxyModel(QSortFilterProxyModel):
    """Search plus useful Phase 5 field groups without mutating source order."""

    def __init__(self) -> None:
        super().__init__()
        self._group = "all"
        self.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.setFilterKeyColumn(-1)

    def set_group(self, group: str) -> None:
        self._group = group
        self.invalidateFilter()

    def filterAcceptsRow(
        self,
        source_row: int,
        source_parent: QModelIndex | QPersistentModelIndex,
    ) -> bool:
        if not super().filterAcceptsRow(source_row, source_parent):
            return False
        source = self.sourceModel()
        if not isinstance(source, MappingTableModel):
            return True
        column = source.column_draft(source_row)
        if self._group == "exported":
            return column.export
        if self._group == "warnings":
            return bool(column.warnings or column.entirely_empty)
        if self._group == "temporal":
            return column.output_type in {
                SemanticType.DATE,
                SemanticType.TIME,
                SemanticType.DATETIME,
            }
        if self._group == "numeric":
            return column.is_numeric
        return True


class ProposedPreviewTableModel(QAbstractTableModel):
    def __init__(self, preview: ProposedPreview | None = None) -> None:
        super().__init__()
        self._preview = preview or ProposedPreview((), (), 1)

    def set_preview(self, preview: ProposedPreview) -> None:
        self.beginResetModel()
        self._preview = preview
        self.endResetModel()

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex = _ROOT_INDEX) -> int:
        return 0 if parent.isValid() else len(self._preview.rows)

    def columnCount(self, parent: QModelIndex | QPersistentModelIndex = _ROOT_INDEX) -> int:
        return 0 if parent.isValid() else len(self._preview.headers)

    def data(
        self,
        index: QModelIndex | QPersistentModelIndex,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> object:
        if not index.isValid() or role not in {
            Qt.ItemDataRole.DisplayRole,
            Qt.ItemDataRole.ToolTipRole,
        }:
            return None
        return _display_value(self._preview.rows[index.row()][index.column()])

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> object:
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return self._preview.headers[section]
        return self._preview.source_row_start + section


def _status(column: ColumnDraft) -> str:
    if column.entirely_empty:
        return "○ Empty"
    if column.warnings:
        return "⚠ Review"
    if not column.export:
        return "— Excluded"
    return "✓ Ready"


def _transformation_label(column: ColumnDraft) -> str:
    labels: list[str] = []
    if column.transform is not TransformChoice.KEEP:
        labels.append(column.transform.value.replace("_", " "))
    if column.target_timezone:
        labels.append(f"→ {column.target_timezone}")
    if any((column.derive_start, column.derive_midpoint, column.derive_end)):
        labels.append("derive interval")
    return " · ".join(labels) or "Keep as is"


def _display_value(value: object | None) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.isoformat(sep=" ")
    if isinstance(value, (date, time)):
        return value.isoformat()
    return str(value)
