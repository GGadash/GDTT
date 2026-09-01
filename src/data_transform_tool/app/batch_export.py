"""Sequential, independently verified batch export orchestration for GDTT.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path

from data_transform_tool.app.export_workflow import (
    PreparedExport,
    WorkflowDraft,
    execute_export,
    prepare_export,
)
from data_transform_tool.export.models import ExportPlan, ExportResult
from data_transform_tool.export.naming import sanitize_windows_name
from data_transform_tool.io.cancellation import CancellationToken, InspectionCancelled
from data_transform_tool.io.models import FileInspection
from data_transform_tool.transformation.recipe import TransformationRecipe

BatchProgressCallback = Callable[[int, str], None]


@dataclass(frozen=True)
class BatchExportItem:
    """Per-source batch outcome; one failure never masquerades as batch success."""

    source: Path
    result: ExportResult | None = None
    error: str | None = None

    @property
    def passed(self) -> bool:
        return self.result is not None and not self.result.errors and self.error is None


@dataclass(frozen=True)
class BatchExportResult:
    """Ordered per-source results for a batch run."""

    items: tuple[BatchExportItem, ...]

    @property
    def passed_count(self) -> int:
        return sum(item.passed for item in self.items)

    @property
    def failed_count(self) -> int:
        return len(self.items) - self.passed_count


def execute_batch_export(
    reference_prepared: PreparedExport,
    inspections: tuple[FileInspection, ...],
    draft: WorkflowDraft,
    recipe: TransformationRecipe,
    plan: ExportPlan,
    cancellation: CancellationToken,
    progress: BatchProgressCallback | None = None,
) -> BatchExportResult:
    """Prepare, export, reopen, and verify each compatible file independently."""
    if not inspections:
        raise ValueError("A batch export requires at least one inspected file.")
    plans = _batch_plans(inspections, recipe.mode, plan)
    items: list[BatchExportItem] = []
    total = len(inspections)
    for index, (inspection, item_plan) in enumerate(zip(inspections, plans, strict=True), start=1):
        cancellation.raise_if_cancelled()
        prepared = reference_prepared if index == 1 else None
        try:
            if progress is not None:
                progress(
                    int(((index - 1) / total) * 100),
                    f"Preparing {index} of {total}: {inspection.path.name}",
                )
            if prepared is None:
                prepared = prepare_export(
                    inspection,
                    draft,
                    recipe,
                    cancellation,
                    _source_progress(progress, index, total, start_percent=0, span=0.45),
                )
            result = execute_export(
                prepared,
                item_plan,
                cancellation,
                _source_progress(progress, index, total, start_percent=45, span=0.55),
            )
        except InspectionCancelled:
            raise
        except Exception as error:  # isolate one source and retain explicit evidence
            items.append(BatchExportItem(inspection.path, error=str(error)))
        else:
            items.append(BatchExportItem(inspection.path, result=result))
        finally:
            if index != 1 and prepared is not None:
                prepared.close()
    if progress is not None:
        progress(100, "Batch export and per-file verification complete")
    return BatchExportResult(tuple(items))


def _batch_plans(
    inspections: tuple[FileInspection, ...],
    mode: str,
    plan: ExportPlan,
) -> tuple[ExportPlan, ...]:
    if len(inspections) == 1:
        return (plan,)
    suffix = "AVG" if mode == "average" else "RF"
    used: set[str] = set()
    plans: list[ExportPlan] = []
    for inspection in inspections:
        base = sanitize_windows_name(f"{inspection.path.stem}_{suffix}")
        candidate = base
        serial = 2
        while candidate.casefold() in used:
            candidate = sanitize_windows_name(f"{base}_{serial}")
            serial += 1
        used.add(candidate.casefold())
        plans.append(replace(plan, base_name=candidate))
    return tuple(plans)


def _scaled_progress(index: int, total: int, percent: int, fraction: float) -> int:
    item_fraction = min(max(percent / 100 * fraction, 0), 1)
    return min(int((((index - 1) + item_fraction) / total) * 100), 99)


def _source_progress(
    progress: BatchProgressCallback | None,
    index: int,
    total: int,
    *,
    start_percent: int,
    span: float,
) -> BatchProgressCallback | None:
    if progress is None:
        return None

    def report(percent: int, message: str) -> None:
        source_percent = start_percent + int(percent * span)
        progress(
            _scaled_progress(index, total, source_percent, 1.0),
            f"{index} of {total} · {message}",
        )

    return report
