"""Semantic parity coverage for bounded-memory Reformat execution."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from data_transform_tool.app.reformat_configuration import create_reformat_draft
from data_transform_tool.app.reformat_preview import execute_reformat_table
from data_transform_tool.domain.batches import iter_rows
from data_transform_tool.domain.spill import SpillWorkspace
from data_transform_tool.domain.table import DataTable
from data_transform_tool.io.cancellation import CancellationToken
from data_transform_tool.io.full_reader import read_full_table
from data_transform_tool.io.inspector import FileInspector
from data_transform_tool.io.options import InspectionOptions
from data_transform_tool.transformation.base import TransformationError
from data_transform_tool.transformation.batch_executor import execute_reformat_batches

FIXTURE = Path(__file__).parents[1] / "fixtures" / "monitoring_gap.csv"


def _case() -> tuple[DataTable, object]:
    token = CancellationToken()
    inspection = FileInspector.default().inspect(
        FIXTURE,
        InspectionOptions(),
        cancellation=token,
    )
    source = read_full_table(inspection, token).table
    draft = replace(
        create_reformat_draft(inspection),
        timestamp_confirmed=True,
        interval_confirmed=True,
        confirmed_missing_markers=("N/A",),
    )
    return source, draft


def test_chunked_reformat_matches_eager_across_gap_boundary(tmp_path: Path) -> None:
    source, untyped_draft = _case()
    draft = untyped_draft
    source_with_gap = DataTable(source.columns, (*source.rows[:4], *source.rows[5:]))
    eager = execute_reformat_table(source_with_gap, draft)
    token = CancellationToken()

    with SpillWorkspace(parent=tmp_path) as workspace:
        staged = workspace.write_table("source", source.columns, source_with_gap.rows, token)
        batch = execute_reformat_batches(
            staged,
            draft,
            workspace,
            token,
            batch_size=3,
        )

        assert batch.table.columns == eager.table.columns
        assert tuple(iter_rows(batch.table, 2)) == eager.table.rows
        assert batch.generated_gap_rows == eager.generated_gap_rows == 1
        assert batch.removed_rows == eager.removed_rows
        assert sum(item.count for item in batch.diagnostics) == sum(
            item.count for item in eager.diagnostics
        )


def test_chunked_reformat_external_sort_matches_explicit_eager_reorder(tmp_path: Path) -> None:
    source, untyped_draft = _case()
    draft = replace(untyped_draft, allow_reorder=True)
    disordered = DataTable(
        source.columns,
        (source.rows[2], source.rows[0], source.rows[1], *source.rows[3:]),
    )
    eager = execute_reformat_table(disordered, draft)
    token = CancellationToken()

    with SpillWorkspace(parent=tmp_path) as workspace:
        staged = workspace.write_table("source", source.columns, disordered.rows, token)
        batch = execute_reformat_batches(
            staged,
            draft,
            workspace,
            token,
            batch_size=2,
        )

        assert tuple(iter_rows(batch.table)) == eager.table.rows


def test_chunked_reformat_rejects_duplicate_across_batches(tmp_path: Path) -> None:
    source, draft = _case()
    duplicated = DataTable(source.columns, (*source.rows[:3], source.rows[1], *source.rows[3:]))
    token = CancellationToken()

    with SpillWorkspace(parent=tmp_path) as workspace:
        staged = workspace.write_table("source", source.columns, duplicated.rows, token)
        with pytest.raises(TransformationError, match="Duplicate primary timestamps"):
            execute_reformat_batches(
                staged,
                draft,
                workspace,
                token,
                batch_size=2,
            )
