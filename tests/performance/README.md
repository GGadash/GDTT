# Performance Tests

Phase 9 generates deterministic synthetic datasets at runtime and records import, processing,
aggregation, export, and peak-process-memory measurements. Candidate outputs must match the
stdlib semantic checksum. Do not commit generated datasets or benchmark outputs.

Run the smoke test with the normal development environment. Run the isolated candidate
comparison with the optional performance environment:

```powershell
uv sync --extra dev --extra performance
uv run python scripts/benchmark_backends.py --rows 100000,1000000,5000000
```

See `About-Info/Data-Processing/PERFORMANCE_BASELINE.md` for the recorded reference run,
limitations, backend direction, and provisional budgets.
