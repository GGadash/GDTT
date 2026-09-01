"""Accessible semantic themes for the GDTT desktop shell.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from data_transform_tool.settings.models import ThemePreference


@dataclass(frozen=True)
class ThemeColors:
    canvas: str
    surface: str
    surface_alt: str
    border: str
    text: str
    muted: str
    primary: str
    primary_hover: str
    primary_text: str
    accent: str
    warning: str
    success: str


LIGHT = ThemeColors(
    canvas="#F3F7F7",
    surface="#FFFFFF",
    surface_alt="#E9F1F1",
    border="#CAD9D8",
    text="#102524",
    muted="#526B69",
    primary="#096B66",
    primary_hover="#075954",
    primary_text="#FFFFFF",
    accent="#0E92A0",
    warning="#A86408",
    success="#2B7A47",
)

DARK = ThemeColors(
    canvas="#101A1B",
    surface="#182526",
    surface_alt="#203031",
    border="#344849",
    text="#EFF8F7",
    muted="#A8BCBA",
    primary="#46BDB3",
    primary_hover="#69CEC5",
    primary_text="#09211F",
    accent="#55C4D1",
    warning="#F2B455",
    success="#7BD39A",
)


def effective_theme(app: QApplication, preference: ThemePreference) -> str:
    """Resolve Auto to Light or Dark while preserving explicit selections."""
    if preference != "auto":
        return preference
    color_scheme = app.styleHints().colorScheme()
    return "dark" if color_scheme == Qt.ColorScheme.Dark else "light"


def apply_theme(app: QApplication, preference: ThemePreference) -> None:
    """Apply semantic colors to widgets and native Qt controls."""
    resolved_theme = effective_theme(app, preference)
    if resolved_theme == "system":
        app.setPalette(app.style().standardPalette())
        colors = _system_colors(app.palette())
        app.setStyleSheet(_style_sheet(colors))
        return

    colors = DARK if resolved_theme == "dark" else LIGHT
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(colors.canvas))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(colors.text))
    palette.setColor(QPalette.ColorRole.Base, QColor(colors.surface))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(colors.surface_alt))
    palette.setColor(QPalette.ColorRole.Text, QColor(colors.text))
    palette.setColor(QPalette.ColorRole.Button, QColor(colors.surface_alt))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(colors.text))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(colors.primary))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(colors.primary_text))
    app.setPalette(palette)
    app.setStyleSheet(_style_sheet(colors))


def _system_colors(palette: QPalette) -> ThemeColors:
    """Derive semantic tokens from Qt's current system palette."""
    return ThemeColors(
        canvas=palette.color(QPalette.ColorRole.Window).name(),
        surface=palette.color(QPalette.ColorRole.Base).name(),
        surface_alt=palette.color(QPalette.ColorRole.AlternateBase).name(),
        border=palette.color(QPalette.ColorRole.Mid).name(),
        text=palette.color(QPalette.ColorRole.WindowText).name(),
        muted=palette.color(QPalette.ColorRole.PlaceholderText).name(),
        primary="#087F78",
        primary_hover="#066760",
        primary_text="#FFFFFF",
        accent="#0FA5B3",
        warning="#B66B08",
        success="#2B8A50",
    )


def _style_sheet(c: ThemeColors) -> str:
    return f"""
    * {{
        font-family: "Segoe UI Variable", "Segoe UI";
        font-size: 14px;
    }}
    QMainWindow, QWidget#AppRoot {{ background: {c.canvas}; color: {c.text}; }}
    QLabel {{ color: {c.text}; background: transparent; }}
    QLabel[role="eyebrow"] {{
        color: {c.primary}; font-size: 12px; font-weight: 700;
        letter-spacing: 1px;
    }}
    QLabel[role="title"] {{ font-size: 34px; font-weight: 700; }}
    QLabel[role="subtitle"] {{ color: {c.muted}; font-size: 16px; }}
    QLabel[role="sectionTitle"] {{ font-size: 21px; font-weight: 650; }}
    QLabel[role="muted"] {{ color: {c.muted}; }}
    QLabel[role="badge"] {{
        color: {c.success}; background: {c.surface_alt}; border: 1px solid {c.border};
        border-radius: 12px; padding: 4px 10px; font-size: 12px; font-weight: 650;
    }}
    QFrame[role="header"], QFrame[role="footer"] {{
        background: {c.surface}; border-bottom: 1px solid {c.border};
    }}
    QFrame[role="footer"] {{ border-top: 1px solid {c.border}; border-bottom: none; }}
    QFrame[role="modeCard"] {{
        background: {c.surface}; border: 1px solid {c.border}; border-radius: 20px;
    }}
    QFrame[role="modeCard"][featured="true"] {{ border: 2px solid {c.primary}; }}
    QLabel[role="cardIcon"] {{
        color: {c.primary}; background: {c.surface_alt}; border-radius: 18px;
        font-size: 16px; font-weight: 800; padding: 9px;
    }}
    QLabel[role="cardTitle"] {{ font-size: 20px; font-weight: 700; }}
    QLabel[role="cardDescription"] {{ color: {c.muted}; line-height: 1.35; }}
    QLabel[role="samplePanel"] {{
        color: {c.text}; background: {c.surface_alt}; border: 1px solid {c.border};
        border-radius: 9px; padding: 10px; font-family: "Cascadia Mono", "Consolas";
        font-size: 12px;
    }}
    QPushButton {{
        color: {c.text}; background: {c.surface_alt}; border: 1px solid {c.border};
        border-radius: 8px; padding: 9px 16px; font-weight: 650;
    }}
    QPushButton:hover {{ border-color: {c.primary}; }}
    QPushButton:focus {{ border: 2px solid {c.accent}; }}
    QPushButton[role="primary"] {{
        color: {c.primary_text}; background: {c.primary}; border-color: {c.primary};
    }}
    QPushButton[role="primary"]:hover {{ background: {c.primary_hover}; }}
    QPushButton[role="ghost"] {{ background: transparent; border-color: transparent; }}
    QPushButton[role="ghost"]:hover {{ background: {c.surface_alt}; border-color: {c.border}; }}
    QPushButton:disabled {{ color: {c.muted}; background: {c.surface_alt}; }}
    QComboBox, QSpinBox, QDoubleSpinBox {{
        color: {c.text}; background: {c.surface_alt}; border: 1px solid {c.border};
        border-radius: 8px; padding: 7px 28px 7px 10px;
    }}
    QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{ border: 2px solid {c.accent}; }}
    QComboBox QAbstractItemView {{
        color: {c.text}; background: {c.surface}; selection-background-color: {c.primary};
        selection-color: {c.primary_text}; border: 1px solid {c.border};
    }}
    QToolTip {{
        color: {c.text}; background: {c.surface}; border: 1px solid {c.border}; padding: 5px;
    }}
    QLabel[role="dialogTitle"] {{ font-size: 26px; font-weight: 750; }}
    QTabWidget::pane {{
        border: 1px solid {c.border}; border-radius: 10px; background: {c.surface};
    }}
    QTabBar::tab {{ padding: 9px 16px; color: {c.muted}; }}
    QTabBar::tab:selected {{
        color: {c.primary}; font-weight: 700; border-bottom: 2px solid {c.primary};
    }}
    QTableView {{
        background: {c.surface}; alternate-background-color: {c.surface_alt}; color: {c.text};
        border: 1px solid {c.border}; border-radius: 10px; gridline-color: {c.border};
        selection-background-color: {c.primary}; selection-color: {c.primary_text};
    }}
    QGroupBox {{
        color: {c.text}; background: {c.surface}; border: 1px solid {c.border};
        border-radius: 12px; margin-top: 12px; padding: 14px 10px 10px 10px;
        font-weight: 700;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin; left: 12px; padding: 0 6px; color: {c.primary};
    }}
    QCheckBox {{ color: {c.text}; spacing: 8px; }}
    QCheckBox::indicator {{
        width: 17px; height: 17px; border: 1px solid {c.border}; border-radius: 4px;
        background: {c.surface_alt};
    }}
    QCheckBox::indicator:checked {{ background: {c.primary}; border-color: {c.primary}; }}
    QScrollArea {{ background: transparent; border: none; }}
    QSplitter::handle {{ background: {c.border}; width: 1px; }}
    QHeaderView::section {{
        background: {c.surface_alt}; color: {c.text}; border: none;
        border-bottom: 1px solid {c.border}; padding: 8px; font-weight: 700;
    }}
    QLineEdit, QListWidget {{
        background: {c.surface}; color: {c.text}; border: 1px solid {c.border};
        border-radius: 8px; padding: 8px;
    }}
    QProgressBar {{
        border: 1px solid {c.border}; border-radius: 6px; background: {c.surface_alt};
        text-align: center;
    }}
    QProgressBar::chunk {{ background: {c.primary}; border-radius: 5px; }}
    """
