"""Qt worker that keeps file inspection off the GUI thread.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from data_transform_tool.app.batch_input import inspect_source_batch
from data_transform_tool.domain.errors import AppError
from data_transform_tool.io.cancellation import CancellationToken, InspectionCancelled
from data_transform_tool.io.inspector import FileInspector
from data_transform_tool.io.options import InspectionOptions

LOGGER = logging.getLogger(__name__)


class InspectionWorker(QObject):
    """Run one read-only inspection with progress and cooperative cancellation."""

    completed = Signal(object)
    failed = Signal(str, str)
    cancelled = Signal()
    progress_changed = Signal(str, object)

    def __init__(
        self,
        *,
        inspector: FileInspector,
        path: Path,
        options: InspectionOptions,
        cancellation: CancellationToken,
    ) -> None:
        super().__init__()
        self._inspector = inspector
        self._path = path
        self._options = options
        self._cancellation = cancellation

    @Slot()
    def run(self) -> None:
        try:
            result = self._inspector.inspect(
                self._path,
                self._options,
                cancellation=self._cancellation,
                progress=self._on_progress,
            )
        except InspectionCancelled:
            self.cancelled.emit()
        except AppError as error:
            self.failed.emit(error.user_message, error.detail or "")
        except Exception as error:  # pragma: no cover - defensive process boundary
            LOGGER.exception("Unexpected file inspection failure")
            self.failed.emit(
                "The file could not be inspected because of an unexpected error.",
                str(error),
            )
        else:
            self.completed.emit(result)

    def _on_progress(self, phase: str, rows: int | None) -> None:
        self.progress_changed.emit(phase, rows)


class BatchInspectionWorker(QObject):
    """Inspect one or more sources and calculate reference-schema compatibility."""

    completed = Signal(object)
    failed = Signal(str, str)
    cancelled = Signal()
    progress_changed = Signal(str, object)

    def __init__(
        self,
        *,
        inspector: FileInspector,
        paths: tuple[Path, ...],
        options: InspectionOptions,
        cancellation: CancellationToken,
    ) -> None:
        super().__init__()
        self._inspector = inspector
        self._paths = paths
        self._options = options
        self._cancellation = cancellation

    @Slot()
    def run(self) -> None:
        try:
            result = inspect_source_batch(
                self._inspector,
                self._paths,
                self._options,
                self._cancellation,
                self._on_progress,
            )
        except InspectionCancelled:
            self.cancelled.emit()
        except AppError as error:
            self.failed.emit(error.user_message, error.detail or "")
        except Exception as error:  # pragma: no cover - defensive process boundary
            LOGGER.exception("Unexpected batch inspection failure")
            self.failed.emit("The selected files could not be inspected.", str(error))
        else:
            self.completed.emit(result)

    def _on_progress(self, phase: str, rows: int | None) -> None:
        self.progress_changed.emit(phase, rows)
