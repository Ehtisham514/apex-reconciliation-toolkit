"""Behavioral checks for ingestion integrity and exact financial aggregation."""
import csv
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest

from financial_intelligence.enterprise import REQUIRED, aggregate_csv


def ledger(tmp_path, rows, header=REQUIRED, name="ledger.csv"):
    path = tmp_path / name
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output)
        writer.writerow(header)
        writer.writerows(rows)
    return path


def transaction(identifier="A", amount="100.10", **changes):
    row = dict(transaction_id=identifier, date="2026-01-01", entity="Example Ltd", project="P1",
               account="Operating", amount=amount, currency="USD")
    row.update(changes)
    return [row[key] for key in REQUIRED]


def test_exact_totals_first_valid_duplicate_and_source_hash(tmp_path):
    path = ledger(tmp_path, [transaction("A", "100.10"), transaction("B", "-25.05"), transaction("B", "999.99")])
    result = aggregate_csv(path)
    assert (result["records_read"], result["accepted_rows"], result["rejected_rows"]) == (3, 2, 1)
    assert result["totals"][0]["amount"] == "75.05"
    assert result["cash_in"] == "100.10"
    assert result["cash_out"] == "25.05"
    assert result["net_amount"] == "75.05"
    assert result["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert result["errors"][0]["line"] == 4
    assert all(result["checks"].values())


@pytest.mark.parametrize("amount", ["nan", "Infinity", "1e3", "0.001", "2.000", "$2.50", "1,000.00", "--1", "", "10000000000000"])
def test_invalid_money_is_rejected_not_rounded(tmp_path, amount):
    result = aggregate_csv(ledger(tmp_path, [transaction(amount=amount)]))
    assert result["accepted_rows"] == 0
    assert result["rejected_rows"] == 1
    assert result["net_amount"] == "0.00"


def test_exact_integer_totals_exceed_sqlite_signed_integer_range(tmp_path):
    # 10,000 × 999,999,999,999,999 cents = 9,999,999,999,999,990,000 cents.
    # A native SQLite INTEGER sum would overflow; our group arithmetic stays exact.
    count = 10_000
    path = ledger(tmp_path, (transaction(str(i), "9999999999999.99") for i in range(count)))
    result = aggregate_csv(path)
    assert result["net_amount"] == "99999999999999900.00"
    assert result["totals"][0]["amount"] == "99999999999999900.00"
    assert result["totals"][0]["row_count"] == count


def test_invalid_first_row_does_not_consume_identifier(tmp_path):
    result = aggregate_csv(ledger(tmp_path, [transaction("A", "bad"), transaction("A", "+0.01")]))
    assert result["accepted_rows"] == 1
    assert result["rejected_rows"] == 1
    assert result["net_amount"] == "0.01"


@pytest.mark.parametrize("changes", [
    {"date": "2026-02-30"}, {"date": "20260101"}, {"date": "2026-W01-1"},
    {"date": "01/01/2026"}, {"entity": " "}, {"account": ""}, {"transaction_id": ""},
    {"entity": "A\nB"}, {"transaction_id": "A" * 257}, {"currency": "EUR"},
])
def test_invalid_row_fields_are_reported(tmp_path, changes):
    result = aggregate_csv(ledger(tmp_path, [transaction(**changes)]))
    assert result["rejected_rows"] == 1
    assert result["errors"][0]["line"] == 2


def test_rows_are_partitioned_by_entity_project_account(tmp_path):
    rows = [transaction("1", "1", entity="A", project="X"),
            transaction("2", "2", entity="A", project="Y"),
            transaction("3", "3", entity="B", project="X"),
            transaction("4", "4", entity="B", project="X", account="Reserve")]
    result = aggregate_csv(ledger(tmp_path, rows))
    assert result["group_count"] == 4
    assert result["net_amount"] == "10.00"
    assert {x["currency"] for x in result["totals"]} == {"USD"}


def test_currency_cannot_be_silently_mixed(tmp_path):
    path = ledger(tmp_path, [transaction("1", "10", currency="USD"), transaction("2", "20", currency="EUR")])
    result = aggregate_csv(path, expected_currency=" eur ")
    assert result["net_amount"] == "20.00"
    assert result["currency"] == "EUR"
    assert result["rejected_rows"] == 1


def test_preview_and_error_samples_are_bounded_but_exports_are_complete(tmp_path):
    rows = [transaction(str(i), "1.25", project=str(i)) for i in range(5)]
    rows.extend(transaction("bad" + str(i), "NaN") for i in range(4))
    totals_path = tmp_path / "totals.csv"
    errors_path = tmp_path / "rejects.csv"
    result = aggregate_csv(ledger(tmp_path, rows), max_errors=2, group_limit=2,
                           totals_csv=totals_path, rejected_csv=errors_path)
    assert result["accepted_rows"] == 5
    assert result["rejected_rows"] == 4
    assert len(result["totals"]) == len(result["errors"]) == 2
    assert result["totals_truncated"] and result["errors_truncated"]
    with totals_path.open(newline="") as source:
        assert len(list(csv.DictReader(source))) == 5
    with errors_path.open(newline="") as source:
        assert len(list(csv.DictReader(source))) == 4


def test_header_normalization_extra_columns_and_blank_lines(tmp_path):
    path = tmp_path / "ledger.csv"
    path.write_text(" Transaction_ID , Date , ENTITY, project , Account , Amount , currency,comment\n"
                    "\nA,2026-01-01,Example Ltd,,Operating,2.50,usd,optional\n", encoding="utf-8")
    result = aggregate_csv(path)
    assert result["accepted_rows"] == 1
    assert result["records_read"] == 1
    assert result["totals"][0]["project"] == ""


@pytest.mark.parametrize("header", [(), ("id", "amount"), REQUIRED + (" Amount ",), REQUIRED + ("",)])
def test_bad_headers_fail_entire_import(tmp_path, header):
    with pytest.raises(ValueError):
        aggregate_csv(ledger(tmp_path, [], header=header))


def test_short_or_extra_fields_do_not_hide_or_shift_values(tmp_path):
    valid = transaction()
    result = aggregate_csv(ledger(tmp_path, [valid[:-1], valid + ["extra"]]))
    assert result["accepted_rows"] == 0
    assert result["rejected_rows"] == 2


def test_retain_sqlite_records_and_run_metadata(tmp_path):
    path = ledger(tmp_path, [transaction("a", "10"), transaction("b", "bad")])
    database = tmp_path / "ledger.sqlite"
    result = aggregate_csv(path, database_path=database)
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT amount_minor FROM transactions").fetchone() == (1000,)
        assert connection.execute("SELECT COUNT(*) FROM rejected").fetchone()[0] == 1
        assert json.loads(connection.execute("SELECT value FROM metadata WHERE key='sha256'").fetchone()[0]) == result["sha256"]
    assert result["database_retained"]
    assert result["database_bytes"] == database.stat().st_size


def test_failed_parse_does_not_leave_a_completed_database(tmp_path):
    path = tmp_path / "broken.csv"
    path.write_text(",".join(REQUIRED) + '\nA,2026-01-01,"unclosed quote', encoding="utf-8")
    database = tmp_path / "failed.sqlite"
    with pytest.raises(ValueError, match="Unreadable UTF-8 CSV"):
        aggregate_csv(path, database_path=database)
    assert not database.exists()


def test_invalid_utf8_fails_without_import(tmp_path):
    path = tmp_path / "invalid.csv"
    path.write_bytes(b"transaction_id,date,entity,project,account,amount,currency\n\xff")
    with pytest.raises(ValueError, match="Unreadable UTF-8 CSV"):
        aggregate_csv(path)


def test_existing_source_and_outputs_are_never_overwritten(tmp_path):
    path = ledger(tmp_path, [transaction()])
    before = path.read_bytes()
    with pytest.raises(ValueError, match="distinct"):
        aggregate_csv(path, totals_csv=path)
    target = tmp_path / "existing.sqlite"
    target.write_text("keep this", encoding="utf-8")
    with pytest.raises(FileExistsError):
        aggregate_csv(path, database_path=target)
    assert target.read_text() == "keep this"
    assert path.read_bytes() == before


def test_csv_export_formula_defense_and_sql_boundaries(tmp_path):
    entity = "=SUM(1,2)"
    account = "'); DROP TABLE transactions; --"
    output = tmp_path / "totals.csv"
    result = aggregate_csv(ledger(tmp_path, [transaction(entity=entity, account=account)]), totals_csv=output)
    assert result["accepted_rows"] == 1
    with output.open(newline="") as source:
        row = next(csv.DictReader(source))
    assert row["entity"] == "'" + entity
    assert row["account"] == account
    assert row["amount"] == "100.10"


def test_utf8_bom_included_in_hash(tmp_path):
    path = ledger(tmp_path, [transaction()])
    path.write_bytes(b"\xef\xbb\xbf" + path.read_bytes())
    result = aggregate_csv(path)
    assert result["accepted_rows"] == 1
    assert result["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()


def test_zero_preview_returns_counts_and_exact_net(tmp_path):
    result = aggregate_csv(ledger(tmp_path, [transaction(), transaction("B", "bad")]), max_errors=0, group_limit=0)
    assert result["errors"] == result["totals"] == []
    assert result["rejected_rows"] == result["group_count"] == 1
    assert result["net_amount"] == "100.10"


@pytest.mark.parametrize("arguments", [{"max_errors": -1}, {"group_limit": True}, {"group_limit": 10001}, {"expected_currency": "US"}])
def test_bad_configuration_fails_before_processing(tmp_path, arguments):
    with pytest.raises(ValueError):
        aggregate_csv(ledger(tmp_path, [transaction()]), **arguments)


def test_cli_writes_full_outputs_and_signals_rejections(tmp_path):
    path = ledger(tmp_path, [transaction("A", "3.50"), transaction("B", "bad")])
    report = tmp_path / "report.json"
    totals = tmp_path / "totals.csv"
    result = subprocess.run([sys.executable, "-m", "financial_intelligence.enterprise", str(path),
                             "--report", str(report), "--totals", str(totals)],
                            cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True)
    assert result.returncode == 2, result.stderr
    assert json.loads(report.read_text())["net_amount"] == "3.50"
    assert totals.exists()


def test_database_connect_failure_cleans_exclusively_created_file(tmp_path, monkeypatch):
    from financial_intelligence import enterprise
    source = ledger(tmp_path, [transaction()])
    database = tmp_path / "failed-connect.sqlite"

    def fail_connect(*args, **kwargs):
        raise sqlite3.OperationalError("simulated initialization failure")

    monkeypatch.setattr(enterprise.sqlite3, "connect", fail_connect)
    with pytest.raises(sqlite3.OperationalError, match="initialization"):
        aggregate_csv(source, database_path=database)
    assert not database.exists()


def test_database_schema_failure_closes_connection_and_removes_partial_file(tmp_path, monkeypatch):
    from financial_intelligence import enterprise
    source = ledger(tmp_path, [transaction()])
    database = tmp_path / "failed-schema.sqlite"
    original_connect = sqlite3.connect
    connections = []

    class FailingSchema(sqlite3.Connection):
        def executescript(self, script):
            super().executescript("CREATE TABLE partial (id INTEGER);")
            raise sqlite3.OperationalError("simulated schema failure")

    def connect_with_failure(*args, **kwargs):
        connection = original_connect(*args, factory=FailingSchema, **kwargs)
        connections.append(connection)
        return connection

    monkeypatch.setattr(enterprise.sqlite3, "connect", connect_with_failure)
    with pytest.raises(sqlite3.OperationalError, match="schema failure"):
        aggregate_csv(source, database_path=database)
    assert not database.exists()
    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        connections[0].execute("SELECT 1")


def test_export_failure_removes_partial_csv_but_keeps_completed_database(tmp_path, monkeypatch):
    from financial_intelligence import enterprise
    source = ledger(tmp_path, [transaction()])
    database = tmp_path / "completed.sqlite"
    output = tmp_path / "failed-export.csv"

    def fail_export_cell(value):
        raise OSError("simulated output failure after header")

    monkeypatch.setattr(enterprise, "_spreadsheet_text", fail_export_cell)
    with pytest.raises(OSError, match="output failure"):
        aggregate_csv(source, database_path=database, totals_csv=output)
    assert not output.exists()
    assert database.exists()
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM transactions").fetchone()[0] == 1


def test_source_mutation_aborts_and_removes_retained_database(tmp_path, monkeypatch):
    from financial_intelligence import enterprise
    source = ledger(tmp_path, [transaction()])
    database = tmp_path / "changed-source.sqlite"
    original_minor_units = enterprise._minor_units
    changed = False

    def change_during_read(value):
        nonlocal changed
        if not changed:
            changed = True
            with source.open("a", newline="", encoding="utf-8") as output:
                csv.writer(output).writerow(transaction("changed", "2"))
        return original_minor_units(value)

    monkeypatch.setattr(enterprise, "_minor_units", change_during_read)
    with pytest.raises(ValueError, match="Source file changed while reading"):
        aggregate_csv(source, database_path=database)
    assert not database.exists()
