# Changelog

All notable changes to GDTT — Data Transform Tool by Gadash (Akila DJ) are documented here. The project follows
semantic-style versioning while it matures.

## [Unreleased]

### Added

- GDTT product identity across UI, About metadata, executable, installer, archives, reports,
  documentation, and machine-readable release metadata; the legacy source command remains an
  alias for compatibility.
- Single/multi-file browsing and drag-and-drop input, strict reference-schema compatibility
  evidence, reference preview labeling, per-source batch output/report/reopen verification,
  isolated batch failures, and a post-export process-more continuation.
- Replayable `DataBatch`/`TabularData` contracts and private SQLite spill workspaces for
  bounded-memory complete-source execution.
- Chunked Reformat execution with cross-batch gap, duplicate, off-grid, stable-metadata,
  explicit reorder, null-row removal, diagnostic, and output-format parity.
- Streamed Direct/Incremental Averaging by exact reporting-period windows with retained stage
  tables and completeness evidence.
- Batch-based CSV/XLSX writing and constant-memory reopen verification with cancellation and
  deterministic partial-file/workspace cleanup.
- Reproducible stdlib/Polars/PyArrow/DuckDB large-file benchmarks with semantic checksums,
  provisional performance budgets, and read-only Windows/Ubuntu quality CI.
- Canonical application SVG/PNG/ICO assets, generated Windows version resources, a maintained
  PyInstaller `onedir` spec, hermetic build automation, packaged smoke verification, manifest,
  portable ZIP, and SHA-256 checksums.
- A current-user NSIS 3.12 installer with license page, Start Menu/uninstall registration,
  optional desktop shortcut, build-time owner/Codex metadata, and automated silent
  install/application-smoke/uninstall verification.
- PyInstaller and NSIS citations in About and third-party notices.
- Local Combination C-lite release acceptance with fresh-path extraction, stripped Python/PATH
  environment, disposable settings/logs, bundled dependency inventory, representative
  CSV/TSV/XLSX workflows, source/secret/dataset hygiene audit, and full checksum verification.
- An audited source ZIP, portable checksum verifier, machine-readable C-lite evidence,
  release-candidate checklist, and one-command release-candidate build.
- Finalized read-only Windows/Ubuntu CI and Windows packaging workflows with timeouts,
  concurrency control, representative-format evidence, source archive, and C-lite gates.
- Conservative monthly Dependabot version checks for uv and GitHub Actions dependencies.
- Repository sponsorship links for the GDTT Ko-fi page and its dedicated Ko-fi support offer.
- Tag-triggered GitHub Release publishing with manifest/version validation, self-contained
  downloadable checksums, pre-release detection, least-privilege write permissions, and
  immutable-on-rerun behavior.

### Fixed

- Pinned the Windows packaging workflow to the same immutable setup-uv v9 commit as CI after the
  mutable `@v9` reference failed resolution during the first release-tag run.
- Corrected CI action references, pinned setup-uv to its documented v9.0.0 commit, and installed
  the Linux EGL runtime required to import PySide6 during headless tests.
- Prevented unrelated private ICU DLLs on a developer PATH from contaminating frozen Qt builds.

## [0.8.0] - 2026-08-30

### Added

- Guarded complete-source CSV/TXT/XLSX reading and separate full-file Reformat/Averaging
  execution, with a visible 1 GB semantic-working-set safety limit ahead of Phase 9.
- Atomic UTF-8 CSV, plain XLSX, and Environmental Technical formatted XLSX writers with
  Windows-safe RF/AVG names, true-null/N/A/-999/custom output choices, overwrite protection,
  AutoFilter, frozen header, column widths, native date/numeric formats, and style presets.
- Complete input/output first/middle/last review, background processing, cooperative
  cancellation, output/report selection, and visible verification results in the desktop app.
- Reopen verification for existence, readability, filename, row count, ordered columns,
  duplicate Index fields, values/nulls, timestamps, and formatted worksheet structure.
- Transformation information, versioned recipe, concise summary, and conditional warning/error
  sidecars.
- Versioned local recipe-template and XLSX-style repositories with schema-count matching,
  import/export, duplicate, rename, and confirmed deletion.
- XlsxWriter dependency and license attribution in `THIRD_PARTY_NOTICES.md` and About.

### Fixed

- Full-file gap generation now runs while timestamps are typed and applies requested output
  formatting only after gap/removal operations.

## [0.7.0] - 2026-08-30

### Added

- A working Average / Aggregate route from source inspection into an immutable Phase 7
  configuration workspace.
- Explicit timestamp, parser profile, reporting timezone, input interval, field-statistic,
  missing-marker, and output-null decisions with reversible Reset, Undo, and Redo.
- Direct and Incremental controls with a visible editable chain, per-stage thresholds, optional
  valid 2-of-3 rules, common/custom clock periods, day/week/month/fixed-day/quarter/season/year
  configuration, and editable season boundaries.
- Advisory and overridable Leq, rainfall, and rain-rate field rules, output naming, and optional
  Leq duration weighting.
- Bounded proposed-output and retained per-stage completeness previews executed by the Phase 6
  engine, plus readable warnings and typed average-recipe review.

## [0.6.0] - 2026-08-30

### Added

- Immutable aggregation configuration, period, field-strategy, completeness, stage-report, and
  result contracts.
- Timezone-aware clock, day, week, calendar month, fixed-day, quarter, season, calendar-year,
  and fixed-year boundaries with exact DST-aware expected counts.
- Direct aggregation and visible configurable Incremental chains with retained per-stage tables,
  per-field availability evidence, 75% defaults, and explicit Incremental-only 2-of-3 rules.
- Arithmetic mean, min, max, sum, median, population standard deviation, count, equal/duration-
  weighted Leq, rainfall accumulation, and rain-rate mean strategies.
- Duplicate/disorder/off-grid validation, cooperative cancellation, canonical-null rejected
  results, counted diagnostics, and typed Python/JSON aggregation recipes.

## [0.5.0] - 2026-08-30

### Added

- Searchable virtualized field mapping and bounded proposed-output preview connected to source
  inspection.
- Reversible immutable configuration drafts with inline output selection/rename, per-column
  controls, a sequential wizard, live samples, Back, Reset, Undo, and Redo.
- Format profiles, timestamp roles, timezone sources/targets, start/mid/end derivation, numeric
  transformations, and readable recipe validation/summary.
- Default-on optional gap insertion with required timestamp/interval confirmation, explicit
  generated-row policies, and one global True Null / N/A / -999 / custom output choice.

## [0.4.0] - 2026-08-30

### Added

- Confirmed-interval suggestions, exact elapsed-time timestamp grids, gap spans, duplicate,
  disorder, invalid-timestamp, and off-grid diagnostics.
- Deterministic generated rows with explicit null, stable metadata, fixed-value, and
  timestamp-derived policies; measurement interpolation remains prohibited.
- Invalid-numeric summaries and resolution policies, previewable canonical-null row-removal
  rules, and 100%-null export-field suggestions.
- Strict CSV/TSV and XLSX true-null adapters plus typed gap and missing-data recipe models.

## [0.3.0] - 2026-08-30

### Added

- Immutable headless transformation tables, operations, plans, diagnostics, and audit entries.
- Column, numeric, ppm/ppb, safe calculated-field, date/time, timezone, shift, interval, and
  confirmed-null operations.
- Versioned recipe models and synchronized machine-readable date/time profiles.
- UTC/Asia-Colombo, manual-offset, DST, ambiguity, and air-quality acceptance regressions.

## [0.2.0] - 2026-08-30

### Added

- Streaming CSV/TSV/TXT and read-only XLSX source inspection.
- Type, missing-marker, timestamp, interval, empty-column, and large-file profiling.
- Background inspection UI with first/middle/last previews and detection overrides.
- Dark, Light, Auto, and System themes plus About-only credits and dependency citations.

## [0.1.0] - 2026-08-30

### Added

- PySide6 desktop application foundation with Reformat, Averaging, and future-mode cards.
- Environmental Technical visual system with System, Light, and Dark themes.
- Validated local settings, rotating privacy-conscious logging, and central error types.
- `uv`/`pyproject.toml` development setup, automated checks, and test foundation.
- Codex navigation, architecture, Git, requirement traceability, and AI handoff documents.
- Project license, third-party notices, and Akila DJ/OpenAI Codex attribution.
