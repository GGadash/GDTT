"""Background tasks for the independent Split & Join view.

Copyright (c) 2026 Akila DJ +. Gadash (Akila DJ); OpenAI Codex.
"""

from collections.abc import Callable

from PySide6.QtCore import QObject, Signal, Slot

from data_transform_tool.domain.errors import AppError
from data_transform_tool.io.cancellation import CancellationToken, InspectionCancelled


class SplitJoinWorker(QObject):
    completed = Signal(object)
    failed = Signal(str)
    progress = Signal(str)
    finished = Signal()

    def __init__(
        self,
        task: Callable[[CancellationToken, Callable[[str], None]], object],
        token: CancellationToken,
    ) -> None:
        super().__init__()
        self.task = task
        self.token = token

    @Slot()
    def run(self) -> None:
        try:
            result = self.task(self.token, self.progress.emit)
        except InspectionCancelled:
            self.failed.emit("Cancelled. No new export folder was published.")
        except AppError as error:
            self.failed.emit(error.user_message)
        except Exception as error:
            self.failed.emit(str(error))
        else:
            self.completed.emit(result)
        finally:
            self.finished.emit()
