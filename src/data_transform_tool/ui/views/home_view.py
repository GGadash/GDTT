"""Home screen for selecting a GDTT processing workflow.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QGridLayout, QLabel, QVBoxLayout, QWidget

from data_transform_tool.ui.widgets.mode_card import ModeCard


class HomeView(QWidget):
    """Welcome screen with primary mode cards and progressive disclosure."""

    reformat_requested = Signal()
    averaging_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 38, 48, 38)
        layout.setSpacing(12)

        eyebrow = QLabel("PRIVATE DATA WORKSPACE  •  LOCAL  •  VERIFIABLE")
        eyebrow.setProperty("role", "eyebrow")
        layout.addWidget(eyebrow)

        title = QLabel("Shape monitoring data with confidence")
        title.setProperty("role", "title")
        title.setWordWrap(True)
        layout.addWidget(title)

        subtitle = QLabel(
            "Data forging, transitions, and aggregations—mainly for air-quality-related "
            "data—with visible decisions, clear previews, and local-only processing."
        )
        subtitle.setProperty("role", "subtitle")
        subtitle.setWordWrap(True)
        subtitle.setMaximumWidth(900)
        layout.addWidget(subtitle)
        layout.addSpacing(22)

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

        future = ModeCard(
            short_label="+",
            title="Future processing modes",
            description=(
                "The architecture reserves room for additional verification and environmental "
                "data workflows without crowding the current experience."
            ),
            button_text="Planned",
            enabled=False,
        )
        cards.addWidget(future, 0, 2)
        cards.setColumnStretch(0, 1)
        cards.setColumnStretch(1, 1)
        cards.setColumnStretch(2, 1)
        layout.addLayout(cards)
        layout.addStretch()

        privacy = QLabel(
            "Your datasets stay on this computer. No account, cloud processing, "
            "or dataset telemetry."
        )
        privacy.setProperty("role", "muted")
        privacy.setWordWrap(True)
        layout.addWidget(privacy)
