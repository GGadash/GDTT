"""Atomic persistence for local non-dataset preferences.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from pydantic import ValidationError

from data_transform_tool.settings.models import AppSettings
from data_transform_tool.settings.paths import application_data_directory

LOGGER = logging.getLogger(__name__)


class SettingsRepository:
    """Read and write validated settings from a JSON file."""

    def __init__(self, path: Path) -> None:
        self.path = path

    @classmethod
    def default(cls) -> SettingsRepository:
        return cls(application_data_directory() / "settings.json")

    def load(self) -> AppSettings:
        if not self.path.exists():
            return AppSettings()
        try:
            return AppSettings.model_validate_json(self.path.read_text(encoding="utf-8"))
        except (OSError, ValidationError, json.JSONDecodeError) as error:
            LOGGER.warning("Invalid settings file; defaults will be used: %s", error)
            return AppSettings()

    def save(self, settings: AppSettings) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.path.with_suffix(".tmp")
        temporary_path.write_text(
            settings.model_dump_json(indent=2) + "\n",
            encoding="utf-8",
        )
        temporary_path.replace(self.path)
