"""Immutable Phase 8 export, style, artifact, and verification contracts.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from data_transform_tool.transformation.recipe import OutputFormat, OutputMissingPolicy


class VerificationStatus(StrEnum):
    PASSED = "passed"
    PASSED_WITH_WARNINGS = "passed_with_warnings"
    FAILED = "failed"


@dataclass(frozen=True)
class XlsxStyle:
    name: str = "Environmental Technical"
    font_name: str = "Aptos"
    font_size: int = 10
    header_fill: str = "#0F766E"
    header_text: str = "#FFFFFF"
    border_color: str = "#CBD5E1"
    alternating_fill: str = "#ECFDF5"
    autofilter: bool = True
    freeze_header: bool = True
    column_width: float = 16.0
    datetime_format: str = "yyyy-mm-dd hh:mm:ss"
    numeric_format: str = "0.00"

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.font_name.strip():
            raise ValueError("Style and font names must not be blank.")
        if not 6 <= self.font_size <= 72:
            raise ValueError("Excel font size must be between 6 and 72.")
        if not 4 <= self.column_width <= 100:
            raise ValueError("Excel column width must be between 4 and 100.")
        for color in (
            self.header_fill,
            self.header_text,
            self.border_color,
            self.alternating_fill,
        ):
            if len(color) != 7 or not color.startswith("#"):
                raise ValueError("Excel colors must use #RRGGBB notation.")


@dataclass(frozen=True)
class ExportPlan:
    destination: Path
    base_name: str
    formats: tuple[OutputFormat, ...]
    missing_policy: OutputMissingPolicy = OutputMissingPolicy.TRUE_NULL
    custom_missing_sentinel: str | int | float | None = None
    xlsx_style: XlsxStyle = XlsxStyle()
    allow_overwrite: bool = False
    write_transformation_info: bool = True
    write_recipe: bool = True
    write_error_report: bool = True
    write_summary: bool = True
    number_profiles: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not self.base_name.strip():
            raise ValueError("The output base name must not be blank.")
        if not self.formats:
            raise ValueError("Select at least one data output format.")
        if len(set(self.formats)) != len(self.formats):
            raise ValueError("Output formats must be unique.")
        if self.missing_policy is OutputMissingPolicy.CUSTOM and (
            self.custom_missing_sentinel is None or not str(self.custom_missing_sentinel).strip()
        ):
            raise ValueError("A custom missing policy requires a sentinel.")


@dataclass(frozen=True)
class ExportArtifact:
    kind: str
    path: Path
    rows: int | None = None


@dataclass(frozen=True)
class VerificationCheck:
    name: str
    passed: bool
    detail: str
    warning: bool = False


@dataclass(frozen=True)
class VerificationResult:
    artifact: Path
    status: VerificationStatus
    checks: tuple[VerificationCheck, ...]


@dataclass(frozen=True)
class ExportResult:
    artifacts: tuple[ExportArtifact, ...]
    verifications: tuple[VerificationResult, ...]
    report_text: str
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
