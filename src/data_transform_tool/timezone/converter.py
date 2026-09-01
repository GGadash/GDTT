"""IANA/manual-offset localization with explicit DST ambiguity handling.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone
from enum import StrEnum
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError, available_timezones

from data_transform_tool.domain.table import CellValue, DataTable
from data_transform_tool.transformation.base import (
    OperationResult,
    TransformationError,
    TransformationOperation,
    write_column,
)


class TimezoneSourceKind(StrEnum):
    EMBEDDED = "embedded"
    FIXED_IANA = "fixed_iana"
    IANA_COLUMN = "iana_column"
    MANUAL_OFFSET = "manual_offset"


class DstResolution(StrEnum):
    RAISE = "raise"
    FIRST_OCCURRENCE = "first_occurrence"
    SECOND_OCCURRENCE = "second_occurrence"


@dataclass(frozen=True)
class TimezoneSource:
    kind: TimezoneSourceKind
    zone_name: str | None = None
    zone_column: str | None = None
    offset_minutes: int | None = None

    def __post_init__(self) -> None:
        requirements = {
            TimezoneSourceKind.EMBEDDED: (
                self.zone_name is None and self.zone_column is None and self.offset_minutes is None
            ),
            TimezoneSourceKind.FIXED_IANA: (
                self.zone_name is not None
                and self.zone_column is None
                and self.offset_minutes is None
            ),
            TimezoneSourceKind.IANA_COLUMN: (
                self.zone_name is None
                and self.zone_column is not None
                and self.offset_minutes is None
            ),
            TimezoneSourceKind.MANUAL_OFFSET: (
                self.zone_name is None
                and self.zone_column is None
                and self.offset_minutes is not None
            ),
        }
        if not requirements[self.kind]:
            raise ValueError(f"Timezone source '{self.kind.value}' has inconsistent settings.")
        if self.offset_minutes is not None and not -1439 <= self.offset_minutes <= 1439:
            raise ValueError("Manual UTC offset must be between -23:59 and +23:59.")

    @classmethod
    def embedded(cls) -> TimezoneSource:
        return cls(TimezoneSourceKind.EMBEDDED)

    @classmethod
    def fixed(cls, zone_name: str) -> TimezoneSource:
        return cls(TimezoneSourceKind.FIXED_IANA, zone_name=zone_name)

    @classmethod
    def from_column(cls, column: str) -> TimezoneSource:
        return cls(TimezoneSourceKind.IANA_COLUMN, zone_column=column)

    @classmethod
    def manual_offset(cls, minutes: int) -> TimezoneSource:
        return cls(TimezoneSourceKind.MANUAL_OFFSET, offset_minutes=minutes)


@dataclass(frozen=True)
class TimezoneConversion(TransformationOperation):
    """Convert timestamps while preserving their represented instant."""

    source: str
    target_zone: str
    source_timezone: TimezoneSource
    output: str | None = None
    dst_resolution: DstResolution = DstResolution.RAISE

    def __post_init__(self) -> None:
        _zone(self.target_zone)
        if self.source_timezone.zone_name is not None:
            _zone(self.source_timezone.zone_name)

    @property
    def operation_id(self) -> str:
        return "timezone_conversion"

    def apply(self, table: DataTable) -> OperationResult:
        target = _zone(self.target_zone)
        zone_values = (
            table.column_values(self.source_timezone.zone_column)
            if self.source_timezone.zone_column is not None
            else (None,) * table.row_count
        )
        converted: list[CellValue] = []
        for row_number, (value, zone_value) in enumerate(
            zip(table.column_values(self.source), zone_values, strict=True), start=1
        ):
            if value is None:
                converted.append(None)
                continue
            if not isinstance(value, datetime):
                raise TransformationError(
                    f"Timezone conversion requires DateTime values; row {row_number} is invalid."
                )
            try:
                aware = self._source_aware(value, zone_value)
            except (ValueError, ZoneInfoNotFoundError) as error:
                raise TransformationError(
                    f"Timezone conversion failed at row {row_number}.", detail=str(error)
                ) from error
            converted.append(aware.astimezone(target))
        return OperationResult(
            write_column(
                table,
                source_name=self.source,
                output_name=self.output,
                values=tuple(converted),
            )
        )

    def _source_aware(self, value: datetime, zone_value: CellValue) -> datetime:
        has_embedded_offset = value.utcoffset() is not None
        if self.source_timezone.kind is TimezoneSourceKind.EMBEDDED:
            if not has_embedded_offset:
                raise ValueError("Naive timestamps require an explicit source zone or offset.")
            return value
        if has_embedded_offset:
            raise ValueError(
                "An aware timestamp must use the embedded source mode to avoid overriding "
                "its offset."
            )
        if self.source_timezone.kind is TimezoneSourceKind.MANUAL_OFFSET:
            minutes = self.source_timezone.offset_minutes
            if minutes is None:  # pragma: no cover - guarded by TimezoneSource
                raise ValueError("Manual offset is missing.")
            return value.replace(tzinfo=timezone(timedelta(minutes=minutes)))
        zone_name: str | None
        if self.source_timezone.kind is TimezoneSourceKind.IANA_COLUMN:
            if zone_value is None or not str(zone_value).strip():
                raise ValueError("Timezone column contains a blank value.")
            zone_name = str(zone_value).strip()
        else:
            zone_name = self.source_timezone.zone_name
        if zone_name is None:  # pragma: no cover - guarded by TimezoneSource
            raise ValueError("Source timezone is missing.")
        return _localize_iana(value, zone_name, self.dst_resolution)


def list_iana_timezones(query: str = "") -> tuple[str, ...]:
    """Return a searchable IANA list with common project zones first."""
    needle = query.strip().casefold()
    matches = [zone for zone in available_timezones() if needle in zone.casefold()]
    priorities = ("UTC", "Asia/Colombo")
    return tuple(zone for zone in priorities if zone in matches) + tuple(
        sorted(zone for zone in matches if zone not in priorities)
    )


def _zone(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError as error:
        raise ValueError(f"Unknown IANA timezone '{name}'.") from error


def _localize_iana(
    value: datetime,
    zone_name: str,
    resolution: DstResolution,
) -> datetime:
    zone = _zone(zone_name)
    candidates: list[datetime] = []
    for fold in (0, 1):
        candidate = value.replace(tzinfo=zone, fold=fold)
        round_trip = candidate.astimezone(UTC).astimezone(zone).replace(tzinfo=None)
        if round_trip == value:
            candidates.append(candidate)

    unique_offsets = {candidate.utcoffset() for candidate in candidates}
    if not candidates:
        raise ValueError(
            f"Local time {value.isoformat(sep=' ')} does not exist in {zone_name} because "
            "of a daylight-saving transition."
        )
    if len(unique_offsets) > 1:
        if resolution is DstResolution.RAISE:
            raise ValueError(
                f"Local time {value.isoformat(sep=' ')} is ambiguous in {zone_name}; "
                "choose the first or second occurrence."
            )
        fold = 0 if resolution is DstResolution.FIRST_OCCURRENCE else 1
        return next(candidate for candidate in candidates if candidate.fold == fold)
    return candidates[0]
