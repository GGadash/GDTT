"""Phase 8 full-file preparation, evidence review, export, and verification.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from data_transform_tool import __version__
from data_transform_tool.aggregation.batch_engine import execute_averaging_batches
from data_transform_tool.app.averaging_configuration import AveragingDraft
from data_transform_tool.app.reformat_configuration import ReformatDraft
from data_transform_tool.domain.batches import TabularData
from data_transform_tool.domain.errors import AppError
from data_transform_tool.domain.spill import SpillWorkspace
from data_transform_tool.export.models import ExportPlan, ExportResult, VerificationStatus
from data_transform_tool.export.naming import (
    data_output_path,
    sanitize_windows_name,
    suggest_base_name,
)
from data_transform_tool.export.verification import verify_artifacts
from data_transform_tool.export.writers import write_data_outputs
from data_transform_tool.io.cancellation import CancellationToken
from data_transform_tool.io.full_reader import read_full_spill
from data_transform_tool.io.models import FileInspection, PreviewSlice
from data_transform_tool.reporting import (
    ProcessingEvidence,
    build_processing_report,
    recipe_for_export,
    write_report_sidecars,
)
from data_transform_tool.transformation.batch_executor import execute_reformat_batches
from data_transform_tool.transformation.recipe import TransformationRecipe

type WorkflowDraft = ReformatDraft | AveragingDraft
ProgressCallback = Callable[[int, str], None]


@dataclass(frozen=True)
class PreparedExport:
    inspection: FileInspection
    draft: WorkflowDraft
    recipe: TransformationRecipe
    input_table: TabularData
    output_table: TabularData
    input_previews: tuple[PreviewSlice, ...]
    output_previews: tuple[PreviewSlice, ...]
    suggested_base_name: str
    evidence: ProcessingEvidence
    workspace: SpillWorkspace | None = field(default=None, repr=False, compare=False)

    def close(self) -> None:
        """Release private spill files after export, reset, or navigation."""
        if self.workspace is not None:
            self.workspace.close()


def prepare_export(
    inspection: FileInspection,
    draft: WorkflowDraft,
    recipe: TransformationRecipe,
    cancellation: CancellationToken,
    progress: ProgressCallback | None = None,
) -> PreparedExport:
    """Execute the complete source independently of bounded UI previews."""
    if progress is not None:
        progress(0, "Reading complete source")
    read_progress = (
        (lambda message, count: progress(20, f"{message}: {count:,} rows"))
        if progress is not None
        else None
    )
    workspace: SpillWorkspace | None = None
    output: TabularData
    if isinstance(draft, ReformatDraft):
        workspace = SpillWorkspace()
        try:
            spill_read = read_full_spill(
                inspection,
                cancellation,
                workspace,
                progress=read_progress,
            )
            cancellation.raise_if_cancelled()
            if progress is not None:
                progress(35, "Applying confirmed transformation plan in batches")
            reformat_result = execute_reformat_batches(
                spill_read.table,
                draft,
                workspace,
                cancellation,
                progress=(
                    (lambda message, count: progress(55, f"{message}: {count:,} rows"))
                    if progress is not None
                    else None
                ),
            )
            output = reformat_result.table
            invalid_values = sum(item.count for item in reformat_result.diagnostics)
            diagnostic_warnings = tuple(
                f"{item.message} ({item.count:,})" if item.count else item.message
                for item in reformat_result.diagnostics
            )
            evidence = ProcessingEvidence(
                spill_read.table,
                output,
                spill_read.strategy + "; chunked Reformat with external spill ordering",
                generated_gap_rows=reformat_result.generated_gap_rows,
                removed_rows=reformat_result.removed_rows,
                invalid_values=invalid_values,
                warnings=(*inspection.warnings, *diagnostic_warnings),
            )
            input_table: TabularData = spill_read.table
        except Exception:
            workspace.close()
            raise
    else:
        workspace = SpillWorkspace()
        try:
            spill_read = read_full_spill(
                inspection,
                cancellation,
                workspace,
                progress=read_progress,
            )
            cancellation.raise_if_cancelled()
            if progress is not None:
                progress(35, "Applying confirmed aggregation plan in period batches")
            aggregation_result = execute_averaging_batches(
                spill_read.table,
                draft,
                workspace,
                cancellation,
                progress=(
                    (lambda message, count: progress(55, f"{message}: {count:,} rows"))
                    if progress is not None
                    else None
                ),
            )
            output = aggregation_result.table
            stage_summaries = tuple(
                (
                    f"Stage {stage.report.stage_index} ({stage.report.label}): "
                    f"{stage.report.periods_evaluated:,} periods, "
                    f"{stage.report.values_accepted:,} accepted, "
                    f"{stage.report.values_rejected:,} rejected, "
                    f"threshold {stage.report.completeness.threshold:.0%}"
                )
                for stage in aggregation_result.stages
            )
            diagnostics = tuple(
                f"{item.message} ({item.count:,})" if item.count else item.message
                for item in aggregation_result.diagnostics
            )
            evidence = ProcessingEvidence(
                spill_read.table,
                output,
                spill_read.strategy
                + "; streamed reporting-period aggregation with retained stage evidence",
                rejected_averages=sum(
                    stage.report.values_rejected for stage in aggregation_result.stages
                ),
                stage_summaries=stage_summaries,
                warnings=(*inspection.warnings, *diagnostics),
            )
            input_table = spill_read.table
        except Exception:
            workspace.close()
            raise
    warning_list = list(evidence.warnings)
    if output.row_count + 1 > 1_048_576:
        warning_list.append(
            "The result exceeds Excel's worksheet row limit; select CSV or split the output."
        )
        evidence = ProcessingEvidence(
            evidence.input_table,
            evidence.output_table,
            evidence.execution_strategy,
            evidence.generated_gap_rows,
            evidence.removed_rows,
            evidence.invalid_values,
            evidence.rejected_averages,
            evidence.stage_summaries,
            tuple(warning_list),
            evidence.errors,
        )
    if progress is not None:
        progress(100, "Full-file review is ready")
    return PreparedExport(
        inspection,
        draft,
        recipe,
        input_table,
        output,
        _preview_slices(input_table),
        _preview_slices(output),
        suggest_base_name(inspection.path, output, recipe.mode),
        evidence,
        workspace,
    )


def execute_export(
    prepared: PreparedExport,
    plan: ExportPlan,
    cancellation: CancellationToken,
    progress: ProgressCallback | None = None,
) -> ExportResult:
    """Write, reopen, verify, report, and preserve failures as explicit evidence."""
    export_recipe = recipe_for_export(prepared.recipe, plan)
    _preflight_targets(plan)
    if progress is not None:
        progress(0, "Writing selected outputs")
    data_artifacts = write_data_outputs(
        prepared.output_table,
        plan,
        cancellation,
        progress=(
            (lambda percent, message: progress(int(percent * 0.65), message))
            if progress is not None
            else None
        ),
    )
    cancellation.raise_if_cancelled()
    if progress is not None:
        progress(70, "Reopening and verifying outputs")
    verifications = verify_artifacts(
        data_artifacts,
        prepared.output_table,
        plan,
        cancellation,
    )
    verification_errors = tuple(
        f"{result.artifact.name}: {check.name} — {check.detail}"
        for result in verifications
        if result.status is VerificationStatus.FAILED
        for check in result.checks
        if not check.passed and not check.warning
    )
    evidence = ProcessingEvidence(
        prepared.evidence.input_table,
        prepared.evidence.output_table,
        prepared.evidence.execution_strategy,
        prepared.evidence.generated_gap_rows,
        prepared.evidence.removed_rows,
        prepared.evidence.invalid_values,
        prepared.evidence.rejected_averages,
        prepared.evidence.stage_summaries,
        prepared.evidence.warnings,
        (*prepared.evidence.errors, *verification_errors),
    )
    report = build_processing_report(
        app_version=__version__,
        inspection=prepared.inspection,
        recipe=export_recipe,
        evidence=evidence,
        artifacts=data_artifacts,
        verifications=verifications,
    )
    sidecars = write_report_sidecars(
        plan,
        export_recipe,
        report,
        warnings=evidence.warnings,
        errors=evidence.errors,
    )
    if progress is not None:
        progress(100, "Export and verification complete")
    return ExportResult(
        (*data_artifacts, *sidecars),
        verifications,
        report,
        evidence.warnings,
        evidence.errors,
    )


def _preview_slices(table: TabularData, size: int = 5) -> tuple[PreviewSlice, ...]:
    if table.row_count == 0:
        return (PreviewSlice("First", 1, ()),)
    starts = (
        ("First", 0),
        ("Middle", max((table.row_count - size) // 2, 0)),
        ("Last", max(table.row_count - size, 0)),
    )
    unique: list[PreviewSlice] = []
    seen: set[int] = set()
    for label, start in starts:
        if start in seen:
            continue
        seen.add(start)
        unique.append(PreviewSlice(label, start + 1, table.read_rows(start, size)))
    return tuple(unique)


def _preflight_targets(plan: ExportPlan) -> None:
    """Reject all known collisions before the first output is written."""
    base_name = sanitize_windows_name(plan.base_name)
    targets = [data_output_path(plan.destination, plan.base_name, item) for item in plan.formats]
    if plan.write_transformation_info:
        targets.append(plan.destination / f"{base_name}_Transformation_Info.txt")
    if plan.write_recipe:
        targets.append(plan.destination / f"{base_name}_Recipe.json")
    if plan.write_summary:
        targets.append(plan.destination / f"{base_name}_Summary.txt")
    if plan.write_error_report:
        targets.append(plan.destination / f"{base_name}_Warnings_Errors.txt")
    collisions = tuple(path.name for path in targets if path.exists())
    if collisions and not plan.allow_overwrite:
        raise AppError(
            "One or more planned output files already exist. "
            "Choose another name or explicitly allow overwrite.",
            detail=", ".join(collisions),
        )
