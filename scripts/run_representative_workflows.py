"""Exercise synthetic CSV, TSV, and XLSX workflows and preserve release evidence.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import os
import sys
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timedelta
from pathlib import Path

from openpyxl import Workbook


@dataclass(frozen=True)
class WorkflowEvidence:
    source_format: str
    source_name: str
    input_rows: int
    output_rows: int
    generated_gap_rows: int
    artifacts: tuple[str, ...]
    artifact_sha256: dict[str, str]
    verification_statuses: tuple[str, ...]
    report_verified: bool


HEADERS = ("Timestamp", "Station", "PM2.5", "Temperature", "Unused")


def synthetic_rows() -> tuple[tuple[object, ...], ...]:
    start = datetime(2026, 1, 1)
    offsets = (0, 1, 2, 4, 5)
    values: list[tuple[object, ...]] = []
    for index, offset in enumerate(offsets):
        particulate: object = 10.5 + index
        if offset == 2:
            particulate = "N/A"
        temperature: object = 26.0 + index / 10
        if offset == 4:
            temperature = "-999"
        values.append(
            (
                (start + timedelta(hours=offset)).strftime("%Y-%m-%d %H:%M"),
                "SYNTHETIC-STATION",
                particulate,
                temperature,
                "",
            )
        )
    return tuple(values)


def write_csv(path: Path, delimiter: str) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, delimiter=delimiter, lineterminator="\n")
        writer.writerow(HEADERS)
        writer.writerows(synthetic_rows())


def write_xlsx(path: Path) -> None:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Monitoring"
    worksheet.append(HEADERS)
    for row in synthetic_rows():
        worksheet.append(row)
    notes = workbook.create_sheet("Notes")
    notes.append(("Purpose", "Synthetic release acceptance only"))
    workbook.save(path)
    workbook.close()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def exercise_case(
    source: Path,
    output_root: Path,
    options: object,
) -> WorkflowEvidence:
    from data_transform_tool.app.export_workflow import execute_export, prepare_export
    from data_transform_tool.app.reformat_configuration import (
        build_transformation_recipe,
        create_reformat_draft,
    )
    from data_transform_tool.export import ExportPlan, VerificationStatus
    from data_transform_tool.io.cancellation import CancellationToken
    from data_transform_tool.io.inspector import FileInspector
    from data_transform_tool.transformation.recipe import OutputFormat

    inspection = FileInspector.default().inspect(
        source,
        options,
        cancellation=CancellationToken(),
    )
    draft = replace(
        create_reformat_draft(inspection),
        timestamp_confirmed=True,
        interval_confirmed=True,
        confirmed_missing_markers=tuple(
            marker.value for marker in inspection.potential_missing_markers
        ),
    )
    recipe = build_transformation_recipe(draft)
    prepared = prepare_export(inspection, draft, recipe, CancellationToken())
    try:
        case_name = f"{source.stem}-{source.suffix.lower().lstrip('.')}"
        destination = output_root / case_name
        destination.mkdir(parents=True, exist_ok=True)
        result = execute_export(
            prepared,
            ExportPlan(
                destination,
                f"{case_name}_RF",
                (
                    OutputFormat.CSV,
                    OutputFormat.XLSX_PLAIN,
                    OutputFormat.XLSX_FORMATTED,
                ),
            ),
            CancellationToken(),
        )
        statuses = tuple(item.status.value for item in result.verifications)
        if not statuses or any(status != VerificationStatus.PASSED.value for status in statuses):
            raise RuntimeError(f"{source.name} export verification did not pass: {statuses}")
        if prepared.input_table.row_count != 5 or prepared.output_table.row_count != 6:
            raise RuntimeError(
                f"{source.name} did not preserve the expected 5 input / 6 output rows."
            )
        if prepared.evidence.generated_gap_rows != 1:
            raise RuntimeError(f"{source.name} did not generate the expected one-row gap.")
        required_kinds = {
            "csv",
            "xlsx_plain",
            "xlsx_formatted",
            "transformation_info",
            "recipe",
            "summary",
        }
        artifact_kinds = {item.kind for item in result.artifacts}
        if not required_kinds.issubset(artifact_kinds):
            raise RuntimeError(
                f"{source.name} is missing artifacts: {sorted(required_kinds - artifact_kinds)}"
            )
        report_verified = all(
            phrase in result.report_text
            for phrase in (
                "Input rows: 5",
                "Output rows: 6",
                "Generated gap rows: 1",
                "POST-EXPORT VERIFICATION",
            )
        )
        if not report_verified:
            raise RuntimeError(f"{source.name} processing report is incomplete.")
        artifacts = tuple(item.path for item in result.artifacts)
        return WorkflowEvidence(
            source_format=inspection.file_kind.value,
            source_name=source.name,
            input_rows=prepared.input_table.row_count,
            output_rows=prepared.output_table.row_count,
            generated_gap_rows=prepared.evidence.generated_gap_rows,
            artifacts=tuple(path.name for path in artifacts),
            artifact_sha256={path.name: sha256(path) for path in artifacts},
            verification_statuses=statuses,
            report_verified=report_verified,
        )
    finally:
        prepared.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    arguments = parser.parse_args()
    output_root = arguments.output_root.resolve()
    input_root = output_root / "synthetic-inputs"
    result_root = output_root / "workflow-outputs"
    profile_root = output_root / "isolated-profile"
    for directory in (input_root, result_root, profile_root):
        directory.mkdir(parents=True, exist_ok=True)

    os.environ["APPDATA"] = str(profile_root / "AppData/Roaming")
    os.environ["LOCALAPPDATA"] = str(profile_root / "AppData/Local")
    os.environ["TEMP"] = str(profile_root / "Temp")
    os.environ["TMP"] = str(profile_root / "Temp")
    os.environ["DTT_DATA_DIRECTORY"] = str(profile_root / "Data")
    os.environ["DTT_LOG_DIRECTORY"] = str(profile_root / "Logs")
    Path(os.environ["TEMP"]).mkdir(parents=True, exist_ok=True)

    from data_transform_tool import __version__
    from data_transform_tool.io.options import InspectionOptions
    from data_transform_tool.reporting.logging_setup import configure_logging
    from data_transform_tool.settings.paths import logs_directory

    csv_path = input_root / "representative.csv"
    tsv_path = input_root / "representative.tsv"
    xlsx_path = input_root / "representative.xlsx"
    write_csv(csv_path, ",")
    write_csv(tsv_path, "\t")
    write_xlsx(xlsx_path)

    cases = (
        (csv_path, InspectionOptions()),
        (tsv_path, InspectionOptions()),
        (xlsx_path, InspectionOptions(worksheet="Monitoring")),
    )
    evidence = tuple(exercise_case(path, result_root, options) for path, options in cases)

    configure_logging()
    safe_message = "Release acceptance completed for synthetic formats: csv, tsv, xlsx."
    logging.getLogger("data_transform_tool.release_acceptance").info(safe_message)
    for handler in logging.getLogger().handlers:
        handler.flush()
    log_path = logs_directory() / "data-transform-tool.log"
    if not log_path.is_file():
        raise RuntimeError("The isolated rotating application log was not created.")
    log_text = log_path.read_text(encoding="utf-8")
    if safe_message not in log_text or "SYNTHETIC-STATION" in log_text:
        raise RuntimeError("The application log is missing safe evidence or contains row data.")

    report = {
        "status": "passed",
        "product": "GDTT",
        "version": __version__,
        "syntheticDataOnly": True,
        "profileIsolation": str(profile_root),
        "log": {
            "path": str(log_path),
            "sha256": sha256(log_path),
            "containsDatasetRows": False,
        },
        "workflows": [asdict(item) for item in evidence],
    }
    evidence_path = output_root / "REPRESENTATIVE_WORKFLOWS.json"
    evidence_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
