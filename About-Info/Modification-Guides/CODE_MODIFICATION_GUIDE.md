# Code Modification Guide

## Module locator

| Feature | Main module | Relevant tests | Documentation |
|---|---|---|---|
| App launch | `app/bootstrap.py` | `tests/integration/test_desktop_shell.py` | `Architecture/ARCHITECTURE.md` |
| Settings | `settings/` | `tests/unit/test_settings.py` | `Architecture/MODULE_MAP.md` |
| Theme/home UI | `ui/` | `tests/integration/` | `Modification-Guides/UI_MODIFICATION_GUIDE.md` |
| CSV/XLSX import | `io/` | `tests/unit/test_file_inspection.py` | `Data-Processing/DATA_PIPELINE_SPEC.md` |
| Transformations | `transformation/` | `tests/unit/test_*transformations.py` | `Data-Processing/TRANSFORMATION_ENGINE.md` |
| Date parsing | `datetime/` | `tests/unit/test_datetime_transformations.py` | `Data-Processing/DATE_TIME_DESIGN.md` |
| Timezone conversion | `timezone/` | `tests/unit/test_timezone_transformations.py` | `Data-Processing/TIMEZONE_DESIGN.md` |
| Gap filling | future `gaps/` | future regression tests | `Data-Processing/GAP_FILLING.md` |
| Aggregation / Leq | future `aggregation/` | future aggregation tests | `Data-Processing/AVERAGING_DESIGN.md` |
| Export/verification | `export/`, `app/export_workflow.py`, `reporting/processing_report.py` | `test_export_outputs.py`, `test_phase8_workflow.py`, `test_phase8_acceptance.py` | user guide and master specification |

## Manual modification

Run `uv sync --extra dev`, locate the owner module and focused tests, make a cohesive edit,
run focused tests, then all relevant regression/lint/type checks. Update documentation,
requirement status, changelog, and handoff files before reviewing the Git diff.

## Codex modification

Name the intended feature and boundaries. Ask Codex to inspect before editing, reproduce a
bug with a test, preserve unrelated behavior, and avoid UI-only business logic. For a UI
change, explicitly say calculations and parsing must remain untouched. For a refactor,
state the behavior that tests must preserve. If interrupted, use `Vibe-Coding/RESUME_PROMPT.md`.
