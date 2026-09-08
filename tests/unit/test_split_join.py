import json
from dataclasses import replace
from datetime import UTC, datetime, time, timedelta
from pathlib import Path

import pytest

from data_transform_tool.aggregation.models import PeriodKind, PeriodSpec, SeasonBoundary
from data_transform_tool.app.split_join_workflow import export_split_join, prepare_split_join
from data_transform_tool.domain.batches import iter_rows
from data_transform_tool.export.models import ExportPlan
from data_transform_tool.io.cancellation import CancellationToken, InspectionCancelled
from data_transform_tool.io.options import InspectionOptions
from data_transform_tool.split_join.models import (
    Action,
    DuplicatePolicy,
    FieldGroup,
    MatchPolicy,
    SourceSpec,
    SplitJoinSpec,
)
from data_transform_tool.split_join.naming import automatic_output_name
from data_transform_tool.split_join.temporal import SplitPeriods, parse_timestamp, resolve_zone
from data_transform_tool.transformation.recipe import OutputFormat


def source(tmp_path: Path, name: str, text: str, zone: str = "UTC") -> SourceSpec:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return SourceSpec(path, "Time", zone, options=InspectionOptions(has_header=True))


@pytest.mark.parametrize(
    "zone,count", [("UTC", 1), ("Asia/Colombo", 2), ("+05:30", 2), ("+5.5", 2)]
)
def test_year_split_at_exact_local_midnight(tmp_path: Path, zone: str, count: int) -> None:
    src = source(tmp_path, "input.csv", "Time,PM\n2025-12-31T18:29:59Z,1\n2025-12-31T18:30:00Z,2\n")
    prepared = prepare_split_join(
        (src,), SplitJoinSpec(boundary_timezone=zone), CancellationToken()
    )
    try:
        assert len(prepared.outputs) == count
        assert sum(output.table.row_count for output in prepared.outputs) == 2
        if count == 2:
            assert prepared.outputs[1].period_start == "2026-01-01T00:00:00+05:30"
            assert prepared.outputs[1].table.read_rows(0, 1)[0][1] == "2"
    finally:
        prepared.close()


@pytest.mark.parametrize(
    "kind,start,end",
    [
        (PeriodKind.CALENDAR_MONTH, "2026-02-15T06:30:00+05:30", "2026-03-15T06:30:00+05:30"),
        (PeriodKind.QUARTER, "2026-01-15T06:30:00+05:30", "2026-04-15T06:30:00+05:30"),
        (PeriodKind.CALENDAR_YEAR, "2026-01-15T06:30:00+05:30", "2027-01-15T06:30:00+05:30"),
        (PeriodKind.WEEK, "2026-03-01T06:30:00+05:30", "2026-03-08T06:30:00+05:30"),
    ],
)
def test_configurable_boundaries(kind: PeriodKind, start: str, end: str) -> None:
    spec = SplitJoinSpec(
        boundary_timezone="Asia/Colombo",
        month_start_day=15,
        period=PeriodSpec(kind, day_start=time(6, 30), week_start=6, year_start_day=15),
    )
    bounds = SplitPeriods(spec).period_for(datetime.fromisoformat("2026-03-02T07:00:00+05:30"))
    assert (bounds.start.isoformat(), bounds.end.isoformat()) == (start, end)


def test_custom_seasons_wrap_year_and_leap_day() -> None:
    spec = SplitJoinSpec(
        period=PeriodSpec(
            PeriodKind.SEASON, seasons=(SeasonBoundary("Dry", 12, 15), SeasonBoundary("Wet", 5, 10))
        )
    )
    bounds = SplitPeriods(spec).period_for(datetime(2024, 2, 29, tzinfo=UTC))
    assert bounds.start == datetime(2023, 12, 15, tzinfo=UTC)
    assert bounds.end == datetime(2024, 5, 10, tzinfo=UTC)


def test_dst_days_and_invalid_local_timestamps() -> None:
    zone = resolve_zone("America/New_York")
    spec = SplitJoinSpec(boundary_timezone="America/New_York", period=PeriodSpec(PeriodKind.DAY))
    bounds = SplitPeriods(spec).period_for(datetime(2026, 3, 8, 12, tzinfo=UTC))
    assert bounds.end.astimezone(UTC) - bounds.start.astimezone(UTC) == timedelta(hours=23)
    for timestamp in ("2026-03-08T02:30", "2026-11-01T01:30"):
        with pytest.raises(ValueError):
            parse_timestamp(timestamp, "ISO", zone)
    with pytest.raises(ValueError):
        SplitPeriods(
            replace(spec, period=PeriodSpec(PeriodKind.DAY, day_start=time(2, 30)))
        ).period_for(datetime(2026, 3, 8, 12, tzinfo=UTC))
    assert parse_timestamp("2026-11-01T01:30:00-05:00", "ISO", zone).utcoffset() == timedelta(
        hours=-5
    )


@pytest.mark.parametrize(
    "match,rows", [(MatchPolicy.OUTER, 3), (MatchPolicy.INNER, 1), (MatchPolicy.LEFT, 2)]
)
def test_field_join_matches_instants_and_preserves_collisions(
    tmp_path: Path, match: MatchPolicy, rows: int
) -> None:
    left = source(tmp_path, "left.csv", "Time,PM\n2026-01-01T00:00:00Z,1\n2026-01-01T01:00:00Z,2\n")
    right = source(
        tmp_path,
        "right.tsv",
        "Time\tPM\n2026-01-01 05:30\t3\n2026-01-01 07:30\t4\n",
        "Asia/Colombo",
    )
    prepared = prepare_split_join(
        (left, right), SplitJoinSpec(action=Action.JOIN_FIELDS, match=match), CancellationToken()
    )
    try:
        output = prepared.outputs[0].table
        assert output.columns == ("Timestamp", "S1_PM", "S2_PM")
        assert output.row_count == rows
        assert output.read_rows(0, 1)[0] == ("2026-01-01T00:00:00+00:00", "1", "3")
        if match is MatchPolicy.OUTER:
            assert output.read_rows(1, 2)[0][2] is None
            assert output.read_rows(2, 1)[0][1] is None
    finally:
        prepared.close()


@pytest.mark.parametrize(
    "policy,values",
    [
        (DuplicatePolicy.FIRST, ("1",)),
        (DuplicatePolicy.LAST, ("3",)),
        (DuplicatePolicy.KEEP, ("1", "2", "3")),
    ],
)
def test_time_join_duplicate_policy(
    tmp_path: Path, policy: DuplicatePolicy, values: tuple[str, ...]
) -> None:
    one = source(tmp_path, "one.csv", "Time,PM\n2026-01-01,1\n2026-01-01,2\n")
    two = source(tmp_path, "two.csv", "Time,PM\n2026-01-01,3\n")
    prepared = prepare_split_join(
        (one, two), SplitJoinSpec(action=Action.JOIN_TIME, duplicates=policy), CancellationToken()
    )
    try:
        assert tuple(row[1] for row in iter_rows(prepared.outputs[0].table)) == values
    finally:
        prepared.close()
    with pytest.raises(ValueError, match="Duplicate"):
        prepare_split_join((one, two), SplitJoinSpec(action=Action.JOIN_TIME), CancellationToken())


def test_named_field_groups_metadata_and_verified_exports(tmp_path: Path) -> None:
    src = source(tmp_path, "input.csv", "Time,Site,PM,NO2\n2026-01-02,A,2,4\n2026-01-01,A,1,3\n")
    spec = SplitJoinSpec(
        action=Action.SPLIT_FIELDS,
        groups=(FieldGroup("Air", ("PM", "NO2")),),
        shared_fields=("Site",),
    )
    prepared = prepare_split_join((src,), spec, CancellationToken())
    try:
        assert prepared.outputs[0].table.columns == ("Time", "Site", "PM", "NO2")
        assert prepared.outputs[0].table.read_rows(0, 1)[0][2:] == ("1", "3")
        plan = ExportPlan(tmp_path / "exports", "unused", tuple(OutputFormat))
        target = export_split_join(prepared, plan, CancellationToken())
        report = json.loads((target / "SPLIT_JOIN_REPORT.json").read_text())
        assert len(report["outputs"][0]["verification"]) == 3
        assert all(item["status"] == "passed" for item in report["outputs"][0]["verification"])
        assert not list(plan.destination.glob(".gdtt-sj-pending-*"))
    finally:
        prepared.close()


def test_split_then_time_join_roundtrip_and_regroup(tmp_path: Path) -> None:
    src = source(tmp_path, "source.csv", "Time,PM\n2026-02-01,2\n2026-01-01,1\n2025-12-31,0\n")
    spec = SplitJoinSpec(period=PeriodSpec(PeriodKind.CALENDAR_MONTH))
    prepared = prepare_split_join((src,), spec, CancellationToken())
    try:
        target = export_split_join(
            prepared,
            ExportPlan(tmp_path / "out", "unused", (OutputFormat.CSV,)),
            CancellationToken(),
        )
    finally:
        prepared.close()
    sources = tuple(
        SourceSpec(path, "Time", options=InspectionOptions(has_header=True))
        for path in sorted(target.glob("*.csv"))
    )
    joined = prepare_split_join(
        sources, replace(spec, action=Action.JOIN_TIME), CancellationToken()
    )
    try:
        assert tuple(row[1] for row in iter_rows(joined.outputs[0].table)) == ("0", "1", "2")
    finally:
        joined.close()
    regrouped = prepare_split_join(
        sources, replace(spec, action=Action.JOIN_TIME, regroup_join=True), CancellationToken()
    )
    try:
        assert len(regrouped.outputs) == 3
    finally:
        regrouped.close()


def test_failed_or_cancelled_export_leaves_no_partial_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    src = source(tmp_path, "source.csv", "Time,PM\n2026-01-01,1\n2025-12-31,0\n")
    prepared = prepare_split_join((src,), SplitJoinSpec(), CancellationToken())
    plan = ExportPlan(tmp_path / "out", "unused", (OutputFormat.CSV,))
    token = CancellationToken()
    try:

        def cancel_on_second(message: str) -> None:
            if "2/2" in message:
                token.cancel()

        with pytest.raises(InspectionCancelled):
            export_split_join(prepared, plan, token, cancel_on_second)
        assert list(plan.destination.iterdir()) == []
    finally:
        prepared.close()


def test_invalid_schema_dates_and_output_limit_block(tmp_path: Path) -> None:
    one = source(tmp_path, "one.csv", "Time,PM\n2026-01-01,1\n2025-12-31,2\n")
    two = source(tmp_path, "two.csv", "Time,NO2\n2026-01-01,3\n")
    with pytest.raises(ValueError, match="matching"):
        prepare_split_join((one, two), SplitJoinSpec(action=Action.JOIN_TIME), CancellationToken())
    with pytest.raises(ValueError, match="limit"):
        prepare_split_join((one,), SplitJoinSpec(max_outputs=1), CancellationToken())
    invalid = source(tmp_path, "invalid.csv", "Time,PM\n01/02/2026 00:00,1\n")
    with pytest.raises(ValueError, match="timestamp"):
        prepare_split_join((invalid,), SplitJoinSpec(), CancellationToken())
    explicit = replace(invalid, datetime_format="%d/%m/%Y %H:%M")
    prepared = prepare_split_join((explicit,), SplitJoinSpec(), CancellationToken())
    prepared.close()


@pytest.mark.parametrize(
    "action,suffix",
    [
        (Action.SPLIT_TIME, "_SPLIT_YEAR"),
        (Action.SPLIT_FIELDS, "_SPLIT_FIELDS"),
        (Action.JOIN_TIME, "_JOIN_TIME"),
        (Action.JOIN_FIELDS, "_JOIN_FIELDS"),
    ],
)
def test_automatic_names_preserve_suffix_and_are_unique(
    tmp_path: Path, action: Action, suffix: str
) -> None:
    one = source(tmp_path, "one.csv", "Time,PM\n2026-01-01,1\n")
    two = source(tmp_path, "two.csv", "Time,PM\n2026-01-02,2\n")
    spec = SplitJoinSpec(action=action)
    prepared = prepare_split_join((one, two), spec, CancellationToken())
    try:
        names = [item.name for item in prepared.outputs]
        assert all(name.endswith(suffix) for name in names)
        assert len(set(name.casefold() for name in names)) == len(names)
        long_name = replace(prepared.outputs[0], name="Long<>:" + "name" * 100)
        rendered = automatic_output_name(long_name, 1, spec)
        assert len(rendered) <= 160 and rendered.endswith(suffix)
        assert not any(character in rendered for character in '<>:"/\\|?*')
        assert automatic_output_name(long_name, 2, spec) != rendered
        assert "20260101" in rendered
    finally:
        prepared.close()
