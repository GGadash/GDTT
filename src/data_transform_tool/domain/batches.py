"""Batch-oriented tabular contracts for bounded-memory production execution.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Protocol

from data_transform_tool.domain.table import DataRow

DEFAULT_BATCH_SIZE = 10_000


@dataclass(frozen=True)
class DataBatch:
    """One ordered, immutable row batch with a zero-based source offset."""

    start: int
    rows: tuple[DataRow, ...]

    def __post_init__(self) -> None:
        if self.start < 0:
            raise ValueError("A batch start offset must not be negative.")

    @property
    def stop(self) -> int:
        return self.start + len(self.rows)


class TabularData(Protocol):
    """Minimal replayable table boundary shared by eager and spill backends."""

    @property
    def columns(self) -> tuple[str, ...]: ...

    @property
    def row_count(self) -> int: ...

    @property
    def column_count(self) -> int: ...

    def iter_batches(self, batch_size: int = DEFAULT_BATCH_SIZE) -> Iterator[DataBatch]: ...

    def read_rows(self, start: int, count: int) -> tuple[DataRow, ...]: ...


def iter_rows(table: TabularData, batch_size: int = DEFAULT_BATCH_SIZE) -> Iterator[DataRow]:
    """Yield rows in stable order without retaining more than one batch."""
    for batch in table.iter_batches(batch_size):
        yield from batch.rows
