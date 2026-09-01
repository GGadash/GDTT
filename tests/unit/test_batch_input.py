"""Compatible batch-input inspection contracts."""

from __future__ import annotations

from pathlib import Path

from data_transform_tool.app.batch_input import inspect_source_batch
from data_transform_tool.io.cancellation import CancellationToken
from data_transform_tool.io.inspector import FileInspector
from data_transform_tool.io.options import InspectionOptions

FIXTURE = Path(__file__).parents[1] / "fixtures" / "monitoring_gap.csv"


def test_matching_files_are_accepted_as_one_batch(tmp_path) -> None:
    first = tmp_path / "station-a.csv"
    second = tmp_path / "station-b.csv"
    content = FIXTURE.read_text(encoding="utf-8")
    first.write_text(content, encoding="utf-8")
    second.write_text(content.replace("Station-A", "Station-B"), encoding="utf-8")

    result = inspect_source_batch(
        FileInspector.default(),
        (first, second),
        InspectionOptions(),
        CancellationToken(),
    )

    assert result.is_compatible
    assert result.reference.path == first
    assert len(result.inspections) == 2


def test_changed_schema_is_reported_and_blocks_batch(tmp_path) -> None:
    first = tmp_path / "station-a.csv"
    second = tmp_path / "station-b.csv"
    content = FIXTURE.read_text(encoding="utf-8")
    first.write_text(content, encoding="utf-8")
    second.write_text(content.replace("PM2.5", "PM10", 1), encoding="utf-8")

    result = inspect_source_batch(
        FileInspector.default(),
        (first, second),
        InspectionOptions(),
        CancellationToken(),
    )

    assert not result.is_compatible
    assert "ordered column names" in result.incompatible[0].reasons[0]
