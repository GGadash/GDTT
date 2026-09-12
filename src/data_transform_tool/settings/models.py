"""Validated user preference models for GDTT.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ThemePreference = Literal["dark", "light", "auto", "system"]
ColorPreference = Literal["teal", "blue", "graphite", "violet", "spectrum"]


class AppSettings(BaseModel):
    """Preferences that are safe to reuse across datasets."""

    model_config = ConfigDict(extra="ignore")

    schema_version: int = 1
    theme: ThemePreference = "auto"
    color_theme: ColorPreference = "teal"
    font_size: int = Field(default=14, ge=10, le=20)
    window_width: int = Field(default=1240, ge=900, le=5000)
    window_height: int = Field(default=780, ge=620, le=5000)
