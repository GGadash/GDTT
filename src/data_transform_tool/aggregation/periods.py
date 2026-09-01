"""Timezone-aware reporting-period alignment and expected-count calculation.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from data_transform_tool.aggregation.models import (
    AggregationError,
    PeriodBounds,
    PeriodKind,
    PeriodSpec,
)


class Periodizer:
    """Map instants to explicit clock, calendar, season, or anchored periods."""

    def __init__(self, spec: PeriodSpec, reporting_timezone: str) -> None:
        self.spec = spec
        self.zone = ZoneInfo(reporting_timezone)

    def period_for(self, value: datetime) -> PeriodBounds:
        if value.utcoffset() is None:
            raise AggregationError(
                "Aggregation timestamps must be timezone-aware before reporting boundaries "
                "can be applied."
            )
        local = value.astimezone(self.zone)
        match self.spec.kind:
            case PeriodKind.FIXED_CLOCK:
                return self._clock_period(local)
            case PeriodKind.DAY:
                return self._day_period(local)
            case PeriodKind.WEEK:
                return self._week_period(local)
            case PeriodKind.CALENDAR_MONTH:
                return self._month_period(local)
            case PeriodKind.FIXED_DAYS | PeriodKind.FIXED_YEAR:
                return self._anchored_period(local)
            case PeriodKind.QUARTER:
                return self._quarter_period(local)
            case PeriodKind.SEASON:
                return self._season_period(local)
            case PeriodKind.CALENDAR_YEAR:
                return self._year_period(local)

    def next_period(self, current: PeriodBounds) -> PeriodBounds:
        """Return the adjacent positive-duration period after ``current``."""
        next_period = self.period_for(current.end)
        if _instant(next_period.start) != _instant(current.end):
            raise AggregationError(
                "The configured period strategy produced overlapping or discontinuous boundaries."
            )
        if _instant(next_period.start) <= _instant(current.start):
            raise AggregationError("The configured period strategy did not advance.")
        return next_period

    def periods_between(
        self,
        first: datetime,
        last: datetime,
        *,
        max_periods: int = 1_000_000,
    ) -> tuple[PeriodBounds, ...]:
        if _instant(last) < _instant(first):
            raise ValueError("The last timestamp must not precede the first timestamp.")
        stop = self.period_for(last)
        current = self.period_for(first)
        periods: list[PeriodBounds] = []
        while _instant(current.start) <= _instant(stop.start):
            if len(periods) >= max_periods:
                raise AggregationError(
                    f"The selected range exceeds the configured {max_periods:,}-period limit."
                )
            periods.append(current)
            current = self.next_period(current)
        return tuple(periods)

    def component_periods(
        self,
        target: PeriodBounds,
        *,
        max_periods: int = 1_000_000,
    ) -> tuple[PeriodBounds, ...]:
        """Enumerate lower-level periods that exactly tile one target period."""
        current = self.period_for(target.start)
        if _instant(current.start) != _instant(target.start):
            raise AggregationError(
                "Incremental stage boundaries do not align at the target-period start."
            )
        components: list[PeriodBounds] = []
        while _instant(current.start) < _instant(target.end):
            if len(components) >= max_periods:
                raise AggregationError(
                    "The incremental component count exceeds the configured period limit."
                )
            if _instant(current.end) > _instant(target.end):
                raise AggregationError(
                    "Incremental stage boundaries do not tile the target period exactly."
                )
            components.append(current)
            current = self.next_period(current)
        if not components or _instant(components[-1].end) != _instant(target.end):
            raise AggregationError(
                "Incremental stage boundaries do not end at the target-period boundary."
            )
        return tuple(components)

    def expected_observations(self, bounds: PeriodBounds, interval: timedelta) -> int:
        """Count exact elapsed input slots between timezone-aware wall boundaries."""
        if interval <= timedelta(0):
            raise ValueError("Expected-count interval must be greater than zero.")
        elapsed = _instant(bounds.end) - _instant(bounds.start)
        quotient, remainder = divmod(elapsed, interval)
        if remainder:
            raise AggregationError(
                f"The {elapsed} elapsed period cannot be divided exactly by the confirmed "
                f"input interval {interval}."
            )
        if quotient <= 0:
            raise AggregationError("A reporting period must contain at least one expected slot.")
        return quotient

    def _clock_period(self, local: datetime) -> PeriodBounds:
        duration = self.spec.duration
        if duration is None:
            raise AssertionError("Validated fixed-clock periods always have a duration.")
        reporting_date = _reporting_date(local, self.spec.day_start)
        anchor = datetime.combine(reporting_date, self.spec.day_start)
        local_naive = local.replace(tzinfo=None)
        slot = (local_naive - anchor) // duration
        start_naive = anchor + slot * duration
        end_naive = start_naive + duration
        start = _localize_boundary(start_naive, self.zone)
        end = _localize_boundary(end_naive, self.zone)
        if _instant(end) <= _instant(start):
            # No real instant can fall in a skipped DST wall-clock slot.
            return self.period_for(end)
        return PeriodBounds(start, end, _range_label(start, end))

    def _day_period(self, local: datetime) -> PeriodBounds:
        reporting_date = _reporting_date(local, self.spec.day_start)
        start = _localize_boundary(datetime.combine(reporting_date, self.spec.day_start), self.zone)
        end = _localize_boundary(
            datetime.combine(reporting_date + timedelta(days=1), self.spec.day_start), self.zone
        )
        return PeriodBounds(start, end, reporting_date.isoformat())

    def _week_period(self, local: datetime) -> PeriodBounds:
        reporting_date = _reporting_date(local, self.spec.day_start)
        start_date = reporting_date - timedelta(
            days=(reporting_date.weekday() - self.spec.week_start) % 7
        )
        start = _localize_boundary(datetime.combine(start_date, self.spec.day_start), self.zone)
        end = _localize_boundary(
            datetime.combine(start_date + timedelta(days=7), self.spec.day_start), self.zone
        )
        return PeriodBounds(start, end, f"Week {start_date.isoformat()}")

    def _month_period(self, local: datetime) -> PeriodBounds:
        reporting_date = _reporting_date(local, self.spec.day_start)
        start_date = date(reporting_date.year, reporting_date.month, 1)
        end_date = _add_months(start_date, 1)
        start = _localize_boundary(datetime.combine(start_date, self.spec.day_start), self.zone)
        end = _localize_boundary(datetime.combine(end_date, self.spec.day_start), self.zone)
        return PeriodBounds(start, end, start_date.strftime("%Y-%m"))

    def _anchored_period(self, local: datetime) -> PeriodBounds:
        anchor = self.spec.anchor
        if anchor is None:
            raise AssertionError("Validated anchored periods always have an anchor.")
        localized_anchor = (
            _localize_boundary(anchor, self.zone)
            if anchor.utcoffset() is None
            else anchor.astimezone(self.zone)
        )
        duration = (
            timedelta(days=365) if self.spec.kind is PeriodKind.FIXED_YEAR else self.spec.duration
        )
        if duration is None:
            raise AssertionError("Validated fixed-day periods always have a duration.")
        anchor_instant = _instant(localized_anchor)
        index = (_instant(local) - anchor_instant) // duration
        start = (anchor_instant + index * duration).astimezone(self.zone)
        end = (anchor_instant + (index + 1) * duration).astimezone(self.zone)
        return PeriodBounds(start, end, _range_label(start, end))

    def _quarter_period(self, local: datetime) -> PeriodBounds:
        reporting_date = _reporting_date(local, self.spec.day_start)
        relative_month = (reporting_date.month - self.spec.quarter_start_month) % 12
        start_month_offset = relative_month - (relative_month % 3)
        candidate_year = reporting_date.year
        candidate_month = self.spec.quarter_start_month + start_month_offset
        if candidate_month > 12:
            candidate_year += (candidate_month - 1) // 12
            candidate_month = ((candidate_month - 1) % 12) + 1
        if date(candidate_year, candidate_month, 1) > reporting_date:
            candidate_year -= 1
        start_date = date(candidate_year, candidate_month, 1)
        end_date = _add_months(start_date, 3)
        start = _localize_boundary(datetime.combine(start_date, self.spec.day_start), self.zone)
        end = _localize_boundary(datetime.combine(end_date, self.spec.day_start), self.zone)
        quarter_number = start_month_offset // 3 + 1
        return PeriodBounds(start, end, f"Q{quarter_number} {start_date.year}")

    def _season_period(self, local: datetime) -> PeriodBounds:
        local_naive = local.replace(tzinfo=None)
        candidates: list[tuple[datetime, str]] = []
        for year in range(local.year - 1, local.year + 2):
            for boundary in self.spec.seasons:
                candidates.append(
                    (
                        datetime.combine(
                            date(year, boundary.month, boundary.day), self.spec.day_start
                        ),
                        boundary.name,
                    )
                )
        candidates.sort(key=lambda item: item[0])
        start_index = max(
            index for index, (candidate, _) in enumerate(candidates) if candidate <= local_naive
        )
        start_naive, name = candidates[start_index]
        end_naive, _ = candidates[start_index + 1]
        start = _localize_boundary(start_naive, self.zone)
        end = _localize_boundary(end_naive, self.zone)
        return PeriodBounds(start, end, f"{name} {start_naive.year}")

    def _year_period(self, local: datetime) -> PeriodBounds:
        reporting_date = _reporting_date(local, self.spec.day_start)
        boundary = date(reporting_date.year, self.spec.year_start_month, self.spec.year_start_day)
        if reporting_date < boundary:
            boundary = date(
                reporting_date.year - 1,
                self.spec.year_start_month,
                self.spec.year_start_day,
            )
        end_date = date(boundary.year + 1, self.spec.year_start_month, self.spec.year_start_day)
        start = _localize_boundary(datetime.combine(boundary, self.spec.day_start), self.zone)
        end = _localize_boundary(datetime.combine(end_date, self.spec.day_start), self.zone)
        return PeriodBounds(start, end, f"Year {boundary.isoformat()}")


def _instant(value: datetime) -> datetime:
    if value.utcoffset() is None:
        raise AggregationError("Aggregation timestamps must be timezone-aware.")
    return value.astimezone(UTC)


def _reporting_date(local: datetime, day_start: time) -> date:
    local_time = local.replace(tzinfo=None).time()
    return local.date() if local_time >= day_start else local.date() - timedelta(days=1)


def _localize_boundary(naive: datetime, zone: ZoneInfo) -> datetime:
    if naive.tzinfo is not None:
        return naive.astimezone(zone)
    candidates = _valid_local_candidates(naive, zone)
    if candidates:
        return min(candidates, key=_instant)
    probe = naive
    for _ in range(24 * 60):
        probe += timedelta(minutes=1)
        candidates = _valid_local_candidates(probe, zone)
        if candidates:
            return min(candidates, key=_instant)
    raise AggregationError(f"Could not resolve local reporting boundary {naive!s} in {zone.key}.")


def _valid_local_candidates(naive: datetime, zone: ZoneInfo) -> tuple[datetime, ...]:
    candidates: dict[datetime, datetime] = {}
    for fold in (0, 1):
        candidate = naive.replace(tzinfo=zone, fold=fold)
        round_trip = candidate.astimezone(UTC).astimezone(zone).replace(tzinfo=None)
        if round_trip == naive:
            candidates[_instant(candidate)] = candidate
    return tuple(candidates.values())


def _add_months(value: date, months: int) -> date:
    total = value.year * 12 + value.month - 1 + months
    return date(total // 12, total % 12 + 1, 1)


def _range_label(start: datetime, end: datetime) -> str:
    return f"{start.isoformat()} / {end.isoformat()}"
