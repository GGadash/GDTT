"""Phase 8 atomic writer, naming, styling, and reopen-verification coverage."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from openpyxl import load_workbook

from data_transform_tool.domain.errors import AppError
from data_transform_tool.domain.table import DataTable
from data_transform_tool.export import (
    ExportPlan,
    VerificationStatus,
    XlsxStyle,
    data_output_path,
    sanitize_windows_name,
    suggest_base_name,
    verify_artifacts,
    write_data_outputs,
)
from data_transform_tool.io.cancellation import CancellationToken
from data_transform_tool.transformation.recipe import OutputFormat, OutputMissingPolicy


def test_atomic_csv_and_xlsx_outputs_reopen_and_verify(tmp_path) -> None:
    table = DataTable(
        ("Timestamp", "PM2.5", "Note"),
        (
            (datetime(2026, 1, 1, tzinfo=UTC), 12.25, ""),
            (datetime(2026, 1, 1, 1, tzinfo=UTC), None, "calibration"),
        ),
    )
    plan = ExportPlan(
        tmp_path,
        "station_RF",
        (
            OutputFormat.CSV,
            OutputFormat.XLSX_PLAIN,
            OutputFormat.XLSX_FORMATTED,
        ),
    )

    artifacts = write_data_outputs(table, plan, CancellationToken())
    verifications = verify_artifacts(artifacts, table, plan)

    assert [artifact.path.name for artifact in artifacts] == [
        "station_RF.csv",
        "station_RF_P.xlsx",
        "station_RF_F.xlsx",
    ]
    assert all(result.status is VerificationStatus.PASSED for result in verifications)
    csv_text = artifacts[0].path.read_text(encoding="utf-8-sig")
    assert '12.25,""' in csv_text
    assert ",,calibration" in csv_text
    workbook = load_workbook(artifacts[2].path)
    try:
        worksheet = workbook["Data"]
        assert worksheet.freeze_panes == "A2"
        assert worksheet.auto_filter.ref == "A1:C3"
        assert worksheet["B3"].value is None
    finally:
        workbook.close()


@pytest.mark.parametrize(
    ("policy", "sentinel"),
    [
        (OutputMissingPolicy.NA, "N/A"),
        (OutputMissingPolicy.MINUS_999, -999),
        (OutputMissingPolicy.CUSTOM, "missing"),
    ],
)
def test_explicit_missing_output_policies(tmp_path, policy, sentinel) -> None:  # type: ignore[no-untyped-def]
    table = DataTable(("Timestamp", "Value"), (("2026-01-01T00:00:00", None),))
    plan = ExportPlan(
        tmp_path,
        f"policy_{policy.value}",
        (OutputFormat.CSV,),
        missing_policy=policy,
        custom_missing_sentinel=sentinel if policy is OutputMissingPolicy.CUSTOM else None,
    )

    artifact = write_data_outputs(table, plan, CancellationToken())[0]

    assert str(sentinel) in artifact.path.read_text(encoding="utf-8-sig")
    assert verify_artifacts((artifact,), table, plan)[0].status is VerificationStatus.PASSED


def test_existing_output_requires_explicit_overwrite(tmp_path) -> None:
    table = DataTable(("Value",), ((1,),))
    plan = ExportPlan(tmp_path, "existing", (OutputFormat.CSV,))
    write_data_outputs(table, plan, CancellationToken())

    with pytest.raises(AppError, match="already exists"):
        write_data_outputs(table, plan, CancellationToken())

    overwrite = ExportPlan(
        tmp_path,
        "existing",
        (OutputFormat.CSV,),
        allow_overwrite=True,
    )
    assert write_data_outputs(table, overwrite, CancellationToken())[0].path.is_file()


def test_windows_safe_naming_and_time_range() -> None:
    table = DataTable(
        ("timestamp", "value"),
        (
            (datetime(2026, 1, 1, 2, 30), 1),
            (datetime(2026, 1, 2, 3, 45), 2),
        ),
    )

    suggested = suggest_base_name(
        tmp_path := __import__("pathlib").Path("bad:name.csv"), table, "average"
    )

    assert suggested == "bad_name_2026-01-01_02h30_to_2026-01-02_03h45_AVG"
    assert sanitize_windows_name("CON") == "_CON"
    assert data_output_path(tmp_path.parent, "result", OutputFormat.XLSX_FORMATTED).name == (
        "result_F.xlsx"
    )


def test_formatted_style_validates_bounds() -> None:
    with pytest.raises(ValueError, match="font size"):
        XlsxStyle(font_size=5)
