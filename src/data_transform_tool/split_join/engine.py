"""Bounded-memory splits and sorted streaming joins, without measurement aggregation.

Copyright (c) 2026 Akila DJ +. Gadash (Akila DJ); OpenAI Codex.
"""

from __future__ import annotations

import heapq
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import datetime
from itertools import groupby
from typing import cast

from data_transform_tool.domain.spill import SpillTable, SpillWorkspace
from data_transform_tool.domain.table import DataRow
from data_transform_tool.io.cancellation import CancellationToken
from data_transform_tool.split_join.models import (
    Action,
    DuplicatePolicy,
    FieldGroup,
    MatchPolicy,
    SplitJoinSpec,
)
from data_transform_tool.split_join.temporal import SplitPeriods, instant_key, resolve_zone


@dataclass(frozen=True)
class OutputTable:
    name: str
    table: SpillTable
    period_start: str | None = None
    period_end: str | None = None


def timestamp_key(row: DataRow) -> int:
    return instant_key(cast(datetime, row[0]))


def join_rows(
    tables: tuple[SpillTable, ...], spec: SplitJoinSpec, token: CancellationToken
) -> Iterator[DataRow]:
    """Merge pre-sorted sources using at most one active row per source and timestamp."""
    streams = [_indexed_rows(index, table) for index, table in enumerate(tables)]
    merged = heapq.merge(*streams, key=lambda item: timestamp_key(item[1]))
    for _, records in groupby(merged, key=lambda item: timestamp_key(item[1])):
        token.raise_if_cancelled()
        if spec.action is Action.JOIN_TIME:
            selected: DataRow | None = None
            for _, row in records:
                token.raise_if_cancelled()
                if spec.duplicates is DuplicatePolicy.KEEP:
                    yield row
                elif selected is None or spec.duplicates is DuplicatePolicy.LAST:
                    selected = row
                elif spec.duplicates is DuplicatePolicy.ERROR:
                    raise ValueError(
                        "Duplicate/overlapping timestamp found. Choose a duplicate policy."
                    )
            if selected is not None:
                yield selected
        else:
            selected_sources: dict[int, DataRow] = {}
            for source, row in records:
                token.raise_if_cancelled()
                if source in selected_sources:
                    if spec.duplicates is DuplicatePolicy.ERROR:
                        raise ValueError(f"Source {source + 1} has duplicate timestamps.")
                    if spec.duplicates is DuplicatePolicy.FIRST:
                        continue
                selected_sources[source] = row
            if spec.match is MatchPolicy.INNER and len(selected_sources) != len(tables):
                continue
            if spec.match is MatchPolicy.LEFT and 0 not in selected_sources:
                continue
            first = next(iter(selected_sources.values()))
            values = [first[0]]
            for index, table in enumerate(tables):
                found = selected_sources.get(index)
                values.extend(
                    found[1:] if found is not None else (None,) * (table.column_count - 1)
                )
            yield tuple(values)


def _indexed_rows(index: int, table: SpillTable) -> Iterator[tuple[int, DataRow]]:
    for row in _rows(table):
        yield index, row


def _rows(table: SpillTable) -> Iterator[DataRow]:
    # Close each SQLite read connection before yielding. A failed merge may retain generator
    # frames in its traceback; none should keep Windows file handles locked during cleanup.
    for start in range(0, table.row_count, 1000):
        yield from table.read_rows(start, 1000)


def create_outputs(
    tables: tuple[SpillTable, ...],
    source_names: tuple[str, ...],
    spec: SplitJoinSpec,
    workspace: SpillWorkspace,
    token: CancellationToken,
    progress: Callable[[str], None],
) -> tuple[OutputTable, ...]:
    outputs: list[OutputTable] = []
    zone = resolve_zone(spec.boundary_timezone)

    def add_output(
        name: str,
        columns: tuple[str, ...],
        rows: Iterator[DataRow],
        start: str | None = None,
        end: str | None = None,
    ) -> None:
        if len(outputs) >= spec.max_outputs:
            raise ValueError(f"The plan exceeds the {spec.max_outputs:,} output-file limit.")
        token.raise_if_cancelled()
        progress(f"Preparing output {len(outputs) + 1}: {name}")

        def serialize() -> Iterator[DataRow]:
            for row in rows:
                token.raise_if_cancelled()
                timestamp = cast(datetime, row[0]).astimezone(zone).isoformat()
                yield (timestamp, *row[1:])

        table = workspace.write_table(f"output-{len(outputs)}", columns, serialize(), token)
        outputs.append(OutputTable(name, table, start, end))

    def split_periods(name: str, table: SpillTable) -> None:
        periods = SplitPeriods(spec)

        def period_key(row: DataRow) -> int:
            return instant_key(periods.period_for(cast(datetime, row[0])).start)

        for _, rows in groupby(_rows(table), key=period_key):
            first = next(rows)
            bounds = periods.period_for(cast(datetime, first[0]))
            add_output(
                f"{name}_{bounds.label}",
                table.columns,
                _prepend(first, rows),  # noqa: B031 - consume the remainder after next(rows).
                bounds.start.isoformat(),
                bounds.end.isoformat(),
            )

    if spec.action in {Action.JOIN_TIME, Action.JOIN_FIELDS}:
        if len(tables) < 2:
            raise ValueError("Joining requires at least two input files.")
        if spec.action is Action.JOIN_TIME:
            fields = tables[0].columns[1:]
            if any(table.columns[1:] != fields for table in tables[1:]):
                raise ValueError("Time joining requires matching selected field names and order.")
            columns = tables[0].columns
        else:
            # Stable source-number prefixes preserve every field even with identical names/stems.
            columns = (
                "Timestamp",
                *(
                    f"S{index + 1}_{name}"
                    for index, table in enumerate(tables)
                    for name in table.columns[1:]
                ),
            )
        joined = workspace.write_table("joined", columns, join_rows(tables, spec, token), token)
        if spec.regroup_join:
            split_periods(f"Joined_{len(tables)}files", joined)
        else:
            add_output(f"Joined_{len(tables)}files", columns, _rows(joined))
    else:
        for index, table in enumerate(tables):
            name = f"S{index + 1}_{source_names[index]}"
            if spec.action is Action.SPLIT_TIME:
                split_periods(name, table)
                continue
            available = table.columns[1:]
            if not set(spec.shared_fields).issubset(available):
                raise ValueError("Shared metadata fields must exist in every selected source.")
            groups = spec.groups or tuple(
                FieldGroup(field, (field,))
                for field in available
                if field not in spec.shared_fields
            )
            if not groups:
                raise ValueError("Select at least one parameter to split.")
            for group in groups:
                selected = tuple(dict.fromkeys((*spec.shared_fields, *group.fields)))
                if not set(selected).issubset(available):
                    raise ValueError(f"Group '{group.name}' contains an unavailable parameter.")
                positions = (0, *(table.columns.index(field) for field in selected))
                add_output(
                    f"{name}_{group.name}",
                    (table.columns[0], *selected),
                    _project(table, positions),
                )
    if not outputs:
        raise ValueError("No output rows matched this plan. Check the sources and join matching.")
    return tuple(outputs)


def _project(table: SpillTable, positions: tuple[int, ...]) -> Iterator[DataRow]:
    for row in _rows(table):
        yield tuple(row[index] for index in positions)


def _prepend(first: DataRow, rows: Iterator[DataRow]) -> Iterator[DataRow]:
    yield first
    yield from rows
