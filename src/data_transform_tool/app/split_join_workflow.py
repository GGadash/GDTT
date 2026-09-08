"""Inspection, preparation, transactional export and evidence for Split & Join.

Copyright (c) 2026 Akila DJ +. Gadash (Akila DJ); OpenAI Codex.
"""

from __future__ import annotations

import json
import shutil
import tempfile
from collections.abc import Callable, Iterator
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from uuid import uuid4

from data_transform_tool import __version__
from data_transform_tool.domain.spill import SpillTable, SpillWorkspace
from data_transform_tool.domain.table import DataRow
from data_transform_tool.export.models import ExportPlan, VerificationStatus
from data_transform_tool.export.naming import data_output_path
from data_transform_tool.export.verification import verify_artifacts
from data_transform_tool.export.writers import write_data_outputs
from data_transform_tool.io.cancellation import CancellationToken
from data_transform_tool.io.full_reader import iter_full_rows
from data_transform_tool.io.inspector import FileInspector
from data_transform_tool.io.models import FileInspection
from data_transform_tool.split_join.engine import OutputTable, create_outputs, timestamp_key
from data_transform_tool.split_join.models import SourceSpec, SplitJoinSpec
from data_transform_tool.split_join.naming import automatic_output_name
from data_transform_tool.split_join.temporal import parse_timestamp, resolve_zone


@dataclass
class PreparedSplitJoin:
    workspace: SpillWorkspace
    sources: tuple[SourceSpec, ...]
    spec: SplitJoinSpec
    outputs: tuple[OutputTable, ...]
    input_rows: tuple[int, ...]

    def close(self) -> None:
        self.workspace.close()


def _normalized_rows(
    inspection: FileInspection,
    source: SourceSpec,
    token: CancellationToken,
    selected: tuple[str, ...],
) -> Iterator[DataRow]:
    zone = resolve_zone(source.timezone)
    timestamp_index = inspection.column_names.index(source.timestamp)
    indices = tuple(inspection.column_names.index(field) for field in selected)
    for number, row in enumerate(iter_full_rows(inspection, token), 1):
        try:
            timestamp = parse_timestamp(row[timestamp_index], source.datetime_format, zone)
        except (ValueError, TypeError, OverflowError) as error:
            raise ValueError(
                f"{source.path.name}, row {number}: invalid, missing, or ambiguous timestamp. "
                "Check the chosen format, source timezone, and any daylight-saving transition."
            ) from error
        yield (timestamp, *(row[index] for index in indices))


def prepare_split_join(
    sources: tuple[SourceSpec, ...],
    spec: SplitJoinSpec,
    token: CancellationToken,
    progress: Callable[[str], None] = lambda _: None,
) -> PreparedSplitJoin:
    """Read each complete source once into an immutable, independently sorted snapshot."""
    if not sources:
        raise ValueError("Select at least one input file.")
    if len({source.path.resolve() for source in sources}) != len(sources):
        raise ValueError("The same input file cannot be added twice.")
    if len(sources) > 100:
        raise ValueError("Select at most 100 sources per operation.")
    resolve_zone(spec.boundary_timezone)
    workspace = SpillWorkspace()
    tables: list[SpillTable] = []
    try:
        for index, source in enumerate(sources):
            token.raise_if_cancelled()
            before = source.path.stat()
            progress(f"Inspecting source {index + 1}/{len(sources)}: {source.path.name}")
            inspection = FileInspector.default().inspect(
                source.path, source.options, cancellation=token
            )
            if source.timestamp not in inspection.column_names:
                raise ValueError(f"Select an existing timestamp column for {source.path.name}.")
            selected = source.fields or tuple(
                field for field in inspection.column_names if field != source.timestamp
            )
            if (
                not selected
                or source.timestamp in selected
                or len(set(selected)) != len(selected)
                or not set(selected).issubset(inspection.column_names)
            ):
                raise ValueError(f"Select unique non-timestamp fields for {source.path.name}.")
            progress(f"Reading and sorting source {index + 1}/{len(sources)}")
            table = workspace.write_sorted_table(
                f"source-{index}",
                (source.timestamp, *selected),
                _normalized_rows(inspection, source, token, selected),
                timestamp_key,
                token,
            )
            after = source.path.stat()
            if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                raise ValueError("An input changed during preparation. Prepare it again.")
            tables.append(table)
        outputs = create_outputs(
            tuple(tables),
            tuple(source.path.stem for source in sources),
            spec,
            workspace,
            token,
            progress,
        )
        # Ordinal prefixes guarantee distinct names even after Windows sanitization/truncation.
        outputs = tuple(
            replace(output, name=automatic_output_name(output, index + 1, spec))
            for index, output in enumerate(outputs)
        )
        return PreparedSplitJoin(
            workspace, sources, spec, outputs, tuple(t.row_count for t in tables)
        )
    except BaseException:
        workspace.close()
        raise


def export_split_join(
    prepared: PreparedSplitJoin,
    plan: ExportPlan,
    token: CancellationToken,
    progress: Callable[[str], None] = lambda _: None,
) -> Path:
    """Publish a new run folder only after every output passes reopen verification."""
    token.raise_if_cancelled()
    plan.destination.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".gdtt-sj-pending-", dir=plan.destination))
    target = plan.destination / f"GDTT_SplitJoin_{uuid4().hex[:12]}"
    try:
        records: list[dict[str, object]] = []
        for index, output in enumerate(prepared.outputs):
            token.raise_if_cancelled()
            progress(f"Exporting and verifying {index + 1}/{len(prepared.outputs)}")
            local_plan = replace(
                plan, destination=stage, base_name=output.name, allow_overwrite=False
            )
            artifacts = write_data_outputs(output.table, local_plan, token)
            checks = verify_artifacts(artifacts, output.table, local_plan, token)
            if any(check.status is VerificationStatus.FAILED for check in checks):
                raise ValueError("An output failed reopen verification. No run was published.")
            records.append(
                {
                    "name": output.name,
                    "rows": output.table.row_count,
                    "columns": output.table.columns,
                    "period_start": output.period_start,
                    "period_end_exclusive": output.period_end,
                    "files": [
                        data_output_path(Path(), output.name, fmt).name for fmt in plan.formats
                    ],
                    "verification": [
                        {
                            "file": check.artifact.name,
                            "status": check.status.value,
                            "checks": [
                                {"name": item.name, "passed": item.passed} for item in check.checks
                            ],
                        }
                        for check in checks
                    ],
                }
            )
        evidence = {
            "product": "GDTT",
            "version": __version__,
            "mode": "split_join",
            "configuration": asdict(prepared.spec),
            "sources": [
                {**asdict(source), "path": source.path.name, "rows": rows}
                for source, rows in zip(prepared.sources, prepared.input_rows, strict=True)
            ],
            "formats": [fmt.value for fmt in plan.formats],
            "missing_policy": plan.missing_policy.value,
            "custom_missing_sentinel": plan.custom_missing_sentinel,
            "timestamp_output": "ISO 8601 with offset in the boundary/output timezone",
            "ordering": "Ascending instant; ties retain input-file and source-row order",
            "outputs": records,
        }
        (stage / "SPLIT_JOIN_REPORT.json").write_text(
            json.dumps(evidence, indent=2, default=str), encoding="utf-8"
        )
        token.raise_if_cancelled()
        stage.rename(target)
        return target
    except BaseException:
        shutil.rmtree(stage)
        raise
