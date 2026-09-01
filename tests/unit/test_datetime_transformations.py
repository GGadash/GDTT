"""Date parsing, formatting, interval semantics, and time-shift tests."""

from __future__ import annotations

import json
from datetime import date, datetime, time, timedelta
from pathlib import Path

import pytest

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
    assert DateTimeProfileRegistry.default().groups() == ("Recommended / ISO", "Regional")


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
