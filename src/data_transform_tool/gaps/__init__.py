"""Confirmed-interval gap analysis and deterministic row generation.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from data_transform_tool.gaps.analyzer import analyze_timestamps, suggest_interval
from data_transform_tool.gaps.generator import generate_gap_rows, suggest_stable_metadata
from data_transform_tool.gaps.models import (
    ConfirmedInterval,
    GapFieldPolicy,
    GapGenerationConfig,
    GapGenerationResult,
    MetadataBehavior,
    TimestampAnalysis,
    TimestampDerivation,
)

__all__ = [
    "ConfirmedInterval",
    "GapFieldPolicy",
    "GapGenerationConfig",
    "GapGenerationResult",
    "MetadataBehavior",
    "TimestampAnalysis",
    "TimestampDerivation",
    "analyze_timestamps",
    "generate_gap_rows",
    "suggest_interval",
    "suggest_stable_metadata",
]
