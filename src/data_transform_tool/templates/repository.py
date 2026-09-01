"""Atomic local CRUD/import/export for recipes and XLSX style presets.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, replace
from datetime import UTC, datetime
from pathlib import Path

from data_transform_tool.export.models import XlsxStyle
from data_transform_tool.export.naming import sanitize_windows_name
from data_transform_tool.settings.paths import styles_directory, templates_directory
from data_transform_tool.templates.models import TemplateMatch, TemplateRecord
from data_transform_tool.transformation.recipe import TransformationRecipe


class TemplateRepository:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or templates_directory()

    def list(self) -> tuple[TemplateRecord, ...]:
        if not self.root.exists():
            return ()
        records = tuple(self._load_path(path) for path in sorted(self.root.glob("*.json")))
        return tuple(sorted(records, key=lambda record: record.name.casefold()))

    def get(self, identifier: str) -> TemplateRecord:
        return self._load_path(self.root / f"{identifier}.json")

    def save(
        self,
        name: str,
        recipe: TransformationRecipe,
        style: XlsxStyle | None = None,
    ) -> TemplateRecord:
        self._ensure_unique_name(name)
        record = TemplateRecord.create(name, recipe, style)
        self._write(record)
        return record

    def duplicate(self, identifier: str, new_name: str) -> TemplateRecord:
        source = self.get(identifier)
        return self.save(new_name, source.recipe, source.style)

    def rename(self, identifier: str, new_name: str) -> TemplateRecord:
        if not new_name.strip():
            raise ValueError("A template name must not be blank.")
        self._ensure_unique_name(new_name, except_identifier=identifier)
        source = self.get(identifier)
        updated = replace(
            source,
            name=new_name.strip(),
            updated_at=datetime.now(UTC).isoformat(timespec="seconds"),
        )
        self._write(updated)
        return updated

    def delete(self, identifier: str) -> None:
        path = self.root / f"{identifier}.json"
        if not path.is_file():
            raise FileNotFoundError(f"Template '{identifier}' was not found.")
        path.unlink()

    def import_file(self, source: Path) -> TemplateRecord:
        record = TemplateRecord.from_json(source.read_text(encoding="utf-8"))
        self._ensure_unique_name(record.name)
        if (self.root / f"{record.identifier}.json").exists():
            record = TemplateRecord.create(record.name, record.recipe, record.style)
        self._write(record)
        return record

    def export_file(self, identifier: str, destination: Path) -> Path:
        record = self.get(identifier)
        destination.mkdir(parents=True, exist_ok=True)
        target = destination / f"{sanitize_windows_name(record.name)}.dtt-template.json"
        _write_atomic(target, record.to_json() + "\n")
        return target

    def matches(self, columns: tuple[str, ...]) -> tuple[TemplateMatch, ...]:
        source = {column.casefold() for column in columns}
        matches: list[TemplateMatch] = []
        for record in self.list():
            expected = {column.casefold() for column in record.recipe.source.expected_columns}
            if len(expected) != len(source) or not source:
                continue
            overlap = len(source.intersection(expected)) / len(source)
            if overlap >= 0.5:
                matches.append(TemplateMatch(record, overlap, source == expected))
        return tuple(sorted(matches, key=lambda item: (-item.score, item.record.name.casefold())))

    def _ensure_unique_name(self, name: str, except_identifier: str | None = None) -> None:
        normalized = name.strip().casefold()
        if not normalized:
            raise ValueError("A template name must not be blank.")
        if any(
            record.name.casefold() == normalized and record.identifier != except_identifier
            for record in self.list()
        ):
            raise ValueError(f"A template named '{name.strip()}' already exists.")

    def _write(self, record: TemplateRecord) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        _write_atomic(self.root / f"{record.identifier}.json", record.to_json() + "\n")

    @staticmethod
    def _load_path(path: Path) -> TemplateRecord:
        if not path.is_file():
            raise FileNotFoundError(f"Template '{path.stem}' was not found.")
        return TemplateRecord.from_json(path.read_text(encoding="utf-8"))


class StyleRepository:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or styles_directory()

    def list(self) -> tuple[XlsxStyle, ...]:
        if not self.root.exists():
            return ()
        return tuple(
            XlsxStyle(**json.loads(path.read_text(encoding="utf-8")))
            for path in sorted(self.root.glob("*.json"))
        )

    def save(self, style: XlsxStyle) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        target = self.root / f"{sanitize_windows_name(style.name)}.json"
        _write_atomic(target, json.dumps(asdict(style), indent=2) + "\n")
        return target

    def delete(self, name: str) -> None:
        target = self.root / f"{sanitize_windows_name(name)}.json"
        if not target.is_file():
            raise FileNotFoundError(f"Style '{name}' was not found.")
        target.unlink()


def _write_atomic(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.stem}-", suffix=path.suffix, dir=path.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        temporary.write_text(payload, encoding="utf-8")
        os.replace(temporary, path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
