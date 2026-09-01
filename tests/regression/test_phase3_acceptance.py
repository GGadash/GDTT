"""Air-quality-style Phase 3 acceptance plan without gap filling or export."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from data_transform_tool.datetime.models import TimestampRole, TimestampSemantics
from data_transform_tool.datetime.operations import (
    CombineDateAndTime,
    DeriveIntervalFields,
    NormalizeIntervalEnd,
    ParseDateTimeColumn,
)
from data_transform_tool.domain.table import DataTable
from data_transform_tool.timezone import TimezoneConversion, TimezoneSource
from data_transform_tool.transformation.base import TransformationPlan
from data_transform_tool.transformation.column_operations import AddIndexColumn, SelectColumns
from data_transform_tool.transformation.nulls import NormalizeConfirmedNulls
from data_transform_tool.transformation.numeric import (
    ConcentrationConversion,
    ConvertConcentration,
    RoundNumeric,
)


def test_hourly_air_quality_transformation_plan() -> None:
    source = DataTable(
        ("Date", "Start Time", "End Time", "CO_ppm", "Source", "Unused"),
        (
            ("08/20/2025", "08:00", "08:59", "0.0254", "Station A", None),
            ("08/20/2025", "09:00", "09:59", "-999", "Station A", None),
        ),
    )
    plan = TransformationPlan(
        (
            NormalizeConfirmedNulls(("-999",), columns=("CO_ppm",)),
            ParseDateTimeColumn("Date", "mdy_slash_date"),
            ParseDateTimeColumn("Start Time", "time_minute"),
            ParseDateTimeColumn("End Time", "time_minute"),
            CombineDateAndTime("Date", "Start Time", "UTC Start"),
            CombineDateAndTime("Date", "End Time", "UTC End"),
            NormalizeIntervalEnd("UTC Start", "UTC End", timedelta(hours=1)),
            TimezoneConversion(
                "UTC Start",
                "Asia/Colombo",
                TimezoneSource.fixed("UTC"),
                output="Local Start",
            ),
            DeriveIntervalFields(
                TimestampSemantics("Local Start", TimestampRole.START, timedelta(hours=1)),
                start_output=None,
                midpoint_output="Local Mid",
                end_output="Local End",
            ),
            ConvertConcentration(
                "CO_ppm",
                ConcentrationConversion.PPM_TO_PPB,
                output="CO_ppb",
            ),
            RoundNumeric("CO_ppb", 2),
            AddIndexColumn(),
            SelectColumns(
                (
                    "Index",
                    "Source",
                    "UTC Start",
                    "UTC End",
                    "Local Start",
                    "Local Mid",
                    "Local End",
                    "CO_ppb",
                )
            ),
        )
    )

    result = plan.execute(source)

    assert result.table.columns == (
        "Index",
        "Source",
        "UTC Start",
        "UTC End",
        "Local Start",
        "Local Mid",
        "Local End",
        "CO_ppb",
    )
    assert result.table.rows[0][0:4] == (
        1,
        "Station A",
        datetime(2025, 8, 20, 8),
        datetime(2025, 8, 20, 9),
    )
    assert result.table.rows[0][4].isoformat() == "2025-08-20T13:30:00+05:30"
    assert result.table.rows[0][5].isoformat() == "2025-08-20T14:00:00+05:30"
    assert result.table.rows[0][6].isoformat() == "2025-08-20T14:30:00+05:30"
    assert result.table.rows[0][7] == Decimal("25.40")
    assert result.table.rows[1][7] is None
    assert source.rows[0][0] == "08/20/2025"
    assert len(result.audit) == len(plan.operations)
