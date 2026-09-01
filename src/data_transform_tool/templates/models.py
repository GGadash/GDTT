"""Versioned template records that contain configuration but never measurement rows.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from uuid import uuid4

from data_transform_tool.export.models import XlsxStyle
from data_transform_tool.transformation.recipe import TransformationRecipe


@dataclass(frozen=True)
class TemplateRecord:
    identifier: str
    name: str
    recipe: TransformationRecipe
    style: XlsxStyle
    created_at: str
    updated_at: str
    template_schema_version: int = 1

    @classmethod
    def create(
        cls,
        name: str,
        recipe: TransformationRecipe,
        style: XlsxStyle | None = None,
    ) -> TemplateRecord:
        if not name.strip():
            raise ValueError("A template name must not be blank.")
        now = datetime.now(UTC).isoformat(timespec="seconds")
        return cls(str(uuid4()), name.strip(), recipe, style or XlsxStyle(), now, now)

    def to_json(self) -> str:
        payload = {
            "template_schema_version": self.template_schema_version,
            "identifier": self.identifier,
            "name": self.name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "recipe": self.recipe.model_dump(mode="json"),
            "style": asdict(self.style),
        }
        return json.dumps(payload, indent=2, ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str | bytes) -> TemplateRecord:
        raw = json.loads(payload)
        if not isinstance(raw, dict) or raw.get("template_schema_version") != 1:
            raise ValueError("Unsupported template schema version.")
        required = {"identifier", "name", "created_at", "updated_at", "recipe", "style"}
        if not required.issubset(raw):
            raise ValueError("The template file is incomplete.")
        return cls(
            identifier=str(raw["identifier"]),
            name=str(raw["name"]),
            recipe=TransformationRecipe.model_validate(raw["recipe"]),
            style=XlsxStyle(**raw["style"]),
            created_at=str(raw["created_at"]),
            updated_at=str(raw["updated_at"]),
        )


@dataclass(frozen=True)
class TemplateMatch:
    record: TemplateRecord
    score: float
    exact: bool

    @property
    def label(self) -> str:
        return "Exact schema" if self.exact else f"Likely match ({self.score:.0%})"
