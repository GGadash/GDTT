"""Benchmark large-file backends on deterministic air-quality data.

Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import subprocess
import sys
import tempfile
import threading
import time
from collections import defaultdict
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class BenchmarkResult:
    backend: str
    rows: int
    source_bytes: int
    import_seconds: float
    processing_aggregation_seconds: float
    export_seconds: float
    total_seconds: float
    peak_rss_bytes: int
    output_rows: int
    valid_pm25: int
    pm25_sum: float
    no2_ppb_sum: float


def generate_dataset(path: Path, rows: int) -> None:
    """Write a repeatable one-minute source without retaining its rows."""
    start = datetime(2025, 1, 1)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(("Timestamp", "PM2.5", "NO2_ppm", "Station"))
        for index in range(rows):
            timestamp = start + timedelta(minutes=index)
            missing = index % 97 == 0
            writer.writerow(
                (
                    timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "N/A" if missing else f"{10 + (index % 100) / 10:.1f}",
                    "N/A" if missing else f"{0.010 + (index % 30) / 1000:.3f}",
                    "STN-01",
                )
            )


def _stdlib(path: Path, target: Path) -> tuple[float, float, float, dict[str, float | int]]:
    started = time.perf_counter()
    with path.open("r", encoding="utf-8", newline="") as stream:
        imported = sum(1 for _ in csv.reader(stream)) - 1
    import_seconds = time.perf_counter() - started

    started = time.perf_counter()
    grouped: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0, 0.0])
    with path.open("r", encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            if row["PM2.5"] == "N/A":
                continue
            values = grouped[row["Timestamp"][:10]]
            values[0] += 1
            values[1] += float(row["PM2.5"])
            values[2] += float(row["NO2_ppm"]) * 1000
    processing_seconds = time.perf_counter() - started

    started = time.perf_counter()
    with target.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(("Date", "Valid_PM25", "PM25_Mean", "NO2_ppb_Mean"))
        for day, (count, pm25, no2) in sorted(grouped.items()):
            writer.writerow((day, int(count), pm25 / count, no2 / count))
    export_seconds = time.perf_counter() - started
    return import_seconds, processing_seconds, export_seconds, _summary(imported, grouped)


def _polars(path: Path, target: Path) -> tuple[float, float, float, dict[str, float | int]]:
    import polars as pl

    def scan() -> Any:
        return pl.scan_csv(path, infer_schema=False, null_values=["N/A"], try_parse_dates=False)

    started = time.perf_counter()
    source_rows = int(scan().select(pl.len()).collect(engine="streaming").item())
    import_seconds = time.perf_counter() - started

    started = time.perf_counter()
    aggregated = (
        scan()
        .with_columns(
            pl.col("Timestamp").str.slice(0, 10).alias("Date"),
            pl.col("PM2.5").cast(pl.Float64, strict=False),
            (pl.col("NO2_ppm").cast(pl.Float64, strict=False) * 1000).alias("NO2_ppb"),
        )
        .group_by("Date")
        .agg(
            pl.col("PM2.5").count().alias("Valid_PM25"),
            pl.col("PM2.5").mean().alias("PM25_Mean"),
            pl.col("NO2_ppb").mean().alias("NO2_ppb_Mean"),
            pl.col("PM2.5").sum().alias("_PM25_Sum"),
            pl.col("NO2_ppb").sum().alias("_NO2_Sum"),
        )
        .sort("Date")
        .collect(engine="streaming")
    )
    processing_seconds = time.perf_counter() - started
    started = time.perf_counter()
    aggregated.drop("_PM25_Sum", "_NO2_Sum").write_csv(target)
    export_seconds = time.perf_counter() - started
    return (
        import_seconds,
        processing_seconds,
        export_seconds,
        {
            "source_rows": source_rows,
            "output_rows": aggregated.height,
            "valid_pm25": int(aggregated["Valid_PM25"].sum()),
            "pm25_sum": float(aggregated["_PM25_Sum"].sum()),
            "no2_ppb_sum": float(aggregated["_NO2_Sum"].sum()),
        },
    )


def _pyarrow(path: Path, target: Path) -> tuple[float, float, float, dict[str, float | int]]:
    import pyarrow as pa
    import pyarrow.csv as arrow_csv

    read_options = arrow_csv.ReadOptions(block_size=1 << 20)
    convert_options = arrow_csv.ConvertOptions(
        column_types={name: pa.string() for name in ("Timestamp", "PM2.5", "NO2_ppm", "Station")},
        null_values=["N/A"],
        strings_can_be_null=True,
    )

    def reader() -> Any:
        return arrow_csv.open_csv(path, read_options=read_options, convert_options=convert_options)

    started = time.perf_counter()
    source_rows = sum(batch.num_rows for batch in reader())
    import_seconds = time.perf_counter() - started

    started = time.perf_counter()
    grouped: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0, 0.0])
    for batch in reader():
        timestamps = batch.column("Timestamp").to_pylist()
        pm25_values = batch.column("PM2.5").to_pylist()
        no2_values = batch.column("NO2_ppm").to_pylist()
        for timestamp, pm25, no2 in zip(timestamps, pm25_values, no2_values, strict=True):
            if pm25 is None or no2 is None:
                continue
            values = grouped[timestamp[:10]]
            values[0] += 1
            values[1] += float(pm25)
            values[2] += float(no2) * 1000
    processing_seconds = time.perf_counter() - started

    rows = [
        (day, int(values[0]), values[1] / values[0], values[2] / values[0])
        for day, values in sorted(grouped.items())
    ]
    table = pa.table(
        {
            "Date": [row[0] for row in rows],
            "Valid_PM25": [row[1] for row in rows],
            "PM25_Mean": [row[2] for row in rows],
            "NO2_ppb_Mean": [row[3] for row in rows],
        }
    )
    started = time.perf_counter()
    arrow_csv.write_csv(table, target)
    export_seconds = time.perf_counter() - started
    return import_seconds, processing_seconds, export_seconds, _summary(source_rows, grouped)


def _duckdb(path: Path, target: Path) -> tuple[float, float, float, dict[str, float | int]]:
    import duckdb

    connection = duckdb.connect()
    source = str(path).replace("'", "''")
    started = time.perf_counter()
    source_rows = int(
        connection.execute(
            f"SELECT count(*) FROM read_csv('{source}', all_varchar=true, nullstr='N/A')"
        ).fetchone()[0]
    )
    import_seconds = time.perf_counter() - started
    query = f"""
        SELECT substr(Timestamp, 1, 10) AS Date,
               count(try_cast("PM2.5" AS DOUBLE)) AS Valid_PM25,
               avg(try_cast("PM2.5" AS DOUBLE)) AS PM25_Mean,
               avg(try_cast(NO2_ppm AS DOUBLE) * 1000) AS NO2_ppb_Mean,
               sum(try_cast("PM2.5" AS DOUBLE)) AS PM25_Sum,
               sum(try_cast(NO2_ppm AS DOUBLE) * 1000) AS NO2_Sum
        FROM read_csv('{source}', all_varchar=true, nullstr='N/A')
        GROUP BY Date ORDER BY Date
    """
    started = time.perf_counter()
    rows = connection.execute(query).fetchall()
    processing_seconds = time.perf_counter() - started
    started = time.perf_counter()
    with target.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(("Date", "Valid_PM25", "PM25_Mean", "NO2_ppb_Mean"))
        writer.writerows(row[:4] for row in rows)
    export_seconds = time.perf_counter() - started
    connection.close()
    return (
        import_seconds,
        processing_seconds,
        export_seconds,
        {
            "source_rows": source_rows,
            "output_rows": len(rows),
            "valid_pm25": sum(int(row[1]) for row in rows),
            "pm25_sum": sum(float(row[4]) for row in rows),
            "no2_ppb_sum": sum(float(row[5]) for row in rows),
        },
    )


def _summary(source_rows: int, grouped: dict[str, list[float]]) -> dict[str, float | int]:
    return {
        "source_rows": source_rows,
        "output_rows": len(grouped),
        "valid_pm25": int(sum(values[0] for values in grouped.values())),
        "pm25_sum": sum(values[1] for values in grouped.values()),
        "no2_ppb_sum": sum(values[2] for values in grouped.values()),
    }


_BACKENDS: dict[str, Callable[[Path, Path], tuple[float, float, float, dict[str, float | int]]]] = {
    "stdlib": _stdlib,
    "polars": _polars,
    "pyarrow": _pyarrow,
    "duckdb": _duckdb,
}


def _rss_bytes() -> int:
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        psapi.GetProcessMemoryInfo.argtypes = (
            wintypes.HANDLE,
            ctypes.POINTER(Counters),
            wintypes.DWORD,
        )
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        process = kernel32.GetCurrentProcess()
        if not psapi.GetProcessMemoryInfo(process, ctypes.byref(counters), counters.cb):
            raise ctypes.WinError(ctypes.get_last_error())
        return int(counters.WorkingSetSize)
    statm = Path("/proc/self/statm")
    if statm.exists():
        resident_pages = int(statm.read_text(encoding="ascii").split()[1])
        return resident_pages * os.sysconf("SC_PAGE_SIZE")
    return 0


def _worker(backend: str, source: Path, target: Path, rows: int) -> BenchmarkResult:
    peak = _rss_bytes()
    stop = threading.Event()

    def sample() -> None:
        nonlocal peak
        while not stop.wait(0.01):
            peak = max(peak, _rss_bytes())

    sampler = threading.Thread(target=sample, daemon=True)
    sampler.start()
    started = time.perf_counter()
    try:
        imported, processed, exported, summary = _BACKENDS[backend](source, target)
    finally:
        stop.set()
        sampler.join()
        peak = max(peak, _rss_bytes())
    return BenchmarkResult(
        backend=backend,
        rows=rows,
        source_bytes=source.stat().st_size,
        import_seconds=imported,
        processing_aggregation_seconds=processed,
        export_seconds=exported,
        total_seconds=time.perf_counter() - started,
        peak_rss_bytes=peak,
        output_rows=int(summary["output_rows"]),
        valid_pm25=int(summary["valid_pm25"]),
        pm25_sum=float(summary["pm25_sum"]),
        no2_ppb_sum=float(summary["no2_ppb_sum"]),
    )


def _run_isolated(backend: str, source: Path, rows: int, output: Path) -> BenchmarkResult:
    completed = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--worker",
            backend,
            "--source",
            str(source),
            "--output",
            str(output),
            "--worker-rows",
            str(rows),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return BenchmarkResult(**json.loads(completed.stdout))


def _validate(results: Sequence[BenchmarkResult]) -> None:
    reference = next(result for result in results if result.backend == "stdlib")
    for result in results:
        if (
            result.rows != reference.rows
            or result.output_rows != reference.output_rows
            or result.valid_pm25 != reference.valid_pm25
            or abs(result.pm25_sum - reference.pm25_sum) > 1e-6 * reference.rows
            or abs(result.no2_ppb_sum - reference.no2_ppb_sum) > 1e-6 * reference.rows
        ):
            raise RuntimeError(f"{result.backend} did not match the stdlib semantic checksum.")


def _parse_rows(value: str) -> tuple[int, ...]:
    rows = tuple(int(item.strip()) for item in value.split(","))
    if not rows or any(item <= 0 for item in rows):
        raise argparse.ArgumentTypeError("Row sizes must be positive comma-separated integers.")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=_parse_rows, default=(100_000, 1_000_000))
    parser.add_argument(
        "--backends", type=lambda value: tuple(value.split(",")), default=tuple(_BACKENDS)
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--worker", choices=tuple(_BACKENDS), help=argparse.SUPPRESS)
    parser.add_argument("--source", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--output", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--worker-rows", type=int, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        if args.source is None or args.output is None or args.worker_rows is None:
            parser.error("Worker execution requires source, output, and row count.")
        print(json.dumps(asdict(_worker(args.worker, args.source, args.output, args.worker_rows))))
        return 0

    unknown = sorted(set(args.backends).difference(_BACKENDS))
    if unknown:
        parser.error("Unknown backend(s): " + ", ".join(unknown))
    if "stdlib" not in args.backends:
        parser.error("The stdlib backend is required as the semantic checksum reference.")

    all_results: list[BenchmarkResult] = []
    with tempfile.TemporaryDirectory(prefix="dtt-benchmark-") as temporary:
        root = Path(temporary)
        for rows in args.rows:
            source = root / f"air-quality-{rows}.csv"
            generate_dataset(source, rows)
            size_results = [
                _run_isolated(backend, source, rows, root / f"{backend}-{rows}.csv")
                for backend in args.backends
            ]
            _validate(size_results)
            all_results.extend(size_results)
    payload = {
        "environment": {"platform": platform.platform(), "python": platform.python_version()},
        "results": [asdict(result) for result in all_results],
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print("backend rows source_mb import_s process_s export_s total_s peak_rss_mb")
        for result in all_results:
            print(
                result.backend,
                result.rows,
                f"{result.source_bytes / 1_000_000:.1f}",
                f"{result.import_seconds:.3f}",
                f"{result.processing_aggregation_seconds:.3f}",
                f"{result.export_seconds:.3f}",
                f"{result.total_seconds:.3f}",
                f"{result.peak_rss_bytes / 1_000_000:.1f}",
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
