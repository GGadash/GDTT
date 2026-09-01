"""Clock, calendar, season, anchor, and DST reporting-period coverage."""

from __future__ import annotations

from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

from data_transform_tool.aggregation import Periodizer, PeriodKind, PeriodSpec, SeasonBoundary


def test_clock_day_week_month_quarter_and_year_boundaries_are_distinct() -> None:
    timestamp = datetime(2026, 5, 6, 2, 30, tzinfo=UTC)

    clock = Periodizer(PeriodSpec.clock(timedelta(hours=8)), "UTC").period_for(timestamp)
    day = Periodizer(PeriodSpec.day(day_start=time(6)), "UTC").period_for(timestamp)
    week = Periodizer(
        PeriodSpec(PeriodKind.WEEK, day_start=time(6), week_start=6), "UTC"
    ).period_for(timestamp)
    month = Periodizer(PeriodSpec(PeriodKind.CALENDAR_MONTH), "UTC").period_for(timestamp)
    quarter = Periodizer(PeriodSpec(PeriodKind.QUARTER), "UTC").period_for(timestamp)
    year = Periodizer(PeriodSpec(PeriodKind.CALENDAR_YEAR, year_start_month=4), "UTC").period_for(
        datetime(2026, 2, 1, tzinfo=UTC)
    )

    assert (clock.start.hour, clock.end.hour) == (0, 8)
    assert day.start == datetime(2026, 5, 5, 6, tzinfo=UTC)
    assert day.end == datetime(2026, 5, 6, 6, tzinfo=UTC)
    assert week.start == datetime(2026, 5, 3, 6, tzinfo=UTC)
    assert month.start == datetime(2026, 5, 1, tzinfo=UTC)
    assert month.end == datetime(2026, 6, 1, tzinfo=UTC)
    assert quarter.start == datetime(2026, 4, 1, tzinfo=UTC)
    assert quarter.end == datetime(2026, 7, 1, tzinfo=UTC)
    assert year.start == datetime(2025, 4, 1, tzinfo=UTC)
    assert year.end == datetime(2026, 4, 1, tzinfo=UTC)


def test_fixed_30_day_and_fixed_year_periods_use_explicit_anchors() -> None:
    fixed_30 = Periodizer(
        PeriodSpec(
            PeriodKind.FIXED_DAYS,
            duration=timedelta(days=30),
            anchor=datetime(2026, 1, 1, tzinfo=UTC),
        ),
        "UTC",
    ).period_for(datetime(2026, 2, 5, tzinfo=UTC))
    fixed_year = Periodizer(
        PeriodSpec(
            PeriodKind.FIXED_YEAR,
            anchor=datetime(2025, 7, 1, tzinfo=UTC),
        ),
        "UTC",
    ).period_for(datetime(2026, 8, 1, tzinfo=UTC))

    assert fixed_30.start == datetime(2026, 1, 31, tzinfo=UTC)
    assert fixed_30.end == datetime(2026, 3, 2, tzinfo=UTC)
    assert fixed_year.end - fixed_year.start == timedelta(days=365)


def test_configurable_seasons_cross_calendar_years() -> None:
    seasons = (
        SeasonBoundary("Northeast Monsoon", 12),
        SeasonBoundary("First Intermonsoon", 3),
        SeasonBoundary("Southwest Monsoon", 6),
        SeasonBoundary("Second Intermonsoon", 10),
    )
    periodizer = Periodizer(PeriodSpec(PeriodKind.SEASON, seasons=seasons), "Asia/Colombo")

    january = periodizer.period_for(datetime(2026, 1, 15, tzinfo=ZoneInfo("Asia/Colombo")))
    april = periodizer.period_for(datetime(2026, 4, 15, tzinfo=ZoneInfo("Asia/Colombo")))

    assert january.label == "Northeast Monsoon 2025"
    assert january.start.month == 12 and january.end.month == 3
    assert april.label == "First Intermonsoon 2026"
    assert april.start.month == 3 and april.end.month == 6


def test_dst_days_have_23_and_25_expected_hourly_observations() -> None:
    new_york = ZoneInfo("America/New_York")
    day = Periodizer(PeriodSpec.day(), "America/New_York")
    spring = day.period_for(datetime(2026, 3, 8, 12, tzinfo=new_york))
    autumn = day.period_for(datetime(2026, 11, 1, 12, tzinfo=new_york))

    assert day.expected_observations(spring, timedelta(hours=1)) == 23
    assert day.expected_observations(autumn, timedelta(hours=1)) == 25


def test_repeated_fall_back_hour_is_one_wall_period_with_two_expected_slots() -> None:
    new_york = ZoneInfo("America/New_York")
    hours = Periodizer(PeriodSpec.clock(timedelta(hours=1)), "America/New_York")
    first = hours.period_for(datetime(2026, 11, 1, 1, 30, tzinfo=new_york, fold=0))
    second = hours.period_for(datetime(2026, 11, 1, 1, 30, tzinfo=new_york, fold=1))

    assert first.start.astimezone(UTC) == second.start.astimezone(UTC)
    assert first.end.astimezone(UTC) == second.end.astimezone(UTC)
    assert hours.expected_observations(first, timedelta(hours=1)) == 2
