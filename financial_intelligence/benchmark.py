"""Reproducible synthetic ledger benchmark; never use private client data.

Run from the repository root:
    python -m financial_intelligence.benchmark --rows 1000000

Input and database live in a temporary directory and are deleted at completion.
The report measures this environment and workload, not a promised capacity.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import sqlite3
import sys
import tempfile
import time

from .enterprise import REQUIRED, aggregate_csv


def _format_minor(value):
    sign = "-" if value < 0 else ""
    whole, cents = divmod(abs(value), 100)
    return f"{sign}{whole}.{cents:02d}"


def _peak_rss_mib():
    try:
        import resource
        value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return round(value / (1024 * 1024 if sys.platform == "darwin" else 1024), 2)
    except (ImportError, AttributeError):
        return None


def run_benchmark(rows=1_000_000, work_dir=None):
    if isinstance(rows, bool) or not isinstance(rows, int) or not 1 <= rows <= 10_000_000:
        raise ValueError("rows must be an integer from 1 to 10,000,000")
    with tempfile.TemporaryDirectory(prefix="apex-benchmark-", dir=work_dir) as temporary:
        source = Path(temporary) / "synthetic.csv"
        database = Path(temporary) / "synthetic.sqlite"
        generation_start = time.perf_counter()
        with source.open("w", encoding="utf-8", newline="") as output:
            writer = csv.writer(output)
            writer.writerow(REQUIRED)
            for i in range(rows):
                writer.writerow((f"DEMO-{i:09d}", f"2026-01-{i % 28 + 1:02d}", f"Entity-{i % 50:02d}",
                                 f"Project-{(i // 50) % 20:02d}", f"Account-{(i // 1000) % 8:02d}",
                                 _format_minor((i % 20_001) - 10_000), "USD"))
        generation_seconds = time.perf_counter() - generation_start
        start = time.perf_counter()
        result = aggregate_csv(source, database_path=database, group_limit=10, max_errors=10)
        elapsed = time.perf_counter() - start
        # Every complete cycle sums to zero. Check the remaining arithmetic
        # series independently of the engine's ingestion and aggregation logic.
        remainder = rows % 20_001
        expected_minor = remainder * (remainder - 1) // 2 - 10_000 * remainder
        verified = (result["accepted_rows"] == rows and result["rejected_rows"] == 0
                    and result["net_amount"] == _format_minor(expected_minor)
                    and all(result["checks"].values()))
        if not verified:
            raise RuntimeError("Synthetic benchmark failed independent control totals")
        return {
            "recorded_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "python": platform.python_version(), "sqlite": sqlite3.sqlite_version,
            "platform": platform.system(), "architecture": platform.machine(),
            "workload": "deterministic synthetic, unique IDs, up to 50 entities / 20 projects / 8 accounts; one currency",
            "input_rows": rows, "accepted_rows": result["accepted_rows"], "rejected_rows": result["rejected_rows"],
            "group_count": result["group_count"], "preview_groups": len(result["totals"]),
            "source_bytes": result["source_bytes"], "source_sha256": result["sha256"],
            "database_bytes": result["database_bytes"], "expected_net_amount": _format_minor(expected_minor),
            "actual_net_amount": result["net_amount"], "control_totals_verified": verified,
            "generation_seconds": round(generation_seconds, 3), "ingestion_seconds": round(elapsed, 3),
            "rows_per_second": round(rows / elapsed, 1), "process_peak_rss_mib": _peak_rss_mib(),
            "measurement_notes": "Wall-clock ingestion includes parsing, validation, deduplication, disk writes and control checks. "
                                 "RSS is whole-process peak, including generation, not a per-operation allocation measure. "
                                 "A single synthetic run does not establish concurrency, production suitability or capacity limits.",
        }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=1_000_000)
    parser.add_argument("--work-dir", help="Existing directory for temporary source/database files")
    parser.add_argument("--report", help="Write a new JSON evidence file (never overwrites)")
    args = parser.parse_args(argv)
    if args.report and Path(args.report).exists():
        parser.error("Report already exists; choose a new output file")
    try:
        report = run_benchmark(args.rows, args.work_dir)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"Benchmark failed: {exc}\n")
    output = json.dumps(report, indent=2)
    if args.report:
        with Path(args.report).open("x", encoding="utf-8") as stream:
            stream.write(output + "\n")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
