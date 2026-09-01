"""Semantic parity for streamed Direct and Incremental Averaging."""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from pathlib import Path

from data_transform_tool.aggregation import AggregationApproach, PeriodSpec
from data_transform_tool.aggregation.batch_engine import execute_averaging_batches
from data_transform_tool.app.averaging_configuration import (
    AveragingDraft,
    AveragingStageDraft,
    create_averaging_draft,
)
from data_transform_tool.app.averaging_preview import execute_averaging_table
from data_transform_tool.domain.batches import iter_rows
from data_transform_tool.domain.spill import SpillWorkspace
from data_transform_tool.domain.table import DataTable
from data_transform_tool.io.cancellation import CancellationToken
from data_transform_tool.io.full_reader import read_full_table
from data_transform_tool.io.inspector import FileInspector
from data_transform_tool.io.options import InspectionOptions

FIXTURE = Path(__file__).parents[1] / "fixtures" / "monitoring_gap.csv"


def _case() -> tuple[DataTable, AveragingDraft]:
    token = CancellationToken()
    inspection = FileInspector.default().inspect(
        FIXTURE,
        InspectionOptions(),
        cancellation=token,
    )
    source = read_full_table(inspection, token).table
    initial = create_averaging_draft(inspection)
    fields = tuple(
        replace(field, statistic_confirmed=True) if field.include else field
        for field in initial.fields
    )
    draft = replace(
        initial,
        fields=fields,
        timestamp_confirmed=True,
        source_timezone_confirmed=True,
        reporting_timezone_confirmed=True,
        interval_confirmed=True,
        confirmed_missing_markers=("N/A",),
        missing_marker_decisions_confirmed=True,
    )
    return source, draft


def test_streamed_direct_averaging_matches_eager_with_empty_period(tmp_path: Path) -> None:
    source, draft = _case()
    source_with_missing_period = DataTable(source.columns, (*source.rows[:4], *source.rows[5:]))
    eager = execute_averaging_table(source_with_missing_period, draft)
    token = CancellationToken()

    with SpillWorkspace(parent=tmp_path) as workspace:
        staged = workspace.write_table(
            "source",
            source.columns,
            source_with_missing_period.rows,
            token,
        )
        streamed = execute_averaging_batches(
            staged,
            draft,
            workspace,
            token,
            batch_size=3,
        )

        assert tuple(iter_rows(streamed.table)) == eager.table.rows
        assert streamed.stages[0].completeness == eager.stages[0].completeness
        assert streamed.stages[0].report == eager.stages[0].report


def test_streamed_incremental_averaging_matches_eager_across_batches(
    tmp_path: Path,
) -> None:
    source, direct = _case()
    draft = replace(
        direct,
        approach=AggregationApproach.INCREMENTAL,
        stages=(
            AveragingStageDraft(PeriodSpec.clock(timedelta(hours=1)), label="1 hour"),
            AveragingStageDraft(PeriodSpec.clock(timedelta(hours=8)), label="8 hours"),
        ),
    )
    disordered = DataTable(
        source.columns,
        (source.rows[2], source.rows[0], source.rows[1], *source.rows[3:]),
    )
    draft = replace(draft, allow_reorder=True)
    eager = execute_averaging_table(disordered, draft)
    token = CancellationToken()

    with SpillWorkspace(parent=tmp_path) as workspace:
        staged = workspace.write_table("source", source.columns, disordered.rows, token)
        streamed = execute_averaging_batches(
            staged,
            draft,
            workspace,
            token,
            batch_size=2,
        )

        assert tuple(iter_rows(streamed.table)) == eager.table.rows
        assert tuple(stage.table for stage in streamed.stages) == tuple(
            stage.table for stage in eager.stages
        )
        assert tuple(stage.completeness for stage in streamed.stages) == tuple(
            stage.completeness for stage in eager.stages
        )
        assert any(item.code == "aggregation.input_reordered" for item in streamed.diagnostics)
