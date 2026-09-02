# AI Handoff Changelog

## 2026-09-02 — Automatic GitHub Release publishing

- Added a tag-only dependent release job that downloads the verified Windows artifact and gives
  `contents: write` only to the publication boundary.
- Added strict semantic tag/build-manifest version matching, required flat-asset validation, and
  downloaded checksum verification before GitHub CLI creates a Release.
- Hyphenated `v*` tags create non-Latest pre-releases; stable tags create normal releases;
  branch/manual builds never publish and reruns leave existing Release assets unchanged.
- Made `SHA256SUMS.txt` self-contained for downloaded Release files while retaining and checking
  the unpacked executable hash in `BUILD_MANIFEST.json`.
- The first `v0.8.0-rc.1` trigger exposed an unresolvable mutable setup-uv `@v9` reference in
  the Windows packaging workflow. Replaced it with CI's verified immutable v9.0.0 commit; a new
  pre-release tag is required because published Git tags are not rewritten.
- The `v0.8.0-rc.2` Windows build then passed portable packaging, installer, source archive,
  C-lite, and Actions artifact upload. Publication validation correctly stopped because the
  workflow had not called the checklist/verifier finalization logic.
- Extracted that logic into `finalize_release_candidate.ps1`, invoked it from local and GitHub
  builds, and made it defensively remove nested non-downloadable checksum targets.
- Pushed `v0.8.0-rc.3`; tag CI and the complete Windows build both passed, and the dependent
  publication job created the non-draft GitHub pre-release with all eight required assets.
- Independently downloaded the published assets and ran `VERIFY_CHECKSUMS.ps1`: all six content
  entries passed, while all eight files were present, non-empty, uploaded, and digest-addressed.

## 2026-09-01 — GDTT identity and compatible multi-file workflows

- Standardized user-facing, package, executable, installer, archive, report, source-document, and
  metadata identity on GDTT — Data Transform Tool by Gadash (Akila DJ), while keeping creator
  credit out of persistent application chrome.
- Added multi-file picker and local drag/drop input with the first file as the visible reference.
  Compatibility requires the same file kind, ordered columns and header decision, plus matching
  text delimiter/quote settings or XLSX worksheet.
- Added explicit incompatibility reasons and blocking, reference-labelled previews, sequential
  per-source execution, source-derived collision-safe RF/AVG names, isolated errors, and
  per-source reopen-verification evidence.
- Added a Process more similar files continuation action after export while preserving the
  original single-file workflow.
- Added IO-003 and EXP-002 traceability, focused batch tests, clean static gates, and a full
  136-test regression pass with 80% branch-aware coverage.

## 2026-09-01 — Combination C-lite and local release candidate

- Added explicit disposable data/log directory overrides and used them for packaged and installed
  smoke tests without changing normal user application state.
- Added fresh portable extraction in a path containing spaces, minimal PATH, removal of inherited
  Python environment variables, bundled dependency inventory, signature checks, and normal-log
  immutability evidence.
- Exercised synthetic CSV, TSV, and XLSX complete-source Reformat workflows. Each generated the
  expected gap and passed CSV/plain-XLSX/formatted-XLSX reopen verification plus report, recipe,
  summary, warnings, artifact-hash, and log-privacy checks.
- Audited 220 prospective release files with zero blocking secret/dataset/build/temp/local-path
  findings; retained one expected owner metadata property in the specification DOCX.
- Added a Git-optional audited source archive, portable checksum verifier, finalized read-only CI
  and Windows build gates, one-command release-candidate build, and manual other-computer guide.
- Full local release-candidate run passed 132 tests, Ruff, mypy, portable packaging, current-user
  install/smoke/registration/uninstall cleanup, source archive, C-lite, and all checksums.

## 2026-08-31 — Phase 9 Combination A production executor

- Added replayable batch contracts and private SQLite spill workspaces for complete-source
  CSV/TXT/read-only-XLSX execution without retaining one Python tuple per source row.
- Added chunked Reformat execution with eager-reference parity for gaps across batches, stable
  metadata, duplicate/error precedence, external reorder, removal, formatting, and diagnostics.
- Added streamed Direct/Incremental first-stage Averaging with missing-period completeness and
  retained later-stage tables/evidence.
- Converted CSV/XLSX writers and reopen verification to replay batches; CSV lexical/null checks
  use streaming digests and XLSX cells compare row by row.
- Added cancellation propagation and deterministic partial-export/spill cleanup plus non-UTF8
  delimited and read-only XLSX fallback tests.
- Removed the full-workflow 1 GB estimate guard while retaining the confirmed 1,000,000-row gap
  grid safety limit.
- Verified 128 tests, 81% branch-aware coverage, 132 formatted files, Ruff lint, and mypy across
  96 source files.
- Rebuilt the portable and installer artifacts after integrating the executor. Packaged smoke,
  hashes, silent install, registration readback, installed-app smoke, uninstall, and cleanup
  passed again on the build host.
- Assessed Combination C locally: Windows Sandbox is absent and firmware virtualization is
  disabled, so separate clean-Windows evidence remains blocked on an environment change.

## 2026-08-31 — Phase 9 Combinations B and D Windows distribution checkpoint

- Added canonical SVG/PNG/ICO application assets and replaced the former text shell mark with the
  app icon while retaining authorship only in About and source/build metadata.
- Added a locked PyInstaller 6.22 `onedir` build, generated Windows version resource, required
  licenses/assets, portable ZIP, JSON build manifest, SHA-256 checksums, and packaged smoke test.
- Made PyInstaller builds hermetic against unrelated private ICU DLLs found on a developer PATH;
  the original package failure was reproduced with a minimal frozen Qt program and resolved.
- Added a pinned-hash workspace NSIS 3.12 bootstrap and a current-user installer with license page,
  Start Menu/uninstall registration, optional desktop shortcut, and preserved user data.
- Verified the installer through a silent temporary install, installed-app offscreen smoke,
  registry/shortcut readback, silent uninstall, and cleanup. A separate clean Windows host remains
  Combination C work.
- Final quality gates passed: 125 formatted files, Ruff lint, mypy across 92 source files, and 116
  tests.

## 2026-08-31 — Phase 9 Combination A benchmark and CI checkpoint

- Added a deterministic temporary air-quality generator and isolated stdlib/Polars/PyArrow/
  DuckDB benchmark covering import, transformation/aggregation, export, peak RSS, and semantic
  checksums at 100,000, 1 million, and 5 million rows.
- Confirmed the Polars-first/PyArrow-interchange direction while retaining DuckDB as an optional
  measured external-sort/local-query candidate and stdlib/openpyxl as exact format fallbacks.
- Added provisional 1-million/5-million-row performance budgets, locked optional performance
  dependencies, complete third-party citations, and a benchmark smoke test.
- Added an early read-only Windows/Ubuntu GitHub Actions quality workflow for locked dependency
  installation, Ruff formatting/lint, mypy, and all tests.
- Verified 113 tests plus clean formatting, lint, and strict typing. The Phase 8 1 GB guard is
  intentionally retained until the remaining batch/spill executor and streaming verifier land.

## 2026-08-30 — Phase 8 full-file execution, export, templates, and verification

- Added guarded complete-source readers independent of bounded inspection previews, plus
  full-table Reformat and Averaging execution and complete first/middle/last review evidence.
- Added atomic CSV, plain XLSX, and formatted XLSX writers; RF/AVG Windows-safe naming; explicit
  null representations; overwrite protection; style presets; and Excel row-limit guidance.
- Added post-export reopen verification, detailed transformation reports, recipe/summary/
  warning sidecars, and visible Passed/Passed with Warnings/Failed UI results.
- Added versioned local recipe templates and XLSX styles with schema-count matching and
  CRUD/import/export services plus deletion confirmation in the template manager.
- Added XlsxWriter to the locked environment and to About/third-party attribution; advanced the
  application to 0.8.0.
- Verified 112 tests, 79% branch-aware coverage, clean formatting/lint, strict typing across 91
  source files, and an installed-package offscreen 0.8.0 desktop smoke.

## 2026-08-30 — Phase 7 averaging configuration and evidence UI

- Connected Average / Aggregate through a dedicated source-inspection route into one immutable,
  undoable application-layer averaging draft and typed recipe.
- Added explicit timestamp/profile/separate source and reporting timezone/interval and missing-marker review, advisory but
  confirmable per-field statistic/output controls, and True Null/N/A/-999/custom output choices.
- Added Direct/Incremental selection, a visible editable chain, per-stage thresholds and valid
  2-of-3 choices, common/custom clock periods, day/week/month/fixed-day/quarter/configurable-
  season/reporting-year/fixed-year controls, and fixed anchors.
- Added bounded final and retained per-stage table/completeness previews over the Phase 6 engine,
  readable warnings, Back/Reset/Undo/Redo, virtualized models, and a Phase 7 acceptance regression.
- Verified 97 tests, 80% branch-aware coverage, clean formatting/lint, strict typing across 77
  source files, an installed 0.7.0 smoke, and native 1500×920 Light/Dark visual QA.

## 2026-08-30 — Phase 6 completeness-aware averaging engine

- Added immutable aggregation, reporting-period, field-strategy, completeness, stage-report, and
  final-result contracts plus cooperative cancellation and blocking source-grid validation.
- Added reporting-zone clock/day/week/month/fixed-day/quarter/season/calendar-year/fixed-year
  periodizers with exact expected counts and 23/25-hour DST-day behavior.
- Added Direct and configurable Incremental execution with retained intermediate tables,
  per-field availability records, 75% defaults, and explicit Incremental-only 2-of-3 handling.
- Added mean/min/max/sum/median/population-standard-deviation/count, equal/duration-weighted Leq,
  rainfall accumulation, and rain-rate mean strategies.
- Replaced the generic aggregation recipe placeholder with frozen typed Python models and a
  synchronized JSON Schema; verified 89 tests, clean static checks, and an installed 0.6.0 smoke.

## 2026-08-30 — Phase 5 reformat configuration UI

- Added one immutable configuration session for mapping-grid, selected-column, sequential-wizard,
  global controls, validation, reset, and undo/redo behavior.
- Added virtualized input mapping and bounded proposed-output models with live samples, format,
  timestamp, timezone, start/mid/end, and numeric transformation controls.
- Added default-on optional gap insertion with explicit timestamp/interval confirmation, generated
  metadata policies, and global True Null / N/A / -999 / custom output representation.
- Connected Inspect → Configure → recipe review without moving calculations into Qt handlers and
  added focused unit/integration coverage plus native Light/Dark visual QA.

## 2026-08-30 — Phase 4 gap and validation engine

- Added advisory interval suggestions and confirmed exact grids with elapsed-time DST behavior.
- Added separate gap, duplicate, chronological-break, invalid-timestamp, and off-grid analysis.
- Added deterministic row generation with explicit metadata policies, populated derived/index
  fields, and canonical-null measurement fields without interpolation.
- Added invalid-numeric summaries/resolution, previewable remove-null rules, empty-field export
  suggestions, and strict delimited/XLSX true-null adapters.
- Added typed version-1 gap/missing-data recipe sections and synchronized JSON Schema coverage.
- Verified 60 tests, clean lint, strict typing, and a composed Phase 4 acceptance workflow.

## 2026-08-30 — Phase 3 transformation domain engine

- Added immutable `DataTable`, operation results, transformation plans, counted diagnostics,
  cancellation checkpoints, and per-step audit entries.
- Added column, rounding, ppm/ppb, safe calculated-field, and confirmed-null operations.
- Added named ISO/regional date profiles, ambiguity previews, parsing/formatting, combine/split,
  timestamp roles, intervals, start/mid/end, semantic end normalization, and time shifts.
- Added instant-preserving timezone conversion for embedded, fixed-IANA, IANA-column, and manual
  offset sources with explicit ambiguous/nonexistent DST handling.
- Added frozen version-1 recipe models and aligned the machine-readable recipe/profile contracts.
- Verified 46 tests, 84% branch-aware coverage, clean formatting/lint, strict typing, and a
  composed air-quality transformation acceptance plan.

## 2026-08-30 — Phase 2 source inspection

- Added read-only CSV, TSV, delimited TXT, and multi-worksheet XLSX ingestion with visible
  encoding, delimiter, header, and worksheet decisions.
- Added streaming profiling for row/column counts, type confidence, missing-marker candidates,
  likely timestamp/interval, empty columns, large-file policy, and bounded previews.
- Added a responsive background inspection screen with cancellation, progress, virtualized
  tables, and explicit detection overrides.
- Refined the Environmental Technical interface and added Dark, Light, Auto, and System themes
  with Auto as the clean-install default.
- Moved owner and OpenAI Codex credits out of the persistent shell and into About, alongside
  dependency citations and the project license.
- Added synthetic reader and GUI coverage and visually verified the key Light/Dark screens.

## 2026-08-30 — Phase 0 and Phase 1 foundation

- Confirmed Data Transform Tool product name and owner-supplied licensing text.
- Selected PySide6/Qt Widgets, Python 3.13, Polars-first processing, `uv`, and a phased
  PyInstaller-based packaging path.
- Established source, test, configuration, documentation, Git, logging, settings, error,
  and desktop-shell foundations.
- Verified formatting, lint, strict typing, five automated tests, and native Windows light
  and dark application renders.
- Used OpenAI Codex as the AI-assisted architecture and implementation collaborator.
