"""Streaming column profiling, type inference, and interval detection.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime, time
from itertools import pairwise
from typing import cast

from data_transform_tool.io.models import (
    ColumnProfile,
    MissingMarkerDetection,
    SemanticType,
)

_POTENTIAL_MISSING = {"na", "n/a", "null", "none", "nan", "-999", "-999.0"}
_TRUE_TEXT = {"true", "yes", "y"}
_FALSE_TEXT = {"false", "no", "n"}
_REGIONAL_DATE = re.compile(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$")


@dataclass
class _ColumnAccumulator:
    blank_count: int = 0
    marker_counts: Counter[str] = field(default_factory=Counter)
    samples: list[object] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)
    unique_samples: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class ProfileSummary:
    columns: tuple[ColumnProfile, ...]
    markers: tuple[MissingMarkerDetection, ...]
    likely_datetime_column: str | None
    likely_interval_seconds: float | None
    likely_interval_label: str | None


class TableProfiler:
    """Collect bounded samples while counting blanks and markers across all rows."""

    def __init__(self, headers: list[str], *, sample_limit: int) -> None:
        self.headers = headers
        self.sample_limit = sample_limit
        self.rows_seen = 0
        self._columns = [_ColumnAccumulator() for _ in headers]

    def add_row(self, row: tuple[object | None, ...]) -> None:
        self._ensure_width(len(row))
        for index, accumulator in enumerate(self._columns):
            value = row[index] if index < len(row) else None
            self._add_value(accumulator, value)
        self.rows_seen += 1

    def _ensure_width(self, width: int) -> None:
        while len(self._columns) < width:
            self.headers.append(f"Column {len(self.headers) + 1}")
            self._columns.append(_ColumnAccumulator(blank_count=self.rows_seen))

    def _add_value(self, accumulator: _ColumnAccumulator, value: object | None) -> None:
        if value is None or (isinstance(value, str) and not value.strip()):
            accumulator.blank_count += 1
            return

        text = _display_value(value)
        normalized = text.strip().casefold()
        if normalized in _POTENTIAL_MISSING:
            accumulator.marker_counts[text.strip()] += 1
            return

        if len(accumulator.samples) < self.sample_limit:
            accumulator.samples.append(value)
        if len(accumulator.examples) < 3 and text not in accumulator.examples:
            accumulator.examples.append(text)
        if len(accumulator.unique_samples) < self.sample_limit:
            accumulator.unique_samples.add(text)

    def finalize(self) -> ProfileSummary:
        profiles: list[ColumnProfile] = []
        combined_markers: Counter[str] = Counter()
        parsed_by_column: dict[int, list[datetime]] = {}

        for index, accumulator in enumerate(self._columns):
            inferred_type, confidence, warnings, parsed_datetimes = _infer_type(accumulator.samples)
            if parsed_datetimes:
                parsed_by_column[index] = parsed_datetimes
            combined_markers.update(accumulator.marker_counts)
            potential_missing = sum(accumulator.marker_counts.values())
            missing_total = accumulator.blank_count + potential_missing
            missing_percent = (
                round(missing_total / self.rows_seen * 100, 2) if self.rows_seen else 0.0
            )
            profiles.append(
                ColumnProfile(
                    name=self.headers[index],
                    inferred_type=inferred_type,
                    confidence=confidence,
                    blank_count=accumulator.blank_count,
                    potential_missing_count=potential_missing,
                    missing_percent=missing_percent,
                    unique_sample_count=len(accumulator.unique_samples),
                    examples=tuple(accumulator.examples),
                    entirely_empty=accumulator.blank_count == self.rows_seen,
                    warnings=warnings,
                )
            )

        datetime_index = _best_datetime_column(profiles, parsed_by_column)
        interval_seconds = None
        interval_label = None
        datetime_name = None
        if datetime_index is not None:
            datetime_name = profiles[datetime_index].name
            interval_seconds = _likely_interval(parsed_by_column[datetime_index])
            interval_label = _format_interval(interval_seconds)

        markers = tuple(
            MissingMarkerDetection(value=value, count=count)
            for value, count in combined_markers.most_common()
        )
        return ProfileSummary(
            columns=tuple(profiles),
            markers=markers,
            likely_datetime_column=datetime_name,
            likely_interval_seconds=interval_seconds,
            likely_interval_label=interval_label,
        )


def _infer_type(
    values: list[object],
) -> tuple[SemanticType, float, tuple[str, ...], list[datetime]]:
    if not values:
        return SemanticType.EMPTY, 1.0, (), []

    if all(isinstance(value, bool) for value in values):
        return SemanticType.BOOLEAN, 1.0, (), []

    if all(isinstance(value, int) and not isinstance(value, bool) for value in values):
        return SemanticType.INTEGER, 1.0, (), []

    if all(
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and not (isinstance(value, float) and math.isnan(value))
        for value in values
    ):
        inferred = (
            SemanticType.INTEGER
            if all(float(cast(int | float, value)).is_integer() for value in values)
            else SemanticType.DECIMAL
        )
        return inferred, 1.0, (), []

    if all(isinstance(value, datetime) for value in values):
        return SemanticType.DATETIME, 1.0, (), list(values)  # type: ignore[arg-type]
    if all(isinstance(value, date) and not isinstance(value, datetime) for value in values):
        parsed = [datetime.combine(value, time.min) for value in values]  # type: ignore[arg-type]
        return SemanticType.DATE, 1.0, (), parsed
    if all(isinstance(value, time) for value in values):
        return SemanticType.TIME, 1.0, (), []

    texts = [str(value).strip() for value in values]
    if all(text.casefold() in _TRUE_TEXT | _FALSE_TEXT for text in texts):
        return SemanticType.BOOLEAN, 1.0, (), []

    integer_count = sum(_is_integer(text) for text in texts)
    if integer_count / len(texts) >= 0.95:
        return SemanticType.INTEGER, integer_count / len(texts), (), []

    decimal_count = sum(_is_decimal(text) for text in texts)
    if decimal_count / len(texts) >= 0.95:
        return SemanticType.DECIMAL, decimal_count / len(texts), (), []

    parsed_datetimes = [_parse_datetime(value) for value in values]
    datetime_matches = [value for value in parsed_datetimes if value is not None]
    if len(datetime_matches) / len(values) >= 0.8:
        inferred_type = _date_time_kind(values)
        warnings = (
            ("Ambiguous regional date order; user confirmation is required.",)
            if _has_ambiguous_regional_dates(texts)
            else ()
        )
        return inferred_type, len(datetime_matches) / len(values), warnings, datetime_matches

    unique_count = len(set(texts))
    category_limit = min(20, max(2, round(len(texts) * 0.2)))
    if unique_count <= category_limit and len(texts) >= 5:
        return SemanticType.CATEGORY, 0.8, (), []
    return SemanticType.TEXT, 0.9, (), []


def _is_integer(value: str) -> bool:
    try:
        int(value)
    except ValueError:
        return False
    return True


def _is_decimal(value: str) -> bool:
    try:
        parsed = float(value)
    except ValueError:
        return False
    return math.isfinite(parsed)


def _parse_datetime(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, time.min)
    if isinstance(value, time):
        return datetime.combine(date(2000, 1, 1), value)

    text = str(value).strip()
    normalized = text.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        pass

    patterns = (
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y %H:%M",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%H:%M:%S",
        "%H:%M",
    )
    for pattern in patterns:
        try:
            return datetime.strptime(text, pattern)
        except ValueError:
            continue
    return None


def _date_time_kind(values: list[object]) -> SemanticType:
    texts = [str(value).strip() for value in values]
    if all(
        isinstance(value, time) or re.fullmatch(r"\d{1,2}:\d{2}(:\d{2})?", text)
        for value, text in zip(values, texts, strict=True)
    ):
        return SemanticType.TIME
    if all(
        (isinstance(value, date) and not isinstance(value, datetime))
        or (":" not in text and "T" not in text)
        for value, text in zip(values, texts, strict=True)
    ):
        return SemanticType.DATE
    return SemanticType.DATETIME


def _has_ambiguous_regional_dates(texts: list[str]) -> bool:
    matches = [_REGIONAL_DATE.match(text) for text in texts]
    relevant = [match for match in matches if match is not None]
    return bool(relevant) and all(
        int(match.group(1)) <= 12 and int(match.group(2)) <= 12 for match in relevant
    )


def _best_datetime_column(
    profiles: list[ColumnProfile], parsed_by_column: dict[int, list[datetime]]
) -> int | None:
    candidates = [
        index
        for index, profile in enumerate(profiles)
        if profile.inferred_type in {SemanticType.DATETIME, SemanticType.DATE}
        and len(parsed_by_column.get(index, [])) >= 2
    ]
    if not candidates:
        return None
    return max(
        candidates, key=lambda index: (profiles[index].confidence, len(parsed_by_column[index]))
    )


def _likely_interval(values: list[datetime]) -> float | None:
    deltas = [
        (later - earlier).total_seconds()
        for earlier, later in pairwise(values)
        if (later - earlier).total_seconds() > 0
    ]
    if not deltas:
        return None
    rounded_counts = Counter(round(delta, 6) for delta in deltas)
    return float(rounded_counts.most_common(1)[0][0])


def _format_interval(seconds: float | None) -> str | None:
    if seconds is None:
        return None
    common = {
        60.0: "1 minute",
        300.0: "5 minutes",
        900.0: "15 minutes",
        3600.0: "1 hour",
        28800.0: "8 hours",
        86400.0: "1 day",
    }
    if seconds in common:
        return common[seconds]
    if seconds % 3600 == 0:
        return f"{seconds / 3600:g} hours"
    if seconds % 60 == 0:
        return f"{seconds / 60:g} minutes"
    return f"{seconds:g} seconds"


def _display_value(value: object) -> str:
    if isinstance(value, datetime):
        return value.isoformat(sep=" ")
    if isinstance(value, (date, time)):
        return value.isoformat()
    return str(value)
