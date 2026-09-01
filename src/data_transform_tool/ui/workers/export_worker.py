"""Qt workers for Phase 8 full-file preparation and verified export.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import QObject, Signal, Slot

from data_transform_tool.app.batch_export import execute_batch_export
from data_transform_tool.app.export_workflow import (
    PreparedExport,
    WorkflowDraft,
    execute_export,
    prepare_export,
)
from data_transform_tool.domain.errors import AppError
from data_transform_tool.export.models import ExportPlan
from data_transform_tool.io.cancellation import CancellationToken, InspectionCancelled
from data_transform_tool.io.models import FileInspection
from data_transform_tool.transformation.recipe import TransformationRecipe

LOGGER = logging.getLogger(__name__)


class PreparationWorker(QObject):
    completed = Signal(object)
    failed = Signal(str, str)
    cancelled = Signal()
    progress_changed = Signal(int, str)

    def __init__(
        self,
        inspection: FileInspection,
        draft: WorkflowDraft,
        recipe: TransformationRecipe,
        cancellation: CancellationToken,
    ) -> None:
        super().__init__()
        self._inspection = inspection
        self._draft = draft
        self._recipe = recipe
        self._cancellation = cancellation

    @Slot()
    def run(self) -> None:
        try:
            result = prepare_export(
                self._inspection,
                self._draft,
                self._recipe,
                self._cancellation,
                self._progress,
            )
        except InspectionCancelled:
            self.cancelled.emit()
        except AppError as error:
            self.failed.emit(error.user_message, error.detail or "")
        except Exception as error:  # pragma: no cover - defensive worker boundary
            LOGGER.exception("Unexpected full-file preparation failure")
            self.failed.emit("The full-file review could not be prepared.", str(error))
        else:
            self.completed.emit(result)

    def _progress(self, percent: int, message: str) -> None:
        self.progress_changed.emit(percent, message)


class ExecutionWorker(QObject):
    completed = Signal(object)
    failed = Signal(str, str)
    cancelled = Signal()
    progress_changed = Signal(int, str)

    def __init__(
        self,
        prepared: PreparedExport,
        plan: ExportPlan,
        cancellation: CancellationToken,
    ) -> None:
        super().__init__()
        self._prepared = prepared
        self._plan = plan
        self._cancellation = cancellation

    @Slot()
    def run(self) -> None:
        try:
            result = execute_export(
                self._prepared,
                self._plan,
                self._cancellation,
                self._progress,
            )
        except InspectionCancelled:
            self.cancelled.emit()
        except AppError as error:
            self.failed.emit(error.user_message, error.detail or "")
        except Exception as error:  # pragma: no cover - defensive worker boundary
            LOGGER.exception("Unexpected export failure")
            self.failed.emit("The export could not be completed.", str(error))
        else:
            self.completed.emit(result)

    def _progress(self, percent: int, message: str) -> None:
        self.progress_changed.emit(percent, message)


class BatchExecutionWorker(QObject):
    """Run compatible sources sequentially with independent verification evidence."""

    completed = Signal(object)
    failed = Signal(str, str)
    cancelled = Signal()
    progress_changed = Signal(int, str)

    def __init__(
        self,
        prepared: PreparedExport,
        inspections: tuple[FileInspection, ...],
        draft: WorkflowDraft,
        recipe: TransformationRecipe,
        plan: ExportPlan,
        cancellation: CancellationToken,
    ) -> None:
        super().__init__()
        self._prepared = prepared
        self._inspections = inspections
        self._draft = draft
        self._recipe = recipe
        self._plan = plan
        self._cancellation = cancellation

    @Slot()
    def run(self) -> None:
        try:
            result = execute_batch_export(
                self._prepared,
                self._inspections,
                self._draft,
                self._recipe,
                self._plan,
                self._cancellation,
                self._progress,
            )
        except InspectionCancelled:
            self.cancelled.emit()
        except AppError as error:
            self.failed.emit(error.user_message, error.detail or "")
        except Exception as error:  # pragma: no cover - defensive worker boundary
            LOGGER.exception("Unexpected batch export failure")
            self.failed.emit("The batch export could not be completed.", str(error))
        else:
            self.completed.emit(result)

    def _progress(self, percent: int, message: str) -> None:
        self.progress_changed.emit(percent, message)
