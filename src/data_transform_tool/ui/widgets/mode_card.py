"""Large accessible workflow entry card.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class ModeCard(QFrame):
    """Present one major processing mode with a single clear action."""

    activated = Signal()

    def __init__(
        self,
        *,
        short_label: str,
        title: str,
        description: str,
        button_text: str,
        featured: bool = False,
        enabled: bool = True,
    ) -> None:
        super().__init__()
        self.setProperty("role", "modeCard")
        self.setProperty("featured", featured)
        self.setMinimumHeight(224)
        self.setAccessibleName(title)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(26)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(8, 45, 43, 32))
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        icon_row = QHBoxLayout()
        icon = QLabel(short_label)
        icon.setProperty("role", "cardIcon")
        icon.setFixedSize(48, 48)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_row.addWidget(icon)
        icon_row.addStretch()
        layout.addLayout(icon_row)

        title_label = QLabel(title)
        title_label.setProperty("role", "cardTitle")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        description_label = QLabel(description)
        description_label.setProperty("role", "cardDescription")
        description_label.setWordWrap(True)
        layout.addWidget(description_label)
        layout.addStretch()

        self.action_button = QPushButton(button_text)
        self.action_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.action_button.setProperty("role", "primary" if featured else "secondary")
        self.action_button.setEnabled(enabled)
        self.action_button.clicked.connect(self.activated)
        layout.addWidget(self.action_button)
