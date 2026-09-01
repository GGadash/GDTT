"""Phase 8 full-file execution, reports, recipes, and template persistence."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from tempfile import gettempdir

import pytest

from data_transform_tool.app.batch_export import execute_batch_export
from data_transform_tool.app.batch_input import inspect_source_batch
from data_transform_tool.app.export_workflow import execute_export, prepare_export
from data_transform_tool.app.reformat_configuration import (
    build_transformation_recipe,
    create_reformat_draft,
)
from data_transform_tool.app.template_application import apply_reformat_template
from data_transform_tool.domain.errors import AppError
from data_transform_tool.export import ExportPlan, VerificationStatus, XlsxStyle
from data_transform_tool.io.cancellation import CancellationToken, InspectionCancelled
from data_transform_tool.io.inspector import FileInspector
from data_transform_tool.io.options import InspectionOptions
from data_transform_tool.templates import StyleRepository, TemplateRepository
from data_transform_tool.transformation.recipe import OutputFormat

FIXTURE = Path(__file__).parents[1] / "fixtures" / "monitoring_gap.csv"


def _configured_case():  # type: ignore[no-untyped-def]
    inspection = FileInspector.default().inspect(
        FIXTURE,
        InspectionOptions(),
        cancellation=CancellationToken(),
    )
    draft = replace(
        create_reformat_draft(inspection),
        timestamp_confirmed=True,
        interval_confirmed=True,
        confirmed_missing_markers=("N/A",),
    )
    return inspection, draft, build_transformation_recipe(draft)


def test_full_file_workflow_prepares_reviews_exports_and_reports(tmp_path) -> None:
    inspection, draft, recipe = _configured_case()

    prepared = prepare_export(inspection, draft, recipe, CancellationToken())

    assert prepared.input_table.row_count == inspection.row_count
    assert prepared.output_table.row_count >= prepared.input_table.row_count
    assert prepared.input_previews[0].label == "First"
    assert prepared.output_previews[-1].label in {"Middle", "Last"}
    assert prepared.suggested_base_name.endswith("_RF")

    plan = ExportPlan(
        tmp_path,
        prepared.suggested_base_name,
        (OutputFormat.CSV, OutputFormat.XLSX_FORMATTED),
    )
    result = execute_export(prepared, plan, CancellationToken())

    assert all(item.status is VerificationStatus.PASSED for item in result.verifications)
    assert "POST-EXPORT VERIFICATION" in result.report_text
    assert "Generated gap rows:" in result.report_text
    assert any(artifact.kind == "recipe" for artifact in result.artifacts)
    assert all(artifact.path.is_file() for artifact in result.artifacts)


def test_template_crud_import_export_matching_and_styles(tmp_path) -> None:
    _, _, recipe = _configured_case()
    repository = TemplateRepository(tmp_path / "templates")
    record = repository.save("Station recipe", recipe)

    assert repository.get(record.identifier) == record
    assert repository.matches(recipe.source.expected_columns)[0].exact

    duplicate = repository.duplicate(record.identifier, "Station recipe copy")
    renamed = repository.rename(duplicate.identifier, "Renamed recipe")
    assert renamed.name == "Renamed recipe"

    exported = repository.export_file(record.identifier, tmp_path / "shared")
    repository.delete(record.identifier)
    imported = repository.import_file(exported)
    assert imported.recipe == recipe
    assert {item.name for item in repository.list()} == {"Renamed recipe", "Station recipe"}

    styles = StyleRepository(tmp_path / "styles")
    style = XlsxStyle(name="Laboratory")
    assert styles.save(style).is_file()
    assert styles.list() == (style,)
    styles.delete(style.name)
    assert styles.list() == ()


def test_exact_schema_reformat_template_round_trips_to_reviewable_draft() -> None:
    _, draft, recipe = _configured_case()
    changed = replace(
        draft,
        gap_fill_enabled=False,
        timestamp_confirmed=False,
        interval_confirmed=False,
        confirmed_missing_markers=(),
    )

    applied = apply_reformat_template(changed, recipe)

    assert applied.timestamp_confirmed
    assert applied.interval_confirmed
    assert build_transformation_recipe(applied) == recipe


def test_sidecar_collision_blocks_before_any_data_output_is_written(tmp_path) -> None:
    inspection, draft, recipe = _configured_case()
    prepared = prepare_export(inspection, draft, recipe, CancellationToken())
    (tmp_path / "collision_Summary.txt").write_text("existing", encoding="utf-8")
    plan = ExportPlan(tmp_path, "collision", (OutputFormat.CSV,))

    with pytest.raises(AppError, match="planned output files"):
        execute_export(prepared, plan, CancellationToken())

    assert not (tmp_path / "collision.csv").exists()


def test_cancelled_full_file_preparation_cleans_private_workspace() -> None:
    inspection, draft, recipe = _configured_case()
    temporary_root = Path(gettempdir())
    before = set(temporary_root.glob("data-transform-tool-*"))
    cancellation = CancellationToken()
    cancellation.cancel()

    with pytest.raises(InspectionCancelled):
        prepare_export(inspection, draft, recipe, cancellation)

    assert set(temporary_root.glob("data-transform-tool-*")) == before


def test_compatible_batch_exports_and_verifies_each_source(tmp_path) -> None:
    source_root = tmp_path / "sources"
    output_root = tmp_path / "outputs"
    source_root.mkdir()
    first = source_root / "station-a.csv"
    second = source_root / "station-b.csv"
    content = FIXTURE.read_text(encoding="utf-8")
    first.write_text(content, encoding="utf-8")
    second.write_text(content.replace("Station-A", "Station-B"), encoding="utf-8")
    batch = inspect_source_batch(
        FileInspector.default(),
        (first, second),
        InspectionOptions(),
        CancellationToken(),
    )
    draft = replace(
        create_reformat_draft(batch.reference),
        timestamp_confirmed=True,
        interval_confirmed=True,
        confirmed_missing_markers=("N/A",),
    )
    recipe = build_transformation_recipe(draft)
    prepared = prepare_export(batch.reference, draft, recipe, CancellationToken())
    try:
        result = execute_batch_export(
            prepared,
            batch.inspections,
            draft,
            recipe,
            ExportPlan(output_root, "ignored-in-batch", (OutputFormat.CSV,)),
            CancellationToken(),
        )
    finally:
        prepared.close()

    assert result.passed_count == 2
    assert result.failed_count == 0
    assert (output_root / "station-a_RF.csv").is_file()
    assert (output_root / "station-b_RF.csv").is_file()
