"""Cross-strategy acceptance coverage for the Phase 6 averaging engine."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from data_transform_tool.aggregation import (
    AggregationConfig,
    AggregationStage,
    AggregationStatistic,
    FieldAggregation,
    PeriodSpec,
    aggregate_table,
)
from data_transform_tool.domain.table import DataTable


def test_air_quality_sound_and_rain_fields_share_completeness_not_statistics() -> None:
    rows = tuple(
        (
            datetime(2026, 5, 1, tzinfo=UTC) + index * timedelta(minutes=5),
            float(index + 1) if index < 9 else None,
            60.0 if index < 9 else None,
            0.2 if index < 9 else None,
            2.0 if index < 9 else None,
        )
        for index in range(12)
    )
    config = AggregationConfig(
        timestamp_column="Timestamp",
        input_interval=timedelta(minutes=5),
        reporting_timezone="UTC",
        fields=(
            FieldAggregation("PM2.5", output_name="PM2.5 - Mean"),
            FieldAggregation(
                "LAeq",
                AggregationStatistic.ENERGY_AVERAGE_LEQ,
                "LAeq - Energy Avg",
            ),
            FieldAggregation(
                "Rainfall",
                AggregationStatistic.RAINFALL_ACCUMULATION,
                "Rainfall - Sum",
            ),
            FieldAggregation(
                "Rain Rate",
                AggregationStatistic.RAIN_RATE_MEAN,
                "Rain Rate - Mean",
            ),
        ),
        stages=(AggregationStage(PeriodSpec.clock(timedelta(hours=1))),),
    )

    result = aggregate_table(
        DataTable(("Timestamp", "PM2.5", "LAeq", "Rainfall", "Rain Rate"), rows),
        config,
    )

    record = result.table.records()[0]
    assert record["PM2.5 - Mean"] == 5
    assert record["LAeq - Energy Avg"] == pytest.approx(60)
    assert record["Rainfall - Sum"] == pytest.approx(1.8)
    assert record["Rain Rate - Mean"] == 2
    assert all(
        item.availability == 0.75 and item.accepted for item in result.stages[0].completeness
    )
