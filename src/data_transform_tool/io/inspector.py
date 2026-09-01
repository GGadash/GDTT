"""Reader registry and safe entry point for file inspection.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from pathlib import Path

from data_transform_tool.domain.errors import AppError
from data_transform_tool.io.cancellation import CancellationToken
from data_transform_tool.io.models import FileInspection
from data_transform_tool.io.options import InspectionOptions
from data_transform_tool.io.reader import DataFileReader, ProgressCallback
from data_transform_tool.io.readers import DelimitedTextReader, XlsxReader


class FileInspector:
    """Resolve a file to a registered local reader and return a transparent profile."""

    def __init__(self, readers: tuple[DataFileReader, ...]) -> None:
        self._readers = readers

    @classmethod
    def default(cls) -> FileInspector:
        return cls((DelimitedTextReader(), XlsxReader()))

    @property
    def supported_extensions(self) -> tuple[str, ...]:
        return tuple(
            sorted({extension for reader in self._readers for extension in reader.extensions})
        )

    def available_worksheets(self, path: str | Path) -> tuple[str, ...]:
        resolved = self._validate_path(path)
        return self._reader_for(resolved).available_worksheets(resolved)

    def inspect(
        self,
        path: str | Path,
        options: InspectionOptions | None = None,
        *,
        cancellation: CancellationToken | None = None,
        progress: ProgressCallback | None = None,
    ) -> FileInspection:
        resolved = self._validate_path(path)
        return self._reader_for(resolved).inspect(
            resolved,
            options or InspectionOptions(),
            cancellation or CancellationToken(),
            progress,
        )

    def _reader_for(self, path: Path) -> DataFileReader:
        suffix = path.suffix.casefold()
        for reader in self._readers:
            if suffix in reader.extensions:
                return reader
        supported = ", ".join(self.supported_extensions)
        raise AppError(f"Unsupported file type '{suffix or '(none)'}'. Supported: {supported}.")

    @staticmethod
    def _validate_path(path: str | Path) -> Path:
        resolved = Path(path).expanduser().resolve()
        if not resolved.exists():
            raise AppError("The selected input file does not exist.")
        if not resolved.is_file():
            raise AppError("The selected input path is not a file.")
        return resolved
