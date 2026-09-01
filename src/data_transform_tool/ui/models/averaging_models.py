"""Virtualized Qt models for Phase 7 averaging fields and previews.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from datetime import date, datetime, time

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QPersistentModelIndex,
    Qt,
    Signal,
)

from data_transform_tool.app.averaging_configuration import AveragingDraft, AveragingFieldDraft
from data_transform_tool.app.averaging_preview import PreviewTable

_ROOT_INDEX = QModelIndex()


class AveragingFieldTableModel(QAbstractTableModel):
    edit_requested = Signal(int, str, object)
    HEADERS = (
        "Use",
        "Source field",
        "Detected type",
        "Missing %",
        "Aggregation rule",
        "Decision",
        "Output field",
    )

    def __init__(self) -> None:
        super().__init__()
        self._draft: AveragingDraft | None = None

    def set_draft(self, draft: AveragingDraft) -> None:
        self.beginResetModel()
        self._draft = draft
        self.endResetModel()

    def field_draft(self, row: int) -> AveragingFieldDraft:
        if self._draft is None:
            raise IndexError("No averaging draft is loaded.")
        return self._draft.fields[row]

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex = _ROOT_INDEX) -> int:
        return 0 if parent.isValid() or self._draft is None else len(self._draft.fields)

    def columnCount(self, parent: QModelIndex | QPersistentModelIndex = _ROOT_INDEX) -> int:
        return 0 if parent.isValid() else len(self.HEADERS)

    def data(
        self,
        index: QModelIndex | QPersistentModelIndex,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> object:
        if not index.isValid() or self._draft is None:
            return None
        field = self._draft.fields[index.row()]
        if index.column() == 0 and role == Qt.ItemDataRole.CheckStateRole:
            return Qt.CheckState.Checked if field.include else Qt.CheckState.Unchecked
        if role not in {Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.ToolTipRole}:
            return None
        values = (
            "",
            field.source_name,
            f"{field.detected_type.value} · {field.confidence:.0%}",
            f"{field.missing_percent:.2f}%",
            field.statistic.value.replace("_", " ").title(),
            "Confirmed" if field.statistic_confirmed else "Suggestion — confirm",
            field.output_name,
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
            self.edit_requested.emit(index.row(), "include", value == Qt.CheckState.Checked.value)
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
        return self.HEADERS[section] if orientation == Qt.Orientation.Horizontal else section + 1


class SimplePreviewTableModel(QAbstractTableModel):
    def __init__(self) -> None:
        super().__init__()
        self._table = PreviewTable((), ())

    def set_table(self, table: PreviewTable) -> None:
        self.beginResetModel()
        self._table = table
        self.endResetModel()

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex = _ROOT_INDEX) -> int:
        return 0 if parent.isValid() else len(self._table.rows)

    def columnCount(self, parent: QModelIndex | QPersistentModelIndex = _ROOT_INDEX) -> int:
        return 0 if parent.isValid() else len(self._table.headers)

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
        return _display(self._table.rows[index.row()][index.column()])

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> object:
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        return (
            self._table.headers[section]
            if orientation == Qt.Orientation.Horizontal
            else section + 1
        )


def _display(value: object | None) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.isoformat(sep=" ")
    if isinstance(value, (date, time)):
        return value.isoformat()
    return str(value)
