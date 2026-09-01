"""Local file ingestion and profiling interfaces.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from data_transform_tool.io.full_reader import (
    FullReadResult,
    FullSpillReadResult,
    iter_full_rows,
    read_full_spill,
    read_full_table,
)
from data_transform_tool.io.inspector import FileInspector
from data_transform_tool.io.models import FileInspection, FileKind, SemanticType
from data_transform_tool.io.options import InspectionOptions

__all__ = [
    "FileInspection",
    "FileInspector",
    "FileKind",
    "FullReadResult",
    "FullSpillReadResult",
    "InspectionOptions",
    "SemanticType",
    "iter_full_rows",
    "read_full_spill",
    "read_full_table",
]
