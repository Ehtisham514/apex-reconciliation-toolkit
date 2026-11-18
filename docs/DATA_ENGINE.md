# Large-file ledger validation and aggregation

The Python ledger engine accepts a signed cash-movement CSV, checks each record, and produces exact totals by entity, project, account and currency. Transaction IDs and grouped balances are held in a local SQLite file, not an in-memory Python set. A new import can retain that database or remove temporary storage at completion.

**Best for:** checking large exports before analysis, finding duplicate IDs and invalid records, and producing traceable project/entity totals. It does not post entries, connect to bank accounts, perform double-entry accounting, eliminate intercompany balances, or establish that a bank account reconciles.

## Quick start

Python 3.10+ with its standard-library SQLite support is sufficient. From the repository root:

```sh
python -m financial_intelligence.enterprise financial_intelligence/sample_ledger.csv
```

The four fictional sample rows produce **4 accepted records**, **0 rejections**, and **86,799.50 USD** net movement: `100,000.00 − 25,000.00 + 15,000.00 − 3,200.50`.

For a large local file, use the command line so a browser does not hold the entire upload in memory:

```sh
python -m financial_intelligence.enterprise ledger.csv \
  --currency USD \
  --database ledger-run.sqlite \
  --totals grouped-totals.csv \
  --errors rejected-rows.csv \
  --report import-report.json
```

All output paths must be new and different from the input. Existing files are never deliberately overwritten. Choose a new set of filenames for each run. The process exits with `0` when every record is accepted, `2` when a completed import contains rejected records, and `1` on a fatal import or output error.

The database commits before CSV exports begin. If an individual CSV export fails, its incomplete new file is removed; a completed retained database and any earlier successful export remain available. A database initialization or parse failure removes only the new database created by that run.

## Input contract

Use UTF-8, comma-delimited CSV; a UTF-8 byte-order mark is accepted. Required header names are normalized for case and leading/trailing whitespace. Every normalized column name must be nonempty and unique. Up to 64 named columns are allowed; additional named columns beyond the seven below are ignored. Blank physical lines outside a quoted field are not records.

| Column | Required value |
| --- | --- |
| `transaction_id` | Nonempty ID, globally unique within the import; at most 256 characters. Namespace IDs yourself when combining systems. |
| `date` | Valid calendar date, strictly `YYYY-MM-DD`. |
| `entity` | Nonempty entity label; at most 1,024 characters. |
| `project` | Project label; may be blank; at most 1,024 characters. |
| `account` | Nonempty account label; at most 1,024 characters. Use consistent names. |
| `amount` | Positive money in; negative money out. Plain signed decimal with no more than two decimal places. No currency symbols, commas, scientific notation, or rounding. |
| `currency` | Three-letter label matching `--currency`; case is normalized. Currency labels are not checked against an ISO register. No FX conversion occurs. |

```csv
transaction_id,date,entity,project,account,amount,currency
DEMO-001,2026-01-01,Example Ltd,Project Cedar,Operating,1000.00,USD
DEMO-002,2026-01-02,Example Ltd,Project Cedar,Operating,-250.25,USD
```

Entity, project and account values are trimmed and then compared case-sensitively. Control characters in these fields or IDs are rejected. The two-decimal convention must fit the dataset; currencies or unit prices requiring more precision need a different schema. The maximum magnitude of one transaction is **9,999,999,999,999.99 currency units**. Group sums use exact Python integer arithmetic and can exceed the individual-transaction limit without becoming floating-point values.

The first **valid** occurrence of an ID is accepted. Later occurrences are rejected even when other fields differ. An invalid row does not reserve its ID. This policy detects an identifier conflict; it does not prove that one of two business transactions should be deleted.

## What the reports mean

- `records_read = accepted_rows + rejected_rows` is checked before the import commits.
- Accepted database row counts, grouped row counts and input acceptance counts must agree.
- Exact accepted-row sums, grouped sums and `cash_in − cash_out` must agree.
- `sha256` hashes the bytes consumed by the parser. Source size and modification time are checked again after reading; a changed source aborts the import. Work from a stable exported file.
- `errors` contains at most 100 examples by default; `rejected_rows` counts **all** rejected records. `--errors` streams the full rejected-row report from disk.
- `totals` contains at most 1,000 groups by default. `group_count` and `totals_truncated` make that limit visible. `--totals` streams **every** group.
- `status=complete_with_rejections` means the file finished reading but some records were excluded. Resolve those exceptions before relying on its financial totals.

`max_errors` in the Python API now controls the error **sample size**, replacing the older prototype's early-abort behavior. Error samples and group previews each have a hard maximum of 10,000. The full disk exports remain available.

The retained database includes `transactions`, `totals`, `rejected` and `metadata`. It contains the imported records and should be handled as financial data. Without `--database`, this temporary database is removed at the end of the call. CSV text fields with spreadsheet-formula prefixes are apostrophe-prefixed on export; numeric amount columns preserve their signs.

## A measured million-row run

This is a reproducible synthetic test, not a statement that every million-row file will take the same time or that the software satisfies enterprise operating requirements.

```sh
python -m financial_intelligence.benchmark --rows 1000000
```

Recorded **19 November 2026, 01:22:39 Pakistan time** (`2026-11-18T20:22:39+00:00`). The generator uses unique IDs, one currency, 50 entity labels, 20 project labels, eight account labels and deterministic amounts. It deletes its temporary source and database when finished.

| Measurement | Observed result |
| --- | ---: |
| Input records | 1,000,000 |
| Accepted / rejected | 1,000,000 / 0 |
| Distinct aggregation groups | 8,000 |
| Groups retained in returned preview | 10 |
| Source CSV bytes | 69,400,209 |
| SQLite database bytes | 84,111,360 |
| Data generation | 3.408 seconds |
| Ingestion, validation, aggregation and control checks | 15.962 seconds |
| Throughput for this run | 62,649.4 records/second |
| Whole-process peak resident memory | 22.88 MiB |
| Expected / actual net movement | −4,987.75 / −4,987.75 USD |
| Runtime | Python 3.12.14; SQLite 3.53.1; Linux x86_64 |

The expected net is independently derived from the generator's arithmetic sequence. Each complete 20,001-row cycle sums to zero cents. For 1,000,000 rows, the remainder is 19,951; its total is `19,951 × 19,950 ÷ 2 − 10,000 × 19,951 = −498,775 cents = −4,987.75`.

Source SHA-256:

```text
7912f0b2f7035966ac1bb78b76a014c491a7e250ffec0658c4274236a03c4ac2
```

The memory figure is the process peak, including generation. The database cache setting is a suggestion to SQLite, not an enforced process memory ceiling. This single run does not establish concurrent-user capacity, recovery guarantees, the largest supported dataset, or suitability for a particular company size. Transaction count, field lengths, group count, rejected-row count, disk speed and available temporary storage all affect resource use.

## Verification and implementation references

```sh
python -m pytest financial_intelligence/test_enterprise.py -q
```

The ingestion suite checks exact cents, totals beyond SQLite's signed-integer range, duplicate IDs, mixed currencies, dates and field validation, malformed CSV/UTF-8, output preservation, retained metadata, bounded previews, full exports and spreadsheet-formula text. It executes the shipped engine.

Implementation choices are based on the primary documentation below; accounting outcomes are still limited to the explicit checks described above.

- [Python `sqlite3`: parameter binding, transactions and connection lifecycle](https://docs.python.org/3/library/sqlite3.html). User data is bound through placeholders and connections are explicitly closed.
- [SQLite aggregate functions](https://www.sqlite.org/lang_aggfunc.html). Native integer `sum()` can overflow, and floating-point `total()` is approximate. This engine stores grouped minor-unit sums as text and uses Python integers for the arithmetic.
- [SQLite PRAGMA reference](https://www.sqlite.org/pragma.html). This implementation uses an 8 MiB suggested page cache, file-backed temporary storage, rollback journaling and `synchronous=FULL`.

This release is a local analysis tool. Shared-host authentication, access roles, encrypted databases, disaster-recovery procedures, general-ledger posting and an approval audit trail are not implemented.
