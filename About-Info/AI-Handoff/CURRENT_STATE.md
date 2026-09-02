# Current State

Last updated: 2026-09-02

## What works

- Product identity is standardized on **GDTT**. Formal descriptions use
  **GDTT — Data Transform Tool by Gadash (Akila DJ)**; package and Windows artifact names use
  GDTT, owner/Codex credit remains in About and metadata, and persistent application chrome does
  not display creator text.
- Product and Phase 0 architectural decisions are recorded.
- The Git repository is published at `GGadash/GDTT` with `main` tracking `origin/main`.
- `uv` is installed and the project declares Python 3.13.
- Phase 2 source inspection is implemented for CSV, TSV, delimited TXT, and selected XLSX
  worksheets using bounded-memory readers.
- File input supports single or multiple selection through the picker and local drag/drop. The
  first file is the batch reference; file kind, ordered columns, header decision, delimiter/quote
  settings, or selected worksheet must match before configuration can continue.
- Phase 3 headless transformation semantics are implemented with immutable tables, versioned
  recipes, operation plans, counted diagnostics, cancellation checkpoints, and audit entries.
- Column operations cover rename/order/selection, empty and duplicate fields, one-based Index,
  and entirely-empty-field deselection.
- Numeric and calculated operations cover arithmetic rounding, ppm/ppb, explicit invalid-value
  policies, nested safe expression trees, and linear formulas without `eval`.
- Date/time and timezone operations cover named profiles, ambiguous-date previews, milliseconds,
  combine/split, timestamp roles/durations, start/mid/end, semantic end normalization, time
  shifts, UTC/Asia-Colombo, embedded/fixed/column/manual-offset sources, and DST edge cases.
- Confirmed missing markers normalize to canonical `None`; Phase 2 detections remain advisory.
- Phase 4 interval suggestions remain advisory and gap generation requires a positive confirmed
  interval. Exact expected grids use elapsed-time arithmetic for timezone-aware timestamps.
- Gap analysis reports missing timestamps, gap spans, duplicates, chronological breaks, invalid
  timestamps, and off-grid rows separately. Generation blocks ambiguity and never interpolates
  measurement values.
- Generated rows support explicit Null, Carry Stable Metadata, Fixed Value, and Derived from
  Timestamp policies, plus populated indexes and generated-row flags.
- Invalid-numeric inspection supports Null and Continue, Inspect, Stop, and Preserve Source;
  canonical-null row-removal rules provide counts before application.
- Strict atomic CSV/XLSX writers preserve canonical null output policy, keep CSV empty source
  text distinct, and support plain or styled XLSX without modifying the source.
- Version-1 recipes and their JSON Schema include typed gap and missing-data configuration.
- The desktop shell includes a working Reformat inspection and Phase 5 configuration flow,
  Averaging and future-mode cards, and Dark/Light/Auto/System themes.
- Inspection reports row/column counts, encoding/delimiter/header decisions, type confidence,
  potential missing markers, likely time structure, empty columns, large-file policy, and
  first/middle/last previews.
- Phase 5 provides a searchable virtualized mapping grid, bounded proposed-output preview,
  inline export/name edits, selected-column controls, a sequential wizard, live samples,
  summary/validation, Back, Reset, and undo/redo history over one immutable draft.
- Gap insertion is optional and enabled by default. Timestamp and interval suggestions require
  confirmation; generated measurements remain canonical `None` while True Null, N/A, -999, or
  Custom Sentinel controls only the proposed/output representation.
- Phase 6 provides immutable aggregation configuration, timezone-aware periodizers, exact
  boundary-derived expected counts, Direct execution, and configurable Incremental chains that
  retain every stage table and completeness record.
- Reporting periods cover clock intervals, configurable local days/weeks, calendar months,
  anchored fixed days, quarters, configurable seasons, calendar years, and anchored fixed years;
  DST days correctly expect 23 or 25 hourly observations.
- Aggregation strategies cover arithmetic mean, min, max, sum, median, population standard
  deviation, count, equal/duration-weighted Leq, rainfall accumulation, and rain-rate mean.
- The default completeness rule is 75%. Explicit 2-of-3 is limited to three-component
  Incremental stages; rejected field-period results remain canonical `None` with counted
  diagnostics.
- Average-mode transformation recipes and the machine-readable JSON Schema now use typed
  aggregation fields, stages, periods, completeness rules, and runtime round trips.
- The Average / Aggregate card now opens a dedicated inspection route and Phase 7 configuration
  workspace over one immutable undoable draft.
- Phase 7 exposes explicit timestamp/profile, separate source/reporting timezones, input interval, missing-marker,
  field statistic/output-name, Direct/Incremental chain, per-stage period/threshold, day/week,
  quarter, season, reporting-year, fixed-anchor, and output-null choices.
- Name-based Leq/rainfall/rain-rate suggestions require confirmation or remain overridable.
  Detected missing-marker choices require an explicit reviewed decision before preview.
- Bounded proposed-output and retained per-stage tables/completeness records are executed by the
  Phase 6 engine and displayed through virtualized Qt models; Qt handlers do not calculate them.
- Phase 8 introduced a separate complete-source reader rather than reusing bounded preview rows.
  Phase 9 now streams CSV/TXT and read-only XLSX through replayable private spill storage, while
  the guarded eager reader remains available only as a reference path for focused tests.
- Phase 9 Combination A is complete. A deterministic isolated-process harness benchmarks stdlib,
  Polars, PyArrow, and optional DuckDB over 100,000, 1 million, and 5 million generated rows.
  All candidates matched row-count, valid-value, PM2.5, and converted-NO2 semantic checksums.
- The measured direction remains Polars-first with PyArrow record-batch interoperability;
  DuckDB remains optional for measured external-sort/local-query cases. Provisional performance
  budgets and the full local Windows baseline are versioned with the repository.
- Phase 9 Combination A production execution is complete. Complete CSV/TXT/read-only-XLSX
  sources stream into private replayable spill tables instead of one full Python tuple table.
- Reformat executes row-local operations in chunks and preserves stable metadata, duplicates,
  explicit external reorder, exact gaps, null-row removal, formatting, and diagnostics across
  batch boundaries.
- Direct/Incremental Averaging streams exact first-stage reporting periods and retains all later
  stage tables and completeness records. Writers and reopen verification also consume batches.
- Cancellation removes partial outputs and private workspaces. Non-UTF8 delimited and read-only
  XLSX fallbacks are covered. The former workflow-level 1 GB estimate guard is removed.
- An early Phase 10 CI workflow now runs the locked Python 3.13 development environment, Ruff
  formatting/lint, mypy, and pytest on Windows and Ubuntu without write credentials.
- Dependabot version-update configuration checks uv and GitHub Actions dependencies monthly with
  a three-pull-request limit per ecosystem; repository alerts/security updates remain GitHub
  settings controlled by the owner.
- GitHub repository sponsorship metadata links to the owner-supplied GDTT Ko-fi page and
  dedicated Ko-fi support offer without storing payment or account credentials.
- The Windows workflow automatically publishes verified assets for an explicitly pushed `v*`
  tag. Hyphenated tags become pre-releases; branch/manual builds do not publish; the write token
  is isolated to the dependent release job; and existing releases remain unchanged on rerun.
- Phase 9 Combination B is complete on the build host. The shell uses canonical SVG/PNG/ICO
  artwork; PyInstaller 6.22 produces a versioned `onedir` bundle, portable ZIP, manifest, and
  SHA-256 checksums through hermetic Windows build and smoke-verification scripts.
- Optional Combination D is complete on the build host. A pinned-hash workspace NSIS 3.12
  compiler produces a current-user/no-admin installer with license page, Start Menu/uninstall
  registration, optional desktop shortcut, and preserved user settings/log data.
- Both workflows continue into complete-file first/middle/last review, RF/AVG Windows-safe
  naming, CSV/plain-XLSX/formatted-XLSX choices, True Null/N/A/-999/custom output, explicit
  overwrite permission, style presets, optional evidence sidecars, and background cancellation.
- Compatible batches execute and reopen-verify each source independently with source-derived,
  collision-safe names and visible per-source outcomes. A failed item does not hide successful
  items, and Process more similar files returns to the appropriate input screen after export.
- Every data output is reopened and checked for filename, readability, row count, ordered
  columns, duplicate Index fields, values/null representation, timestamp boundaries, and
  formatted worksheet structure. Passed, Passed with Warnings, and Failed remain visible.
- Versioned local recipe templates and XLSX styles contain no measurements and support
  schema-count matching, Apply/Review/Ignore, duplicate, rename, confirmed delete, import, and
  export. Apply reconstructs the reversible draft and returns to configuration review.
- Authorship is absent from the persistent shell and available in About with the license,
  OpenAI Codex development credit, dependency versions, and project links.
- Settings are validated and written atomically to per-user local storage.
- Privacy-conscious rotating logs and central user-facing error levels exist.
- Synthetic unit, regression, and desktop integration tests cover Phases 2 through 8.

## Verification status

- `uv.lock` resolves GDTT 0.8.0 under Python 3.13.15 with PySide6 6.10.3,
  XlsxWriter 3.2.9, and the optional PyInstaller 6.22.2 packaging environment.
- `ruff format --check .`: passed across 138 files.
- `ruff check .`: passed.
- `mypy`: passed with no issues in 98 source files.
- `pytest`: 136 passed.
- `pytest --cov=data_transform_tool --cov-branch`: 136 passed with 80% coverage.
- Phase 9 benchmark: 100,000/1,000,000/5,000,000-row candidate checksums passed. At 5 million
  rows, measured process/aggregate times were Polars 0.261 s, DuckDB 0.397 s, PyArrow 3.833 s,
  and stdlib 11.044 s; peak RSS was 308.2/149.4/130.7/27.2 MB respectively.
- Installed-package desktop smoke: passed at version 0.8.0 with Home and Export views available.
- Installed-package Phase 6 smoke: passed at version 0.6.0 with a 75%-complete daily Direct
  mean of 8.5 and a lossless typed aggregation recipe/runtime round trip.
- Native Windows Phase 5 configuration renders: passed at 1500×920 in Light and Dark.
- Native mapping, preview, selected-field, gap/missing, and summary layout was visually
  inspected; the editor was widened and split into tabs after the first pass.
- Native Windows Phase 7 field-rules and stage-completeness layouts render at 1500×920 in Light
  and Dark; final preview and completeness tables contain bounded Phase 6 results.
- PyInstaller portable package: passed on Windows 11 for product/version metadata, icon and
  required notices/assets, offscreen app smoke, archive readability, and manifest SHA-256 hashes.
- NSIS current-user installer: passed silent temporary install, installed-app offscreen smoke,
  Start Menu and uninstall-registry readback, silent uninstall, and cleanup on the build host.
- Final GDTT Windows artifacts were rebuilt and reverified. Their authoritative SHA-256 values
  are generated in `packaging/output/BUILD_MANIFEST.json` and `SHA256SUMS.txt`, avoiding a
  circular source-archive hash inside versioned handoff documentation.
- Local Combination C-lite passed a fresh portable extraction in a path containing spaces with
  minimal PATH, inherited Python variables removed, disposable settings/logs, normal log
  unchanged, bundled dependency metadata present, and current-user installer cleanup.
- Synthetic CSV, TSV, and XLSX inputs each produced a six-row gap-completed result from five
  source rows; CSV/plain-XLSX/formatted-XLSX artifacts and processing sidecars reopened and
  verified successfully.
- The prospective release set audit covered 223 files with zero blocking findings and two
  expected informational specification properties: `creator=Gadash (Akila DJ)` and
  `lastModifiedBy=Gadash (Akila DJ)`. Operational datasets and private output remain excluded.
- An audited source archive, portable verifier, C-lite JSON evidence, checksum list, and local
  release-candidate checklist are generated under ignored `packaging/output/`.
- Public `SHA256SUMS.txt` entries now cover only flat downloadable Release files. The unpacked
  executable remains hashed and verified through `BUILD_MANIFEST.json` before ZIP publication.
- Local and GitHub builds share one release finalizer that creates the acceptance checklist and
  portable verifier, updates the manifest/checksums, removes nested non-downloadable checksum
  targets, and verifies the complete flat asset set before upload.
- The pushed `v0.8.0-rc.3` tag completed both GitHub workflows successfully. The Windows package
  run published a non-draft pre-release with all eight expected assets; an independent download
  of those assets passed the supplied verifier for all six content checksums, and the release
  asset digests match the downloaded files.

## Unfinished

- Combination C separate-computer distribution verification, code-signing selection, and
  screenshots remain later work. The current artifacts are unsigned development builds and have
  only been exercised on the build host.
- This build host cannot supply the clean disposable environment: Windows Sandbox is absent,
  `HypervisorPresent` is false, and CPU firmware virtualization reports disabled. Enable
  virtualization in firmware and install Windows Sandbox, or use another clean Windows VM/host.

## Exact next step

Combinations A, B, and optional D are complete on the build host, and the `v0.8.0-rc.3` GitHub
pre-release is published and verified. Combination C is next: use a
separate clean Windows environment for rebuild/install/launch/uninstall/dependency verification,
including picker, drag/drop, compatible/incompatible batch, per-file verification, and
continuation smoke tests. Then decide signing and finish release-readiness evidence. Local C-lite
already passes; the exact artifact-only and full-rebuild instructions are in
`About-Info/Human-Docs/RELEASE_ACCEPTANCE.md`. Keep CI green on the published GitHub repository.
