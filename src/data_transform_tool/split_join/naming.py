"""Descriptive, collision-safe automatic output names for Split & Join.

Copyright (c) 2026 Akila DJ +. Gadash (Akila DJ); OpenAI Codex.
"""

from datetime import datetime

from data_transform_tool.aggregation.models import PeriodKind
from data_transform_tool.export.naming import sanitize_windows_name
from data_transform_tool.split_join.engine import OutputTable
from data_transform_tool.split_join.models import Action, SplitJoinSpec

_PERIOD_SUFFIX = {
    PeriodKind.CALENDAR_YEAR: "YEAR",
    PeriodKind.CALENDAR_MONTH: "MONTH",
    PeriodKind.WEEK: "WEEK",
    PeriodKind.QUARTER: "QUARTER",
    PeriodKind.SEASON: "SEASON",
    PeriodKind.DAY: "DAY",
}


def automatic_output_name(output: OutputTable, ordinal: int, spec: SplitJoinSpec) -> str:
    """Keep the operation suffix intact when a long source/group name is shortened."""
    suffix = {
        Action.SPLIT_FIELDS: "SPLIT_FIELDS",
        Action.JOIN_FIELDS: "JOIN_FIELDS",
        Action.JOIN_TIME: "JOIN_TIME",
        Action.SPLIT_TIME: "SPLIT",
    }[spec.action]
    if spec.action is Action.SPLIT_TIME:
        suffix += "_" + _PERIOD_SUFFIX[spec.period.kind]
    elif spec.regroup_join:
        suffix += "_BY_" + _PERIOD_SUFFIX[spec.period.kind]
    if output.period_start is not None:
        # A boundary marker distinguishes calendar files even when only a partial period exists.
        period = datetime.fromisoformat(output.period_start).strftime("%Y%m%dT%H%M%S")
        date_part = f"_{period}"
    elif output.table.row_count:
        first = str(output.table.read_rows(0, 1)[0][0])
        last = str(output.table.read_rows(output.table.row_count - 1, 1)[0][0])
        stamps = [
            datetime.fromisoformat(value).strftime("%Y%m%dT%H%M%S") for value in (first, last)
        ]
        date_part = f"_{stamps[0]}" if stamps[0] == stamps[1] else f"_{stamps[0]}_to_{stamps[1]}"
    else:
        date_part = "_EMPTY"
    prefix = f"SJ_{ordinal:04d}_"
    tail = f"{date_part}_{suffix}"
    label = sanitize_windows_name(output.name)[: 160 - len(prefix) - len(tail)].rstrip(". ")
    return prefix + label + tail
