"""Strict canonical-null adapters for future CSV/TSV and XLSX exporters.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

import csv
from io import StringIO

from data_transform_tool.domain.table import CellValue, DataRow


def serialize_delimited_row(row: DataRow, *, delimiter: str = ",") -> str:
    """Serialize None as an unquoted empty field and preserve empty text as ``""``."""
    if len(delimiter) != 1:
        raise ValueError("A delimiter must be exactly one character.")
    return delimiter.join(
        "" if value is None else _serialize_non_null(value, delimiter=delimiter) for value in row
    )


def xlsx_cell_value(value: CellValue) -> CellValue:
    """Keep canonical None genuinely blank while preserving an empty source string."""
    return value


def _serialize_non_null(value: CellValue, *, delimiter: str) -> str:
    output = StringIO(newline="")
    writer = csv.writer(output, delimiter=delimiter, lineterminator="\n")
    writer.writerow([value])
    return output.getvalue().removesuffix("\n")
