# Phase 9 Performance Baseline

Last updated: 2026-08-31

## Purpose

Combination A began with measured backend selection before production-executor changes. The
benchmark generates deterministic one-minute air-quality data at runtime, normalizes `N/A`,
converts NO2 ppm to ppb, aggregates daily PM2.5/NO2 values, writes a CSV result, and requires
every candidate to match the standard-library semantic checksum.

Run it without retaining operational or generated datasets:

```powershell
uv sync --extra dev --extra performance
uv run python scripts/benchmark_backends.py --rows 100000,1000000,5000000
```

## Reference environment

- Windows 11 10.0.26100
- Python 3.13.15
- Polars 1.44.1
- PyArrow 25.0.1
- DuckDB 1.5.5
- Single isolated process per backend and size
- Peak RSS is absolute process working set sampled every 10 ms

The figures are a local engineering baseline, not a universal hardware guarantee. Source-file
generation is excluded. `total` includes backend import/startup, while the stage columns measure
source scan, transformation/aggregation, and result export separately.

## Results

| Rows | Source | Backend | Import | Process + aggregate | Export | Total | Peak RSS |
|---:|---:|---|---:|---:|---:|---:|---:|
| 100,000 | 3.8 MB | stdlib reference | 0.073 s | 0.219 s | 0.001 s | 0.293 s | 22.4 MB |
| 100,000 | 3.8 MB | Polars | 0.005 s | 0.012 s | 0.002 s | 0.345 s | 69.5 MB |
| 100,000 | 3.8 MB | PyArrow | 0.016 s | 0.078 s | 0.001 s | 0.162 s | 61.4 MB |
| 100,000 | 3.8 MB | DuckDB | 0.073 s | 0.087 s | 0.001 s | 0.266 s | 51.6 MB |
| 1,000,000 | 38.0 MB | stdlib reference | 0.668 s | 2.241 s | 0.003 s | 2.912 s | 23.1 MB |
| 1,000,000 | 38.0 MB | Polars | 0.010 s | 0.070 s | 0.002 s | 0.369 s | 145.5 MB |
| 1,000,000 | 38.0 MB | PyArrow | 0.140 s | 0.792 s | 0.002 s | 1.003 s | 121.4 MB |
| 1,000,000 | 38.0 MB | DuckDB | 0.108 s | 0.151 s | 0.002 s | 0.372 s | 89.8 MB |
| 5,000,000 | 189.8 MB | stdlib reference | 3.297 s | 11.044 s | 0.011 s | 14.354 s | 27.2 MB |
| 5,000,000 | 189.8 MB | Polars | 0.035 s | 0.261 s | 0.002 s | 0.581 s | 308.2 MB |
| 5,000,000 | 189.8 MB | PyArrow | 0.675 s | 3.833 s | 0.003 s | 4.574 s | 130.7 MB |
| 5,000,000 | 189.8 MB | DuckDB | 0.238 s | 0.397 s | 0.009 s | 0.755 s | 149.4 MB |

All row counts, valid-value counts, PM2.5 sums, and converted NO2 sums matched the reference.

## Direction and provisional budgets

- Keep Polars as the primary lazy expression engine for compatible delimited sources and
  transformation/aggregation plans.
- Use PyArrow for stable record-batch interchange and bounded streaming where it provides a
  clearer contract than a Polars callback.
- Keep DuckDB optional; consider it for external sorting or local-query operations only when a
  measured production plan benefits from it.
- Retain the standard-library CSV reader and openpyxl read-only reader as exact semantic
  fallbacks for supported encodings, dialects, and XLSX input.

Provisional local budgets for this backend-isolation scenario are: exact semantic checksum; under one
second and 256 MiB peak RSS for 1 million rows with Polars; under three seconds and 512 MiB for
5 million rows. These are engine-direction figures, not end-to-end desktop promises.

## Production executor checkpoint

The Phase 9 production path now:

1. streams CSV/TXT and read-only XLSX sources into replayable private spill tables;
2. executes row-local Reformat operations in bounded batches;
3. preserves duplicate, gap, stable-metadata, order, timezone, removal, and output-format
   semantics across chunk boundaries;
4. uses an external SQLite sort only when explicit timestamp reordering is needed;
5. streams the first Averaging stage by exact reporting-period windows and retains every
   subsequent Incremental stage and completeness record;
6. writes and reopens CSV/XLSX through replayable batches without whole-output row lists; and
7. propagates cancellation while deleting partial exports and private spill workspaces.

The former application-level 1 GB estimated-working-set guard is no longer used by full-file
Reformat or Averaging preparation. The eager `DataTable` remains the correctness/reference
executor, and its guarded reader remains available to bounded tests. A confirmed gap grid still
honors the existing 1,000,000 expected-row safety limit.

The production semantic path intentionally uses a backend-neutral `DataBatch` contract and a
standard-library private spill store. Polars remains the measured first vectorized optimizer for
compatible delimited plans, with PyArrow as the intended record-batch interchange; neither is a
correctness dependency yet. Add such acceleration only behind parity tests for every supported
fallback and global semantic.
