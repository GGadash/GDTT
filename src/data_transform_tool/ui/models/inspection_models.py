"""Virtualized Qt table adapters for immutable inspection results.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from datetime import date, datetime, time

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QPersistentModelIndex, Qt

from data_transform_tool.io.models import ColumnProfile, PreviewSlice

_ROOT_INDEX = QModelIndex()


class ColumnProfileTableModel(QAbstractTableModel):
    """Present column profiles without copying data into table widgets."""

    _HEADERS = (
        "Column",
        "Detected type",
        "Confidence",
        "Potential missing",
        "Unique sample",
        "Examples",
        "Status",
    )

    def __init__(self, columns: tuple[ColumnProfile, ...]) -> None:
        super().__init__()
        self._columns = columns

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex = _ROOT_INDEX) -> int:
        return 0 if parent.isValid() else len(self._columns)

    def columnCount(self, parent: QModelIndex | QPersistentModelIndex = _ROOT_INDEX) -> int:
        return 0 if parent.isValid() else len(self._HEADERS)

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
        profile = self._columns[index.row()]
        values = (
            profile.name,
            profile.inferred_type.value,
            f"{profile.confidence:.0%}",
            f"{profile.missing_percent:.2f}%",
            str(profile.unique_sample_count),
            " · ".join(profile.examples) or "—",
            _profile_status(profile),
        )
        return values[index.column()]

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> object:
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return self._HEADERS[section]
        return section + 1


class PreviewTableModel(QAbstractTableModel):
    """Present a bounded first/middle/last preview with real source row numbers."""

    def __init__(self, headers: tuple[str, ...], preview: PreviewSlice) -> None:
        super().__init__()
        self._headers = headers
        self._preview = preview

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex = _ROOT_INDEX) -> int:
        return 0 if parent.isValid() else len(self._preview.rows)

    def columnCount(self, parent: QModelIndex | QPersistentModelIndex = _ROOT_INDEX) -> int:
        return 0 if parent.isValid() else len(self._headers)

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
        value = self._preview.rows[index.row()][index.column()]
        return _display_value(value)

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> object:
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return self._headers[section]
        return self._preview.start_row + section


def _profile_status(profile: ColumnProfile) -> str:
    statuses: list[str] = []
    if profile.entirely_empty:
        statuses.append("Empty")
    statuses.extend(profile.warnings)
    return " • ".join(statuses) or "Ready to review"


def _display_value(value: object | None) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.isoformat(sep=" ")
    if isinstance(value, (date, time)):
        return value.isoformat()
    return str(value)
