"""Generate PyInstaller Windows version metadata from the canonical app version.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from data_transform_tool import __version__


def version_tuple(version: str) -> tuple[int, int, int, int]:
    """Convert the semantic core to the four integers required by Windows."""
    core = version.split("+", 1)[0].split("-", 1)[0]
    parts = tuple(int(part) for part in core.split("."))
    if not 1 <= len(parts) <= 4:
        raise ValueError(f"Unsupported application version: {version}")
    return (*parts, *(0 for _ in range(4 - len(parts))))


def version_resource(version: str) -> str:
    """Return PyInstaller's text representation of a Windows version resource."""
    numbers = version_tuple(version)
    return f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={numbers},
    prodvers={numbers},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '040904B0',
        [StringStruct('CompanyName', 'Gadash (Akila DJ)'),
         StringStruct('FileDescription', 'GDTT — Data Transform Tool by Gadash (Akila DJ)'),
         StringStruct('FileVersion', '{version}'),
         StringStruct('InternalName', 'GDTT'),
         StringStruct('LegalCopyright', 'Copyright (c) 2026 Akila DJ +'),
         StringStruct('OriginalFilename', 'GDTT.exe'),
         StringStruct('ProductName', 'GDTT'),
         StringStruct('ProductVersion', '{version}'),
         StringStruct('Comments', 'AI-assisted development with OpenAI Codex.')])
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(version_resource(__version__), encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
