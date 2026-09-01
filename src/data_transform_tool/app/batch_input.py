"""Compatible single-file and multi-file input inspection for GDTT.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from data_transform_tool.domain.errors import AppError
from data_transform_tool.io.cancellation import CancellationToken
from data_transform_tool.io.inspector import FileInspector
from data_transform_tool.io.models import FileInspection, FileKind
from data_transform_tool.io.options import InspectionOptions

BatchProgressCallback = Callable[[str, int | None], None]


@dataclass(frozen=True)
class CompatibilityResult:
    """Explain whether one inspected file can reuse the reference configuration."""

    path: Path
    compatible: bool
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class BatchInspection:
    """A reference inspection plus compatibility evidence for every selected file."""

    inspections: tuple[FileInspection, ...]
    compatibility: tuple[CompatibilityResult, ...]

    def __post_init__(self) -> None:
        if not self.inspections:
            raise ValueError("A batch inspection requires at least one file.")
        if len(self.inspections) != len(self.compatibility):
            raise ValueError("Every inspected file requires compatibility evidence.")

    @property
    def reference(self) -> FileInspection:
        return self.inspections[0]

    @property
    def is_compatible(self) -> bool:
        return all(item.compatible for item in self.compatibility)

    @property
    def incompatible(self) -> tuple[CompatibilityResult, ...]:
        return tuple(item for item in self.compatibility if not item.compatible)


def inspect_source_batch(
    inspector: FileInspector,
    paths: Sequence[Path],
    options: InspectionOptions,
    cancellation: CancellationToken,
    progress: BatchProgressCallback | None = None,
) -> BatchInspection:
    """Inspect selected sources locally and compare each with the first file."""
    unique_paths = tuple(dict.fromkeys(Path(path).resolve() for path in paths))
    if not unique_paths:
        raise AppError("Choose at least one input file.")
    inspections: list[FileInspection] = []
    total = len(unique_paths)
    for index, path in enumerate(unique_paths, start=1):
        cancellation.raise_if_cancelled()
        if progress is not None:
            progress(f"Inspecting {index} of {total}: {path.name}", None)

        def on_progress(phase: str, rows: int | None, *, _index: int = index) -> None:
            if progress is not None:
                progress(f"{_index} of {total} · {phase}", rows)

        try:
            inspections.append(
                inspector.inspect(
                    path,
                    options,
                    cancellation=cancellation,
                    progress=on_progress,
                )
            )
        except AppError as error:
            detail = f"{path.name}: {error.detail or error.user_message}"
            raise AppError(f"{path.name} could not be inspected.", detail=detail) from error

    reference = inspections[0]
    compatibility = tuple(
        CompatibilityResult(item.path, not reasons, reasons)
        for item in inspections
        for reasons in (_compatibility_reasons(reference, item),)
    )
    return BatchInspection(tuple(inspections), compatibility)


def _compatibility_reasons(
    reference: FileInspection,
    candidate: FileInspection,
) -> tuple[str, ...]:
    if candidate.path == reference.path:
        return ()
    reasons: list[str] = []
    if candidate.file_kind is not reference.file_kind:
        reasons.append(
            f"file type is {candidate.file_kind.value}; expected {reference.file_kind.value}"
        )
    if candidate.column_names != reference.column_names:
        reasons.append("ordered column names do not match the reference schema")
    if candidate.header_detected != reference.header_detected:
        reasons.append("header detection does not match the reference file")
    if reference.file_kind is FileKind.XLSX:
        if candidate.worksheet != reference.worksheet:
            reasons.append("worksheet name does not match the reference workbook")
    else:
        if candidate.delimiter != reference.delimiter:
            reasons.append("delimiter does not match the reference file")
        if candidate.quote_character != reference.quote_character:
            reasons.append("quote-character behavior does not match the reference file")
    return tuple(reasons)
