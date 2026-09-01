# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller onedir specification for GDTT.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from pathlib import Path

import PySide6
from PyInstaller.utils.hooks import copy_metadata

repository = Path(SPECPATH).resolve().parent
source = repository / "src"
icon = source / "data_transform_tool" / "resources" / "icons" / "data-transform-tool.ico"
version_file = repository / "packaging" / "temp" / "windows_version_info.txt"
pyside_directory = Path(PySide6.__file__).resolve().parent
codecvt_runtime = pyside_directory / "msvcp140_codecvt_ids.dll"
if not codecvt_runtime.is_file():
    raise FileNotFoundError(f"Required PySide6 runtime is missing: {codecvt_runtime}")

datas = [
    (str(source / "data_transform_tool" / "resources"), "data_transform_tool/resources"),
    (str(repository / "LICENSE"), "."),
    (str(repository / "THIRD_PARTY_NOTICES.md"), "."),
]
for distribution in (
    "data-transform-tool",
    "PySide6",
    "pydantic",
    "platformdirs",
    "tzdata",
    "charset-normalizer",
    "openpyxl",
    "XlsxWriter",
):
    datas += copy_metadata(distribution)

analysis = Analysis(
    [str(source / "data_transform_tool" / "__main__.py")],
    pathex=[str(source)],
    binaries=[(str(codecvt_runtime), "PySide6")],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter"],
    noarchive=False,
    optimize=1,
)
python_archive = PYZ(analysis.pure)

executable = EXE(
    python_archive,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="GDTT",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    icon=str(icon),
    version=str(version_file),
)

bundle = COLLECT(
    executable,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="GDTT",
)
