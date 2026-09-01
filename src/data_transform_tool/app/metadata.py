"""Product metadata and third-party citations shown by the About dialog.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ComponentCitation:
    """Describe one product used by the application and where it comes from."""

    distribution: str | None
    name: str
    purpose: str
    project_url: str
    version_label: str | None = None


PRODUCT_NAME = "GDTT"
PRODUCT_FORMAL_NAME = "GDTT — Data Transform Tool by Gadash (Akila DJ)"
PRODUCT_DESCRIPTION = (
    f"{PRODUCT_FORMAL_NAME} is a local, offline-first workspace for data forging, "
    "transitions, and aggregations—mainly for air-quality-related and other "
    "environmental time-series data."
)
COPYRIGHT_NOTICE = "Copyright (c) 2026 Akila DJ +"
DEVELOPMENT_CREDIT = "AI-assisted architecture and development with OpenAI Codex."

LICENSE_TEXT = """Copyright (c) 2026 Akila DJ +

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies, without restriction.

The software is provided "as is", without warranty of any kind, express or
implied. In no event shall the authors or copyright holders be liable for any
claim or damages arising from its use.

Attribution is not legally required, but citing GDTT / Data Transform Tool by Gadash (Akila DJ)
is greatly appreciated if this project is useful to you."""

COMPONENT_CITATIONS = (
    ComponentCitation(
        "PySide6",
        "PySide6 / Qt for Python",
        "Desktop interface",
        "https://doc.qt.io/qtforpython-6/",
    ),
    ComponentCitation(
        "pydantic", "Pydantic", "Validated configuration", "https://docs.pydantic.dev/"
    ),
    ComponentCitation(
        "platformdirs",
        "platformdirs",
        "Local application paths",
        "https://platformdirs.readthedocs.io/",
    ),
    ComponentCitation("tzdata", "tzdata", "IANA timezone data", "https://pypi.org/project/tzdata/"),
    ComponentCitation(
        "charset-normalizer",
        "charset-normalizer",
        "Text encoding detection",
        "https://charset-normalizer.readthedocs.io/",
    ),
    ComponentCitation(
        "openpyxl",
        "openpyxl",
        "Streaming XLSX inspection and verification",
        "https://openpyxl.readthedocs.io/",
    ),
    ComponentCitation(
        "XlsxWriter",
        "XlsxWriter",
        "Plain and formatted XLSX export",
        "https://xlsxwriter.readthedocs.io/",
    ),
    ComponentCitation(
        None,
        "PyInstaller",
        "Windows portable packaging (build-time)",
        "https://pyinstaller.org/",
        "6.22.2 build tool",
    ),
    ComponentCitation(
        None,
        "NSIS",
        "Windows installer creation (build-time)",
        "https://nsis.sourceforge.io/",
        "3.12 build tool",
    ),
)
