"""Completeness-aware environmental time-series aggregation.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from data_transform_tool.aggregation.engine import (
    aggregate_first_stage,
    aggregate_table,
    continue_incremental_stages,
)
from data_transform_tool.aggregation.models import (
    AggregationApproach,
    AggregationConfig,
    AggregationError,
    AggregationResult,
    AggregationStage,
    AggregationStageReport,
    AggregationStageResult,
    AggregationStatistic,
    CompletenessRecord,
    CompletenessRule,
    FieldAggregation,
    PeriodBounds,
    PeriodKind,
    PeriodSpec,
    SeasonBoundary,
)
from data_transform_tool.aggregation.periods import Periodizer
from data_transform_tool.aggregation.strategies import (
    aggregate_numeric,
    duration_seconds,
    suggest_output_name,
    suggest_statistic,
)

__all__ = [
    "AggregationApproach",
    "AggregationConfig",
    "AggregationError",
    "AggregationResult",
    "AggregationStage",
    "AggregationStageReport",
    "AggregationStageResult",
    "AggregationStatistic",
    "CompletenessRecord",
    "CompletenessRule",
    "FieldAggregation",
    "PeriodBounds",
    "PeriodKind",
    "PeriodSpec",
    "Periodizer",
    "SeasonBoundary",
    "aggregate_first_stage",
    "aggregate_numeric",
    "aggregate_table",
    "continue_incremental_stages",
    "duration_seconds",
    "suggest_output_name",
    "suggest_statistic",
]
