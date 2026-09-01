"""Interval suggestions and timezone-aware timestamp-grid analysis.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta, tzinfo
from itertools import pairwise

from data_transform_tool.domain.table import DataTable
from data_transform_tool.gaps.models import (
    ConfirmedInterval,
    GapSpan,
    IntervalSuggestion,
    TimestampAnalysis,
)
from data_transform_tool.transformation.base import TransformationError


def suggest_interval(table: DataTable, timestamp_column: str) -> IntervalSuggestion | None:
    """Suggest the most frequent positive elapsed interval; never confirm it."""
    timestamps = _validated_timestamps(table, timestamp_column, allow_invalid=True)
    if len(timestamps) < 2:
        return None
    _ensure_consistent_awareness(value for _, value in timestamps)
    keys = sorted({_instant_key(value) for _, value in timestamps})
    deltas = tuple(later - earlier for earlier, later in pairwise(keys))
    if not deltas:
        return None
    counts = Counter(deltas)
    duration, matching = min(counts.items(), key=lambda item: (-item[1], item[0]))
    return IntervalSuggestion(
        interval=ConfirmedInterval(duration, _interval_label(duration)),
        matching_steps=matching,
        total_steps=len(deltas),
    )


def analyze_timestamps(
    table: DataTable,
    timestamp_column: str,
    interval: ConfirmedInterval,
    *,
    max_expected_rows: int = 1_000_000,
) -> TimestampAnalysis:
    """Compare valid timestamps with an exact, elapsed-time expected grid."""
    if max_expected_rows <= 0:
        raise ValueError("Maximum expected rows must be greater than zero.")
    raw_values = table.column_values(timestamp_column)
    valid = tuple(
        (row_number, value)
        for row_number, value in enumerate(raw_values, start=1)
        if isinstance(value, datetime)
    )
    invalid_rows = tuple(
        row_number
        for row_number, value in enumerate(raw_values, start=1)
        if not isinstance(value, datetime)
    )
    if not valid:
        return TimestampAnalysis(
            interval,
            (),
            (),
            (),
            (),
            (),
            invalid_rows,
            (),
        )

    aware = _ensure_consistent_awareness(value for _, value in valid)
    keyed_rows = tuple((row_number, _instant_key(value)) for row_number, value in valid)
    rows_by_key: dict[datetime, list[int]] = defaultdict(list)
    for row_number, key in keyed_rows:
        rows_by_key[key].append(row_number)
    duplicate_groups = tuple(
        tuple(row_numbers) for _, row_numbers in sorted(rows_by_key.items()) if len(row_numbers) > 1
    )
    chronological_breaks = tuple(
        current_row
        for (_, previous), (current_row, current) in pairwise(keyed_rows)
        if current < previous
    )

    unique_keys = tuple(sorted(rows_by_key))
    first_key, last_key = unique_keys[0], unique_keys[-1]
    expected_count = ((last_key - first_key) // interval.duration) + 1
    if expected_count > max_expected_rows:
        raise TransformationError(
            f"The confirmed interval would create {expected_count:,} expected rows, "
            f"above the configured limit of {max_expected_rows:,}."
        )
    expected_keys = tuple(first_key + index * interval.duration for index in range(expected_count))
    expected_key_set = set(expected_keys)
    off_grid = tuple(row_number for row_number, key in keyed_rows if key not in expected_key_set)
    missing_keys = tuple(key for key in expected_keys if key not in rows_by_key)
    representative_timezone = valid[0][1].tzinfo if aware else None
    expected = tuple(_display_timestamp(key, representative_timezone) for key in expected_keys)
    missing = tuple(_display_timestamp(key, representative_timezone) for key in missing_keys)
    gaps = _group_gaps(expected, set(missing))
    return TimestampAnalysis(
        interval=interval,
        expected_timestamps=expected,
        missing_timestamps=missing,
        gaps=gaps,
        duplicate_row_groups=duplicate_groups,
        chronological_break_rows=chronological_breaks,
        invalid_timestamp_rows=invalid_rows,
        off_grid_rows=off_grid,
    )


def _validated_timestamps(
    table: DataTable, timestamp_column: str, *, allow_invalid: bool
) -> tuple[tuple[int, datetime], ...]:
    result: list[tuple[int, datetime]] = []
    for row_number, value in enumerate(table.column_values(timestamp_column), start=1):
        if isinstance(value, datetime):
            result.append((row_number, value))
        elif not allow_invalid:
            raise TransformationError(
                f"The primary timestamp is missing or invalid at row {row_number}."
            )
    return tuple(result)


def _ensure_consistent_awareness(timestamps: Iterable[datetime]) -> bool:
    values: tuple[datetime, ...] = tuple(timestamps)
    awareness = {value.utcoffset() is not None for value in values}
    if len(awareness) > 1:
        raise TransformationError(
            "The primary timestamp column mixes timezone-aware and timezone-naive values."
        )
    return awareness.pop() if awareness else False


def _instant_key(value: datetime) -> datetime:
    return value.astimezone(UTC) if value.utcoffset() is not None else value


def _display_timestamp(value: datetime, timezone: tzinfo | None) -> datetime:
    if timezone is None:
        return value.replace(tzinfo=None)
    return value.astimezone(timezone)


def _group_gaps(expected: tuple[datetime, ...], missing: set[datetime]) -> tuple[GapSpan, ...]:
    spans: list[GapSpan] = []
    start = 0
    while start < len(expected):
        if expected[start] not in missing:
            start += 1
            continue
        end = start
        while end + 1 < len(expected) and expected[end + 1] in missing:
            end += 1
        if start > 0 and end + 1 < len(expected):
            spans.append(GapSpan(expected[start - 1], expected[end + 1], expected[start : end + 1]))
        start = end + 1
    return tuple(spans)


def _interval_label(duration: timedelta) -> str:
    seconds = duration.total_seconds()
    common: dict[float, str] = {
        60: "1 minute",
        300: "5 minutes",
        900: "15 minutes",
        3600: "1 hour",
    }
    return common.get(seconds, "Custom")
