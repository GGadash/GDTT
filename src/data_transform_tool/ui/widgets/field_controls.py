"""Shared explicit format, timezone and bulk-selection controls.

Copyright (c) 2026 Gadash +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QComboBox, QHBoxLayout, QListWidget, QPushButton

from data_transform_tool.datetime.custom_formats import FieldFormat, decode
from data_transform_tool.datetime.profiles import DateTimeProfileRegistry
from data_transform_tool.timezone.converter import list_iana_timezones


def kind_for_type(kind: str) -> str:
    kind = kind.casefold().split(" / ")[0]
    return (
        "number"
        if kind in {"integer", "decimal"}
        else kind
        if kind in {"date", "time", "datetime", "boolean"}
        else "text"
    )


class ProfileCombo(QComboBox):
    """Editable masks backed by stable legacy IDs or inert custom profile strings."""

    def __init__(self, *, input_profile: bool = False) -> None:
        super().__init__()
        self.input_profile = input_profile
        self.kind = "text"
        self.decimal = "."
        self.preserve = False
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.setMinimumContentsLength(14)
        self.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.setMaxVisibleItems(12)
        self.setToolTip(
            "Choose a preset or Custom and type a mask. Numeric masks use . for precision "
            "and , for grouping; decimal separator is selected separately. "
            "Text: @ or prefix {value} suffix. Boolean: Yes|No."
        )
        self.activated.connect(self._custom)

    def _custom(self) -> None:
        data = self.currentData()
        if isinstance(data, str) and data.startswith("custom:"):
            self.kind = data.partition(":")[2]
            self.setEditText("")
            editor = self.lineEdit()
            assert editor is not None
            editor.setPlaceholderText(
                {
                    "number": "0.00",
                    "date": "yyyy-MM-dd",
                    "time": "HH:mm:ss",
                    "datetime": "yyyy-MM-dd HH:mm:ss",
                    "text": "@",
                    "boolean": "Yes|No",
                }[self.kind]
            )
            editor.setFocus()

    def load(self, profile: str | None, kind: str) -> None:
        blocked = self.blockSignals(True)
        self.kind = kind_for_type(kind)
        self.clear()
        self.addItem("Auto / unchanged" if self.input_profile else "As source", None)
        for item in DateTimeProfileRegistry.default().all():
            if self.input_profile or item.temporal_kind.value == self.kind:
                self.addItem(item.display_pattern, item.profile_id)
        presets = {
            "number": ("0.00", "0", "#,##0.00", "0.000", "0.###"),
            "text": ("@", "{value}"),
            "boolean": ("True|False", "Yes|No", "1|0"),
        }
        for category, patterns in presets.items():
            if self.input_profile or category == self.kind:
                for pattern in patterns:
                    self.addItem(pattern, FieldFormat(category, pattern).encode())
        for category in (
            ("number", "date", "time", "datetime", "text", "boolean")
            if self.input_profile
            else (self.kind,)
        ):
            self.addItem(f"Custom {category}…", f"custom:{category}")
        custom = decode(profile)
        if custom and self.input_profile:
            self.kind = custom.kind
        self.decimal = custom.decimal if custom else "."
        self.preserve = custom.preserve if custom else False
        if profile is not None and self.findData(profile) < 0:
            self.addItem(custom.pattern if custom else profile, profile)
        self.setCurrentIndex(max(0, self.findData(profile)))
        self.blockSignals(blocked)

    def profile(self) -> str | None:
        text = self.currentText().strip()
        index = self.currentIndex()
        data = self.currentData() if index >= 0 and text == self.itemText(index) else None
        if data is None and index == 0 and text == self.itemText(0):
            if self.decimal == "," or (self.preserve and not self.input_profile):
                return FieldFormat("number", "0.00", self.decimal, self.preserve).encode()
            return None
        if isinstance(data, str) and not data.startswith("custom:"):
            spec = decode(data)
            if spec is None:
                return data
            return FieldFormat(
                spec.kind,
                spec.pattern,
                self.decimal,
                self.preserve if not self.input_profile else False,
            ).encode()
        return FieldFormat(
            self.kind, text, self.decimal, self.preserve if not self.input_profile else False
        ).encode()


def fill_zones(combo: QComboBox) -> None:
    value = combo.currentText()
    blocked = combo.blockSignals(True)
    combo.clear()
    combo.setEditable(True)
    combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
    combo.addItems(["UTC", "Asia/Colombo", "Custom…"])
    offsets = [
        f"{'+' if minutes >= 0 else '-'}{abs(minutes) // 60:02d}:{abs(minutes) % 60:02d}"
        for minutes in range(-12 * 60, 14 * 60 + 1, 30)
    ]
    combo.addItems(
        offsets + [zone for zone in list_iana_timezones() if zone not in {"UTC", "Asia/Colombo"}]
    )
    combo.setMinimumContentsLength(16)
    combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
    combo.setMaxVisibleItems(12)
    combo.setToolTip(
        "UTC; Colombo = +05:30. Choose an offset or named zone, or type a custom zone. "
        "Named zones retain historical/DST rules."
    )
    combo.setCurrentText(value or "UTC")
    combo.blockSignals(blocked)
    if not combo.property("customZoneConnected"):
        combo.activated.connect(
            lambda: combo.setEditText("") if combo.currentText() == "Custom…" else None
        )
        combo.setProperty("customZoneConnected", True)


def bulk_buttons(
    target: QListWidget | tuple[QCheckBox, ...],
    callback: Callable[[], None] | None = None,
) -> QHBoxLayout:
    row = QHBoxLayout()

    def select(checked: bool) -> None:
        if isinstance(target, QListWidget):
            blocked = target.blockSignals(True)
            for index in range(target.count()):
                item = target.item(index)
                if item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                    item.setCheckState(
                        Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
                    )
            target.blockSignals(blocked)
        else:
            for check in target:
                blocked = check.blockSignals(True)
                check.setChecked(checked)
                check.blockSignals(blocked)
        if callback is not None:
            callback()

    for label, checked in (("Select all", True), ("Deselect all", False)):
        button = QPushButton(label)
        button.setProperty("role", "compact")
        button.setToolTip(
            "Select/deselect every item in this group, not other settings or confirmations."
        )
        button.clicked.connect(lambda unused=False, state=checked: select(state))
        row.addWidget(button)
    row.addStretch()
    return row
