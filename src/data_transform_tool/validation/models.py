"""Version-independent missing-data configuration for Phase 4 workflows.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from dataclasses import dataclass

from data_transform_tool.domain.table import CellValue
from data_transform_tool.validation.numeric import InvalidNumericPolicy
from data_transform_tool.validation.rows import RemoveNullRule


@dataclass(frozen=True)
class MissingDataConfiguration:
    """Explicit decisions applied after confirmed source-marker normalization."""

    measurement_columns: tuple[str, ...]
    confirmed_null_markers: tuple[CellValue, ...] = ()
    invalid_numeric_policy: InvalidNumericPolicy = InvalidNumericPolicy.NULL_AND_CONTINUE
    row_removal_rule: RemoveNullRule | None = None

    def __post_init__(self) -> None:
        if any(not column.strip() for column in self.measurement_columns):
            raise ValueError("Measurement column names must not be blank.")
        if len(set(self.measurement_columns)) != len(self.measurement_columns):
            raise ValueError("Measurement columns must be unique.")
        if any(marker is None for marker in self.confirmed_null_markers):
            raise ValueError(
                "Canonical None is already null and must not be configured as a marker."
            )

    @property
    def canonical_null_only(self) -> bool:
        return True
