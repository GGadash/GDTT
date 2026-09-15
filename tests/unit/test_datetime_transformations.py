"""Date parsing, formatting, interval semantics, and time-shift tests."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, time, timedelta, timezone
from pathlib import Path

import pytest

from data_transform_tool.datetime.custom_formats import FieldFormat
from data_transform_tool.datetime.models import (
    IntervalEndMode,
    TimestampRole,
    TimestampSemantics,
)
from data_transform_tool.datetime.operations import (
    CombineDateAndTime,
    DeriveIntervalFields,
    FormatDateTimeColumn,
    NormalizeIntervalEnd,
    ParseDateTimeColumn,
    SplitDateTime,
    TimeShift,
)
from data_transform_tool.datetime.parser import AmbiguousDateError, DateTimeParser
from data_transform_tool.datetime.profiles import DateTimeProfileRegistry
from data_transform_tool.domain.table import DataTable


def test_iso_regional_and_millisecond_profiles_are_explicit() -> None:
    parser = DateTimeParser()

    assert parser.parse("2025-08-20 08:15", "iso_minute") == datetime(2025, 8, 20, 8, 15)
    assert parser.parse("20/08/2025", "dmy_slash_date") == date(2025, 8, 20)
    parsed = parser.parse("2025-08-20 08:15:30.123456", "iso_millisecond")
    assert parsed == datetime(2025, 8, 20, 8, 15, 30, 123456)
    assert parser.format(parsed, "iso_millisecond") == "2025-08-20 08:15:30.123"
    assert DateTimeProfileRegistry.default().groups() == (
        "Recommended / ISO",
        "Regional",
        "Compact / ISO",
    )


@pytest.mark.parametrize(
    ("profile", "text"),
    [
        ("iso_utc", "2026-09-15T01:02:03Z"),
        ("iso_basic_utc", "20260915T010203Z"),
        ("iso_offset", "2026-09-15T01:02:03+05:30"),
        ("iso_basic_offset", "20260915T010203+0530"),
        ("iso_t_minute", "2026-09-15T01:02"),
        ("iso_basic_minute", "20260915T0102"),
        ("iso_t_second", "2026-09-15T01:02:03"),
        ("iso_basic_second", "20260915T010203"),
    ],
)
def test_iso_presets_parse_format_and_preserve_nulls(profile, text):
    parser = DateTimeParser()
    value = parser.parse(text, profile)
    assert isinstance(value, datetime)
    assert (value.year, value.month, value.day, value.hour, value.minute) == (2026, 9, 15, 1, 2)
    assert value.second == (0 if "minute" in profile else 3)
    assert value.utcoffset() == (
        timedelta(0)
        if "utc" in profile
        else timedelta(hours=5, minutes=30)
        if "offset" in profile
        else None
    )
    assert parser.format(value, profile) == text
    source = DataTable(("When",), ((text,), (None,)))
    parsed = ParseDateTimeColumn("When", profile).apply(source).table
    assert FormatDateTimeColumn("When", profile).apply(parsed).table == source
    assert parser.parse_unambiguous(text) == value
    pattern = parser.registry.get(profile).display_pattern
    custom = FieldFormat("datetime", pattern).encode()
    assert parser.parse(text, custom) == value
    assert parser.format(value, custom) == text


@pytest.mark.parametrize("profile", ["iso_utc", "iso_basic_utc"])
def test_z_output_converts_instant_not_wall_clock_and_requires_source_zone(profile):
    parser = DateTimeParser()
    local = datetime(2026, 1, 1, 1, 2, 3, tzinfo=timezone(timedelta(hours=5, minutes=30)))
    expected = datetime(2025, 12, 31, 19, 32, 3, tzinfo=UTC)
    assert parser.parse(local, profile) == expected
    assert parser.parse(parser.format(local, profile), profile) == expected
    with pytest.raises(ValueError, match="source timezone"):
        parser.format(local.replace(tzinfo=None), profile)
    with pytest.raises(ValueError, match="source timezone"):
        parser.parse(local.replace(tzinfo=None), profile)


@pytest.mark.parametrize(
    ("profile", "text"),
    [
        ("iso_basic_second", "20260915T0102"),
        ("iso_basic_minute", "20260915T010203"),
        ("iso_basic_utc", "20260915T0102Z"),
        ("iso_basic_utc", "20260915T010203+0530"),
        ("iso_utc", "2026-09-15T01:02:03+05:30"),
        ("iso_basic_offset", "20260915T010203"),
        ("iso_t_second", "2026-09-15T01:02"),
        ("iso_t_minute", "2026-09-15T01:02:03"),
    ],
)
def test_iso_presets_reject_wrong_shape_instead_of_guessing(profile, text):
    with pytest.raises(ValueError, match="does not match"):
        DateTimeParser().parse(text, profile)


@pytest.mark.parametrize("profile", ["iso_offset", "iso_basic_offset"])
def test_offset_output_never_silently_omits_unknown_offset(profile):
    with pytest.raises(ValueError, match="source timezone"):
        DateTimeParser().format(datetime(2026, 9, 15), profile)


def test_runtime_profiles_match_machine_readable_registry() -> None:
    path = Path(__file__).parents[2] / "About-Info" / "Machine-Readable" / "format_profiles.json"
    documented = json.loads(path.read_text(encoding="utf-8"))["profiles"]
    runtime = DateTimeProfileRegistry.default().all()

    assert [item["id"] for item in documented] == [profile.profile_id for profile in runtime]
    assert [item["pattern"] for item in documented] == [
        profile.display_pattern for profile in runtime
    ]


def test_ambiguous_regional_date_returns_both_meanings_and_never_guesses() -> None:
    parser = DateTimeParser()

    interpretations = parser.interpretations("04/05/2026")

    assert {item.value for item in interpretations} == {date(2026, 5, 4), date(2026, 4, 5)}
    with pytest.raises(AmbiguousDateError) as captured:
        parser.parse_unambiguous("04/05/2026")
    assert "dd/MM/yyyy" in (captured.value.detail or "")
    assert "MM/dd/yyyy" in (captured.value.detail or "")


def test_parse_then_format_keeps_value_and_printed_representation_separate() -> None:
    source = DataTable(("When",), (("08/20/2025 08:00",), ("08/20/2025 09:00",)))

    parsed = ParseDateTimeColumn("When", "mdy_slash_minute").apply(source).table
    formatted = FormatDateTimeColumn("When", "iso_minute", output="When_ISO").apply(parsed).table

    assert isinstance(parsed.rows[0][0], datetime)
    assert formatted.column_values("When_ISO") == (
        "2025-08-20 08:00",
        "2025-08-20 09:00",
    )


def test_combine_and_split_date_time_columns() -> None:
    table = DataTable(
        ("Date", "Time"),
        ((date(2025, 8, 20), time(8, 0)), (date(2025, 8, 21), time(9, 30))),
    )

    combined = CombineDateAndTime("Date", "Time", "Timestamp").apply(table).table
    split = SplitDateTime("Timestamp", "Date Copy", "Time Copy").apply(combined).table

    assert combined.column_values("Timestamp") == (
        datetime(2025, 8, 20, 8),
        datetime(2025, 8, 21, 9, 30),
    )
    assert split.column_values("Date Copy") == (date(2025, 8, 20), date(2025, 8, 21))
    assert split.column_values("Time Copy") == (time(8), time(9, 30))


@pytest.mark.parametrize(
    ("role", "source", "expected_start"),
    [
        (TimestampRole.START, datetime(2025, 8, 20, 8), datetime(2025, 8, 20, 8)),
        (TimestampRole.MIDPOINT, datetime(2025, 8, 20, 8, 30), datetime(2025, 8, 20, 8)),
        (TimestampRole.END, datetime(2025, 8, 20, 9), datetime(2025, 8, 20, 8)),
    ],
)
def test_start_mid_end_derivation_uses_timestamp_role(
    role: TimestampRole, source: datetime, expected_start: datetime
) -> None:
    table = DataTable(("Timestamp",), ((source,),))

    result = (
        DeriveIntervalFields(TimestampSemantics("Timestamp", role, timedelta(hours=1)))
        .apply(table)
        .table
    )

    assert result.column_values("Start") == (expected_start,)
    assert result.column_values("Mid") == (expected_start + timedelta(minutes=30),)
    assert result.column_values("End") == (expected_start + timedelta(hours=1),)


def test_semantic_end_normalization_changes_0859_to_0900_without_rounding() -> None:
    table = DataTable(
        ("Start", "End"),
        (
            (datetime(2025, 8, 20, 8), datetime(2025, 8, 20, 8, 59)),
            (datetime(2025, 8, 20, 9), datetime(2025, 8, 20, 9, 55)),
        ),
    )

    result = NormalizeIntervalEnd(
        "Start",
        "End",
        timedelta(hours=1),
        IntervalEndMode.SEMANTIC_NORMALIZE,
    ).apply(table)

    assert result.table.column_values("End") == (
        datetime(2025, 8, 20, 9),
        datetime(2025, 8, 20, 9, 55),
    )
    assert [diagnostic.count for diagnostic in result.diagnostics] == [1, 1]


def test_time_shift_changes_clock_value_independently() -> None:
    table = DataTable(("Timestamp",), ((datetime(2025, 8, 20, 8),),))

    shifted = TimeShift("Timestamp", timedelta(minutes=-30), output="Shifted").apply(table).table

    assert shifted.column_values("Timestamp") == (datetime(2025, 8, 20, 8),)
    assert shifted.column_values("Shifted") == (datetime(2025, 8, 20, 7, 30),)
