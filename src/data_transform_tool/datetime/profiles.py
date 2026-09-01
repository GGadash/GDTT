"""Central registry of interoperable and regional date/time profiles.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from collections.abc import Iterable

from data_transform_tool.datetime.models import DateTimeFormatProfile, TemporalKind


class DateTimeProfileRegistry:
    """Validated lookup for date/time parsing and output profiles."""

    def __init__(self, profiles: Iterable[DateTimeFormatProfile]) -> None:
        items = tuple(profiles)
        self._profiles = {profile.profile_id: profile for profile in items}
        if len(self._profiles) != len(items):
            raise ValueError("Date/time profile identifiers must be unique.")

    @classmethod
    def default(cls) -> DateTimeProfileRegistry:
        return cls(DEFAULT_PROFILES)

    def get(self, profile_id: str) -> DateTimeFormatProfile:
        try:
            return self._profiles[profile_id]
        except KeyError as error:
            raise ValueError(f"Unknown date/time profile '{profile_id}'.") from error

    def all(self) -> tuple[DateTimeFormatProfile, ...]:
        return tuple(self._profiles.values())

    def groups(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(profile.group for profile in self._profiles.values()))


DEFAULT_PROFILES = (
    DateTimeFormatProfile(
        "iso_date",
        "Recommended / ISO",
        "ISO date",
        "yyyy-MM-dd",
        ("%Y-%m-%d",),
        TemporalKind.DATE,
        "%Y-%m-%d",
    ),
    DateTimeFormatProfile(
        "iso_minute",
        "Recommended / ISO",
        "ISO date and minute",
        "yyyy-MM-dd HH:mm",
        ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M"),
        TemporalKind.DATETIME,
        "%Y-%m-%d %H:%M",
    ),
    DateTimeFormatProfile(
        "iso_second",
        "Recommended / ISO",
        "ISO date and second",
        "yyyy-MM-dd HH:mm:ss",
        ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"),
        TemporalKind.DATETIME,
        "%Y-%m-%d %H:%M:%S",
    ),
    DateTimeFormatProfile(
        "iso_millisecond",
        "Recommended / ISO",
        "ISO timestamp with fractions",
        "yyyy-MM-dd HH:mm:ss.SSS",
        ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S.%f"),
        TemporalKind.DATETIME,
        "%Y-%m-%d %H:%M:%S.%f",
    ),
    DateTimeFormatProfile(
        "iso_offset",
        "Recommended / ISO",
        "ISO timestamp with offset",
        "yyyy-MM-dd'T'HH:mm:ssXXX",
        ("%Y-%m-%dT%H:%M:%S%z",),
        TemporalKind.DATETIME,
        "%Y-%m-%dT%H:%M:%S%z",
        colonize_offset=True,
    ),
    DateTimeFormatProfile(
        "time_minute",
        "Recommended / ISO",
        "24-hour time and minute",
        "HH:mm",
        ("%H:%M",),
        TemporalKind.TIME,
        "%H:%M",
    ),
    DateTimeFormatProfile(
        "time_second",
        "Recommended / ISO",
        "24-hour time and second",
        "HH:mm:ss",
        ("%H:%M:%S",),
        TemporalKind.TIME,
        "%H:%M:%S",
    ),
    DateTimeFormatProfile(
        "dmy_slash_date",
        "Regional",
        "Day / month / year",
        "dd/MM/yyyy",
        ("%d/%m/%Y",),
        TemporalKind.DATE,
        "%d/%m/%Y",
    ),
    DateTimeFormatProfile(
        "mdy_slash_date",
        "Regional",
        "Month / day / year",
        "MM/dd/yyyy",
        ("%m/%d/%Y",),
        TemporalKind.DATE,
        "%m/%d/%Y",
    ),
    DateTimeFormatProfile(
        "mdy_slash_minute",
        "Regional",
        "Month / day / year and minute",
        "MM/dd/yyyy HH:mm",
        ("%m/%d/%Y %H:%M",),
        TemporalKind.DATETIME,
        "%m/%d/%Y %H:%M",
    ),
    DateTimeFormatProfile(
        "dmy_slash_minute",
        "Regional",
        "Day / month / year and minute",
        "dd/MM/yyyy HH:mm",
        ("%d/%m/%Y %H:%M",),
        TemporalKind.DATETIME,
        "%d/%m/%Y %H:%M",
    ),
)
