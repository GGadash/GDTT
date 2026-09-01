"""Typed Phase 6 aggregation recipe and runtime round-trip coverage."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from data_transform_tool.aggregation import (
    AggregationApproach,
    AggregationConfig,
    AggregationStage,
    AggregationStatistic,
    CompletenessRule,
    FieldAggregation,
    PeriodKind,
    PeriodSpec,
)
from data_transform_tool.transformation.recipe import (
    AggregationRecipe,
    ColumnRecipe,
    OutputFormat,
    OutputRecipe,
    SourceFileType,
    SourceRecipe,
    TransformationRecipe,
)


def test_aggregation_recipe_round_trips_runtime_configuration_and_json() -> None:
    config = AggregationConfig(
        timestamp_column="Timestamp",
        input_interval=timedelta(hours=1),
        reporting_timezone="Asia/Colombo",
        fields=(
            FieldAggregation(
                "LAeq",
                AggregationStatistic.ENERGY_AVERAGE_LEQ,
                "LAeq - Energy Avg",
            ),
        ),
        approach=AggregationApproach.INCREMENTAL,
        stages=(
            AggregationStage(PeriodSpec.clock(timedelta(hours=8))),
            AggregationStage(
                PeriodSpec(PeriodKind.DAY),
                CompletenessRule(0.75, allow_two_of_three=True),
            ),
        ),
    )
    aggregation = AggregationRecipe.from_runtime(config)
    recipe = TransformationRecipe(
        mode="average",
        source=SourceRecipe(file_type=SourceFileType.CSV),
        columns=(ColumnRecipe(source_name="LAeq", output_name="LAeq"),),
        aggregation=aggregation,
        output=OutputRecipe(formats=(OutputFormat.CSV,)),
    )

    restored = TransformationRecipe.from_json(recipe.to_json())

    assert aggregation.to_runtime() == config
    assert restored == recipe
    assert restored.aggregation is not None
    assert restored.aggregation.stages[1].completeness.allow_two_of_three


def test_average_mode_requires_typed_aggregation_configuration() -> None:
    with pytest.raises(ValidationError, match="requires aggregation"):
        TransformationRecipe(
            mode="average",
            source=SourceRecipe(file_type=SourceFileType.CSV),
            columns=(ColumnRecipe(source_name="PM2.5", output_name="PM2.5"),),
            output=OutputRecipe(formats=(OutputFormat.CSV,)),
        )


def test_fixed_period_recipe_preserves_explicit_anchor() -> None:
    config = AggregationConfig(
        "Timestamp",
        timedelta(days=1),
        "UTC",
        (FieldAggregation("Rainfall", AggregationStatistic.RAINFALL_ACCUMULATION),),
        (
            AggregationStage(
                PeriodSpec(
                    PeriodKind.FIXED_DAYS,
                    duration=timedelta(days=30),
                    anchor=datetime(2026, 1, 1, tzinfo=UTC),
                )
            ),
        ),
    )

    restored = AggregationRecipe.from_runtime(config).to_runtime()

    assert restored == config


def test_machine_readable_schema_exposes_typed_aggregation_contract() -> None:
    schema_path = (
        Path(__file__).parents[2]
        / "About-Info"
        / "Machine-Readable"
        / "transformation_recipe_schema.json"
    )
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    aggregation = schema["$defs"]["aggregationRecipe"]
    assert aggregation["additionalProperties"] is False
    assert (
        "energy_average_leq"
        in schema["$defs"]["aggregationField"]["properties"]["statistic"]["enum"]
    )
    assert schema["properties"]["aggregation"]["anyOf"][0]["$ref"].endswith("aggregationRecipe")
