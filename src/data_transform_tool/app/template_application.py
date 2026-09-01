"""Apply a versioned recipe to an inspected draft without hiding schema changes.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from contextlib import suppress
from dataclasses import replace

from data_transform_tool.app.averaging_configuration import AveragingDraft, AveragingStageDraft
from data_transform_tool.app.reformat_configuration import (
    GapBehaviorChoice,
    ReformatDraft,
    TimezoneSourceMode,
    TransformChoice,
)
from data_transform_tool.datetime.models import TimestampRole
from data_transform_tool.io.models import SemanticType
from data_transform_tool.transformation.recipe import TransformationRecipe
from data_transform_tool.validation.numeric import InvalidNumericPolicy
from data_transform_tool.validation.rows import RemoveNullMode


def apply_reformat_template(
    draft: ReformatDraft,
    recipe: TransformationRecipe,
) -> ReformatDraft:
    """Rebuild a Reformat draft only after an exact source-schema match."""
    _validate_schema(tuple(column.source_name for column in draft.columns), recipe)
    if recipe.mode != "reformat":
        raise ValueError("An averaging template cannot be applied to Reformat.")
    recipe_columns = {
        column.source_name.casefold(): column
        for column in recipe.columns
        if column.source_name is not None
    }
    gap_by_output = (
        {policy.column: policy for policy in recipe.gap_policy.field_policies}
        if recipe.gap_policy
        else {}
    )
    columns = []
    timestamp_source: str | None = None
    for current in draft.columns:
        configured = recipe_columns[current.source_name.casefold()]
        operations = {item.kind: item.parameters for item in configured.transformations}
        transform = next(
            (
                TransformChoice(kind)
                for kind in operations
                if kind in {choice.value for choice in TransformChoice}
            ),
            TransformChoice.KEEP,
        )
        timezone_parameters = operations.get("timezone_conversion", {})
        source_mode = TimezoneSourceMode(
            str(timezone_parameters.get("source_mode", TimezoneSourceMode.NONE.value))
        )
        derivation = operations.get("derive_interval_fields", {})
        gap = gap_by_output.get(configured.output_name)
        output_type = current.output_type
        if configured.semantic_type is not None:
            with suppress(ValueError):
                output_type = SemanticType(configured.semantic_type)
        updated = replace(
            current,
            export=configured.export,
            output_name=configured.output_name,
            output_type=output_type,
            input_profile=_text(operations.get("parse_datetime", {}).get("profile_id")),
            output_profile=_text(operations.get("format_datetime", {}).get("profile_id")),
            transform=transform,
            timestamp_role=TimestampRole(str(derivation.get("role", current.timestamp_role.value))),
            timezone_source_mode=source_mode,
            timezone_source_value=_text(timezone_parameters.get("source_value")),
            target_timezone=_text(timezone_parameters.get("target_zone")),
            derive_start=bool(derivation.get("start", False)),
            derive_midpoint=bool(derivation.get("midpoint", False)),
            derive_end=bool(derivation.get("end", False)),
            gap_behavior=GapBehaviorChoice(gap.behavior) if gap else GapBehaviorChoice.NULL,
            gap_fixed_value=gap.fixed_value if gap else None,
        )
        if recipe.timestamp is not None and configured.output_name == recipe.timestamp.column:
            timestamp_source = current.source_name
            updated = replace(updated, timestamp_role=TimestampRole(recipe.timestamp.role))
        columns.append(updated)
    missing = recipe.missing_data
    removal = missing.remove_null_rule if missing else None
    return replace(
        draft,
        columns=tuple(columns),
        confirmed_missing_markers=tuple(str(item) for item in recipe.source.missing_markers),
        gap_fill_enabled=recipe.gap_policy is not None,
        timestamp_column=timestamp_source,
        timestamp_confirmed=timestamp_source is not None,
        interval_seconds=recipe.timestamp.duration_seconds if recipe.timestamp else None,
        interval_confirmed=bool(recipe.timestamp and recipe.timestamp.duration_seconds),
        allow_reorder=recipe.gap_policy.allow_reorder if recipe.gap_policy else False,
        output_missing_policy=recipe.output.missing_policy,
        custom_missing_sentinel=recipe.output.custom_missing_sentinel,
        invalid_numeric_policy=(
            InvalidNumericPolicy(missing.invalid_numeric_policy)
            if missing
            else draft.invalid_numeric_policy
        ),
        remove_empty_enabled=removal is not None,
        remove_empty_mode=RemoveNullMode(removal.mode) if removal else draft.remove_empty_mode,
    )


def apply_averaging_template(
    draft: AveragingDraft,
    recipe: TransformationRecipe,
) -> AveragingDraft:
    """Rebuild an Averaging draft only after an exact source-schema match."""
    _validate_schema(draft.expected_columns, recipe)
    if recipe.mode != "average" or recipe.aggregation is None or recipe.timestamp is None:
        raise ValueError("A Reformat template cannot be applied to Averaging.")
    runtime = recipe.aggregation.to_runtime()
    configured_fields = {field.column: field for field in runtime.fields}
    fields = tuple(
        replace(
            field,
            include=field.source_name in configured_fields,
            statistic=(
                configured_fields[field.source_name].statistic
                if field.source_name in configured_fields
                else field.statistic
            ),
            statistic_confirmed=field.source_name in configured_fields,
            output_name=(
                configured_fields[field.source_name].resolved_output_name
                if field.source_name in configured_fields
                else field.output_name
            ),
            duration_column=(
                configured_fields[field.source_name].duration_column
                if field.source_name in configured_fields
                else None
            ),
        )
        for field in draft.fields
    )
    source_timezone = recipe.timestamp.source_timezone or draft.source_timezone
    if source_timezone.startswith("fixed_iana:"):
        source_timezone = source_timezone.split(":", 1)[1]
    return replace(
        draft,
        fields=fields,
        confirmed_missing_markers=tuple(str(item) for item in recipe.source.missing_markers),
        missing_marker_decisions_confirmed=True,
        timestamp_column=recipe.aggregation.timestamp_column,
        timestamp_profile=recipe.timestamp.input_profile or draft.timestamp_profile,
        timestamp_confirmed=True,
        source_timezone=source_timezone,
        source_timezone_confirmed=True,
        reporting_timezone=recipe.aggregation.reporting_timezone,
        reporting_timezone_confirmed=True,
        interval_seconds=recipe.aggregation.input_interval_seconds,
        interval_confirmed=True,
        approach=recipe.aggregation.approach,
        stages=tuple(
            AveragingStageDraft(
                stage.period,
                stage.completeness.threshold,
                stage.completeness.allow_two_of_three,
                stage.label,
            )
            for stage in runtime.stages
        ),
        allow_reorder=recipe.aggregation.allow_reorder,
        output_missing_policy=recipe.output.missing_policy,
        custom_missing_sentinel=recipe.output.custom_missing_sentinel,
    )


def _validate_schema(columns: tuple[str, ...], recipe: TransformationRecipe) -> None:
    if {name.casefold() for name in columns} != {
        name.casefold() for name in recipe.source.expected_columns
    }:
        raise ValueError(
            "Template Apply requires the same source schema. Review or ignore this likely match."
        )


def _text(value: object) -> str | None:
    return str(value) if value is not None and str(value).strip() else None
