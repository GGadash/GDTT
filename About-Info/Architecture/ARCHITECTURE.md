# Architecture

## Principles

- Desktop UI orchestrates and presents; it does not own calculations.
- Domain behavior is headless and testable.
- Recipes are immutable, versioned intent; an execution plan is derived from them.
- Detection is advisory and overridable.
- Missing values, timestamp meaning, and timezone operations are explicit concepts.
- Files are processed locally with bounded memory and non-destructive exports.

## Layer flow

```text
PySide6 UI
  → application workflows
    → validated domain recipes and plans
      → IO / transformation / datetime / timezone / gaps / aggregation
        → validation → export → post-export verification → report
```

Cross-cutting services provide settings, logging, versioning, configuration registries,
and local templates. UI work runs on the GUI thread; long processing uses cancellable
workers and never updates widgets directly from worker threads.

## Data engines

Phase 2 CSV-family inspection uses bounded samples and streaming standard-library passes;
XLSX inspection uses openpyxl read-only mode. Phase 3 uses an immutable `DataTable` as the
semantic reference executor for correctness tests and bounded previews. Phase 9 adds a
backend-neutral `DataBatch`/`TabularData` boundary and private replayable SQLite spill tables
for production semantics. The measured Polars-first, PyArrow-interchange direction remains the
preferred vectorized optimization for compatible plans; DuckDB remains optional for measured
local-query cases.

First/middle/last preview, global gap/duplicate checks, date range, and aggregation must
remain correct across lazy batches. Operations that cannot stream must disclose estimated
memory or spill to a local temporary workspace.

Phase 6 adds an eager aggregation reference executor with clock/calendar/season periodizers,
exact timezone-aware expected counts, isolated statistic strategies, and retained Direct or
Incremental stage results. It defines correctness for bounded tests and future previews, not the
production large-file backend.

Phase 7 adds an immutable application-layer averaging draft/session and bounded preview composer.
The Qt view edits those contracts, while the Phase 6 executor remains the sole owner of reporting
periods, statistics, and completeness calculations. Final and per-stage tables are virtualized
presentation models.

Phase 8 adds a separate complete-source reader and export workflow; it never treats inspection
previews as production input. Phase 9 now stages CSV/TXT or read-only XLSX rows in a private
spill workspace, executes Reformat chunks with global gap/order passes, and streams Averaging
through exact first-stage reporting windows before retaining smaller stage evidence. The output
boundary writes same-directory temporary files and atomically replaces final paths. Verification
reopens every CSV/XLSX and compares structure and values as a stream.

Phase 9 Combination A adds the production batch/spill executor, deterministic isolated-process
backend benchmark, and Windows/Linux CI gate. Candidate vector engines remain in the optional
`performance` dependency extra until a vectorized compiler proves full semantic parity. Detailed
results are in
`About-Info/Data-Processing/PERFORMANCE_BASELINE.md`.

## Recipe model

A recipe includes a schema version, source expectations, input null interpretation,
column rules, date/time semantics, timezone operations, interval/gap settings, aggregation
instructions, output null policy, field selection/order, and export/report preferences.
It never contains measurement data or user credentials.

The initial JSON Schema is in `About-Info/Machine-Readable/transformation_recipe_schema.json`.

## Transformation semantic engine

`TransformationOperation` objects are deterministic and UI-independent. Every apply returns
an immutable table and diagnostics; `TransformationPlan` also produces ordered audit entries.
Date formatting, timestamp meaning, manual shifts, and timezone conversion are separate
concepts. Safe calculated fields use expression trees and never execute recipe text.
