"""Smoke coverage for the deterministic Phase 9 benchmark harness."""

from __future__ import annotations

import runpy
from pathlib import Path
from typing import Any


def test_stdlib_benchmark_fixture_is_deterministic_and_streamable(tmp_path) -> None:
    script = Path(__file__).parents[2] / "scripts" / "benchmark_backends.py"
    benchmark: dict[str, Any] = runpy.run_path(str(script))
    source = tmp_path / "source.csv"
    output = tmp_path / "output.csv"

    benchmark["generate_dataset"](source, 300)
    imported, processed, exported, summary = benchmark["_stdlib"](source, output)

    assert imported >= 0
    assert processed >= 0
    assert exported >= 0
    assert summary["source_rows"] == 300
    assert summary["output_rows"] == 1
    assert summary["valid_pm25"] == 296
    assert output.read_text(encoding="utf-8").startswith("Date,Valid_PM25")
