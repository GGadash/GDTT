"""Explicit Split & Join configuration; independent of existing recipe schemas.

Copyright (c) 2026 Akila DJ +. Gadash (Akila DJ); OpenAI Codex.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

from data_transform_tool.aggregation.models import PeriodKind, PeriodSpec
from data_transform_tool.io.options import InspectionOptions


class Action(StrEnum):
    SPLIT_TIME = "split_time"
    SPLIT_FIELDS = "split_fields"
    JOIN_TIME = "join_time"
    JOIN_FIELDS = "join_fields"


class DuplicatePolicy(StrEnum):
    ERROR = "error"
    FIRST = "first"
    LAST = "last"
    KEEP = "keep"


class MatchPolicy(StrEnum):
    OUTER = "outer"
    INNER = "inner"
    LEFT = "left"


@dataclass(frozen=True)
class SourceSpec:
    path: Path
    timestamp: str
    timezone: str = "UTC"
    datetime_format: str = "ISO"
    options: InspectionOptions = field(default_factory=InspectionOptions)
    fields: tuple[str, ...] = ()  # Empty means all non-timestamp fields.


@dataclass(frozen=True)
class FieldGroup:
    name: str
    fields: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.fields or len(set(self.fields)) != len(self.fields):
            raise ValueError("Each field group needs a name and unique selected fields.")


@dataclass(frozen=True)
class SplitJoinSpec:
    action: Action = Action.SPLIT_TIME
    boundary_timezone: str = "UTC"
    period: PeriodSpec = field(default_factory=lambda: PeriodSpec(PeriodKind.CALENDAR_YEAR))
    month_start_day: int = 1
    groups: tuple[FieldGroup, ...] = ()
    shared_fields: tuple[str, ...] = ()
    duplicates: DuplicatePolicy = DuplicatePolicy.ERROR
    match: MatchPolicy = MatchPolicy.OUTER
    regroup_join: bool = False
    max_outputs: int = 5000

    def __post_init__(self) -> None:
        if not 1 <= self.month_start_day <= 28:
            raise ValueError("Monthly/quarterly start day must be 1-28, valid in every month.")
        if not 1 <= self.max_outputs <= 10000:
            raise ValueError("Output file limit must be between 1 and 10,000.")
        if self.action is Action.JOIN_FIELDS and self.duplicates is DuplicatePolicy.KEEP:
            raise ValueError("Field joining requires one row per timestamp per source.")
        names = [group.name.casefold() for group in self.groups]
        if len(names) != len(set(names)):
            raise ValueError("Field group names must be unique.")
        if len(set(self.shared_fields)) != len(self.shared_fields):
            raise ValueError("Shared fields must be unique.")
