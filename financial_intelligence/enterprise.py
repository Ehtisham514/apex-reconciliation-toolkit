"""Exact, disk-backed CSV ledger aggregation; Python standard library only.

Money in is positive and money out is negative. This is an aggregation and
validation aid, not double-entry accounting, reconciliation, FX conversion, or
intercompany consolidation. See docs/DATA_ENGINE.md for the data contract.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sqlite3
import tempfile
from contextlib import closing
from datetime import date
from typing import BinaryIO


REQUIRED = ("transaction_id", "date", "entity", "project", "account", "amount", "currency")
MAX_TRANSACTION_MINOR = 999_999_999_999_999  # 9,999,999,999,999.99 currency units
MAX_TEXT_LENGTH = 1_024
MAX_ID_LENGTH = 256
MAX_COLUMNS = 64
MAX_PHYSICAL_LINE = 1_048_576
SCHEMA_VERSION = 1
_AMOUNT = re.compile(r"^[+-]?[0-9]+(?:\.[0-9]{1,2})?$")
_DATE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
_CURRENCY = re.compile(r"^[A-Z]{3}$")


class _HashingReader(io.RawIOBase):
    """Hash the same bytes that the CSV decoder reads, including a UTF-8 BOM."""

    def __init__(self, source: BinaryIO):
        self.source = source
        self.digest = hashlib.sha256()

    def readable(self):
        return True

    def readinto(self, target):
        count = self.source.readinto(target)
        if count:
            self.digest.update(memoryview(target)[:count])
        return count


class _BoundedLines:
    """Keep individual physical input lines bounded before CSV parsing."""

    def __init__(self, stream):
        self.stream = stream

    def __iter__(self):
        return self

    def __next__(self):
        line = self.stream.readline(MAX_PHYSICAL_LINE + 1)
        if not line:
            raise StopIteration
        if len(line) > MAX_PHYSICAL_LINE:
            raise ValueError("CSV physical line exceeds 1,048,576 characters")
        return line


class _ExactSum:
    def __init__(self):
        self.value = 0

    def step(self, value):
        self.value += int(value)

    def finalize(self):
        return str(self.value)


def _minor_units(raw: str) -> int:
    text = raw.strip()
    if len(text) > 32 or not _AMOUNT.fullmatch(text):
        raise ValueError("Amount must be a signed decimal with at most two decimal places")
    sign = -1 if text.startswith("-") else 1
    unsigned = text.lstrip("+-")
    whole, _, fraction = unsigned.partition(".")
    value = sign * (int(whole) * 100 + int((fraction + "00")[:2]))
    if abs(value) > MAX_TRANSACTION_MINOR:
        raise ValueError("Amount exceeds the per-transaction limit 9,999,999,999,999.99")
    return value


def _amount_text(minor: int | str) -> str:
    value = int(minor)
    sign = "-" if value < 0 else ""
    whole, fraction = divmod(abs(value), 100)
    return f"{sign}{whole}.{fraction:02d}"


def _text(raw: str, field: str, *, required: bool = True, limit: int = MAX_TEXT_LENGTH) -> str:
    value = raw.strip()
    if required and not value:
        raise ValueError(f"{field} is required")
    if len(value) > limit:
        raise ValueError(f"{field} exceeds {limit} characters")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise ValueError(f"{field} contains a control character")
    return value


def _spreadsheet_text(value: str) -> str:
    """Neutralize spreadsheet formula prefixes in exported textual fields."""
    return "'" + value if value and value[0] in "=+-@\t\r\n" else value


def _open_database(path: Path) -> sqlite3.Connection:
    # Exclusive creation prevents accidentally overwriting a prior run or source.
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(descriptor)
    connection = None
    try:
        connection = sqlite3.connect(path)
        connection.execute("PRAGMA cache_size = -8192")
        connection.execute("PRAGMA temp_store = FILE")
        connection.execute("PRAGMA journal_mode = DELETE")
        connection.execute("PRAGMA synchronous = FULL")
        connection.create_function("exact_add", 2, lambda left, right: str(int(left) + int(right)))
        connection.create_aggregate("exact_sum", 1, _ExactSum)
        connection.executescript("""
            CREATE TABLE transactions (
                transaction_id TEXT PRIMARY KEY,
                source_line INTEGER NOT NULL,
                transaction_date TEXT NOT NULL,
                entity TEXT NOT NULL,
                project TEXT NOT NULL,
                account TEXT NOT NULL,
                currency TEXT NOT NULL,
                amount_minor INTEGER NOT NULL
            ) WITHOUT ROWID;
            CREATE TABLE totals (
                entity TEXT NOT NULL,
                project TEXT NOT NULL,
                account TEXT NOT NULL,
                currency TEXT NOT NULL,
                amount_minor TEXT NOT NULL,
                row_count INTEGER NOT NULL,
                PRIMARY KEY (entity, project, account, currency)
            ) WITHOUT ROWID;
            CREATE TABLE rejected (
                source_line INTEGER NOT NULL,
                transaction_id TEXT NOT NULL,
                reason TEXT NOT NULL
            );
            CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL) WITHOUT ROWID;
        """)
        return connection
    except BaseException:
        # The caller has no connection handle if initialization has not returned.
        # Clean only the destination exclusively created by this helper.
        try:
            if connection is not None:
                connection.close()
        finally:
            path.unlink(missing_ok=True)
        raise


def _export_csv(connection: sqlite3.Connection, path: Path, kind: str) -> None:
    # Open before entering the cleanup block: a failed exclusive open must never
    # remove a pre-existing file. Partial exports from this run are removed.
    output = path.open("x", encoding="utf-8", newline="")
    try:
        with output:
            writer = csv.writer(output)
            if kind == "totals":
                writer.writerow(("entity", "project", "account", "currency", "amount", "row_count"))
                for entity, project, account, currency, amount, count in connection.execute(
                    "SELECT entity, project, account, currency, amount_minor, row_count "
                    "FROM totals ORDER BY entity, project, account, currency"
                ):
                    writer.writerow((*( _spreadsheet_text(x) for x in (entity, project, account, currency)),
                                     _amount_text(amount), count))
            else:
                writer.writerow(("source_line", "transaction_id", "reason"))
                for line, identifier, reason in connection.execute(
                    "SELECT source_line, transaction_id, reason FROM rejected ORDER BY source_line"
                ):
                    writer.writerow((line, _spreadsheet_text(identifier), _spreadsheet_text(reason)))
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def aggregate_csv(
    path,
    expected_currency="USD",
    max_errors=100,
    *,
    database_path=None,
    group_limit=1_000,
    totals_csv=None,
    rejected_csv=None,
):
    """Validate and aggregate a CSV without retaining its IDs/rows in Python RAM.

    Existing callers retain ``sha256``, ``accepted_rows``, ``rejected_rows``,
    ``errors`` and ``totals``. ``max_errors`` now caps the returned error sample;
    it does not stop reading the input. Exact rejection counts remain available.
    ``group_limit`` caps returned groups; ``totals_csv`` streams every group.

    Unique transaction IDs are global within this import. The first valid row
    wins; later occurrences are rejected. A rejected invalid row does not claim
    an ID. Entity/project/account labels remain case-sensitive after trimming.
    ``database_path`` optionally retains rows, rejects and metadata on disk;
    the destination must not already exist. Otherwise temporary storage is
    removed when the call finishes. All monetary outputs are decimal strings.
    """
    source_path = Path(path).resolve(strict=True)
    if not source_path.is_file():
        raise ValueError("Input must be a regular file")
    currency = str(expected_currency).strip().upper()
    if not _CURRENCY.fullmatch(currency):
        raise ValueError("expected_currency must be a three-letter currency label")
    for name, value in (("max_errors", max_errors), ("group_limit", group_limit)):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{name} must be a nonnegative integer")
    if max_errors > 10_000 or group_limit > 10_000:
        raise ValueError("Error samples and group previews are capped at 10,000; use CSV exports")
    destinations = [Path(value).resolve() for value in (database_path, totals_csv, rejected_csv) if value is not None]
    if len(set(destinations)) != len(destinations) or source_path in destinations:
        raise ValueError("Input, database and output paths must be distinct")
    for destination in destinations:
        if destination.exists():
            raise FileExistsError(f"Destination already exists: {destination}")
        if not destination.parent.is_dir():
            raise FileNotFoundError(f"Destination directory does not exist: {destination.parent}")

    with tempfile.TemporaryDirectory(prefix="apex-ledger-") as temporary:
        db_path = Path(database_path).resolve() if database_path is not None else Path(temporary) / "ledger.sqlite"
        connection = None
        committed = False
        try:
            connection = _open_database(db_path)
            summary = _ingest(connection, source_path, currency, max_errors, group_limit)
            connection.commit()
            committed = True
            summary["database_bytes"] = db_path.stat().st_size
            summary["database_retained"] = database_path is not None
            if database_path is not None:
                summary["database_path"] = str(db_path)
            if totals_csv is not None:
                _export_csv(connection, Path(totals_csv), "totals")
                summary["totals_csv"] = str(Path(totals_csv).resolve())
            if rejected_csv is not None:
                _export_csv(connection, Path(rejected_csv), "rejected")
                summary["rejected_csv"] = str(Path(rejected_csv).resolve())
            return summary
        except (UnicodeDecodeError, csv.Error) as exc:
            raise ValueError(f"Unreadable UTF-8 CSV; no completed import: {exc}") from exc
        finally:
            if connection is not None:
                connection.close()
            # Remove only the database this run exclusively created, after rollback.
            if not committed and connection is not None and db_path.exists():
                db_path.unlink()


def _ingest(connection, source_path, currency, max_errors, group_limit):
    accepted = rejected = record_count = cash_in = cash_out = 0
    with source_path.open("rb", buffering=0) as binary:
        before = os.fstat(binary.fileno())
        hashing_reader = _HashingReader(binary)
        with io.TextIOWrapper(io.BufferedReader(hashing_reader), encoding="utf-8-sig", newline="") as stream:
            reader = csv.reader(_BoundedLines(stream), strict=True)
            try:
                original_header = next(reader)
            except StopIteration as exc:
                raise ValueError("CSV is empty; required header is missing") from exc
            header = [column.strip().lower() for column in original_header]
            if not header or len(header) > MAX_COLUMNS or any(not column for column in header):
                raise ValueError("CSV needs 1–64 nonempty named columns")
            if len(set(header)) != len(header):
                raise ValueError("CSV column names must be unique after case/whitespace normalization")
            missing = sorted(set(REQUIRED) - set(header))
            if missing:
                raise ValueError(f"Missing required CSV columns: {', '.join(missing)}")
            positions = {field: header.index(field) for field in REQUIRED}
            connection.execute("BEGIN")
            previous_line = reader.line_num
            for row in reader:
                source_line = previous_line + 1
                previous_line = reader.line_num
                if not row:  # Blank physical lines are not data records.
                    continue
                record_count += 1
                identifier = ""
                try:
                    if len(row) != len(header):
                        raise ValueError("Row width differs from the header")
                    fields = {field: row[index] for field, index in positions.items()}
                    identifier = _text(fields["transaction_id"], "transaction_id", limit=MAX_ID_LENGTH)
                    entity = _text(fields["entity"], "entity")
                    project = _text(fields["project"], "project", required=False)
                    account = _text(fields["account"], "account")
                    row_currency = fields["currency"].strip().upper()
                    if row_currency != currency:
                        raise ValueError(f"Currency mismatch: expected {currency}; no FX conversion is performed")
                    day = fields["date"].strip()
                    if not _DATE.fullmatch(day):
                        raise ValueError("Date must use YYYY-MM-DD")
                    date.fromisoformat(day)
                    amount = _minor_units(fields["amount"])
                    try:
                        connection.execute("INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                           (identifier, source_line, day, entity, project, account, currency, amount))
                    except sqlite3.IntegrityError as exc:
                        raise ValueError("Duplicate transaction_id; first valid occurrence retained") from exc
                    connection.execute(
                        "INSERT INTO totals VALUES (?, ?, ?, ?, ?, 1) "
                        "ON CONFLICT(entity, project, account, currency) DO UPDATE SET "
                        "amount_minor = exact_add(totals.amount_minor, excluded.amount_minor), "
                        "row_count = totals.row_count + 1",
                        (entity, project, account, currency, str(amount)),
                    )
                    accepted += 1
                    if amount >= 0:
                        cash_in += amount
                    else:
                        cash_out -= amount
                except ValueError as exc:
                    rejected += 1
                    connection.execute("INSERT INTO rejected VALUES (?, ?, ?)",
                                       (source_line, identifier[:MAX_ID_LENGTH], str(exc)))
            after = os.fstat(binary.fileno())
            if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                raise ValueError("Source file changed while reading; rerun on a stable copy")
            source_sha256 = hashing_reader.digest.hexdigest()

    grouped_count, grouped_minor, grouped_rows = connection.execute(
        "SELECT COUNT(*), exact_sum(amount_minor), COALESCE(SUM(row_count), 0) FROM totals"
    ).fetchone()
    transaction_count, transaction_minor = connection.execute(
        "SELECT COUNT(*), exact_sum(amount_minor) FROM transactions"
    ).fetchone()
    net = cash_in - cash_out
    totals_match = int(grouped_minor or 0) == int(transaction_minor or 0) == net
    rows_match = grouped_rows == transaction_count == accepted and accepted + rejected == record_count
    if not (totals_match and rows_match):
        raise RuntimeError("Internal reconciliation failed; import has not been committed")
    errors = [dict(line=line, error=reason, transaction_id=identifier) for line, identifier, reason in
              connection.execute("SELECT source_line, transaction_id, reason FROM rejected ORDER BY source_line LIMIT ?",
                                 (max_errors,))]
    totals = [dict(entity=entity, project=project, account=account, currency=row_currency,
                   amount=_amount_text(amount), row_count=count)
              for entity, project, account, row_currency, amount, count in connection.execute(
                  "SELECT entity, project, account, currency, amount_minor, row_count FROM totals "
                  "ORDER BY entity, project, account, currency LIMIT ?", (group_limit,))]
    summary = {
        "schema_version": SCHEMA_VERSION, "status": "complete" if not rejected else "complete_with_rejections",
        "sha256": source_sha256, "source_bytes": before.st_size, "currency": currency,
        "records_read": record_count, "accepted_rows": accepted, "rejected_rows": rejected,
        "errors": errors, "errors_truncated": rejected > len(errors),
        "group_count": grouped_count, "totals": totals, "totals_truncated": grouped_count > len(totals),
        "cash_in": _amount_text(cash_in), "cash_out": _amount_text(cash_out), "net_amount": _amount_text(net),
        "checks": {"accepted_row_count_matches_database": rows_match, "group_totals_match_accepted_rows": totals_match},
    }
    for key, value in summary.items():
        if key not in {"errors", "totals"}:
            connection.execute("INSERT INTO metadata VALUES (?, ?)", (key, json.dumps(value, sort_keys=True)))
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate a CSV ledger with exact amounts and disk-backed aggregation")
    parser.add_argument("input", help="UTF-8 CSV input; never modified")
    parser.add_argument("--currency", default="USD", help="Required currency label for all accepted rows (default USD)")
    parser.add_argument("--database", help="Retain a new SQLite database at this path")
    parser.add_argument("--totals", help="Write all grouped totals to a new CSV")
    parser.add_argument("--errors", help="Write every rejected-row reason to a new CSV")
    parser.add_argument("--report", help="Write JSON summary to a new file instead of stdout")
    parser.add_argument("--max-errors", type=int, default=100, help="Maximum returned error samples; full count remains exact")
    parser.add_argument("--group-limit", type=int, default=1_000, help="Maximum summary groups; --totals exports every group")
    args = parser.parse_args(argv)
    try:
        if args.report:
            report_path = Path(args.report).resolve()
            other_paths = {Path(x).resolve() for x in (args.input, args.database, args.totals, args.errors) if x}
            if report_path in other_paths or report_path.exists():
                raise ValueError("Report path must be new and distinct from input/database/CSV outputs")
        result = aggregate_csv(args.input, args.currency, args.max_errors, database_path=args.database,
                               group_limit=args.group_limit, totals_csv=args.totals, rejected_csv=args.errors)
        rendered = json.dumps(result, indent=2, ensure_ascii=False)
        if args.report:
            with Path(args.report).open("x", encoding="utf-8") as output:
                output.write(rendered + "\n")
        else:
            print(rendered)
        return 2 if result["rejected_rows"] else 0
    except (ValueError, OSError, sqlite3.Error) as exc:
        parser.exit(1, f"Import failed: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
