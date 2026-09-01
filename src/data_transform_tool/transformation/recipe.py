"""Versioned immutable recipe models that never contain measurement records.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from datetime import datetime, time, timedelta
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from data_transform_tool.aggregation.models import (
    AggregationApproach,
    AggregationConfig,
    AggregationStage,
    AggregationStatistic,
    CompletenessRule,
    FieldAggregation,
    PeriodKind,
    PeriodSpec,
    SeasonBoundary,
)


class RecipeModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class SourceFileType(StrEnum):
    CSV = "csv"
    TSV = "tsv"
    TXT = "txt"
    XLSX = "xlsx"


class OutputFormat(StrEnum):
    CSV = "csv"
    XLSX_PLAIN = "xlsx_plain"
    XLSX_FORMATTED = "xlsx_formatted"


class OutputMissingPolicy(StrEnum):
    TRUE_NULL = "true_null"
    NA = "na"
    MINUS_999 = "minus_999"
    CUSTOM = "custom"


class SourceRecipe(RecipeModel):
    file_type: SourceFileType
    worksheet: str | None = None
    expected_columns: tuple[str, ...] = ()
    missing_markers: tuple[str | int | float, ...] = ()

    @model_validator(mode="after")
    def validate_worksheet(self) -> SourceRecipe:
        if self.file_type is SourceFileType.XLSX and not self.worksheet:
            raise ValueError("An XLSX recipe must name one worksheet.")
        if self.file_type is not SourceFileType.XLSX and self.worksheet is not None:
            raise ValueError("Worksheet is only valid for XLSX sources.")
        return self


class TransformationSpec(RecipeModel):
    """Safe registry key and inert JSON-like parameters; never executable code."""

    kind: str = Field(min_length=1)
    parameters: dict[str, object] = Field(default_factory=dict)


class ColumnRecipe(RecipeModel):
    source_name: str | None
    output_name: str = Field(min_length=1)
    export: bool = True
    semantic_type: str | None = None
    transformations: tuple[TransformationSpec, ...] = ()
    aggregation: dict[str, object] | None = None


class TimestampRecipe(RecipeModel):
    column: str
    role: Literal["start", "end", "midpoint", "instantaneous", "unknown", "custom"]
    duration_seconds: float | None = Field(default=None, gt=0)
    input_profile: str | None = None
    output_profile: str | None = None
    source_timezone: str | None = None
    target_timezone: str | None = None


class GapFieldPolicyRecipe(RecipeModel):
    column: str = Field(min_length=1)
    behavior: Literal["null", "carry_stable", "fixed_value", "derived_from_timestamp"]
    fixed_value: str | int | float | bool | None = None
    derivation: (
        Literal[
            "copy",
            "date",
            "time",
            "year",
            "month",
            "day",
            "iso_weekday",
            "interval_start",
            "interval_midpoint",
            "interval_end",
        ]
        | None
    ) = None
    timezone_name: str | None = None

    @model_validator(mode="after")
    def validate_policy(self) -> GapFieldPolicyRecipe:
        if self.behavior == "derived_from_timestamp" and self.derivation is None:
            raise ValueError("A timestamp-derived gap field requires a derivation.")
        if self.behavior != "derived_from_timestamp" and (
            self.derivation is not None or self.timezone_name is not None
        ):
            raise ValueError("Derivation settings require derived_from_timestamp behavior.")
        return self


class GapRecipe(RecipeModel):
    timestamp_column: str = Field(min_length=1)
    interval_seconds: float = Field(gt=0)
    measurement_columns: tuple[str, ...]
    field_policies: tuple[GapFieldPolicyRecipe, ...] = ()
    allow_reorder: bool = False
    index_column: str | None = None
    index_start: int = 1
    generated_flag_column: str | None = None

    @model_validator(mode="after")
    def validate_gap_columns(self) -> GapRecipe:
        if any(not column.strip() for column in self.measurement_columns):
            raise ValueError("Gap measurement column names must not be blank.")
        if len(set(self.measurement_columns)) != len(self.measurement_columns):
            raise ValueError("Gap measurement columns must be unique.")
        policy_columns = tuple(policy.column for policy in self.field_policies)
        if len(set(policy_columns)) != len(policy_columns):
            raise ValueError("Gap field policy columns must be unique.")
        forbidden = set(self.measurement_columns) | {self.timestamp_column}
        if forbidden.intersection(policy_columns):
            raise ValueError("Timestamp and measurement columns cannot use metadata policies.")
        special_columns = tuple(
            column
            for column in (self.index_column, self.generated_flag_column)
            if column is not None
        )
        if any(not column.strip() for column in special_columns):
            raise ValueError("Gap special column names must not be blank.")
        if forbidden.intersection(special_columns):
            raise ValueError("Gap special columns cannot replace timestamps or measurements.")
        if len(set(special_columns)) != len(special_columns):
            raise ValueError("Gap index and generated-flag columns must be different.")
        return self


class RemoveNullRecipe(RecipeModel):
    mode: Literal[
        "all_measurements_missing",
        "all_selected_missing",
        "any_required_missing",
        "selected_subset_missing",
        "below_present_threshold",
    ]
    columns: tuple[str, ...] = Field(min_length=1)
    minimum_present: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_threshold(self) -> RemoveNullRecipe:
        if any(not column.strip() for column in self.columns):
            raise ValueError("Remove-null column names must not be blank.")
        if len(set(self.columns)) != len(self.columns):
            raise ValueError("Remove-null columns must be unique.")
        if self.mode == "below_present_threshold":
            if self.minimum_present is None:
                raise ValueError("A threshold removal rule requires minimum_present.")
            if self.minimum_present > len(self.columns):
                raise ValueError("minimum_present exceeds the selected column count.")
        elif self.minimum_present is not None:
            raise ValueError("minimum_present is only valid for a threshold removal rule.")
        return self


class MissingDataRecipe(RecipeModel):
    confirmed_null_markers: tuple[str | int | float, ...] = ()
    numeric_columns: tuple[str, ...] = ()
    invalid_numeric_policy: Literal["null_and_continue", "inspect", "stop", "preserve_source"] = (
        "null_and_continue"
    )
    remove_null_rule: RemoveNullRecipe | None = None

    @model_validator(mode="after")
    def validate_numeric_columns(self) -> MissingDataRecipe:
        if any(not column.strip() for column in self.numeric_columns):
            raise ValueError("Numeric column names must not be blank.")
        if len(set(self.numeric_columns)) != len(self.numeric_columns):
            raise ValueError("Numeric columns must be unique.")
        return self


class SeasonBoundaryRecipe(RecipeModel):
    name: str = Field(min_length=1)
    month: int = Field(ge=1, le=12)
    day: int = Field(default=1, ge=1, le=31)

    def to_runtime(self) -> SeasonBoundary:
        return SeasonBoundary(self.name, self.month, self.day)


class AggregationPeriodRecipe(RecipeModel):
    kind: PeriodKind
    duration_seconds: float | None = Field(default=None, gt=0)
    day_start: time = time(0, 0)
    week_start: int = Field(default=0, ge=0, le=6)
    anchor: datetime | None = None
    quarter_start_month: int = Field(default=1, ge=1, le=12)
    year_start_month: int = Field(default=1, ge=1, le=12)
    year_start_day: int = Field(default=1, ge=1, le=31)
    seasons: tuple[SeasonBoundaryRecipe, ...] = ()

    def to_runtime(self) -> PeriodSpec:
        return PeriodSpec(
            kind=self.kind,
            duration=(
                timedelta(seconds=self.duration_seconds)
                if self.duration_seconds is not None
                else None
            ),
            day_start=self.day_start,
            week_start=self.week_start,
            anchor=self.anchor,
            quarter_start_month=self.quarter_start_month,
            year_start_month=self.year_start_month,
            year_start_day=self.year_start_day,
            seasons=tuple(season.to_runtime() for season in self.seasons),
        )

    @classmethod
    def from_runtime(cls, period: PeriodSpec) -> AggregationPeriodRecipe:
        return cls(
            kind=period.kind,
            duration_seconds=(
                period.duration.total_seconds() if period.duration is not None else None
            ),
            day_start=period.day_start,
            week_start=period.week_start,
            anchor=period.anchor,
            quarter_start_month=period.quarter_start_month,
            year_start_month=period.year_start_month,
            year_start_day=period.year_start_day,
            seasons=tuple(
                SeasonBoundaryRecipe(name=item.name, month=item.month, day=item.day)
                for item in period.seasons
            ),
        )


class CompletenessRecipe(RecipeModel):
    threshold: float = Field(default=0.75, gt=0, le=1)
    allow_two_of_three: bool = False

    def to_runtime(self) -> CompletenessRule:
        return CompletenessRule(self.threshold, self.allow_two_of_three)


class AggregationStageRecipe(RecipeModel):
    period: AggregationPeriodRecipe
    completeness: CompletenessRecipe = CompletenessRecipe()
    label: str | None = Field(default=None, min_length=1)

    def to_runtime(self) -> AggregationStage:
        return AggregationStage(
            self.period.to_runtime(),
            self.completeness.to_runtime(),
            self.label,
        )


class AggregationFieldRecipe(RecipeModel):
    column: str = Field(min_length=1)
    statistic: AggregationStatistic = AggregationStatistic.ARITHMETIC_MEAN
    output_name: str | None = Field(default=None, min_length=1)
    duration_column: str | None = Field(default=None, min_length=1)

    def to_runtime(self) -> FieldAggregation:
        return FieldAggregation(
            self.column,
            self.statistic,
            self.output_name,
            self.duration_column,
        )


class AggregationRecipe(RecipeModel):
    timestamp_column: str = Field(min_length=1)
    input_interval_seconds: float = Field(gt=0)
    reporting_timezone: str = Field(min_length=1)
    fields: tuple[AggregationFieldRecipe, ...] = Field(min_length=1)
    stages: tuple[AggregationStageRecipe, ...] = Field(min_length=1)
    approach: AggregationApproach = AggregationApproach.DIRECT
    allow_reorder: bool = False
    max_periods: int = Field(default=1_000_000, gt=0)

    @model_validator(mode="after")
    def validate_aggregation(self) -> AggregationRecipe:
        self.to_runtime()
        return self

    def to_runtime(self) -> AggregationConfig:
        return AggregationConfig(
            timestamp_column=self.timestamp_column,
            input_interval=timedelta(seconds=self.input_interval_seconds),
            reporting_timezone=self.reporting_timezone,
            fields=tuple(field.to_runtime() for field in self.fields),
            stages=tuple(stage.to_runtime() for stage in self.stages),
            approach=self.approach,
            allow_reorder=self.allow_reorder,
            max_periods=self.max_periods,
        )

    @classmethod
    def from_runtime(cls, config: AggregationConfig) -> AggregationRecipe:
        return cls(
            timestamp_column=config.timestamp_column,
            input_interval_seconds=config.input_interval.total_seconds(),
            reporting_timezone=config.reporting_timezone,
            fields=tuple(
                AggregationFieldRecipe(
                    column=field.column,
                    statistic=field.statistic,
                    output_name=field.output_name,
                    duration_column=field.duration_column,
                )
                for field in config.fields
            ),
            stages=tuple(
                AggregationStageRecipe(
                    period=AggregationPeriodRecipe.from_runtime(stage.period),
                    completeness=CompletenessRecipe(
                        threshold=stage.completeness.threshold,
                        allow_two_of_three=stage.completeness.allow_two_of_three,
                    ),
                    label=stage.label,
                )
                for stage in config.stages
            ),
            approach=config.approach,
            allow_reorder=config.allow_reorder,
            max_periods=config.max_periods,
        )


class OutputRecipe(RecipeModel):
    formats: tuple[OutputFormat, ...]
    missing_policy: OutputMissingPolicy = OutputMissingPolicy.TRUE_NULL
    custom_missing_sentinel: str | int | float | None = None
    style_profile: str | None = None

    @model_validator(mode="after")
    def validate_output(self) -> OutputRecipe:
        if not self.formats:
            raise ValueError("At least one output format is required.")
        if len(set(self.formats)) != len(self.formats):
            raise ValueError("Output formats must be unique.")
        if (
            self.missing_policy is OutputMissingPolicy.CUSTOM
            and self.custom_missing_sentinel is None
        ):
            raise ValueError("A custom missing policy requires a sentinel.")
        if (
            self.missing_policy is not OutputMissingPolicy.CUSTOM
            and self.custom_missing_sentinel is not None
        ):
            raise ValueError("A custom sentinel is only valid with the custom policy.")
        return self


class TransformationRecipe(RecipeModel):
    schema_version: Literal[1] = 1
    recipe_name: str | None = Field(default=None, min_length=1)
    mode: Literal["reformat", "average"] = "reformat"
    source: SourceRecipe
    columns: tuple[ColumnRecipe, ...]
    timestamp: TimestampRecipe | None = None
    missing_data: MissingDataRecipe | None = None
    gap_policy: GapRecipe | None = None
    aggregation: AggregationRecipe | None = None
    output: OutputRecipe

    @model_validator(mode="after")
    def validate_columns(self) -> TransformationRecipe:
        output_names = tuple(column.output_name for column in self.columns if column.export)
        if len(set(output_names)) != len(output_names):
            raise ValueError("Exported output column names must be unique.")
        if self.mode == "average" and self.aggregation is None:
            raise ValueError("An average-mode recipe requires aggregation configuration.")
        if self.mode == "reformat" and self.aggregation is not None:
            raise ValueError("Aggregation configuration is only valid in average mode.")
        return self

    def to_json(self) -> str:
        return self.model_dump_json(indent=2)

    @classmethod
    def from_json(cls, payload: str | bytes) -> TransformationRecipe:
        return cls.model_validate_json(payload)
