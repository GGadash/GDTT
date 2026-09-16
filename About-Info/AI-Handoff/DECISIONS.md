# Decisions

## D-027 — Public repository and maintained wiki (2026-09-16)

- Owner authorizes making GGadash/GDTT public and publishing a structured wiki, plus updates to
  existing documentation where copyright, attribution or release disclaimers are unclear.
- Version the wiki source in About-Info/Wiki and publish it into the separate GitHub wiki after
  the initial web Home page exists. Reconcile web edits before synchronizing; do not force-push.
- Keep normal collaborator-only wiki editing; public readability is not authority to grant
  anonymous editing. No Pages-hosted desktop-app conversion is requested.
- Preserve the root license text exactly. Explain its Akila DJ notice and the About panel's
  Gadash notice without a silent license change. Credit OpenAI Codex and dependencies separately.
- Distinguish passed automated Windows/Linux/build-host checks from pending separate hands-on
  clean-Windows/DPI acceptance. Do not imply signatures or regulatory/security certification.
- This is documentation/settings work only; keep app 0.10.1 and existing release assets unchanged.

## D-026 — ISO presets and type-scoped profiles (2026-09-15)

- Implement PEND-017 as patch version 0.10.1; owner authorizes cleanup, commit/push and publication
  of source/binaries with a new tag. Use v0.10.1-rc.1; preserve old tags/releases unchanged.
- Both input/output selectors follow selected type. Custom stays second, common extended ISO
  forms precede compact forms. Existing IDs retain output behavior; new presets use new IDs.
- Z input means UTC; Z output converts known instants, never assumes a naive datetime is UTC.
  Unknown-zone UTC/offset output blocks. Exact new ISO custom masks use the same semantics.
- Explicit type changes reset profiles for review; loading saved recipes does not rewrite rules.
  Keep recipe schemas, dependencies, aggregation and Split & Join behavior unchanged.

## D-025 — Explicit RC1 publication and artifact retention (2026-09-12)

- Owner authorized committing and pushing 0.10.0 with a release tag and binary assets. Use the
  unused `v0.10.0-rc.1` tag, because unsigned/separate-clean-host limitations are still disclosed.
- Names are `GDTT-<version>-windows-x64-Portable.zip` and
  `GDTT-<version>-windows-x64-installer.exe`; source ZIP and evidence names stay unchanged.
  Build scripts, upload filters and tag validation use the same exact naming contract.
- Retain previous releases unchanged; archive prior local builds/evidence under ignored exports.
  Important source/specifications and working environments/tools remain in place. Publish source
  through Git and binaries through GitHub Releases, not via forced Git-add of ignored output.

## D-024 — 0.10.0 explicit formatting and appearance

- Owner approved PEND-001 through PEND-016. Output numeric masks round stored exported values
  by default; optional preserve mode retains numeric precision and applies an Excel display mask.
  Input parsing never rounds. Independent dot/comma choices are recipe data, not global settings.
- Custom masks use a documented bounded subset, encoded into existing profile strings. No recipe
  schema migration, dependency upgrade, or replacement of existing null/timestamp behavior.
- Reuse shared field/zone/bulk-selection controls and existing Qt palettes. Appearance settings
  persist; safety confirmations/overwrite are never included in bulk selection.
- Local 0.10.0 verification/build is authorized; Git publication and shutdown are not.

## D-024 — Separate Split & Join module (2026-09-08)

- Reuse readers, private spill storage, established period definitions, writers and verification.
  Keep new configuration independent of version-1 transformation recipes.
- Match exact instants including microseconds; honor embedded offsets, localize naive timestamps
  in each source's zone, and export ISO text with offsets in the boundary/output zone.
- Calendar periods include the start and exclude the end. Seasonal boundaries recur annually;
  ambiguous/nonexistent DST source times or boundaries block. Monthly/quarterly day starts use
  1-28; annual starts accept any valid recurring non-leap calendar date.
- Joins stop on duplicate keys by default; first/last policies follow source-file then row order.
  Time joins may keep all; field joins use outer/inner/left matching and source-number prefixes.
- Export into a new run folder after every file passes verification. Automatic names include
  source/group/date information, stable ordinals and operation-specific suffixes. No aggregation,
  gap filling, interpolation, source overwriting, or hidden rule persistence occurs.
- Complete the local 0.9.0 builds first, report completion, then commit/push as authorized by the
  owner on 2026-09-08. This supersedes the earlier no-push instruction. Use focused checks during
  development and one final full-suite pass before packaging.

## D-001 — Product identity

- **Decision:** The canonical short product name is **GDTT**. The formal descriptive identity is
  **GDTT — Data Transform Tool by Gadash (Akila DJ)**; **Data Transform Tool by G** may be used
  where a compact title expansion is helpful.
- **Description:** “Data forging, transitions, and aggregations—mainly for air-quality-related
  data” may be used as explanatory copy, not as an alternate product name.
- **Decision:** Persistent application chrome shows GDTT without creator text. Author identity,
  license terms, Codex credit, and third-party citations remain in About, documentation, and
  code/package metadata.
- **Updated:** 2026-09-01 (supersedes the 2026-08-30 provisional identity)

## D-002 — Desktop architecture

- **Decision:** Python 3.13 with PySide6 Qt Widgets and Qt model/view tables.
- **Reason:** Native offline Windows behavior, mature accessibility, model-backed large
  tables, testability, and maintainability are stronger fits than CustomTkinter or a local
  browser shell. Qt Quick/QML remains an option for isolated future visuals, not the core UI.

## D-003 — Data-processing architecture

- **Decision:** Polars will be the primary tabular engine, with PyArrow interoperability.
  DuckDB may be used as an optional out-of-core/local-query backend after benchmarks.
- **Alternatives:** Pandas is familiar but not the primary large-file engine. DuckDB alone
  is less natural for per-column transformation composition and UI previews.

## D-004 — Spreadsheet architecture

- **Decision:** openpyxl read-only mode for XLSX ingestion and verification; XlsxWriter for
  new plain/formatted XLSX exports. openpyxl entered the lockfile in Phase 2; XlsxWriter enters
  with export implementation.

## D-005 — Date/time architecture

- **Decision:** Standard-library timezone-aware `datetime`/`zoneinfo` plus the `tzdata`
  package on Windows. Parsing ambiguity remains explicit and user-overridable.

## D-006 — Dependency management

- **Decision:** `pyproject.toml`, `uv`, and a committed cross-platform `uv.lock` are the one
  dependency source. Do not create contradictory requirements files.

## D-007 — Packaging path

- **Decision:** Develop from source; package with PyInstaller `onedir` first and wrap it in
  a Windows installer. Evaluate Nuitka/`pyside6-deploy` and one-file packaging during Phase
  9 benchmarks. Never treat a build as verified until tested on a clean Windows environment.

## D-008 — UI direction

- **Decision:** Environmental Technical visual language: teal/slate, cyan data accents,
  amber warnings, high contrast, generous spacing, and progressive disclosure. Dark, Light,
  Auto, and System modes share semantic tokens. Auto follows the operating-system
  color preference; System delegates its palette to Qt's platform style.
- **Alternatives retained:** Clean Laboratory and Night Operations can be introduced by
  replacing theme tokens rather than rebuilding screens.

## D-009 — Licensing and credits

- **Decision:** Use the exact owner-supplied permission/warranty terms in root `LICENSE`.
  Credit Akila DJ and OpenAI Codex in documentation, source metadata, and the About dialog—not
  in persistent shell chrome. Maintain separate third-party notices and do not claim
  dependencies use the project license.

## D-010 — Git publication

- **Decision:** Git is local, `main` is primary, and `AUTO_COMMIT = FALSE`. Ask for remote
  details and credentials only after implementation is complete and publication is approved.

## D-011 — Transformation semantic executor

- **Decision:** Phase 3 uses immutable `DataTable` values as the correctness/reference executor
  for domain tests and bounded previews. Operation contracts are backend-neutral; production
  large-file execution will compile them to a benchmarked lazy/chunked backend without changing
  recipe or semantic behavior.

## D-012 — Safe calculation and temporal ambiguity

- **Decision:** Calculated fields use explicit expression trees and never unrestricted `eval`.
  Ambiguous dates and ambiguous/nonexistent IANA DST local times require an explicit choice or
  blocking error. Manual shifts and timezone conversion remain separate operations.

## D-013 — Gap and canonical-null semantics

- **Decision:** Gap grids use the user-confirmed positive interval and elapsed-time arithmetic
  for timezone-aware timestamps. Duplicates, off-grid values, invalid timestamps, and implicit
  chronological reordering block generation.
- **Decision:** Generated measurement fields are always canonical `None`; metadata requires an
  explicit Null, Carry Stable, Fixed Value, or Derived from Timestamp policy. Only `None` is
  internally missing, so unconfirmed empty text remains distinct through validation and export
  adapters.

## D-014 — Reformat configuration and gap choice

- **Decision:** Phase 5 uses one immutable application-layer draft for the mapping grid,
  selected-column editor, sequential wizard, proposed preview, and undo/redo history. A ready
  draft compiles to the existing typed recipe; Qt signal handlers contain no data calculations.
- **Decision:** **Insert Missing Time Rows** is enabled by default but may be deselected. When
  enabled, timestamp and interval suggestions require explicit confirmation. True Null, N/A,
  -999, and Custom Sentinel are global output representations; generated measurements remain
  canonical `None` internally and are never interpolated.

## D-015 — Aggregation boundaries, completeness, and stage evidence

- **Decision:** Direct aggregation evaluates valid source observations against exact expected
  slots derived from the confirmed input interval and reporting-zone boundaries. Incremental
  aggregation uses a visible configurable chain and retains each stage table and completeness
  record instead of exposing only the final value.
- **Decision:** Clock intervals use wall-clock slots; day/week/month/quarter/season/year periods
  use local calendar boundaries; fixed-day and fixed-year periods use explicit anchors. DST
  changes expected elapsed slots rather than fabricating or discarding measurements.
- **Decision:** Completeness defaults to 75%. The 2-of-3 exception is allowed only when explicitly
  configured on an Incremental stage with exactly three expected components. Rejected outputs
  are canonical `None` and incompatible stage tiling is a blocking error.
- **Decision:** Population standard deviation is the Phase 6 standard-deviation definition. Leq
  always uses energy averaging and accepts optional positive duration weights; rainfall amount
  and rain rate remain distinct strategies.

## D-016 — Averaging decisions and bounded evidence

- **Decision:** Phase 7 stores source detections and user confirmations separately in one
  immutable undoable draft. Timestamp, source timezone, reporting timezone, interval, selected field statistics, and
  detected missing-marker decisions must be explicit before a preview is ready.
- **Decision:** Checked detected markers normalize to canonical null; unchecked markers are
  retained only after the marker decision set is explicitly marked reviewed.
- **Decision:** Naive source timestamps are localized with the confirmed source timezone;
  reporting boundaries use a separate confirmed timezone. Changing the reporting zone never
  relabels source instants, and incompatible source-grid/reporting-boundary alignment blocks.
- **Decision:** Qt handlers edit drafts and request previews. The application layer prepares one
  bounded inspection slice and the Phase 6 engine alone calculates periods, statistics, and
  completeness. These previews do not authorize an eager full-file backend.

## D-017 — Phase 8 export, verification, and template boundary

- **Decision:** Full-file execution always rereads the selected source; bounded inspection
  previews are evidence only. Until Phase 9 benchmarks a production backend, execution is
  blocked when the inspected in-memory estimate exceeds 1 GB. D-020 supersedes that temporary
  workflow guard after the batch/spill executor achieved parity.
- **Decision:** CSV/XLSX and report files use same-directory temporary files and atomic replace.
  All known target collisions are checked before the first write unless overwrite is explicitly
  enabled. XLSX output above the worksheet row limit blocks with CSV/split guidance.
- **Decision:** Canonical null remains internal. True Null, N/A, -999, or Custom is applied only
  by writers, and every data output is reopened and compared with the expected result.
- **Decision:** Templates are versioned local configuration/style files without measurement
  data. Matching uses schema count and overlap, never filenames; Apply requires an exact schema,
  rebuilds a reversible draft, and returns to configuration review.

## D-018 — Phase 9 measured backend direction and early CI

- **Decision:** The measured vectorization direction is Polars-first with PyArrow record-batch
  interoperability. Standard-library CSV and openpyxl remain exact supported-format fallbacks.
  DuckDB remains optional for a measured external-sort or local-query need, not a required
  runtime dependency by default.
- **Evidence:** Isolated Windows 11 runs at 100,000, 1 million, and 5 million generated rows
  produced identical semantic checksums. At 5 million rows Polars had the fastest measured
  process/aggregate stage; PyArrow and DuckDB used less peak memory; the stdlib reference used
  the least memory but was substantially slower.
- **Decision:** Candidate engines remain in the optional `performance` extra; D-020 establishes
  the backend-neutral production contract without making them correctness dependencies. CI
  quality checks move forward from Phase 10 and run on Windows and Ubuntu during Phase 9.

## D-019 — Windows portable package and installer

- **Decision:** Use a PyInstaller 6.22 `onedir` bundle as the canonical portable Windows artifact.
  Generate product/version/icon resources, include the project license and third-party notice,
  create a ZIP plus manifest/checksums, and verify the frozen app noninteractively.
- **Decision:** Sanitize only the PyInstaller subprocess PATH so non-system directories exposing
  a private `icuuc.dll` cannot shadow Windows ICU for Qt; restore the original PATH immediately
  afterward. Retain the PySide6-shipped MSVC codecvt runtime explicitly in the bundle.
- **Decision:** Use NSIS 3.12 for optional Combination D because its licensing permits any use and
  it supports a small conventional installer. Bootstrap the official portable archive only after
  checking its pinned SHA-256.
- **Decision:** Install per current user without administrator permission. Show the project
  license, create Start Menu and uninstall entries, offer the desktop shortcut as an unchecked
  option, and preserve per-user settings/log data on uninstall. Code signing is deferred until the
  owner supplies an identity and selects it. Separate clean-Windows verification remains C.

## D-020 — Production batch/spill semantic executor

- **Decision:** Complete-source Reformat and Averaging use a replayable `TabularData` contract
  with private workspace-owned SQLite row spills. The eager `DataTable` remains the bounded
  correctness/reference executor.
- **Decision:** Reformat applies row-local operations in bounded batches, then resolves stable
  metadata, duplicates, explicit external reorder, exact gap grids, removal, and final formatting
  through ordered spill passes.
- **Decision:** Averaging stream-normalizes source batches and evaluates exact first-stage
  reporting-period windows; later Incremental stages reuse the Phase 6 component engine and
  retain stage/completeness evidence.
- **Decision:** Writers and reopen verification consume replayable batches. Cancellation
  propagates and removes private workspaces and same-directory partial files.
- **Decision:** The workflow-level 1 GB estimate guard is removed. The existing 1,000,000-row
  confirmed gap-grid limit remains. Polars/PyArrow stay optional measured vectorization
  candidates until a compiler proves parity with every supported source and global semantic.

## D-021 — Local C-lite release-candidate gate

- **Decision:** When a separate clean Windows guest is unavailable, run a clearly labelled local
  C-lite gate: extract the portable ZIP into a fresh path containing spaces, remove inherited
  Python environment variables, minimize PATH, and redirect settings/logs to disposable roots.
- **Decision:** C-lite also audits the prospective source set for credentials, operational
  datasets, build/runtime output, local paths, and unwanted metadata; exercises synthetic
  CSV/TSV/XLSX workflows; verifies reports/log privacy, bundled dependency metadata, installer
  lifecycle, source archive, signatures, manifest, and every checksum.
- **Decision:** C-lite can qualify a local release candidate but never claims clean-host
  equivalence. A separate Windows computer pass, screenshots, signing decision, owner acceptance,
  and explicit Git publication authority remain external gates.
- **Decision:** Source archives must rebuild without `.git` metadata. The release audit therefore
  uses Git's prospective non-ignored set when available and a matching safe filesystem fallback
  for extracted source archives.

## D-022 — Compatible multi-file input and batch export

- **Decision:** Browse and drag/drop accept one or more supported local files. The first file is
  the reference; a shared configuration is available only when every candidate has the same file
  type, ordered columns, header decision, delimited quote/delimiter behavior, and XLSX worksheet.
- **Decision:** Row counts and measurement values are intentionally not compatibility criteria.
  Incompatibilities remain visible with reasons and block the batch instead of being guessed.
- **Decision:** Pre-export transformed slices are labelled as reference-file evidence. Each batch
  source is then prepared, written, reopened, verified, and reported independently with a
  collision-safe source-derived RF/AVG name. One source failure remains explicit without hiding
  other source outcomes.
- **Decision:** A post-export action returns directly to source selection for another single file
  or compatible batch. It does not silently reuse hidden transformation rules.

## D-023 — Explicit-tag automatic GitHub Release publishing

- **Decision:** Only a pushed `v*` tag authorizes publication. Pull requests, branch pushes, and
  manual workflow dispatches may produce temporary Actions artifacts but never a GitHub Release.
- **Decision:** A dependent Ubuntu release job receives job-scoped `contents: write` only after
  the read-only Windows package job passes. It downloads the exact Actions artifact, validates
  the semantic tag base against the build manifest, verifies every downloadable checksum, and
  publishes through GitHub CLI.
- **Decision:** Hyphenated semantic tags publish as pre-releases and are not Latest. Stable tags
  publish normally. Workflow reruns never replace assets on an existing release.
- **Decision:** Public `SHA256SUMS.txt` covers the flat downloadable set; the unpacked executable
  hash remains in `BUILD_MANIFEST.json` and is verified locally before the portable ZIP is made.
