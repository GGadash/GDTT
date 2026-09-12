"""Shared explicit IANA/fixed-offset timezone resolution.

Copyright (c) 2026 Gadash +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

import re
from datetime import timedelta, timezone, tzinfo
from zoneinfo import ZoneInfo


def resolve_zone(name: str) -> tzinfo:
    name = name.strip()
    if name in {"Colombo", "+5.5", "UTC+5.5"}:
        name = "Asia/Colombo" if name == "Colombo" else "+05:30"
    match = re.fullmatch(r"(?:UTC)?([+-])(\d{2}):(\d{2})", name)
    if match:
        hours, minutes = int(match[2]), int(match[3])
        if hours > 23 or minutes > 59:
            raise ValueError("UTC offsets must be between -23:59 and +23:59.")
        offset = (hours * 60 + minutes) * (1 if match[1] == "+" else -1)
        return timezone(timedelta(minutes=offset))
    try:
        return ZoneInfo(name)
    except (KeyError, ValueError) as error:
        raise ValueError(
            "Choose UTC, Asia/Colombo, an IANA zone, or an offset like +05:30."
        ) from error
