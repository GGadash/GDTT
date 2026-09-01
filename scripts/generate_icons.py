"""Render canonical PNG and ICO assets from the versioned SVG source.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer


def render_icon(source: Path, target: Path, size: int) -> None:
    """Render one square icon using Qt's packaged SVG/image plugins."""
    renderer = QSvgRenderer(str(source))
    if not renderer.isValid():
        raise ValueError(f"The SVG icon is invalid: {source}")
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(QColor(Qt.GlobalColor.transparent))
    painter = QPainter(image)
    try:
        renderer.render(painter)
    finally:
        painter.end()
    target.parent.mkdir(parents=True, exist_ok=True)
    if not image.save(str(target)):
        raise OSError(f"Qt could not write the icon: {target}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("src/data_transform_tool/resources/icons/data-transform-tool.svg"),
    )
    parser.add_argument(
        "--directory",
        type=Path,
        default=Path("src/data_transform_tool/resources/icons"),
    )
    args = parser.parse_args()
    render_icon(args.source, args.directory / "data-transform-tool.png", 512)
    render_icon(args.source, args.directory / "data-transform-tool.ico", 256)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
