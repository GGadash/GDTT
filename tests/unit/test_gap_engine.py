"""Confirmed-interval analysis and generated-row policy coverage."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from data_transform_tool.domain.table import DataTable
from data_transform_tool.gaps import (
    ConfirmedInterval,
    GapFieldPolicy,
    GapGenerationConfig,
    MetadataBehavior,
    TimestampDerivation,
    analyze_timestamps,
    generate_gap_rows,
    suggest_interval,
    suggest_stable_metadata,
)
from data_transform_tool.transformation.base import TransformationError


def test_interval_suggestion_and_multiple_gap_spans_are_separate() -> None:
    table = DataTable(
        ("Timestamp",),
        tuple((datetime(2026, 1, 1, hour),) for hour in (8, 9, 11, 12, 15)),
    )

    suggestion = suggest_interval(table, "Timestamp")
    analysis = analyze_timestamps(table, "Timestamp", ConfirmedInterval.hours(1))

    assert suggestion is not None
    assert suggestion.interval.duration == timedelta(hours=1)
    assert suggestion.matching_steps == 2
    assert suggestion.total_steps == 4
    assert tuple(timestamp.hour for timestamp in analysis.missing_timestamps) == (10, 13, 14)
    assert tuple(len(gap.missing_timestamps) for gap in analysis.gaps) == (1, 2)


def test_duplicates_disorder_invalid_timestamps_and_off_grid_are_reported() -> None:
    table = DataTable(
        ("Timestamp",),
        (
            (datetime(2026, 1, 1, 10),),
            (datetime(2026, 1, 1, 9),),
            (datetime(2026, 1, 1, 10),),
            (None,),
            (datetime(2026, 1, 1, 11, 30),),
        ),
    )

    analysis = analyze_timestamps(table, "Timestamp", ConfirmedInterval.hours(1))

    assert analysis.duplicate_row_groups == ((1, 3),)
    assert analysis.chronological_break_rows == (2,)
    assert analysis.invalid_timestamp_rows == (4,)
    assert analysis.off_grid_rows == (5,)
    assert not analysis.can_reconstruct


def test_elapsed_grid_handles_daylight_saving_transition() -> None:
    new_york = ZoneInfo("America/New_York")
    table = DataTable(
        ("Timestamp",),
        (
            (datetime(2026, 3, 8, 1, tzinfo=new_york),),
            (datetime(2026, 3, 8, 4, tzinfo=new_york),),
        ),
    )

    analysis = analyze_timestamps(table, "Timestamp", ConfirmedInterval.hours(1))

    assert len(analysis.missing_timestamps) == 1
    assert analysis.missing_timestamps[0].hour == 3
    assert analysis.missing_timestamps[0].utcoffset() == timedelta(hours=-4)


def test_mixed_aware_and_naive_timestamps_are_blocked() -> None:
    table = DataTable(
        ("Timestamp",),
        ((datetime(2026, 1, 1, 8),), (datetime(2026, 1, 1, 9, tzinfo=UTC),)),
    )

    with pytest.raises(TransformationError, match="mixes timezone-aware"):
        analyze_timestamps(table, "Timestamp", ConfirmedInterval.hours(1))


def test_gap_rows_keep_measurements_null_and_apply_explicit_metadata() -> None:
    table = DataTable(
        ("Timestamp", "Timestamp_End", "Date", "Station", "PM2.5", "Index", "Generated"),
        (
            (datetime(2026, 1, 1, 8, tzinfo=UTC), None, None, "Colombo Fort", 12.5, 8, None),
            (datetime(2026, 1, 1, 10, tzinfo=UTC), None, None, "Colombo Fort", 15.0, 10, None),
        ),
    )
    config = GapGenerationConfig(
        timestamp_column="Timestamp",
        interval=ConfirmedInterval.hours(1),
        measurement_columns=("PM2.5",),
        field_policies=(
            GapFieldPolicy("Station", MetadataBehavior.CARRY_STABLE),
            GapFieldPolicy(
                "Date",
                MetadataBehavior.DERIVED_FROM_TIMESTAMP,
                derivation=TimestampDerivation.DATE,
            ),
            GapFieldPolicy(
                "Timestamp_End",
                MetadataBehavior.DERIVED_FROM_TIMESTAMP,
                derivation=TimestampDerivation.INTERVAL_END,
                timezone_name="Asia/Colombo",
            ),
        ),
        index_column="Index",
        generated_flag_column="Generated",
    )

    result = generate_gap_rows(table, config)
    generated = result.table.rows[1]

    assert result.report.generated_rows == 1
    assert result.report.stable_metadata_columns == ("Station",)
    assert generated[0] == datetime(2026, 1, 1, 9, tzinfo=UTC)
    assert generated[1] == datetime(2026, 1, 1, 15, 30, tzinfo=ZoneInfo("Asia/Colombo"))
    assert str(generated[2]) == "2026-01-01"
    assert generated[3:] == ("Colombo Fort", None, 2, True)
    assert result.table.column_values("Index") == (1, 2, 3)
    assert result.table.column_values("Generated") == (False, True, False)


def test_unstable_metadata_is_never_silently_carried() -> None:
    table = DataTable(
        ("Timestamp", "Station", "PM"),
        (
            (datetime(2026, 1, 1, 8), "A", 10),
            (datetime(2026, 1, 1, 10), "B", 20),
        ),
    )
    suggestions = suggest_stable_metadata(table, excluded_columns=("Timestamp", "PM"))
    config = GapGenerationConfig(
        "Timestamp",
        ConfirmedInterval.hours(1),
        ("PM",),
        (GapFieldPolicy("Station", MetadataBehavior.CARRY_STABLE),),
    )

    assert suggestions == ()
    with pytest.raises(TransformationError, match="not stable"):
        generate_gap_rows(table, config)


def test_disordered_input_requires_explicit_reordering_permission() -> None:
    table = DataTable(
        ("Timestamp", "PM"),
        (
            (datetime(2026, 1, 1, 10), 20),
            (datetime(2026, 1, 1, 8), 10),
        ),
    )
    blocked = GapGenerationConfig("Timestamp", ConfirmedInterval.hours(1), ("PM",))
    allowed = GapGenerationConfig(
        "Timestamp", ConfirmedInterval.hours(1), ("PM",), allow_reorder=True
    )

    with pytest.raises(TransformationError, match="not chronological"):
        generate_gap_rows(table, blocked)
    assert generate_gap_rows(table, allowed).table.column_values("PM") == (10, None, 20)
