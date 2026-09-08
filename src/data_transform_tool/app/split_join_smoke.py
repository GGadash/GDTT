"""Small synthetic acceptance exercise also run inside packaged GDTT.exe.

Copyright (c) 2026 Akila DJ +. Gadash (Akila DJ); OpenAI Codex.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

from data_transform_tool.app.split_join_workflow import export_split_join, prepare_split_join
from data_transform_tool.export.models import ExportPlan
from data_transform_tool.io.cancellation import CancellationToken
from data_transform_tool.io.options import InspectionOptions
from data_transform_tool.split_join.models import Action, SourceSpec, SplitJoinSpec
from data_transform_tool.transformation.recipe import OutputFormat


def run_split_join_smoke() -> None:
    """Verify all four paths using synthetic values, never the user's datasets."""
    with TemporaryDirectory(prefix="gdtt-split-join-smoke-") as directory:
        root = Path(directory)
        left = root / "left.csv"
        right = root / "right.tsv"
        left.write_text("Time,PM,NO2\n2025-12-31T18:29:59Z,1,3\n", encoding="utf-8")
        right.write_text("Time\tPM\tNO2\n2026-01-01T00:00:00+05:30\t2\t4\n", encoding="utf-8")
        sources = tuple(
            SourceSpec(path, "Time", options=InspectionOptions(has_header=True))
            for path in (left, right)
        )
        for action, expected_tables in (
            (Action.SPLIT_TIME, 2),
            (Action.SPLIT_FIELDS, 4),
            (Action.JOIN_TIME, 1),
            (Action.JOIN_FIELDS, 1),
        ):
            prepared = prepare_split_join(
                sources,
                SplitJoinSpec(action=action, boundary_timezone="Asia/Colombo"),
                CancellationToken(),
            )
            try:
                if len(prepared.outputs) != expected_tables:
                    raise ValueError(f"Unexpected frozen {action} output count.")
                target = export_split_join(
                    prepared,
                    ExportPlan(
                        root / "exports", "smoke", (OutputFormat.CSV, OutputFormat.XLSX_PLAIN)
                    ),
                    CancellationToken(),
                )
                if not (target / "SPLIT_JOIN_REPORT.json").is_file():
                    raise ValueError("Frozen Split & Join report was not generated.")
            finally:
                prepared.close()
