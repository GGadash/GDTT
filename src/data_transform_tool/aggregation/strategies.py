"""Isolated numeric, acoustic, rainfall, and naming aggregation strategies.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from datetime import timedelta
from decimal import Decimal
from statistics import median, pstdev

from data_transform_tool.aggregation.models import AggregationError, AggregationStatistic
from data_transform_tool.domain.table import CellValue


def aggregate_numeric(
    values: Sequence[CellValue],
    statistic: AggregationStatistic,
    *,
    weights: Sequence[float] | None = None,
) -> CellValue:
    """Aggregate already-selected valid components using one explicit strategy."""
    if not values:
        return None
    numbers = tuple(_finite_number(value) for value in values)
    if statistic is AggregationStatistic.COUNT:
        return len(numbers)
    if statistic is AggregationStatistic.MINIMUM:
        return min(numbers)
    if statistic is AggregationStatistic.MAXIMUM:
        return max(numbers)
    if statistic in {AggregationStatistic.SUM, AggregationStatistic.RAINFALL_ACCUMULATION}:
        return math.fsum(numbers)
    if statistic is AggregationStatistic.MEDIAN:
        return float(median(numbers))
    if statistic is AggregationStatistic.STANDARD_DEVIATION:
        return float(pstdev(numbers))
    if statistic in {
        AggregationStatistic.ARITHMETIC_MEAN,
        AggregationStatistic.RAIN_RATE_MEAN,
    }:
        return math.fsum(numbers) / len(numbers)
    if statistic is AggregationStatistic.ENERGY_AVERAGE_LEQ:
        resolved_weights = tuple(weights or (1.0,) * len(numbers))
        if len(resolved_weights) != len(numbers):
            raise AggregationError("Leq values and durations must have the same length.")
        if any(not math.isfinite(weight) or weight <= 0 for weight in resolved_weights):
            raise AggregationError("Leq duration weights must be finite and greater than zero.")
        try:
            weighted_energy = math.fsum(
                weight * math.pow(10.0, level / 10.0)
                for level, weight in zip(numbers, resolved_weights, strict=True)
            )
        except OverflowError as error:
            raise AggregationError("A Leq value is outside the supported numeric range.") from error
        return 10.0 * math.log10(weighted_energy / math.fsum(resolved_weights))
    raise AssertionError(f"Unsupported aggregation statistic: {statistic}.")


def duration_seconds(value: CellValue) -> float:
    """Interpret an explicit duration as positive seconds for weighted Leq."""
    seconds = value.total_seconds() if isinstance(value, timedelta) else _finite_number(value)
    if seconds <= 0:
        raise AggregationError("Leq observation durations must be greater than zero.")
    return seconds


def suggest_statistic(column_name: str) -> AggregationStatistic:
    """Return an advisory name-based strategy suggestion; callers must still confirm it."""
    normalized = "".join(character for character in column_name.casefold() if character.isalnum())
    if any(token in normalized for token in ("laeq", "lceq", "lzeq")) or normalized == "leq":
        return AggregationStatistic.ENERGY_AVERAGE_LEQ
    if "rainrate" in normalized:
        return AggregationStatistic.RAIN_RATE_MEAN
    if "rainfall" in normalized or "rainamount" in normalized:
        return AggregationStatistic.RAINFALL_ACCUMULATION
    return AggregationStatistic.ARITHMETIC_MEAN


def suggest_output_name(column_name: str, statistic: AggregationStatistic) -> str:
    """Offer a readable optional suffix without forcing a field rename."""
    suffixes = {
        AggregationStatistic.ARITHMETIC_MEAN: "Mean",
        AggregationStatistic.MINIMUM: "Min",
        AggregationStatistic.MAXIMUM: "Max",
        AggregationStatistic.SUM: "Sum",
        AggregationStatistic.MEDIAN: "Median",
        AggregationStatistic.STANDARD_DEVIATION: "Std Dev",
        AggregationStatistic.COUNT: "Count",
        AggregationStatistic.ENERGY_AVERAGE_LEQ: "Energy Avg",
        AggregationStatistic.RAINFALL_ACCUMULATION: "Sum",
        AggregationStatistic.RAIN_RATE_MEAN: "Mean",
    }
    return f"{column_name} - {suffixes[statistic]}"


def _finite_number(value: CellValue) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise AggregationError(f"Aggregation requires numeric values; received {value!r}.")
    number = float(value)
    if not math.isfinite(number):
        raise AggregationError("Aggregation values must be finite numbers.")
    return number
