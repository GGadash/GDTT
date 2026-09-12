"""Home screen for selecting a GDTT processing workflow.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import QGridLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from data_transform_tool.ui.widgets.mode_card import ModeCard


class HomeView(QWidget):
    """Welcome screen with primary mode cards and progressive disclosure."""

    reformat_requested = Signal()
    averaging_requested = Signal()
    split_join_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 24, 30, 24)
        scroll.setWidget(content)
        outer.addWidget(scroll)
        layout.setSpacing(12)

        eyebrow = QLabel("ENVIRONMENTAL DATA WORKSPACE")
        eyebrow.setProperty("role", "eyebrow")
        layout.addWidget(eyebrow)

        title = QLabel("Shape monitoring data with confidence")
        title.setProperty("role", "title")
        title.setWordWrap(True)
        layout.addWidget(title)

        subtitle = QLabel(
            "Data forging, transitions, and aggregations—mainly for air-quality-related "
            "data—with visible decisions, clear previews, and verified exports."
        )
        subtitle.setProperty("role", "subtitle")
        subtitle.setWordWrap(True)
        subtitle.setMaximumWidth(900)
        layout.addWidget(subtitle)
        layout.addSpacing(10)

        section_title = QLabel("Choose a workflow")
        section_title.setProperty("role", "sectionTitle")
        layout.addWidget(section_title)

        cards = QGridLayout()
        cards.setHorizontalSpacing(18)
        cards.setVerticalSpacing(18)

        reformat = ModeCard(
            short_label="RF",
            title="Reformat / Transform",
            description=(
                "Inspect a file, standardize columns and timestamps, manage nulls and gaps, "
                "preview the plan, then export and verify the result."
            ),
            button_text="Start reformatting",
            featured=True,
        )
        reformat.activated.connect(self.reformat_requested)
        cards.addWidget(reformat, 0, 0)

        averaging = ModeCard(
            short_label="AVG",
            title="Average / Aggregate",
            description=(
                "Create transparent interval, daily, monthly, seasonal, or annual summaries "
                "with explicit completeness and field-specific statistics."
            ),
            button_text="Start averaging",
        )
        averaging.activated.connect(self.averaging_requested)
        cards.addWidget(averaging, 0, 1)

        splitter = ModeCard(
            short_label="S/J",
            title="Split / Join",
            description=(
                "Split parameters or calendar periods; join fields by timestamp or combine "
                "time-series files with explicit timezone boundaries and verified outputs."
            ),
            button_text="Start splitting / joining",
        )
        splitter.activated.connect(self.split_join_requested)
        self._cards = (reformat, averaging, splitter)
        self._card_layout = cards
        self._card_columns = 0
        self._reflow_cards()
        layout.addLayout(cards)
        layout.addStretch()

        privacy = QLabel(
            "Your datasets stay on this computer. No account, cloud processing, "
            "or dataset telemetry."
        )
        privacy.setProperty("role", "muted")
        privacy.setWordWrap(True)
        layout.addWidget(privacy)

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._reflow_cards()

    def _reflow_cards(self) -> None:
        columns = max(1, min(3, (self.width() - 60) // 320))
        if columns == self._card_columns:
            return
        self._card_columns = columns
        for index, card in enumerate(self._cards):
            self._card_layout.removeWidget(card)
            self._card_layout.addWidget(card, index // columns, index % columns)
        for column in range(3):
            self._card_layout.setColumnStretch(column, 1 if column < columns else 0)
