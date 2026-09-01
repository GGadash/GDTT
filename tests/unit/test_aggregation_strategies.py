"""Numeric, acoustic, rainfall, rain-rate, and suggestion strategy coverage."""

from __future__ import annotations

import math

import pytest

from data_transform_tool.aggregation import (
    AggregationError,
    AggregationStatistic,
    aggregate_numeric,
    suggest_output_name,
    suggest_statistic,
)


def test_common_statistics_are_explicit_and_population_standard_deviation_is_stable() -> None:
    values = (1, 2, 3)

    assert aggregate_numeric(values, AggregationStatistic.ARITHMETIC_MEAN) == 2
    assert aggregate_numeric(values, AggregationStatistic.MINIMUM) == 1
    assert aggregate_numeric(values, AggregationStatistic.MAXIMUM) == 3
    assert aggregate_numeric(values, AggregationStatistic.SUM) == 6
    assert aggregate_numeric(values, AggregationStatistic.MEDIAN) == 2
    assert aggregate_numeric(values, AggregationStatistic.STANDARD_DEVIATION) == pytest.approx(
        math.sqrt(2 / 3)
    )
    assert aggregate_numeric(values, AggregationStatistic.COUNT) == 3


def test_equal_and_duration_weighted_leq_use_energy_not_arithmetic_average() -> None:
    equal = aggregate_numeric((60, 70), AggregationStatistic.ENERGY_AVERAGE_LEQ)
    weighted = aggregate_numeric((60, 70), AggregationStatistic.ENERGY_AVERAGE_LEQ, weights=(9, 1))

    assert equal == pytest.approx(67.40362689)
    assert weighted == pytest.approx(62.78753601)
    assert equal != 65


def test_rainfall_rain_rate_and_acoustic_name_suggestions_remain_advisory() -> None:
    assert suggest_statistic("Rainfall (mm)") is AggregationStatistic.RAINFALL_ACCUMULATION
    assert suggest_statistic("Rain Rate mm/h") is AggregationStatistic.RAIN_RATE_MEAN
    assert suggest_statistic("LAeq dB") is AggregationStatistic.ENERGY_AVERAGE_LEQ
    assert suggest_statistic("PM2.5") is AggregationStatistic.ARITHMETIC_MEAN
    assert (
        suggest_output_name("LAeq (dB)", AggregationStatistic.ENERGY_AVERAGE_LEQ)
        == "LAeq (dB) - Energy Avg"
    )


def test_invalid_or_nonfinite_numeric_values_are_blocked() -> None:
    with pytest.raises(AggregationError, match="requires numeric"):
        aggregate_numeric(("ERROR",), AggregationStatistic.ARITHMETIC_MEAN)
    with pytest.raises(AggregationError, match="finite"):
        aggregate_numeric((float("nan"),), AggregationStatistic.ARITHMETIC_MEAN)
