"""Reader protocol and progress callback contracts.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from data_transform_tool.io.cancellation import CancellationToken
from data_transform_tool.io.models import FileInspection
from data_transform_tool.io.options import InspectionOptions

ProgressCallback = Callable[[str, int | None], None]


class DataFileReader(Protocol):
    """Read-only inspection contract implemented by each file family."""

    extensions: frozenset[str]

    def available_worksheets(self, path: Path) -> tuple[str, ...]: ...

    def inspect(
        self,
        path: Path,
        options: InspectionOptions,
        cancellation: CancellationToken,
        progress: ProgressCallback | None = None,
    ) -> FileInspection: ...
