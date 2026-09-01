"""Cross-module acceptance test for the Phase 4 headless workflow."""

from __future__ import annotations

from datetime import datetime

from data_transform_tool.domain.table import DataTable
from data_transform_tool.gaps import (
    ConfirmedInterval,
    GapFieldPolicy,
    GapGenerationConfig,
    MetadataBehavior,
    generate_gap_rows,
)
from data_transform_tool.transformation.nulls import NormalizeConfirmedNulls
from data_transform_tool.validation import (
    InvalidNumericPolicy,
    RemoveNullMode,
    RemoveNullRule,
    remove_null_rows,
    resolve_invalid_numeric,
    serialize_delimited_row,
)


def test_confirm_normalize_validate_reconstruct_and_serialize() -> None:
    source = DataTable(
        ("Timestamp", "Station", "PM2.5"),
        (
            (datetime(2026, 1, 1, 8), "A", "10.5"),
            (datetime(2026, 1, 1, 10), "A", "N/A"),
            (datetime(2026, 1, 1, 11), "A", "invalid"),
        ),
    )
    normalized = NormalizeConfirmedNulls(("N/A",), columns=("PM2.5",)).apply(source).table
    validated = resolve_invalid_numeric(
        normalized, ("PM2.5",), InvalidNumericPolicy.NULL_AND_CONTINUE
    ).table
    reconstructed = generate_gap_rows(
        validated,
        GapGenerationConfig(
            "Timestamp",
            ConfirmedInterval.hours(1),
            ("PM2.5",),
            (GapFieldPolicy("Station", MetadataBehavior.CARRY_STABLE),),
        ),
    ).table
    cleaned = remove_null_rows(
        reconstructed,
        RemoveNullRule(RemoveNullMode.ALL_MEASUREMENTS_MISSING, ("PM2.5",)),
    )

    assert reconstructed.rows[1] == (datetime(2026, 1, 1, 9), "A", None)
    assert cleaned.preview.matching_row_numbers == (2, 3, 4)
    assert cleaned.table.rows == ((datetime(2026, 1, 1, 8), "A", "10.5"),)
    assert serialize_delimited_row(reconstructed.rows[1]) == "2026-01-01 09:00:00,A,"
