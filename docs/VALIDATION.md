# Release validation — v0.2.0

Checked on **19 November 2026 (Asia/Karachi)**. Results below describe tests that were actually executed on the release files, not a claim of independent audit, production certification or universal accounting compliance.

## Executed checks

| Check | Command | Observed result |
|---|---|---:|
| Original reconciliation engine and input controls | `node --test tests/reconciliation.test.cjs` | 27 passed |
| Accounting workbench shipped core | `node --test tests/workbench.test.cjs` | 26 passed |
| Finance, ingestion and dashboard suite | `python -m pytest financial_intelligence -q` | 93 passed |
| Documentation and CSV structure | `python scripts/check_repository.py` | All local targets and CSV structures checked before publication |

**146 automated behavior checks passed in total:** 27 + 26 + 93. The Python total consists of 34 model/validation checks, 11 Streamlit AppTests and 48 ingestion checks. An installed AnyIO pytest plugin emitted one pytest-10 deprecation warning; it was not a failing test. Execution used Node.js 24.22.3 and Python 3.12.14. GitHub Actions repeats the project commands in its own environment; [view the actual run status](https://github.com/Ehtisham514/apex-reconciliation-toolkit/actions).

## Financial controls covered

- Exact cents, finite inputs, valid dates, duplicates and malformed CSV.
- Reconciliation account/currency isolation, source-row conservation and ambiguous matches.
- AR/AP due-date bucket boundaries, partial payments, future invoices and currency grouping.
- Reciprocal intercompany transfer suggestions and preservation of ambiguous records.
- Independent trust differences, including cases where two differences would otherwise cancel.
- Hand-calculated construction margin, cash, DCF, cost-to-complete and projection cases.
- Consistent model arithmetic at illustrative revenue levels from 1,000 through 1,000,000,000.
- Disk-backed import counts, exact totals beyond SQLite native integer summation, bounded previews, full exports and partial-output cleanup.
- Text protection in spreadsheet CSV exports and no automatic accounting postings.

The scale tests check arithmetic consistency. They do not establish that a business of any particular size has all its reporting or control needs covered.

## Measured data performance

The Python aggregation engine processed a deterministic **1,000,000-row**, **69,400,209-byte** CSV into **8,000 groups**. The observed import/validation/aggregation/control-check time was **15.962 seconds**, and whole-process peak resident memory was **22.88 MiB**. Expected and actual net movement agreed at **−4,987.75 USD**.

See [DATA_ENGINE.md](DATA_ENGINE.md) for the exact command, input hash, independent total calculation, platform and limitations. The machine-readable result is [benchmark-million.json](benchmark-million.json). Timing is one observed run on this environment, not a performance guarantee. The benchmark does **not** apply to browser transaction matching or aging.

## Live desktop smoke checks — 19 November 2026 (Asia/Karachi)

The deployed [public hub](https://ehtisham514.github.io/apex-reconciliation-toolkit/) and its browser tools were manually exercised in a desktop browser. Only built-in fictional examples were used; no real client data was used. These observations supplement the automated release checks above.

| Desktop check | Observed result |
|---|---|
| Public landing page | The hub loaded with the resource directory visible. |
| Resource search | Searching `construction` reduced the displayed count from 9 resources to 2. |
| AR/AP aging demo | 4 loaded rows produced 3 open items and 1 settled item; open balance total USD 4,300, including USD 1,000 past due. |
| Intercompany demo | 6 rows produced 1 suggested pair and 4 unresolved rows. |
| Trust-balance demo | Statement balance 12,500 + deposits in transit 1,000 − outstanding payments 500 = adjusted bank balance 13,000, agreeing with both books and client liabilities. |
| Bank reconciliation demo | 10 bank rows and 10 ledger rows produced 4 suggested pairs, 6 bank exceptions, 6 ledger exceptions and 2 potential duplicate rows. |

This desktop smoke check did not test file uploads, file exports or mobile layouts. It did not visually exercise the separate Python dashboard.

## What remains outside this verification

The Streamlit workspaces were exercised with AppTest; this is programmatic UI testing rather than a visual screenshot review. Browser-tool tests execute the actual embedded core. The landing-page script passed syntax checks and local-link checks. The subsequent desktop browser review is limited to the live smoke checks recorded above; file uploads, file exports and mobile layouts were not exercised in that review.

There was no independent financial audit, multi-user deployment test, penetration test, disaster-recovery exercise, live accounting-system integration, tax-jurisdiction validation or production-client data test. Those functions are not represented as completed capabilities.
