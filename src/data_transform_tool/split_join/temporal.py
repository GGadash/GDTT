"""Exact instant matching and calendar boundaries for Split & Join.

Copyright (c) 2026 Akila DJ +. Gadash (Akila DJ); OpenAI Codex.
"""

from __future__ import annotations

import re
from datetime import UTC, date, datetime, timedelta, timezone, tzinfo
from zoneinfo import ZoneInfo

from data_transform_tool.aggregation.models import PeriodBounds, PeriodKind
from data_transform_tool.aggregation.periods import Periodizer
from data_transform_tool.split_join.models import SplitJoinSpec
from data_transform_tool.timezone.converter import DstResolution, _localize_iana


def resolve_zone(name: str) -> tzinfo:
    """Accept IANA names and explicit minute-precision UTC offsets."""
    name = name.strip()
    if name in {"Colombo", "+5.5", "UTC+5.5"}:
        name = "+05:30" if "5.5" in name else "Asia/Colombo"
    match = re.fullmatch(r"(?:UTC)?([+-])(\d{2}):(\d{2})", name)
    if match:
        hours, minutes = int(match[2]), int(match[3])
        if hours > 23 or minutes > 59:
            raise ValueError("UTC offsets must be between -23:59 and +23:59.")
        offset = (hours * 60 + minutes) * (1 if match[1] == "+" else -1)
        return timezone(timedelta(minutes=offset))
    try:
        return ZoneInfo(name)
    except (KeyError, ValueError) as error:
        raise ValueError(
            "Choose UTC, Asia/Colombo, an IANA zone, or an offset such as +05:30."
        ) from error


def localize(value: datetime, zone: tzinfo) -> datetime:
    if isinstance(zone, ZoneInfo):
        return _localize_iana(value, zone.key, DstResolution.RAISE)
    return value.replace(tzinfo=zone)


def parse_timestamp(value: object, pattern: str, zone: tzinfo) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, date):
        parsed = datetime.combine(value, datetime.min.time())
    elif pattern == "ISO":
        parsed = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
    else:
        parsed = datetime.strptime(str(value).strip(), pattern)
    # An embedded offset already identifies the instant; source zone applies only to naive data.
    return parsed if parsed.utcoffset() is not None else localize(parsed, zone)


def instant_key(value: datetime) -> int:
    elapsed = value.astimezone(UTC) - datetime(1970, 1, 1, tzinfo=UTC)
    return (elapsed.days * 86400 + elapsed.seconds) * 1_000_000 + elapsed.microseconds


class SplitPeriods:
    """Reuse established calendar rules with configurable monthly/quarterly day starts.

    Calendar arithmetic runs on local wall time. Boundaries are then localized explicitly;
    ambiguous or nonexistent DST boundaries block instead of guessing an occurrence.
    """

    def __init__(self, spec: SplitJoinSpec) -> None:
        self.spec = spec
        self.zone = resolve_zone(spec.boundary_timezone)
        self.periodizer = Periodizer(spec.period, "UTC")
        self.day_shift = (
            spec.month_start_day - 1
            if spec.period.kind in {PeriodKind.CALENDAR_MONTH, PeriodKind.QUARTER}
            else 0
        )

    def period_for(self, value: datetime) -> PeriodBounds:
        wall = value.astimezone(self.zone).replace(tzinfo=UTC)
        shifted = wall - timedelta(days=self.day_shift)
        bounds = self.periodizer.period_for(shifted)
        start = localize(
            (bounds.start + timedelta(days=self.day_shift)).replace(tzinfo=None), self.zone
        )
        end = localize(
            (bounds.end + timedelta(days=self.day_shift)).replace(tzinfo=None), self.zone
        )
        if not instant_key(start) <= instant_key(value) < instant_key(end):
            raise ValueError("Timestamp does not belong to its configured period boundaries.")
        return PeriodBounds(start, end, bounds.label)
