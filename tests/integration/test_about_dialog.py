"""About links, licensing and readable small-window coverage.

Copyright (c) 2026 Gadash (Akila DJ) +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from html.parser import HTMLParser

import pytest
from PySide6.QtWidgets import QTabWidget, QTextBrowser

from data_transform_tool import __version__
from data_transform_tool.app.metadata import LICENSE_TEXT
from data_transform_tool.ui.dialogs.about_dialog import AboutDialog
from data_transform_tool.ui.theme import apply_theme


class _Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.urls: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self.urls.update(value for key, value in attrs if key == "href" and value)


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_about_links_license_and_scroll(qtbot, qapp, theme) -> None:  # type: ignore[no-untyped-def]
    old_palette, old_style = qapp.palette(), qapp.styleSheet()
    try:
        apply_theme(qapp, theme, font_size=20)
        dialog = AboutDialog()
        qtbot.addWidget(dialog)
        dialog.resize(680, 500)
        dialog.show()
        browser = dialog.findChild(QTextBrowser, "aboutOverview")
        assert browser is not None
        assert browser.isReadOnly()
        assert browser.openExternalLinks()
        links = _Links()
        links.feed(browser.toHtml())
        project = "https://github.com/GGadash/GDTT"
        assert links.urls == {
            project,
            f"{project}/wiki",
            f"{project}/releases",
            f"{project}/issues",
            f"{project}/wiki/Release-Status-and-Safety",
            f"{project}/blob/main/LICENSE",
            "https://ko-fi.com/gadash",
            "https://ko-fi.com/s/00a96c800b",
        }
        text = browser.toPlainText()
        for expected in (
            __version__,
            "Copyright (c) 2026 Gadash +",
            "OpenAI Codex",
            "without warranty",
            "Entirely optional",
            "Sponsor / Donate",
            "unsigned",
            "clean-Windows",
            "does not upload your dataset",
        ):
            assert expected in text
        tabs = dialog.findChild(QTabWidget)
        assert tabs is not None
        assert [tabs.tabText(i) for i in range(tabs.count())] == [
            "About",
            "Components",
            "License",
        ]
        license_browser = tabs.widget(2)
        assert isinstance(license_browser, QTextBrowser)
        assert license_browser.toPlainText() == LICENSE_TEXT
        qtbot.waitUntil(lambda: browser.verticalScrollBar().maximum() > 0)
        browser.verticalScrollBar().setValue(browser.verticalScrollBar().maximum())
        assert browser.horizontalScrollBar().maximum() == 0
    finally:
        qapp.setPalette(old_palette)
        qapp.setStyleSheet(old_style)
