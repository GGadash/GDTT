# GDTT — Codex Map

GDTT — Data Transform Tool by Gadash (Akila DJ) is an offline-first PySide6 desktop app for
verifiable transformation and aggregation of environmental time-series data.

## Start every substantive task

1. Read this file and `About-Info/AI-Handoff/{CURRENT_STATE,NEXT_STEPS,DECISIONS,KNOWN_ISSUES}.md`.
2. Read relevant requirements in `DATA TRANSFORM TOOL STUDIO.md` and feature docs.
3. Inspect the smallest affected source modules and tests.
4. Identify requirement IDs, implement narrowly, test, and update handoff documentation.

## Code map and boundaries

- `src/data_transform_tool/ui/`: presentation only; no calculations in signal handlers.
- `app/`: workflow composition; `domain/`: UI-independent concepts.
- `io/`, `transformation/`, `datetime/`, `timezone/`, `gaps/`, `aggregation/`, and
  `validation/` own their respective business behavior; future `export/` owns writers.
- `settings/` may persist preferences, never hidden dataset transformation rules.
- `config/` and `About-Info/Machine-Readable/` are versioned sources of truth.
- Do not casually change recipe schemas, null semantics, timestamp semantics, or stable
  requirement IDs.

## Exact commands

```powershell
uv sync --extra dev
uv run data-transform-tool
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest
```

## Definition of done

Preserve unrelated behavior; add focused tests; run appropriate regression checks; update
requirements, feature docs, `CHANGELOG.md`, and AI handoff state; review `git diff`.

## Git safety

`AUTO_COMMIT = FALSE`. Do not discard user work, rewrite history, force-push, change the
remote, publish, tag, or commit unless explicitly requested. Operational datasets never
belong in Git.
