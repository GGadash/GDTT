"""Human-readable and machine-readable Phase 8 processing evidence.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from data_transform_tool.domain.batches import TabularData
from data_transform_tool.export.models import (
    ExportArtifact,
    ExportPlan,
    VerificationResult,
)
from data_transform_tool.export.naming import sanitize_windows_name
from data_transform_tool.io.models import FileInspection
from data_transform_tool.transformation.recipe import OutputRecipe, TransformationRecipe


@dataclass(frozen=True)
class ProcessingEvidence:
    input_table: TabularData
    output_table: TabularData
    execution_strategy: str
    generated_gap_rows: int = 0
    removed_rows: int = 0
    invalid_values: int = 0
    rejected_averages: int = 0
    stage_summaries: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()


def recipe_for_export(recipe: TransformationRecipe, plan: ExportPlan) -> TransformationRecipe:
    output = OutputRecipe(
        formats=plan.formats,
        missing_policy=plan.missing_policy,
        custom_missing_sentinel=(
            plan.custom_missing_sentinel if plan.missing_policy.value == "custom" else None
        ),
        style_profile=(
            plan.xlsx_style.name
            if any(output.value == "xlsx_formatted" for output in plan.formats)
            else None
        ),
    )
    return recipe.model_copy(update={"output": output})


def build_processing_report(
    *,
    app_version: str,
    inspection: FileInspection,
    recipe: TransformationRecipe,
    evidence: ProcessingEvidence,
    artifacts: tuple[ExportArtifact, ...],
    verifications: tuple[VerificationResult, ...],
) -> str:
    now = datetime.now(ZoneInfo("Asia/Colombo")).isoformat(timespec="seconds")
    output_names = ", ".join(artifact.path.name for artifact in artifacts) or "None"
    lines = [
        "DATA TRANSFORM TOOL — TRANSFORMATION INFORMATION",
        "",
        f"Application version: {app_version}",
        f"Processed at: {now}",
        f"Mode: {recipe.mode}",
        f"Input file: {inspection.path}",
        f"Input format: {inspection.file_kind.value}",
        f"Worksheet: {inspection.worksheet or 'Not applicable'}",
        f"Execution strategy: {evidence.execution_strategy}",
        f"Output files: {output_names}",
        "",
        "COUNTS AND STRUCTURE",
        f"Input rows: {evidence.input_table.row_count:,}",
        f"Output rows: {evidence.output_table.row_count:,}",
        f"Input columns: {evidence.input_table.column_count}",
        f"Output columns: {evidence.output_table.column_count}",
        f"Output column order: {', '.join(evidence.output_table.columns)}",
        f"Generated gap rows: {evidence.generated_gap_rows:,}",
        f"Removed rows: {evidence.removed_rows:,}",
        f"Invalid values handled: {evidence.invalid_values:,}",
        f"Rejected averages: {evidence.rejected_averages:,}",
        "",
        "TRANSFORMATION PLAN",
        f"Missing output policy: {recipe.output.missing_policy.value}",
        f"Confirmed input missing markers: {_join(recipe.source.missing_markers)}",
        f"Timestamp column: {recipe.timestamp.column if recipe.timestamp else 'Not configured'}",
        f"Timestamp role: {recipe.timestamp.role if recipe.timestamp else 'Not configured'}",
        (
            f"Timezone conversion: {recipe.timestamp.source_timezone or 'unspecified'} "
            f"to {recipe.timestamp.target_timezone or 'unchanged'}"
            if recipe.timestamp
            else "Timezone conversion: Not configured"
        ),
        f"Gap generation: {'enabled' if recipe.gap_policy else 'disabled'}",
        (
            f"Null-row removal: {recipe.missing_data.remove_null_rule.mode}"
            if recipe.missing_data and recipe.missing_data.remove_null_rule
            else "Null-row removal: disabled"
        ),
        f"Aggregation: {'enabled' if recipe.aggregation else 'disabled'}",
        *evidence.stage_summaries,
        "",
        "POST-EXPORT VERIFICATION",
    ]
    for verification in verifications:
        lines.append(f"{verification.artifact.name}: {verification.status.value}")
        lines.extend(
            f"  - {'PASS' if check.passed else 'FAIL'} — {check.name}: {check.detail}"
            for check in verification.checks
        )
    lines.extend(
        ("", "WARNINGS", *(_items(evidence.warnings)), "", "ERRORS", *(_items(evidence.errors)))
    )
    return "\n".join(lines).rstrip() + "\n"


def write_report_sidecars(
    plan: ExportPlan,
    recipe: TransformationRecipe,
    report_text: str,
    *,
    warnings: tuple[str, ...] = (),
    errors: tuple[str, ...] = (),
) -> tuple[ExportArtifact, ...]:
    base_name = sanitize_windows_name(plan.base_name)
    files: list[tuple[str, Path, str]] = []
    if plan.write_transformation_info:
        files.append(
            (
                "transformation_info",
                plan.destination / f"{base_name}_Transformation_Info.txt",
                report_text,
            )
        )
    if plan.write_recipe:
        files.append(
            ("recipe", plan.destination / f"{base_name}_Recipe.json", recipe.to_json() + "\n")
        )
    if plan.write_summary:
        summary = "\n".join(
            (
                "GDTT export completed.",
                f"Formats: {', '.join(item.value for item in plan.formats)}",
                f"Missing output: {plan.missing_policy.value}",
                f"Warnings: {len(warnings)}",
                f"Errors: {len(errors)}",
            )
        )
        files.append(("summary", plan.destination / f"{base_name}_Summary.txt", summary + "\n"))
    if plan.write_error_report and (warnings or errors):
        detail = "\n".join(("WARNINGS", *(_items(warnings)), "", "ERRORS", *(_items(errors))))
        files.append(
            (
                "warnings_errors",
                plan.destination / f"{base_name}_Warnings_Errors.txt",
                detail + "\n",
            )
        )
    artifacts: list[ExportArtifact] = []
    for kind, path, payload in files:
        if path.exists() and not plan.allow_overwrite:
            raise FileExistsError(f"'{path.name}' already exists.")
        _write_text_atomic(path, payload)
        artifacts.append(ExportArtifact(kind, path))
    return tuple(artifacts)


def _write_text_atomic(path: Path, payload: str) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.stem}-", suffix=path.suffix, dir=path.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        temporary.write_text(payload, encoding="utf-8")
        os.replace(temporary, path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _join(values: tuple[object, ...]) -> str:
    return ", ".join(str(value) for value in values) if values else "None"


def _items(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(f"- {value}" for value in values) or ("None",)
