"""Explicit date/time parsing, ambiguity previews, and output formatting.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, date, datetime, time

from data_transform_tool.datetime.models import DateTimeFormatProfile, TemporalKind
from data_transform_tool.datetime.profiles import DateTimeProfileRegistry
from data_transform_tool.transformation.base import TransformationError

type TemporalValue = date | datetime | time


class AmbiguousDateError(TransformationError):
    """Raised when automatic parsing would silently choose between meanings."""


@dataclass(frozen=True)
class DateTimeInterpretation:
    profile_id: str
    profile_name: str
    display_pattern: str
    value: TemporalValue


class DateTimeParser:
    """Parse only with named profiles or return all distinct interpretations."""

    def __init__(self, registry: DateTimeProfileRegistry | None = None) -> None:
        self.registry = registry or DateTimeProfileRegistry.default()

    def parse(self, value: object, profile_id: str) -> TemporalValue:
        profile = self.registry.get(profile_id)
        if isinstance(value, datetime):
            if profile.utc:
                if value.utcoffset() is None:
                    raise ValueError("UTC format requires a known source timezone.")
                value = value.astimezone(UTC)
            return _coerce_kind(value, profile.temporal_kind)
        if (
            isinstance(value, date)
            and not isinstance(value, datetime)
            and profile.temporal_kind is TemporalKind.DATE
        ):
            return value
        if isinstance(value, time) and profile.temporal_kind is TemporalKind.TIME:
            return value
        text = str(value).strip()
        if profile.input_regex and re.fullmatch(profile.input_regex, text) is None:
            raise ValueError(f"Value {text!r} does not match {profile.display_pattern}.")
        for pattern in profile.python_patterns:
            try:
                parsed = datetime.strptime(text, pattern)
            except ValueError:
                continue
            if profile.utc:
                parsed = parsed.replace(tzinfo=UTC)
            return _coerce_kind(parsed, profile.temporal_kind)
        raise ValueError(
            f"Value {text!r} does not match {profile.name} ({profile.display_pattern})."
        )

    def interpretations(self, value: object) -> tuple[DateTimeInterpretation, ...]:
        candidates: list[DateTimeInterpretation] = []
        distinct: set[tuple[type[object], object]] = set()
        for profile in self.registry.all():
            try:
                parsed = self.parse(value, profile.profile_id)
            except ValueError:
                continue
            key = (type(parsed), parsed)
            if key in distinct:
                continue
            distinct.add(key)
            candidates.append(_interpretation(profile, parsed))
        return tuple(candidates)

    def parse_unambiguous(self, value: object) -> TemporalValue:
        interpretations = self.interpretations(value)
        if not interpretations:
            raise ValueError(f"No date/time profile matched {value!r}.")
        if len(interpretations) > 1:
            choices = ", ".join(
                f"{item.display_pattern} → {item.value.isoformat()}" for item in interpretations
            )
            raise AmbiguousDateError(
                "The date/time value has multiple valid interpretations.",
                detail=choices,
            )
        return interpretations[0].value

    def format(self, value: TemporalValue, profile_id: str) -> str:
        profile = self.registry.get(profile_id)
        if (profile.utc or "%z" in profile.output_pattern) and (
            not isinstance(value, (datetime, time)) or value.utcoffset() is None
        ):
            raise ValueError(
                "UTC/offset output requires a known source timezone. "
                "Configure the source timezone before formatting."
            )
        if profile.utc:
            if not isinstance(value, datetime):
                raise ValueError("UTC datetime output requires a full datetime value.")
            value = value.astimezone(UTC)
        output = value.strftime(profile.output_pattern)
        if profile.profile_id == "iso_millisecond":
            output = output[:-3]
        if profile.colonize_offset and len(output) >= 5:
            output = output[:-2] + ":" + output[-2:]
        return output


def _coerce_kind(value: datetime, kind: TemporalKind) -> TemporalValue:
    if kind is TemporalKind.DATE:
        return value.date()
    if kind is TemporalKind.TIME:
        return value.timetz() if value.tzinfo is not None else value.time()
    return value


def _interpretation(profile: DateTimeFormatProfile, value: TemporalValue) -> DateTimeInterpretation:
    return DateTimeInterpretation(
        profile_id=profile.profile_id,
        profile_name=profile.name,
        display_pattern=profile.display_pattern,
        value=value,
    )
