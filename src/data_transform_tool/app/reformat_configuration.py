"""Immutable Phase 5 reformat configuration drafts and recipe composition.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum

from data_transform_tool.datetime.models import TimestampRole
from data_transform_tool.io.models import FileInspection, FileKind, SemanticType
from data_transform_tool.transformation.recipe import (
    ColumnRecipe,
    GapFieldPolicyRecipe,
    GapRecipe,
    MissingDataRecipe,
    OutputFormat,
    OutputMissingPolicy,
    OutputRecipe,
    RemoveNullRecipe,
    SourceFileType,
    SourceRecipe,
    TimestampRecipe,
    TransformationRecipe,
    TransformationSpec,
)
from data_transform_tool.validation.numeric import InvalidNumericPolicy
from data_transform_tool.validation.rows import RemoveNullMode


class TransformChoice(StrEnum):
    KEEP = "keep"
    ROUND_2 = "round_2"
    PPM_TO_PPB = "ppm_to_ppb"
    PPB_TO_PPM = "ppb_to_ppm"


class TimezoneSourceMode(StrEnum):
    NONE = "none"
    EMBEDDED = "embedded"
    FIXED_IANA = "fixed_iana"
    IANA_COLUMN = "iana_column"
    MANUAL_OFFSET = "manual_offset"


class GapBehaviorChoice(StrEnum):
    NULL = "null"
    CARRY_STABLE = "carry_stable"
    FIXED_VALUE = "fixed_value"
    DERIVED_FROM_TIMESTAMP = "derived_from_timestamp"


@dataclass(frozen=True)
class ColumnDraft:
    source_name: str
    detected_type: SemanticType
    confidence: float
    missing_percent: float
    samples: tuple[str, ...]
    entirely_empty: bool
    warnings: tuple[str, ...]
    export: bool
    output_name: str
    output_type: SemanticType
    input_profile: str | None = None
    output_profile: str | None = None
    transform: TransformChoice = TransformChoice.KEEP
    timestamp_role: TimestampRole = TimestampRole.UNKNOWN
    timezone_source_mode: TimezoneSourceMode = TimezoneSourceMode.NONE
    timezone_source_value: str | None = None
    target_timezone: str | None = None
    derive_start: bool = False
    derive_midpoint: bool = False
    derive_end: bool = False
    gap_behavior: GapBehaviorChoice = GapBehaviorChoice.NULL
    gap_fixed_value: str | int | float | bool | None = None

    def __post_init__(self) -> None:
        if not self.source_name.strip() or not self.output_name.strip():
            raise ValueError("Source and output column names must not be blank.")
        if not 0 <= self.confidence <= 1:
            raise ValueError("Column confidence must be between zero and one.")
        if not 0 <= self.missing_percent <= 100:
            raise ValueError("Missing percentage must be between zero and one hundred.")

    @property
    def is_numeric(self) -> bool:
        return self.output_type in {SemanticType.INTEGER, SemanticType.DECIMAL}


@dataclass(frozen=True)
class ReformatDraft:
    source_kind: FileKind
    worksheet: str | None
    columns: tuple[ColumnDraft, ...]
    detected_missing_markers: tuple[str, ...]
    confirmed_missing_markers: tuple[str, ...] = ()
    gap_fill_enabled: bool = True
    timestamp_column: str | None = None
    timestamp_confirmed: bool = False
    interval_seconds: float | None = None
    interval_confirmed: bool = False
    allow_reorder: bool = False
    output_missing_policy: OutputMissingPolicy = OutputMissingPolicy.TRUE_NULL
    custom_missing_sentinel: str | int | float | None = None
    invalid_numeric_policy: InvalidNumericPolicy = InvalidNumericPolicy.NULL_AND_CONTINUE
    remove_empty_enabled: bool = False
    remove_empty_mode: RemoveNullMode = RemoveNullMode.ALL_MEASUREMENTS_MISSING

    def __post_init__(self) -> None:
        source_names = tuple(column.source_name for column in self.columns)
        if len(set(source_names)) != len(source_names):
            raise ValueError("Configuration source columns must be unique.")
        if self.interval_seconds is not None and self.interval_seconds <= 0:
            raise ValueError("The expected interval must be greater than zero.")

    def column(self, source_name: str) -> ColumnDraft:
        try:
            return next(column for column in self.columns if column.source_name == source_name)
        except StopIteration as error:
            raise ValueError(f"Unknown source column '{source_name}'.") from error

    def update_column(self, updated: ColumnDraft) -> ReformatDraft:
        self.column(updated.source_name)
        return replace(
            self,
            columns=tuple(
                updated if column.source_name == updated.source_name else column
                for column in self.columns
            ),
        )

    @property
    def exported_columns(self) -> tuple[ColumnDraft, ...]:
        return tuple(column for column in self.columns if column.export)

    @property
    def measurement_columns(self) -> tuple[ColumnDraft, ...]:
        return tuple(
            column
            for column in self.exported_columns
            if column.is_numeric and column.source_name != self.timestamp_column
        )


@dataclass(frozen=True)
class DraftValidation:
    errors: tuple[str, ...]
    warnings: tuple[str, ...]

    @property
    def ready(self) -> bool:
        return not self.errors


class ConfigurationSession:
    """Small undo/redo history for immutable configuration edits."""

    def __init__(self, initial: ReformatDraft) -> None:
        self.initial = initial
        self.current = initial
        self._undo: list[ReformatDraft] = []
        self._redo: list[ReformatDraft] = []

    @property
    def can_undo(self) -> bool:
        return bool(self._undo)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo)

    def apply(self, draft: ReformatDraft) -> bool:
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


def create_reformat_draft(inspection: FileInspection) -> ReformatDraft:
    timestamp_name = inspection.likely_datetime_column
    columns = tuple(
        _column_draft(profile, is_timestamp=profile.name == timestamp_name)
        for profile in inspection.columns
    )
    return ReformatDraft(
        source_kind=inspection.file_kind,
        worksheet=inspection.worksheet,
        columns=columns,
        detected_missing_markers=tuple(
            marker.value for marker in inspection.potential_missing_markers
        ),
        timestamp_column=timestamp_name,
        interval_seconds=inspection.likely_interval_seconds,
    )


def validate_reformat_draft(draft: ReformatDraft) -> DraftValidation:
    errors: list[str] = []
    warnings: list[str] = []
    exported = draft.exported_columns
    if not exported:
        errors.append("Select at least one field for export.")
    names = tuple(column.output_name.strip() for column in exported)
    if any(not name for name in names):
        errors.append("Exported output names must not be blank.")
    if len(set(names)) != len(names):
        errors.append("Exported output names must be unique.")
    if draft.output_missing_policy is OutputMissingPolicy.CUSTOM and (
        draft.custom_missing_sentinel is None or not str(draft.custom_missing_sentinel).strip()
    ):
        errors.append("Enter a custom missing-value sentinel.")
    if draft.gap_fill_enabled:
        if draft.timestamp_column is None:
            errors.append("Choose a primary timestamp before inserting missing time rows.")
        elif not draft.timestamp_confirmed:
            errors.append("Confirm the primary timestamp before inserting missing time rows.")
        if draft.interval_seconds is None:
            errors.append("Choose an expected interval before inserting missing time rows.")
        elif not draft.interval_confirmed:
            errors.append("Confirm the expected interval before inserting missing time rows.")
    for column in draft.columns:
        if column.target_timezone and column.timezone_source_mode is TimezoneSourceMode.NONE:
            errors.append(f"Choose how source timezone is supplied for '{column.source_name}'.")
        if (
            column.timezone_source_mode
            not in {
                TimezoneSourceMode.NONE,
                TimezoneSourceMode.EMBEDDED,
            }
            and not (column.timezone_source_value or "").strip()
        ):
            errors.append(f"Complete the source timezone setting for '{column.source_name}'.")
        if any((column.derive_start, column.derive_midpoint, column.derive_end)) and (
            draft.interval_seconds is None
            or column.timestamp_role
            not in {TimestampRole.START, TimestampRole.MIDPOINT, TimestampRole.END}
        ):
            errors.append(
                f"Derived interval fields for '{column.source_name}' require duration and "
                "Start, Midpoint, or End semantics."
            )
        if column.entirely_empty and column.export:
            warnings.append(f"'{column.source_name}' is entirely empty but selected for export.")
        warnings.extend(column.warnings)
    if draft.detected_missing_markers and not draft.confirmed_missing_markers:
        warnings.append("Potential input missing markers remain unconfirmed.")
    if not draft.measurement_columns:
        warnings.append("No exported numeric measurement fields are selected.")
    return DraftValidation(tuple(dict.fromkeys(errors)), tuple(dict.fromkeys(warnings)))


def build_transformation_recipe(draft: ReformatDraft) -> TransformationRecipe:
    validation = validate_reformat_draft(draft)
    if validation.errors:
        raise ValueError(" ".join(validation.errors))
    timestamp_draft = (
        draft.column(draft.timestamp_column) if draft.timestamp_column is not None else None
    )
    timestamp_recipe = None
    if timestamp_draft is not None:
        timestamp_recipe = TimestampRecipe(
            column=timestamp_draft.output_name,
            role=timestamp_draft.timestamp_role.value,
            duration_seconds=draft.interval_seconds,
            input_profile=timestamp_draft.input_profile,
            output_profile=timestamp_draft.output_profile,
            source_timezone=_timezone_source_description(timestamp_draft),
            target_timezone=timestamp_draft.target_timezone,
        )

    gap_recipe = None
    if draft.gap_fill_enabled:
        if timestamp_draft is None or draft.interval_seconds is None:
            raise AssertionError("Validated gap configuration must have timestamp and interval.")
        gap_recipe = GapRecipe(
            timestamp_column=timestamp_draft.output_name,
            interval_seconds=draft.interval_seconds,
            measurement_columns=tuple(column.output_name for column in draft.measurement_columns),
            field_policies=tuple(
                _gap_policy_recipe(column)
                for column in draft.exported_columns
                if column.source_name != draft.timestamp_column and not column.is_numeric
            ),
            allow_reorder=draft.allow_reorder,
        )

    numeric_columns = tuple(column.output_name for column in draft.measurement_columns)
    remove_rule = (
        RemoveNullRecipe(
            mode=draft.remove_empty_mode.value,
            columns=numeric_columns
            or tuple(column.output_name for column in draft.exported_columns),
        )
        if draft.remove_empty_enabled
        else None
    )
    custom_sentinel = (
        draft.custom_missing_sentinel
        if draft.output_missing_policy is OutputMissingPolicy.CUSTOM
        else None
    )
    return TransformationRecipe(
        source=SourceRecipe(
            file_type=_source_file_type(draft.source_kind),
            worksheet=draft.worksheet,
            expected_columns=tuple(column.source_name for column in draft.columns),
            missing_markers=draft.confirmed_missing_markers,
        ),
        columns=tuple(_column_recipe(column) for column in draft.columns),
        timestamp=timestamp_recipe,
        missing_data=MissingDataRecipe(
            confirmed_null_markers=draft.confirmed_missing_markers,
            numeric_columns=numeric_columns,
            invalid_numeric_policy=draft.invalid_numeric_policy.value,
            remove_null_rule=remove_rule,
        ),
        gap_policy=gap_recipe,
        output=OutputRecipe(
            formats=(OutputFormat.CSV,),
            missing_policy=draft.output_missing_policy,
            custom_missing_sentinel=custom_sentinel,
        ),
    )


def configuration_summary(draft: ReformatDraft) -> tuple[str, ...]:
    validation = validate_reformat_draft(draft)
    gap_state = "disabled"
    if draft.gap_fill_enabled:
        gap_state = (
            f"enabled at {_interval_label(draft.interval_seconds)}"
            if draft.interval_seconds is not None
            else "enabled; interval required"
        )
    return (
        f"{len(draft.exported_columns)} of {len(draft.columns)} fields selected",
        f"Gap insertion {gap_state}",
        f"Missing output: {_missing_policy_label(draft.output_missing_policy)}",
        f"Invalid numerics: {draft.invalid_numeric_policy.value.replace('_', ' ')}",
        f"Remove empty rows: {'on' if draft.remove_empty_enabled else 'off'}",
        (
            "Readiness: Ready"
            if validation.ready
            else f"Readiness: {len(validation.errors)} action(s) required"
        ),
    )


def _column_draft(profile: object, *, is_timestamp: bool) -> ColumnDraft:
    from data_transform_tool.io.models import ColumnProfile

    if not isinstance(profile, ColumnProfile):
        raise TypeError("Expected a column profile.")
    input_profile, output_profile = _suggest_profiles(profile.inferred_type)
    is_numeric = profile.inferred_type in {SemanticType.INTEGER, SemanticType.DECIMAL}
    gap_behavior = (
        GapBehaviorChoice.CARRY_STABLE
        if profile.unique_sample_count == 1
        and not profile.entirely_empty
        and not is_numeric
        and not is_timestamp
        else GapBehaviorChoice.NULL
    )
    return ColumnDraft(
        source_name=profile.name,
        detected_type=profile.inferred_type,
        confidence=profile.confidence,
        missing_percent=profile.missing_percent,
        samples=profile.examples,
        entirely_empty=profile.entirely_empty,
        warnings=profile.warnings,
        export=not profile.entirely_empty,
        output_name=profile.name,
        output_type=profile.inferred_type,
        input_profile=input_profile,
        output_profile=output_profile,
        timestamp_role=TimestampRole.START if is_timestamp else TimestampRole.UNKNOWN,
        timezone_source_value=(
            "UTC" if is_timestamp and "utc" in profile.name.casefold() else None
        ),
        gap_behavior=gap_behavior,
    )


def _suggest_profiles(semantic_type: SemanticType) -> tuple[str | None, str | None]:
    profiles = {
        SemanticType.DATE: ("iso_date", "iso_date"),
        SemanticType.TIME: ("time_minute", "time_minute"),
        SemanticType.DATETIME: ("iso_minute", "iso_minute"),
    }
    return profiles.get(semantic_type, (None, None))


def _column_recipe(column: ColumnDraft) -> ColumnRecipe:
    transformations: list[TransformationSpec] = []
    if column.input_profile is not None:
        transformations.append(
            TransformationSpec(
                kind="parse_datetime", parameters={"profile_id": column.input_profile}
            )
        )
    if column.transform is not TransformChoice.KEEP:
        parameters: dict[str, object] = {}
        if column.transform is TransformChoice.ROUND_2:
            parameters["decimals"] = 2
        transformations.append(
            TransformationSpec(kind=column.transform.value, parameters=parameters)
        )
    if column.target_timezone:
        transformations.append(
            TransformationSpec(
                kind="timezone_conversion",
                parameters={
                    "source_mode": column.timezone_source_mode.value,
                    "source_value": column.timezone_source_value,
                    "target_zone": column.target_timezone,
                },
            )
        )
    if any((column.derive_start, column.derive_midpoint, column.derive_end)):
        transformations.append(
            TransformationSpec(
                kind="derive_interval_fields",
                parameters={
                    "start": column.derive_start,
                    "midpoint": column.derive_midpoint,
                    "end": column.derive_end,
                    "role": column.timestamp_role.value,
                },
            )
        )
    if column.output_profile is not None:
        transformations.append(
            TransformationSpec(
                kind="format_datetime", parameters={"profile_id": column.output_profile}
            )
        )
    return ColumnRecipe(
        source_name=column.source_name,
        output_name=column.output_name,
        export=column.export,
        semantic_type=column.output_type.value,
        transformations=tuple(transformations),
    )


def _gap_policy_recipe(column: ColumnDraft) -> GapFieldPolicyRecipe:
    payload: dict[str, object] = {
        "column": column.output_name,
        "behavior": column.gap_behavior.value,
    }
    if column.gap_behavior is GapBehaviorChoice.DERIVED_FROM_TIMESTAMP:
        payload["derivation"] = "copy"
    elif column.gap_behavior is GapBehaviorChoice.FIXED_VALUE:
        payload["fixed_value"] = column.gap_fixed_value
    return GapFieldPolicyRecipe.model_validate(payload)


def _timezone_source_description(column: ColumnDraft) -> str | None:
    if column.timezone_source_mode is TimezoneSourceMode.NONE:
        return None
    if column.timezone_source_mode is TimezoneSourceMode.EMBEDDED:
        return "embedded"
    return f"{column.timezone_source_mode.value}:{column.timezone_source_value or ''}"


def _source_file_type(kind: FileKind) -> SourceFileType:
    return {
        FileKind.CSV: SourceFileType.CSV,
        FileKind.TSV: SourceFileType.TSV,
        FileKind.TXT: SourceFileType.TXT,
        FileKind.XLSX: SourceFileType.XLSX,
    }[kind]


def _interval_label(seconds: float | None) -> str:
    if seconds is None:
        return "unconfirmed interval"
    common = {60.0: "1 minute", 300.0: "5 minutes", 900.0: "15 minutes", 3600.0: "1 hour"}
    return common.get(seconds, f"{seconds:g} seconds")


def _missing_policy_label(policy: OutputMissingPolicy) -> str:
    return {
        OutputMissingPolicy.TRUE_NULL: "True Null",
        OutputMissingPolicy.NA: "N/A",
        OutputMissingPolicy.MINUS_999: "-999",
        OutputMissingPolicy.CUSTOM: "Custom sentinel",
    }[policy]
