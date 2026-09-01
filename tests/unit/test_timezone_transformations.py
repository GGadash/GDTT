"""Timezone conversion, source-mode, manual-offset, and DST tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import pytest

from data_transform_tool.domain.table import DataTable
from data_transform_tool.timezone import (
    DstResolution,
    TimezoneConversion,
    TimezoneSource,
    list_iana_timezones,
)
from data_transform_tool.transformation.base import TransformationError


def test_utc_to_asia_colombo_preserves_instant() -> None:
    table = DataTable(("UTC",), ((datetime(2025, 8, 20, 8),),))

    result = (
        TimezoneConversion(
            "UTC",
            "Asia/Colombo",
            TimezoneSource.fixed("UTC"),
            output="Local",
        )
        .apply(table)
        .table
    )
    local = result.column_values("Local")[0]

    assert isinstance(local, datetime)
    assert local.isoformat() == "2025-08-20T13:30:00+05:30"
    assert local.astimezone(UTC) == datetime(2025, 8, 20, 8, tzinfo=UTC)


def test_embedded_and_timezone_column_sources_are_supported() -> None:
    aware = datetime(2025, 8, 20, 8, tzinfo=UTC)
    embedded_table = DataTable(("Timestamp",), ((aware,),))
    column_table = DataTable(
        ("Timestamp", "Timezone"),
        ((datetime(2025, 8, 20, 8), "UTC"),),
    )

    embedded = (
        TimezoneConversion("Timestamp", "Asia/Colombo", TimezoneSource.embedded())
        .apply(embedded_table)
        .table
    )
    from_column = (
        TimezoneConversion(
            "Timestamp",
            "Asia/Colombo",
            TimezoneSource.from_column("Timezone"),
            output="Local",
        )
        .apply(column_table)
        .table
    )

    assert embedded.rows[0][0].isoformat() == "2025-08-20T13:30:00+05:30"
    assert from_column.column_values("Local")[0].isoformat() == "2025-08-20T13:30:00+05:30"


def test_manual_offset_is_not_treated_as_an_iana_timezone() -> None:
    table = DataTable(("Local",), ((datetime(2025, 7, 1, 12),),))

    fixed_offset = (
        TimezoneConversion("Local", "UTC", TimezoneSource.manual_offset(-300), output="From Offset")
        .apply(table)
        .table
    )
    iana = (
        TimezoneConversion(
            "Local", "UTC", TimezoneSource.fixed("America/New_York"), output="From IANA"
        )
        .apply(table)
        .table
    )

    assert fixed_offset.column_values("From Offset")[0].hour == 17
    assert iana.column_values("From IANA")[0].hour == 16


def test_ambiguous_dst_time_requires_explicit_occurrence() -> None:
    table = DataTable(("Local",), ((datetime(2025, 11, 2, 1, 30),),))
    operation = TimezoneConversion("Local", "UTC", TimezoneSource.fixed("America/New_York"))

    with pytest.raises(TransformationError) as captured:
        operation.apply(table)
    assert "ambiguous" in (captured.value.detail or "")

    first = (
        TimezoneConversion(
            "Local",
            "UTC",
            TimezoneSource.fixed("America/New_York"),
            dst_resolution=DstResolution.FIRST_OCCURRENCE,
        )
        .apply(table)
        .table
    )
    second = (
        TimezoneConversion(
            "Local",
            "UTC",
            TimezoneSource.fixed("America/New_York"),
            dst_resolution=DstResolution.SECOND_OCCURRENCE,
        )
        .apply(table)
        .table
    )
    assert second.rows[0][0] - first.rows[0][0] == timedelta(hours=1)


def test_nonexistent_dst_time_is_never_silently_corrected() -> None:
    table = DataTable(("Local",), ((datetime(2025, 3, 9, 2, 30),),))

    with pytest.raises(TransformationError) as captured:
        TimezoneConversion("Local", "UTC", TimezoneSource.fixed("America/New_York")).apply(table)
    assert "does not exist" in (captured.value.detail or "")


def test_embedded_source_keeps_manual_fixed_offset() -> None:
    embedded = datetime(2025, 8, 20, 13, 30, tzinfo=timezone(timedelta(hours=5, minutes=30)))
    table = DataTable(("Timestamp",), ((embedded,),))

    result = TimezoneConversion("Timestamp", "UTC", TimezoneSource.embedded()).apply(table).table

    assert result.rows[0][0] == datetime(2025, 8, 20, 8, tzinfo=UTC)


def test_iana_search_prioritizes_project_shortcuts() -> None:
    assert list_iana_timezones("colombo")[0] == "Asia/Colombo"
    assert list_iana_timezones("UTC")[0] == "UTC"
