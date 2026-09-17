"""About, credits, dependency citations, and license presentation.

Copyright (c) 2026 Gadash (Akila DJ) +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from html import escape
from importlib.metadata import PackageNotFoundError, version

from PySide6.QtGui import QPalette
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
        browser = QTextBrowser()
        browser.setObjectName("aboutOverview")
        browser.setAccessibleName("About GDTT, project links and optional support")
        browser.setOpenExternalLinks(True)
        browser.setToolTip("Links open in your default browser; no dataset is uploaded.")
        link_color = browser.palette().color(QPalette.ColorRole.Highlight).name()
        browser.document().setDefaultStyleSheet(
            f"a {{ color: {link_color}; text-decoration: underline; }}"
        )
        project = "https://github.com/GGadash/GDTT"
        browser.setHtml(
            f"<p>{escape(PRODUCT_DESCRIPTION)}</p>"
            f"<p><b>Version {escape(__version__)}</b><br>"
            f"Copyright (c) 2026 Gadash +<br>{escape(DEVELOPMENT_CREDIT)}</p>"
            "<h3>Explore GDTT</h3>"
            f'<p><a href="{project}">GitHub project</a> &middot; '
            f'<a href="{project}/wiki">User guide / Wiki</a> &middot; '
            f'<a href="{project}/releases">Downloads and releases</a><br>'
            f'<a href="{project}/issues">Report an issue / Suggest a feature</a> &middot; '
            f'<a href="{project}/wiki/Release-Status-and-Safety">Release safety</a></p>'
            "<h3>License at a glance</h3>"
            "<p>Free to use, modify and redistribute, including commercially. Provided "
            "&ldquo;as is&rdquo;, without warranty. Attribution is appreciated, not required. "
            "See the <b>License</b> tab for the full terms or "
            f'<a href="{project}/blob/main/LICENSE">read the project license online</a>. '
            "Third-party components retain their own licenses; see <b>Components</b>.</p>"
            "<hr><h3>Fuel the next transformation</h3>"
            "<p><b>Sponsor / Donate via Ko-fi</b><br>"
            "If GDTT saves you time, help support its continued development.</p>"
            '<p><a href="https://ko-fi.com/gadash">Support Gadash on Ko-fi</a> &middot; '
            '<a href="https://ko-fi.com/s/00a96c800b">GDTT project support</a></p>'
            "<p>Entirely optional: donations do not unlock features, change the license "
            "or guarantee support or delivery. You can also help by sharing feedback, "
            "reporting reproducible issues or improving the documentation.</p>"
            "<hr><p><small>Data processing stays local. External links open in your browser "
            "and require internet access; GDTT does not upload your dataset. "
            "Remove private data from issue reports.<br>"
            "Release builds are unsigned; separate hands-on clean-Windows acceptance "
            "remains pending. Back up inputs and review important results.</small></p>"
        )
        return browser

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
