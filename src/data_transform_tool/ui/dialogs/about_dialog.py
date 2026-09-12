"""About, credits, dependency citations, and license presentation.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from html import escape
from importlib.metadata import PackageNotFoundError, version

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from data_transform_tool import __version__
from data_transform_tool.app.metadata import (
    COMPONENT_CITATIONS,
    DEVELOPMENT_CREDIT,
    LICENSE_TEXT,
    PRODUCT_DESCRIPTION,
    PRODUCT_NAME,
)


class AboutDialog(QDialog):
    """Keep authorship and dependency information available without UI clutter."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"About {PRODUCT_NAME}")
        self.setMinimumSize(680, 500)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 18)
        layout.setSpacing(16)

        heading = QLabel(PRODUCT_NAME)
        heading.setProperty("role", "dialogTitle")
        layout.addWidget(heading)

        tabs = QTabWidget()
        tabs.addTab(self._about_tab(), "About")
        tabs.addTab(self._components_tab(), "Components")
        tabs.addTab(self._license_tab(), "License")
        layout.addWidget(tabs, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _about_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)
        description = QLabel(PRODUCT_DESCRIPTION)
        description.setWordWrap(True)
        description.setProperty("role", "subtitle")
        layout.addWidget(description)
        layout.addSpacing(12)
        details = QLabel(
            f"Version {__version__}\n\nCopyright (c) 2026 Gadash +\n{DEVELOPMENT_CREDIT}\n\n"
            "Datasets are processed locally. No account or cloud upload is required."
        )
        details.setWordWrap(True)
        details.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(details)
        layout.addStretch()
        return page

    def _components_tab(self) -> QWidget:
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        entries = []
        for component in COMPONENT_CITATIONS:
            component_version = component.version_label
            if component_version is None:
                try:
                    component_version = version(component.distribution or "")
                except PackageNotFoundError:
                    component_version = "not installed"
            entries.append(
                '<li><b>{name}</b> {version} — {purpose}<br><a href="{url}">{url}</a></li>'.format(
                    name=escape(component.name),
                    version=escape(component_version),
                    purpose=escape(component.purpose),
                    url=escape(component.project_url),
                )
            )
        browser.setHtml(
            "<h3>Products and libraries used</h3>"
            "<p>Each component remains subject to its own license.</p><ul>"
            + "".join(entries)
            + "</ul><p>Development collaborator: OpenAI Codex — "
            '<a href="https://openai.com/codex/">https://openai.com/codex/</a></p>'
        )
        return browser

    def _license_tab(self) -> QWidget:
        browser = QTextBrowser()
        browser.setPlainText(LICENSE_TEXT)
        return browser
