"""Shared bounded-memory inspection for tabular row streams.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from collections import Counter, deque
from collections.abc import Callable, Iterator, Sequence
from pathlib import Path

from data_transform_tool.io.cancellation import CancellationToken
from data_transform_tool.io.models import FileInspection, FileKind, PreviewSlice
from data_transform_tool.io.profiling import TableProfiler
from data_transform_tool.io.reader import ProgressCallback

Row = tuple[object | None, ...]
RowFactory = Callable[[], Iterator[Row]]

LARGE_FILE_BYTES = 100 * 1024 * 1024
LARGE_ROW_COUNT = 1_000_000
LARGE_ESTIMATED_MEMORY = 512 * 1024 * 1024


def inspect_row_stream(
    *,
    path: Path,
    file_kind: FileKind,
    initial_headers: Sequence[object | None],
    rows_factory: RowFactory,
    sample_limit: int,
    processing_strategy: str,
    estimated_memory_multiplier: float,
    worksheet: str | None,
    available_worksheets: tuple[str, ...],
    encoding: str | None,
    encoding_confidence: float | None,
    delimiter: str | None,
    quote_character: str | None,
    header_detected: bool,
    header_confidence: float,
    cancellation: CancellationToken,
    progress: ProgressCallback | None,
    warnings: list[str],
) -> FileInspection:
    """Profile one row factory with constant-memory first/last and two-pass middle preview."""
    headers = normalize_headers(initial_headers)
    profiler = TableProfiler(headers, sample_limit=sample_limit)
    first_rows: list[Row] = []
    last_rows: deque[Row] = deque(maxlen=5)
    width_counts: Counter[int] = Counter()

    if progress:
        progress("Reading rows", 0)
    for row_index, row in enumerate(rows_factory(), start=1):
        if row_index % 1_000 == 0:
            cancellation.raise_if_cancelled()
        profiler.add_row(row)
        width_counts[len(row)] += 1
        if len(first_rows) < 5:
            first_rows.append(row)
        last_rows.append(row)
        if progress and row_index % 10_000 == 0:
            progress("Reading rows", row_index)
    cancellation.raise_if_cancelled()

    row_count = profiler.rows_seen
    profile_summary = profiler.finalize()
    width = len(profile_summary.columns)
    first_preview = tuple(_pad_row(row, width) for row in first_rows)
    last_preview = tuple(_pad_row(row, width) for row in last_rows)

    middle_start_zero = max(0, (row_count - 5) // 2)
    middle_rows: list[Row] = []
    if row_count:
        if progress:
            progress("Collecting middle preview", middle_start_zero + 1)
        for index, row in enumerate(rows_factory()):
            if index < middle_start_zero:
                if index % 1_000 == 0:
                    cancellation.raise_if_cancelled()
                continue
            if len(middle_rows) == 5:
                break
            middle_rows.append(_pad_row(row, width))
    cancellation.raise_if_cancelled()

    if len(width_counts) > 1:
        distribution = ", ".join(
            f"{width} fields x {count} rows" for width, count in sorted(width_counts.items())
        )
        warnings.append(f"Inconsistent field counts detected: {distribution}.")

    file_size = path.stat().st_size
    estimated_memory = round(file_size * estimated_memory_multiplier)
    large_file = (
        file_size >= LARGE_FILE_BYTES
        or row_count >= LARGE_ROW_COUNT
        or estimated_memory >= LARGE_ESTIMATED_MEMORY
    )
    if large_file:
        warnings.append(
            "Large file: later processing should use lazy/streaming execution and local "
            "temporary intermediates where required."
        )

    previews = (
        PreviewSlice("First 5", 1 if first_preview else 0, first_preview),
        PreviewSlice(
            "Middle 5",
            middle_start_zero + 1 if middle_rows else 0,
            tuple(middle_rows),
        ),
        PreviewSlice(
            "Last 5",
            max(1, row_count - len(last_preview) + 1) if last_preview else 0,
            last_preview,
        ),
    )
    if progress:
        progress("Profile complete", row_count)

    return FileInspection(
        path=path,
        file_kind=file_kind,
        file_size_bytes=file_size,
        estimated_memory_bytes=estimated_memory,
        processing_strategy=processing_strategy,
        worksheet=worksheet,
        available_worksheets=available_worksheets,
        encoding=encoding,
        encoding_confidence=encoding_confidence,
        delimiter=delimiter,
        quote_character=quote_character,
        header_detected=header_detected,
        header_confidence=header_confidence,
        row_count=row_count,
        column_count=width,
        columns=profile_summary.columns,
        potential_missing_markers=profile_summary.markers,
        likely_datetime_column=profile_summary.likely_datetime_column,
        likely_interval_seconds=profile_summary.likely_interval_seconds,
        likely_interval_label=profile_summary.likely_interval_label,
        previews=previews,
        large_file=large_file,
        warnings=tuple(warnings),
    )


def normalize_headers(values: Sequence[object | None]) -> list[str]:
    """Create non-empty, unique display names without changing source data."""
    headers: list[str] = []
    counts: Counter[str] = Counter()
    for index, value in enumerate(values, start=1):
        base = str(value).strip() if value is not None else ""
        base = base or f"Column {index}"
        counts[base] += 1
        headers.append(base if counts[base] == 1 else f"{base} ({counts[base]})")
    return headers


def row_is_empty(row: Row) -> bool:
    return all(value is None or (isinstance(value, str) and not value.strip()) for value in row)


def _pad_row(row: Row, width: int) -> Row:
    return row[:width] + (None,) * max(0, width - len(row))
