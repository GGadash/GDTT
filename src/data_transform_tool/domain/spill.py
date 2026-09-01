"""Private SQLite spill tables for replayable bounded-memory row batches.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

import pickle
import shutil
import sqlite3
import tempfile
import weakref
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path

from data_transform_tool.domain.batches import DEFAULT_BATCH_SIZE, DataBatch
from data_transform_tool.domain.table import DataRow, DataTable
from data_transform_tool.io.cancellation import CancellationToken


@dataclass(frozen=True)
class SpillTable:
    """Immutable table metadata backed by one private ordered SQLite row store."""

    columns: tuple[str, ...]
    row_count: int
    path: Path

    def __post_init__(self) -> None:
        DataTable(self.columns, ())
        if self.row_count < 0:
            raise ValueError("A spill table row count must not be negative.")

    @property
    def column_count(self) -> int:
        return len(self.columns)

    def iter_batches(self, batch_size: int = DEFAULT_BATCH_SIZE) -> Iterator[DataBatch]:
        if batch_size <= 0:
            raise ValueError("Batch size must be greater than zero.")
        connection = _connect_read_only(self.path)
        try:
            cursor = connection.execute("SELECT ordinal, payload FROM rows ORDER BY ordinal")
            while records := cursor.fetchmany(batch_size):
                start = int(records[0][0])
                yield DataBatch(
                    start,
                    tuple(_deserialize(record[1], self.columns) for record in records),
                )
        finally:
            connection.close()

    def read_rows(self, start: int, count: int) -> tuple[DataRow, ...]:
        if start < 0 or count < 0:
            raise ValueError("Row slice bounds must not be negative.")
        if count == 0:
            return ()
        connection = _connect_read_only(self.path)
        try:
            records = connection.execute(
                "SELECT payload FROM rows WHERE ordinal >= ? ORDER BY ordinal LIMIT ?",
                (start, count),
            )
            return tuple(_deserialize(record[0], self.columns) for record in records)
        finally:
            connection.close()


class DuplicateSortKeyError(ValueError):
    """Raised when a uniqueness-required external sort finds the same key twice."""

    def __init__(self, first_row: int, second_row: int) -> None:
        super().__init__(f"Duplicate sort keys occur at rows {first_row} and {second_row}.")
        self.first_row = first_row
        self.second_row = second_row


class SpillWorkspace:
    """Own temporary spill files and remove them deterministically."""

    def __init__(self, *, parent: Path | None = None) -> None:
        resolved_parent = None if parent is None else str(parent)
        self.path = Path(
            tempfile.mkdtemp(prefix="data-transform-tool-", dir=resolved_parent)
        ).resolve()
        self._closed = False
        self._cleanup = weakref.finalize(self, _remove_workspace, self.path)

    def write_table(
        self,
        name: str,
        columns: tuple[str, ...],
        rows: Iterable[DataRow],
        cancellation: CancellationToken,
        *,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> SpillTable:
        """Write ordered rows atomically within this private workspace."""
        if self._closed:
            raise RuntimeError("The spill workspace is already closed.")
        if batch_size <= 0:
            raise ValueError("Batch size must be greater than zero.")
        safe_name = _safe_name(name)
        target = self.path / f"{safe_name}.sqlite3"
        temporary = self.path / f".{safe_name}.sqlite3"
        temporary.unlink(missing_ok=True)
        connection: sqlite3.Connection | None = None
        row_count = 0
        try:
            active = sqlite3.connect(temporary)
            connection = active
            active.execute("PRAGMA journal_mode=OFF")
            active.execute("PRAGMA synchronous=OFF")
            active.execute("CREATE TABLE rows (ordinal INTEGER PRIMARY KEY, payload BLOB NOT NULL)")
            pending: list[tuple[int, sqlite3.Binary]] = []
            for row in rows:
                if row_count % batch_size == 0:
                    cancellation.raise_if_cancelled()
                validated = DataTable(columns, (tuple(row),)).rows[0]
                pending.append(
                    (
                        row_count,
                        sqlite3.Binary(pickle.dumps(validated, protocol=pickle.HIGHEST_PROTOCOL)),
                    )
                )
                row_count += 1
                if len(pending) >= batch_size:
                    active.executemany(
                        "INSERT INTO rows (ordinal, payload) VALUES (?, ?)",
                        pending,
                    )
                    pending.clear()
            if pending:
                active.executemany(
                    "INSERT INTO rows (ordinal, payload) VALUES (?, ?)",
                    pending,
                )
            cancellation.raise_if_cancelled()
            active.commit()
            active.close()
            connection = None
            temporary.replace(target)
            return SpillTable(columns, row_count, target)
        except Exception:
            if connection is not None:
                connection.close()
            temporary.unlink(missing_ok=True)
            target.unlink(missing_ok=True)
            raise

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._cleanup()

    def write_sorted_table(
        self,
        name: str,
        columns: tuple[str, ...],
        rows: Iterable[DataRow],
        key: Callable[[DataRow], int],
        cancellation: CancellationToken,
        *,
        require_unique: bool = False,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> SpillTable:
        """External-sort rows by an exact integer key without whole-table materialization."""
        if self._closed:
            raise RuntimeError("The spill workspace is already closed.")
        safe_name = _safe_name(name)
        sort_path = self.path / f".{safe_name}-sort.sqlite3"
        sort_path.unlink(missing_ok=True)
        connection = sqlite3.connect(sort_path)
        try:
            connection.execute("PRAGMA journal_mode=OFF")
            connection.execute("PRAGMA synchronous=OFF")
            connection.execute(
                "CREATE TABLE sort_rows ("
                "sort_key INTEGER NOT NULL, "
                "source_ordinal INTEGER NOT NULL, "
                "payload BLOB NOT NULL"
                ")"
            )
            pending: list[tuple[int, int, sqlite3.Binary]] = []
            for source_ordinal, row in enumerate(rows):
                if source_ordinal % batch_size == 0:
                    cancellation.raise_if_cancelled()
                validated = DataTable(columns, (tuple(row),)).rows[0]
                pending.append(
                    (
                        key(validated),
                        source_ordinal,
                        sqlite3.Binary(pickle.dumps(validated, protocol=pickle.HIGHEST_PROTOCOL)),
                    )
                )
                if len(pending) >= batch_size:
                    connection.executemany(
                        "INSERT INTO sort_rows "
                        "(sort_key, source_ordinal, payload) VALUES (?, ?, ?)",
                        pending,
                    )
                    pending.clear()
            if pending:
                connection.executemany(
                    "INSERT INTO sort_rows (sort_key, source_ordinal, payload) VALUES (?, ?, ?)",
                    pending,
                )
            connection.execute(
                "CREATE INDEX sort_rows_order ON sort_rows (sort_key, source_ordinal)"
            )
            if require_unique:
                duplicate = connection.execute(
                    "SELECT MIN(source_ordinal), MAX(source_ordinal) "
                    "FROM sort_rows GROUP BY sort_key HAVING COUNT(*) > 1 LIMIT 1"
                ).fetchone()
                if duplicate is not None:
                    raise DuplicateSortKeyError(int(duplicate[0]) + 1, int(duplicate[1]) + 1)
            connection.commit()

            def sorted_rows() -> Iterator[DataRow]:
                cursor = connection.execute(
                    "SELECT payload FROM sort_rows ORDER BY sort_key, source_ordinal"
                )
                for row_number, record in enumerate(cursor, start=1):
                    if row_number % batch_size == 0:
                        cancellation.raise_if_cancelled()
                    yield _deserialize(record[0], columns)

            result = self.write_table(
                safe_name,
                columns,
                sorted_rows(),
                cancellation,
                batch_size=batch_size,
            )
            return result
        finally:
            connection.close()
            sort_path.unlink(missing_ok=True)

    def __enter__(self) -> SpillWorkspace:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def _connect_read_only(path: Path) -> sqlite3.Connection:
    if not path.is_file():
        raise FileNotFoundError(f"Spill table is unavailable: {path}")
    return sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)


def _deserialize(payload: bytes, columns: tuple[str, ...]) -> DataRow:
    # Payloads are created and consumed only inside a freshly owned private workspace.
    value = pickle.loads(payload)
    if not isinstance(value, tuple):
        raise ValueError("A private spill row is not an immutable tuple.")
    return DataTable(columns, (value,)).rows[0]


def _safe_name(value: str) -> str:
    cleaned = "".join(character for character in value if character.isalnum() or character in "-_")
    if not cleaned:
        raise ValueError("A spill table name must contain a letter or number.")
    return cleaned


def _remove_workspace(root: Path) -> None:
    if root.name.startswith("data-transform-tool-") and root.is_dir():
        shutil.rmtree(root)
