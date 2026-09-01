"""Deterministic Windows-safe RF/AVG output naming.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

import re
from datetime import date, datetime, time
from pathlib import Path

from data_transform_tool.domain.batches import TabularData, iter_rows
from data_transform_tool.domain.table import CellValue
from data_transform_tool.transformation.recipe import OutputFormat

_INVALID = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_RESERVED = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def sanitize_windows_name(value: str, *, fallback: str = "Data_Transform_Output") -> str:
    cleaned = _INVALID.sub("_", value).strip().rstrip(". ")
    cleaned = re.sub(r"\s+", "_", cleaned)
    if not cleaned:
        cleaned = fallback
    if cleaned.upper() in _RESERVED:
        cleaned = f"_{cleaned}"
    return cleaned[:180]


def suggest_base_name(source: Path, table: TabularData, mode: str) -> str:
    stem = sanitize_windows_name(source.stem)
    temporal = _temporal_range(table)
    range_part = f"_{temporal[0]}_to_{temporal[1]}" if temporal is not None else ""
    suffix = "AVG" if mode == "average" else "RF"
    return sanitize_windows_name(f"{stem}{range_part}_{suffix}")


def data_output_path(destination: Path, base_name: str, output: OutputFormat) -> Path:
    base = sanitize_windows_name(base_name)
    suffix = {
        OutputFormat.CSV: ".csv",
        OutputFormat.XLSX_PLAIN: "_P.xlsx",
        OutputFormat.XLSX_FORMATTED: "_F.xlsx",
    }[output]
    return destination / f"{base}{suffix}"


def _temporal_range(table: TabularData) -> tuple[str, str] | None:
    candidates = tuple(
        index
        for index, name in enumerate(table.columns)
        if "time" in name.casefold() or name.casefold() in {"date", "period_start"}
    )
    for index in candidates:
        first: CellValue = None
        last: CellValue = None
        for row in iter_rows(table):
            value = row[index]
            if value is None:
                continue
            if first is None:
                first = value
            last = value
        if first is not None and last is not None:
            return _time_label(first), _time_label(last)
    return None


def _time_label(value: CellValue) -> str:
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d_%Hh%M")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, time):
        return value.strftime("%Hh%M")
    text = str(value).strip()
    text = re.sub(r"[^0-9A-Za-z_-]+", "-", text)
    return text[:24] or "unknown"
