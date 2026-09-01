"""Direct, incremental, completeness, validation, and DST executor coverage."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from data_transform_tool.aggregation import (
    AggregationApproach,
    AggregationConfig,
    AggregationError,
    AggregationStage,
    AggregationStatistic,
    CompletenessRule,
    FieldAggregation,
    PeriodSpec,
    aggregate_table,
)
from data_transform_tool.domain.table import DataTable


def _direct_config(*, allow_reorder: bool = False) -> AggregationConfig:
    return AggregationConfig(
        timestamp_column="Timestamp",
        input_interval=timedelta(hours=1),
        reporting_timezone="UTC",
        fields=(FieldAggregation("PM2.5"),),
        stages=(AggregationStage(PeriodSpec.day()),),
        allow_reorder=allow_reorder,
    )


def test_direct_daily_aggregation_uses_expected_not_observed_rows_for_completeness() -> None:
    rows = tuple(
        (datetime(2026, 1, 1, hour, tzinfo=UTC), float(hour)) for hour in range(18)
    ) + tuple((datetime(2026, 1, 2, hour, tzinfo=UTC), float(hour)) for hour in range(17))

    result = aggregate_table(DataTable(("Timestamp", "PM2.5"), rows), _direct_config())

    assert result.table.row_count == 2
    assert result.table.rows[0][2] == pytest.approx(8.5)
    assert result.table.rows[1][2] is None
    assert result.stages[0].report.values_accepted == 1
    assert result.stages[0].report.values_rejected == 1
    assert result.stages[0].completeness[0].expected_count == 24
    assert result.stages[0].completeness[0].availability == 0.75
    assert result.stages[0].completeness[1].valid_count == 17


def test_incremental_chain_keeps_stage_results_and_allows_explicit_two_of_three() -> None:
    rows = tuple(
        (
            datetime(2026, 1, 1, hour, tzinfo=UTC),
            None if hour in (16, 17, 18) else (1.0 if hour < 8 else 2.0),
        )
        for hour in range(24)
    )
    config = AggregationConfig(
        timestamp_column="Timestamp",
        input_interval=timedelta(hours=1),
        reporting_timezone="UTC",
        fields=(FieldAggregation("PM2.5"),),
        approach=AggregationApproach.INCREMENTAL,
        stages=(
            AggregationStage(PeriodSpec.clock(timedelta(hours=8)), label="Hourly to 8-hour"),
            AggregationStage(
                PeriodSpec.day(),
                CompletenessRule(0.75, allow_two_of_three=True),
                label="Three 8-hour values to day",
            ),
        ),
    )

    result = aggregate_table(DataTable(("Timestamp", "PM2.5"), rows), config)

    assert len(result.stages) == 2
    assert result.stages[0].table.column_values("PM2.5") == (1.0, 2.0, None)
    assert result.table.column_values("PM2.5") == (1.5,)
    final_record = result.stages[1].completeness[0]
    assert (final_record.valid_count, final_record.expected_count) == (2, 3)
    assert final_record.accepted and final_record.used_two_of_three


@pytest.mark.parametrize(
    ("start", "end", "expected"),
    (
        (
            datetime(2026, 3, 8, tzinfo=ZoneInfo("America/New_York")),
            datetime(2026, 3, 9, tzinfo=ZoneInfo("America/New_York")),
            23,
        ),
        (
            datetime(2026, 11, 1, tzinfo=ZoneInfo("America/New_York")),
            datetime(2026, 11, 2, tzinfo=ZoneInfo("America/New_York")),
            25,
        ),
    ),
)
def test_direct_daily_completeness_honors_dst_elapsed_hours(
    start: datetime, end: datetime, expected: int
) -> None:
    start_utc = start.astimezone(UTC)
    end_utc = end.astimezone(UTC)
    rows = tuple(
        ((start_utc + timedelta(hours=index)).astimezone(start.tzinfo), 10.0)
        for index in range(int((end_utc - start_utc) / timedelta(hours=1)))
    )
    config = AggregationConfig(
        "Timestamp",
        timedelta(hours=1),
        "America/New_York",
        (FieldAggregation("PM2.5"),),
        (AggregationStage(PeriodSpec.day()),),
    )

    result = aggregate_table(DataTable(("Timestamp", "PM2.5"), rows), config)

    assert result.table.column_values("PM2.5") == (10.0,)
    assert result.stages[0].completeness[0].expected_count == expected
    assert result.stages[0].completeness[0].availability == 1


def test_duplicate_disorder_and_off_grid_rows_are_not_silently_aggregated() -> None:
    duplicate = DataTable(
        ("Timestamp", "PM2.5"),
        (
            (datetime(2026, 1, 1, tzinfo=UTC), 1.0),
            (datetime(2026, 1, 1, tzinfo=UTC), 2.0),
        ),
    )
    disorder = DataTable(
        ("Timestamp", "PM2.5"),
        (
            (datetime(2026, 1, 1, 1, tzinfo=UTC), 2.0),
            (datetime(2026, 1, 1, tzinfo=UTC), 1.0),
        ),
    )
    off_grid = DataTable(
        ("Timestamp", "PM2.5"),
        ((datetime(2026, 1, 1, 0, 30, tzinfo=UTC), 1.0),),
    )

    with pytest.raises(AggregationError, match="Duplicate timestamp"):
        aggregate_table(duplicate, _direct_config())
    with pytest.raises(AggregationError, match="not chronological"):
        aggregate_table(disorder, _direct_config())
    reordered = aggregate_table(disorder, _direct_config(allow_reorder=True))
    assert reordered.diagnostics[0].code == "aggregation.input_reordered"
    with pytest.raises(AggregationError, match="off the confirmed input grid"):
        aggregate_table(off_grid, _direct_config())


def test_direct_approach_rejects_two_of_three_configuration() -> None:
    with pytest.raises(ValueError, match="only valid for Incremental"):
        AggregationConfig(
            "Timestamp",
            timedelta(hours=1),
            "UTC",
            (FieldAggregation("PM2.5"),),
            (AggregationStage(PeriodSpec.day(), CompletenessRule(0.75, allow_two_of_three=True)),),
        )


def test_duration_weighted_leq_flows_through_the_executor() -> None:
    table = DataTable(
        ("Timestamp", "LAeq", "Duration"),
        (
            (datetime(2026, 1, 1, tzinfo=UTC), 60.0, 9.0),
            (datetime(2026, 1, 1, 0, 30, tzinfo=UTC), 70.0, 1.0),
        ),
    )
    config = AggregationConfig(
        "Timestamp",
        timedelta(minutes=30),
        "UTC",
        (
            FieldAggregation(
                "LAeq",
                AggregationStatistic.ENERGY_AVERAGE_LEQ,
                duration_column="Duration",
            ),
        ),
        (AggregationStage(PeriodSpec.clock(timedelta(hours=1))),),
    )

    result = aggregate_table(table, config)

    assert result.table.column_values("LAeq") == (pytest.approx(62.78753601),)


def test_aggregation_honors_cooperative_cancellation() -> None:
    class Cancelled(Exception):
        pass

    checks = 0

    def cancel() -> None:
        nonlocal checks
        checks += 1
        if checks == 2:
            raise Cancelled

    table = DataTable(
        ("Timestamp", "PM2.5"),
        ((datetime(2026, 1, 1, tzinfo=UTC), 1.0),),
    )

    with pytest.raises(Cancelled):
        aggregate_table(table, _direct_config(), cancellation_check=cancel)
