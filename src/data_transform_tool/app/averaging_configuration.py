"""Immutable Phase 7 averaging drafts, validation, and recipe composition.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, time, timedelta

from data_transform_tool.aggregation import (
    AggregationApproach,
    AggregationConfig,
    AggregationStage,
    AggregationStatistic,
    CompletenessRule,
    FieldAggregation,
    PeriodKind,
    PeriodSpec,
    SeasonBoundary,
    suggest_output_name,
    suggest_statistic,
)
from data_transform_tool.io.models import FileInspection, FileKind, SemanticType
from data_transform_tool.transformation.recipe import (
    AggregationRecipe,
    ColumnRecipe,
    MissingDataRecipe,
    OutputFormat,
    OutputMissingPolicy,
    OutputRecipe,
    SourceFileType,
    SourceRecipe,
    TimestampRecipe,
    TransformationRecipe,
)

DEFAULT_SEASONS = (
    SeasonBoundary("Northeast monsoon", 12, 1),
    SeasonBoundary("First inter-monsoon", 3, 1),
    SeasonBoundary("Southwest monsoon", 6, 1),
    SeasonBoundary("Second inter-monsoon", 10, 1),
)


@dataclass(frozen=True)
class AveragingFieldDraft:
    source_name: str
    detected_type: SemanticType
    confidence: float
    missing_percent: float
    samples: tuple[str, ...]
    warnings: tuple[str, ...]
    include: bool
    statistic: AggregationStatistic
    statistic_confirmed: bool
    output_name: str
    duration_column: str | None = None

    def __post_init__(self) -> None:
        if not self.source_name.strip() or not self.output_name.strip():
            raise ValueError("Source and output field names must not be blank.")
        if not 0 <= self.confidence <= 1:
            raise ValueError("Field confidence must be between zero and one.")
        if not 0 <= self.missing_percent <= 100:
            raise ValueError("Missing percentage must be between zero and one hundred.")

    @property
    def is_numeric(self) -> bool:
        return self.detected_type in {SemanticType.INTEGER, SemanticType.DECIMAL}


@dataclass(frozen=True)
class AveragingStageDraft:
    period: PeriodSpec
    threshold: float = 0.75
    allow_two_of_three: bool = False
    label: str | None = None

    def __post_init__(self) -> None:
        CompletenessRule(self.threshold, self.allow_two_of_three)

    def to_runtime(self) -> AggregationStage:
        return AggregationStage(
            self.period,
            CompletenessRule(self.threshold, self.allow_two_of_three),
            self.label,
        )


@dataclass(frozen=True)
class AveragingDraft:
    source_kind: FileKind
    worksheet: str | None
    expected_columns: tuple[str, ...]
    fields: tuple[AveragingFieldDraft, ...]
    detected_missing_markers: tuple[str, ...]
    confirmed_missing_markers: tuple[str, ...] = ()
    missing_marker_decisions_confirmed: bool = False
    timestamp_column: str | None = None
    timestamp_profile: str = "iso_minute"
    timestamp_confirmed: bool = False
    source_timezone: str = "UTC"
    source_timezone_confirmed: bool = False
    reporting_timezone: str = "UTC"
    reporting_timezone_confirmed: bool = False
    interval_seconds: float | None = None
    interval_confirmed: bool = False
    approach: AggregationApproach = AggregationApproach.DIRECT
    stages: tuple[AveragingStageDraft, ...] = (
        AveragingStageDraft(PeriodSpec.clock(timedelta(hours=1)), label="1 hour"),
    )
    allow_reorder: bool = False
    output_missing_policy: OutputMissingPolicy = OutputMissingPolicy.TRUE_NULL
    custom_missing_sentinel: str | int | float | None = None

    def __post_init__(self) -> None:
        if len(set(self.expected_columns)) != len(self.expected_columns):
            raise ValueError("Expected source columns must be unique.")
        if self.interval_seconds is not None and self.interval_seconds <= 0:
            raise ValueError("The input interval must be greater than zero.")
        source_names = tuple(field.source_name for field in self.fields)
        if len(set(source_names)) != len(source_names):
            raise ValueError("Averaging source fields must be unique.")

    def field(self, source_name: str) -> AveragingFieldDraft:
        try:
            return next(field for field in self.fields if field.source_name == source_name)
        except StopIteration as error:
            raise ValueError(f"Unknown averaging field '{source_name}'.") from error

    def update_field(self, updated: AveragingFieldDraft) -> AveragingDraft:
        self.field(updated.source_name)
        return replace(
            self,
            fields=tuple(
                updated if field.source_name == updated.source_name else field
                for field in self.fields
            ),
        )

    @property
    def selected_fields(self) -> tuple[AveragingFieldDraft, ...]:
        return tuple(field for field in self.fields if field.include)


@dataclass(frozen=True)
class AveragingValidation:
    errors: tuple[str, ...]
    warnings: tuple[str, ...]

    @property
    def ready(self) -> bool:
        return not self.errors


class AveragingConfigurationSession:
    """Undoable history over one immutable averaging draft."""

    def __init__(self, initial: AveragingDraft) -> None:
        self.initial = initial
        self.current = initial
        self._undo: list[AveragingDraft] = []
        self._redo: list[AveragingDraft] = []

    @property
    def can_undo(self) -> bool:
        return bool(self._undo)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo)

    def apply(self, draft: AveragingDraft) -> bool:
        if draft == self.current:
            return False
        self._undo.append(self.current)
        self.current = draft
        self._redo.clear()
        return True

    def undo(self) -> bool:
        if not self._undo:
            return False
        self._redo.append(self.current)
        self.current = self._undo.pop()
        return True

    def redo(self) -> bool:
        if not self._redo:
            return False
        self._undo.append(self.current)
        self.current = self._redo.pop()
        return True

    def reset(self) -> bool:
        return self.apply(self.initial)


def create_averaging_draft(inspection: FileInspection) -> AveragingDraft:
    timestamp = inspection.likely_datetime_column
    fields: list[AveragingFieldDraft] = []
    for profile in inspection.columns:
        if profile.name == timestamp:
            continue
        numeric = profile.inferred_type in {SemanticType.INTEGER, SemanticType.DECIMAL}
        statistic = suggest_statistic(profile.name)
        fields.append(
            AveragingFieldDraft(
                source_name=profile.name,
                detected_type=profile.inferred_type,
                confidence=profile.confidence,
                missing_percent=profile.missing_percent,
                samples=profile.examples,
                warnings=profile.warnings,
                include=numeric and not profile.entirely_empty,
                statistic=statistic,
                statistic_confirmed=False,
                output_name=suggest_output_name(profile.name, statistic),
            )
        )
    timezone_name = "UTC" if timestamp and "utc" in timestamp.casefold() else "Asia/Colombo"
    return AveragingDraft(
        source_kind=inspection.file_kind,
        worksheet=inspection.worksheet,
        expected_columns=inspection.column_names,
        fields=tuple(fields),
        detected_missing_markers=tuple(
            marker.value for marker in inspection.potential_missing_markers
        ),
        timestamp_column=timestamp,
        source_timezone=timezone_name,
        reporting_timezone=timezone_name,
        interval_seconds=inspection.likely_interval_seconds,
    )


def validate_averaging_draft(draft: AveragingDraft) -> AveragingValidation:
    errors: list[str] = []
    warnings: list[str] = []
    if draft.timestamp_column is None:
        errors.append("Choose the timestamp field.")
    elif not draft.timestamp_confirmed:
        errors.append("Confirm the timestamp field.")
    if not draft.source_timezone.strip():
        errors.append("Choose the source timestamp timezone.")
    elif not draft.source_timezone_confirmed:
        errors.append("Confirm the source timestamp timezone.")
    if not draft.reporting_timezone.strip():
        errors.append("Choose the reporting-boundary timezone.")
    elif not draft.reporting_timezone_confirmed:
        errors.append("Confirm the reporting-boundary timezone.")
    if draft.interval_seconds is None:
        errors.append("Choose the input interval.")
    elif not draft.interval_confirmed:
        errors.append("Confirm the input interval.")
    if not draft.selected_fields:
        errors.append("Select at least one numeric field to aggregate.")
    unconfirmed = tuple(
        field.source_name for field in draft.selected_fields if not field.statistic_confirmed
    )
    if unconfirmed:
        errors.append("Confirm the aggregation rule for every selected field.")
    output_names = tuple(field.output_name.strip() for field in draft.selected_fields)
    if any(not name for name in output_names):
        errors.append("Selected output names must not be blank.")
    if len(set(output_names)) != len(output_names):
        errors.append("Selected output names must be unique.")
    if draft.approach is AggregationApproach.DIRECT and len(draft.stages) != 1:
        errors.append("Direct aggregation requires exactly one target stage.")
    if draft.approach is AggregationApproach.INCREMENTAL and len(draft.stages) < 2:
        errors.append("Incremental aggregation requires at least two visible stages.")
    if draft.approach is AggregationApproach.DIRECT and any(
        stage.allow_two_of_three for stage in draft.stages
    ):
        errors.append("The 2-of-3 option is available only for Incremental stages.")
    if draft.output_missing_policy is OutputMissingPolicy.CUSTOM and (
        draft.custom_missing_sentinel is None or not str(draft.custom_missing_sentinel).strip()
    ):
        errors.append("Enter a custom missing-value sentinel.")
    if draft.detected_missing_markers and not draft.missing_marker_decisions_confirmed:
        errors.append("Review the detected input missing-marker decisions.")
    warnings.extend(warning for field in draft.selected_fields for warning in field.warnings)
    if not errors:
        try:
            build_aggregation_config(draft)
        except ValueError as error:
            errors.append(str(error))
    return AveragingValidation(
        tuple(dict.fromkeys(errors)),
        tuple(dict.fromkeys(warnings)),
    )


def build_aggregation_config(draft: AveragingDraft) -> AggregationConfig:
    if draft.timestamp_column is None or draft.interval_seconds is None:
        raise ValueError("Timestamp and input interval are required for aggregation.")
    return AggregationConfig(
        timestamp_column=draft.timestamp_column,
        input_interval=timedelta(seconds=draft.interval_seconds),
        reporting_timezone=draft.reporting_timezone,
        fields=tuple(
            FieldAggregation(
                field.source_name,
                field.statistic,
                field.output_name,
                field.duration_column,
            )
            for field in draft.selected_fields
        ),
        stages=tuple(stage.to_runtime() for stage in draft.stages),
        approach=draft.approach,
        allow_reorder=draft.allow_reorder,
    )


def build_averaging_recipe(draft: AveragingDraft) -> TransformationRecipe:
    validation = validate_averaging_draft(draft)
    if validation.errors:
        raise ValueError(" ".join(validation.errors))
    config = build_aggregation_config(draft)
    custom_sentinel = (
        draft.custom_missing_sentinel
        if draft.output_missing_policy is OutputMissingPolicy.CUSTOM
        else None
    )
    selected_names = {field.source_name for field in draft.selected_fields}
    timestamp = config.timestamp_column
    return TransformationRecipe(
        mode="average",
        source=SourceRecipe(
            file_type=_source_file_type(draft.source_kind),
            worksheet=draft.worksheet,
            expected_columns=draft.expected_columns,
            missing_markers=draft.confirmed_missing_markers,
        ),
        columns=tuple(
            ColumnRecipe(
                source_name=name,
                output_name=name,
                export=name == timestamp or name in selected_names,
                semantic_type=("datetime" if name == timestamp else "numeric"),
            )
            for name in draft.expected_columns
        ),
        timestamp=TimestampRecipe(
            column=timestamp,
            role="start",
            duration_seconds=config.input_interval.total_seconds(),
            input_profile=draft.timestamp_profile,
            source_timezone=f"fixed_iana:{draft.source_timezone}",
            target_timezone=config.reporting_timezone,
        ),
        missing_data=MissingDataRecipe(
            confirmed_null_markers=draft.confirmed_missing_markers,
            numeric_columns=tuple(field.source_name for field in draft.selected_fields),
        ),
        aggregation=AggregationRecipe.from_runtime(config),
        output=OutputRecipe(
            formats=(OutputFormat.CSV,),
            missing_policy=draft.output_missing_policy,
            custom_missing_sentinel=custom_sentinel,
        ),
    )


def averaging_summary(draft: AveragingDraft) -> tuple[str, ...]:
    validation = validate_averaging_draft(draft)
    chain = " → ".join(stage_label(stage) for stage in draft.stages)
    return (
        f"{len(draft.selected_fields)} of {len(draft.fields)} fields selected",
        f"Source zone: {draft.source_timezone}",
        f"Reporting zone: {draft.reporting_timezone}",
        f"Approach: {draft.approach.value.title()}",
        f"Visible chain: {chain or 'No stages configured'}",
        f"Default completeness: {draft.stages[0].threshold:.0%}",
        f"Missing output: {_missing_policy_label(draft.output_missing_policy)}",
        "Readiness: Ready"
        if validation.ready
        else f"Readiness: {len(validation.errors)} action(s) required",
    )


def stage_label(stage: AveragingStageDraft) -> str:
    if stage.label:
        return stage.label
    period = stage.period
    if period.kind is PeriodKind.FIXED_CLOCK and period.duration is not None:
        seconds = period.duration.total_seconds()
        common = {300.0: "5 minutes", 900.0: "15 minutes", 3600.0: "1 hour", 28800.0: "8 hours"}
        return common.get(seconds, f"{seconds:g} seconds")
    labels = {
        PeriodKind.DAY: "Day",
        PeriodKind.WEEK: "Week",
        PeriodKind.CALENDAR_MONTH: "Calendar month",
        PeriodKind.FIXED_DAYS: "Fixed days",
        PeriodKind.QUARTER: "Quarter",
        PeriodKind.SEASON: "Season",
        PeriodKind.CALENDAR_YEAR: "Calendar year",
        PeriodKind.FIXED_YEAR: "Fixed year",
    }
    return labels.get(period.kind, period.kind.value.replace("_", " ").title())


def period_from_choice(
    choice: str,
    *,
    day_start: time = time(0),
    week_start: int = 0,
    quarter_start_month: int = 1,
    year_start_month: int = 1,
    year_start_day: int = 1,
    anchor: datetime | None = None,
    custom_duration_seconds: float | None = None,
    seasons: tuple[SeasonBoundary, ...] = DEFAULT_SEASONS,
) -> PeriodSpec:
    fixed = {
        "5m": timedelta(minutes=5),
        "15m": timedelta(minutes=15),
        "1h": timedelta(hours=1),
        "8h": timedelta(hours=8),
    }
    if choice in fixed:
        return PeriodSpec.clock(fixed[choice], day_start=day_start)
    if choice == "custom_clock":
        if custom_duration_seconds is None:
            raise ValueError("A custom clock period requires a duration.")
        return PeriodSpec.clock(timedelta(seconds=custom_duration_seconds), day_start=day_start)
    if choice == "day":
        return PeriodSpec.day(day_start=day_start)
    if choice == "week":
        return PeriodSpec(PeriodKind.WEEK, day_start=day_start, week_start=week_start)
    if choice == "month":
        return PeriodSpec(PeriodKind.CALENDAR_MONTH, day_start=day_start)
    if choice == "fixed30":
        if anchor is None:
            raise ValueError("A fixed 30-day period requires an explicit anchor.")
        return PeriodSpec(
            PeriodKind.FIXED_DAYS,
            duration=timedelta(days=30),
            day_start=day_start,
            anchor=anchor,
        )
    if choice == "quarter":
        return PeriodSpec(
            PeriodKind.QUARTER,
            day_start=day_start,
            quarter_start_month=quarter_start_month,
        )
    if choice == "season":
        return PeriodSpec(PeriodKind.SEASON, day_start=day_start, seasons=seasons)
    if choice == "year":
        return PeriodSpec(
            PeriodKind.CALENDAR_YEAR,
            day_start=day_start,
            year_start_month=year_start_month,
            year_start_day=year_start_day,
        )
    if choice == "fixedyear":
        if anchor is None:
            raise ValueError("A fixed one-year period requires an explicit anchor.")
        return PeriodSpec(PeriodKind.FIXED_YEAR, day_start=day_start, anchor=anchor)
    raise ValueError(f"Unknown reporting-period choice '{choice}'.")


def _source_file_type(kind: FileKind) -> SourceFileType:
    return {
        FileKind.CSV: SourceFileType.CSV,
        FileKind.TSV: SourceFileType.TSV,
        FileKind.TXT: SourceFileType.TXT,
        FileKind.XLSX: SourceFileType.XLSX,
    }[kind]


def _missing_policy_label(policy: OutputMissingPolicy) -> str:
    return {
        OutputMissingPolicy.TRUE_NULL: "True Null",
        OutputMissingPolicy.NA: "N/A",
        OutputMissingPolicy.MINUS_999: "-999",
        OutputMissingPolicy.CUSTOM: "Custom sentinel",
    }[policy]
