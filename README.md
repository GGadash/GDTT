# GDTT

**GDTT — Data Transform Tool by Gadash (Akila DJ)** is a local, offline-first Windows
desktop application for data forging, transitions, and aggregations—mainly for
air-quality-related and other environmental time-series data.

> Development status: **0.9.0 local build / Split & Join added**. Reformat and Averaging now
> continue from bounded previews into spill-backed full-file execution, CSV/XLSX output, processing
> reports, local templates, and post-export reopen verification. The measured large-file backend
> and CI checkpoint is complete; verified Windows portable and current-user installer builds now
> exist. Combination A batch/spill execution and local Combination C-lite release acceptance are
> complete; the separate clean-machine confirmation remains.

## Why it exists

The application is designed to make transformations explicit and verifiable. Its
eventual workflow is:

`Mode → File → Inspect → Configure → Preview → Validate → Export → Verify`

Core priorities are ease of use, correct timestamp and null handling, local processing,
transparent verification, and safe repeated modification.

## Current interface

The current desktop interface contains:

- a working **Reformat / Transform** source-selection and inspection flow;
- single-file or compatible batch input through file browsing or drag-and-drop, with the first
  file used as the reference and mismatched schemas blocked with explicit reasons;
- a mapping grid, searchable field controls, sequential wizard, live samples, and proposed-output
  preview with Back, Reset, Undo, and Redo;
- default-on optional gap insertion with explicit timestamp/interval confirmation and global
  True Null / N/A / -999 / custom missing-output choices;
- a working **Average / Aggregate** configuration workspace with explicit timestamp, timezone,
  interval, field-rule, target-period, completeness, and missing-value decisions;
- visible Direct/Incremental chains and bounded final/per-stage completeness previews;
- complete-file first/middle/last review, CSV plus plain/formatted XLSX choices, RF/AVG naming,
  explicit null output, overwrite protection, style presets, and optional evidence sidecars;
- local versioned recipe templates and XLSX styles with import/export, schema-count matching,
  duplicate, rename, and confirmed deletion;
- visible post-export Passed / Passed with Warnings / Failed evidence for every data output;
- deterministic per-source batch output names, reports, reopen verification, isolated failure
  results, and a **Process more similar files** continuation action;
- a separate **Data Splitter & Joiner** for fields, named parameter groups, timestamp joins,
  chronological concatenation, and calendar/season splitting with explicit timezone boundaries;
- adaptive Home cards that wrap as modules are added, with no unused module placeholders;
- Dark, Light, Auto, and System themes, with Auto as the clean-install default;
- explicit offline/privacy and development-status information.

The Phase 2 inspection view reports file structure, inferred column types and confidence,
potential missing markers, likely timestamps and intervals, empty columns, processing
strategy, and bounded first/middle/last previews. Consequential detections remain visible
and overridable.

See the [Split & Join guide](About-Info/Human-Docs/SPLIT_JOIN.md) for the four operations,
timezone/format choices, custom period starts, duplicate policies, and export verification.

## Transformation engine

The headless Phase 3 engine supports immutable column selection/rename/order, empty and
duplicate fields, one-based indexes, arithmetic rounding, ppm/ppb conversion, safe calculated
fields, confirmed-null normalization, explicit date parsing/formatting, combine/split,
timestamp roles and intervals, start/mid/end derivation, time shifts, and instant-preserving
timezone conversion. Ambiguous dates and DST transitions are surfaced instead of guessed.

The Phase 4 engine adds confirmed-interval timestamp grids, gaps, generated rows, explicit
stable/fixed/derived metadata policies, duplicate/order/off-grid validation, invalid-numeric
decisions, previewable null-row removal, and strict true-null adapters. It never interpolates
measurement values. The Phase 5 UI composes these contracts into an immutable configuration
draft and typed recipe; it does not duplicate calculations in Qt event handlers.

## Averaging engine

The headless Phase 6 engine supports standard clock intervals, configurable local day and week
starts, calendar months, anchored fixed-day periods, quarters, configurable seasons, calendar
years, and anchored fixed years in an explicit reporting timezone. Expected observations come
from those boundaries and the confirmed input interval, including 23/25-hour DST days.

Direct aggregation calculates from valid source observations. Incremental aggregation retains
every configured intermediate stage and applies its completeness rule independently. The
default threshold is 75%; the optional 2-of-3 rule is restricted to explicit three-component
Incremental stages. Arithmetic mean, min, max, sum, median, population standard deviation,
count, energy/duration-weighted Leq, rainfall accumulation, and rain-rate mean are isolated
strategies. Insufficient results remain canonical nulls.

The Phase 7 desktop workspace composes those contracts without reimplementing calculations in
Qt handlers. Detected timestamps, intervals, and missing markers require review; name-based Leq,
rainfall, and rain-rate suggestions require confirmation or an override. Target periods include
common and custom clock intervals, reporting days/weeks, calendar months, anchored 30-day
periods, quarters, configurable seasons, reporting years, and fixed years. Preview tabs retain
both proposed final rows and per-stage valid/expected availability evidence.

## Supported source files

- CSV
- TSV
- delimited TXT
- XLSX, one selected worksheet at a time

Delimited files use bounded sampling plus two streaming passes. XLSX files use openpyxl
read-only mode. Full-file execution streams into private replayable spill batches. Reformat
preserves global timestamp/gap/order behavior with external spill sorting when explicitly
enabled; Averaging streams exact first-stage reporting periods and retains Incremental evidence.
CSV/XLSX writing and reopen verification also consume batches rather than whole-file row lists.

Operational datasets remain outside Git. Only small, synthetic fixtures belong in the
repository.

## Privacy

Dataset processing, templates, settings, logs, and temporary files are local. The
application requires no account, cloud database, dataset upload, or dataset telemetry.

## Run from source

Requirements:

- Windows 10/11 x64;
- Git;
- [`uv`](https://docs.astral.sh/uv/) for Python and dependency management.

From PowerShell in the repository root:

```powershell
uv sync --extra dev
uv run gdtt
```

If Python 3.13 is unavailable, `uv` downloads and manages it for this project.

## Development checks

```powershell
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest
```

Phase 9 backend benchmarks use only generated temporary data:

```powershell
uv sync --extra dev --extra performance
uv run python scripts/benchmark_backends.py --rows 100000,1000000,5000000
```

Recorded results and limitations are in
[`About-Info/Data-Processing/PERFORMANCE_BASELINE.md`](About-Info/Data-Processing/PERFORMANCE_BASELINE.md).

Apply formatting with:

```powershell
uv run ruff format .
```

## Windows packaged application

Build and verify the PyInstaller one-directory portable package on Windows:

```powershell
./scripts/build_windows.ps1
```

Build its current-user NSIS installer (no administrator permission required at install time):

```powershell
./scripts/bootstrap_nsis.ps1
./scripts/build_installer.ps1
```

The ignored `packaging/output/` directory receives the portable ZIP, installer EXE,
`BUILD_MANIFEST.json`, source ZIP, local acceptance evidence, release checklist, portable
checksum verifier, and `SHA256SUMS.txt`. The installer includes the project license,
Start Menu and uninstall registration, an optional desktop shortcut, and does not remove the
user's settings/log data during uninstall.

Build the complete locally isolated release candidate with:

```powershell
./scripts/build_release_candidate.ps1
```

Local C-lite has passed, including fresh extraction, stripped Python/developer environment,
disposable settings/logs, representative CSV/TSV/XLSX workflows, source audit, installer
lifecycle, dependency inventory, reports, and checksums. A separate clean Windows confirmation
still precedes a final public release. See
[`RELEASE_ACCEPTANCE.md`](About-Info/Human-Docs/RELEASE_ACCEPTANCE.md).

Pushing an explicitly reviewed `v*` tag runs the Windows gates and automatically publishes the
verified files to GitHub Releases. Hyphenated tags such as `v0.8.0-rc.1` become pre-releases;
ordinary pushes and manual builds never publish.

## Repository map

```text
src/data_transform_tool/   Application source
tests/                     Unit, integration, regression, and performance tests
config/                    Versioned defaults, profiles, and templates
scripts/                   Repeatable developer and release commands
packaging/                 Windows packaging configuration
About-Info/                Architecture, data rules, guides, and AI handoff state
```

Start with [`About-Info/README.md`](About-Info/README.md) for the complete documentation
map. Codex sessions must also follow [`AGENTS.md`](AGENTS.md).

## Git workflow

Git is initialized locally on `main`. Automatic commits and pushes are disabled. Use
short-lived branches for substantial changes and Conventional Commit-style messages.
See [`About-Info/Git-GitHub/GIT_AND_GITHUB_GUIDE.md`](About-Info/Git-GitHub/GIT_AND_GITHUB_GUIDE.md).

## License and attribution

The project uses the license text in [`LICENSE`](LICENSE). It is created by Gadash (Akila DJ)
with OpenAI Codex as an AI-assisted development collaborator. Dependencies remain under
their own licenses; see [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

Source, Actions results, and releases are hosted at
[`GGadash/GDTT`](https://github.com/GGadash/GDTT).
