# APEX Reconciliation Toolkit

A small, open-source tool for comparing bank transactions with a bookkeeping ledger. Open **apex-reconcile.html** in your browser, load two CSV files, and review suggested matches and exceptions. No installation, server, account, or subscription is needed to use the HTML tool.

**Status: v0.1.0 — initial prototype.** Use the fictional demo first and independently check results before relying on them.

## Try it

1. Download this repository with **Code → Download ZIP** and extract it.
2. Open `apex-reconcile.html` in a modern browser supporting JavaScript BigInt.
3. Click **Try fictional sample data** to see the workflow.
4. Prepare bank and ledger CSV files using the format below, then load both.
5. Review the suggestions and exceptions. Export the three reports as needed.

The application has no network calls, external scripts, analytics, or browser-storage writes. Selected files are read into the page's memory. **Clear session** removes them from application state; closing the tab ends the session. Downloaded CSV files remain on your device. Browser extensions and other software are outside this application's control.

## What it does

- Suggests one-to-one matches using a unique reference and exact signed amount within a configurable 0–7-day date window.
- Suggests matches with an exact date, signed amount, and normalized description when unambiguous and references do not conflict.
- Holds possible duplicates, repeated references, zero amounts, conflicting references, and reference-linked amount/date differences for review.
- Lists same-amount/date candidates without silently selecting one.
- Separates every account and currency; it never converts currencies or matches between accounts.
- Exports suggested matches, exceptions, and transaction totals, with source row IDs and line numbers.
- Uses integer cents for monetary calculations; it does not use binary floating-point arithmetic for money.

All suggestions are labelled **REVIEW_REQUIRED** in the export. The tool does not approve matches, post adjusting entries, or change source files.

## CSV format

Required columns: `date,description,amount,account,currency`.

Optional columns: `id,reference`. Extra named columns are ignored. Column names are case-insensitive and must be unique. If `id` is omitted or empty, a source/line ID is generated. Nonempty IDs must be unique within each file.

```csv
id,date,description,amount,reference,account,currency
B001,2026-10-01,Client payment,1200.00,RCPT-001,Operating,USD
B002,2026-10-02,Office supplies,-125.50,INV-101,Operating,USD
```

| Field | Rule |
|---|---|
| `date` | Valid calendar date in `YYYY-MM-DD` format. |
| `description` | Nonempty text. |
| `amount` | Positive money in; negative money out on **both** sides. Up to two decimal places; no currency symbol. Comma-grouped values must be quoted. Parentheses indicate negative values. |
| `account` | Same label for the same account in both files. Case and repeated whitespace are normalized. Do not use real account numbers in public examples. |
| `currency` | Three-letter currency code supplied by you; uppercase/lowercase accepted. No exchange-rate conversion or ISO-code lookup is performed. |
| `reference` | Optional transaction reference. Case and whitespace are normalized; punctuation is preserved. |
| `id` | Optional stable ID, unique within its file. |

Use UTF-8, comma-delimited files. Limits: **5,000 transaction rows per file**, **3 MiB per file in the browser**, and **9,999,999,999,999.99 per transaction**. Amounts with more than two decimal places are rejected, not rounded. Currencies requiring three decimal places are not supported.

Convert debit/credit columns to the required sign convention before importing. Align reporting periods and account labels yourself. In CSV exports, text starting with a spreadsheet-formula prefix is prefixed with an apostrophe; numeric amount columns retain their numeric signs.

## Matching policy

1. Identify possible duplicates separately within each file using account, currency, date, signed amount, and reference (or normalized description when reference is blank). Keep all rows and hold them for review.
2. Hold repeated nonblank references within each account/currency group and zero-amount rows.
3. For unique references shared by both files, compare exact amounts and dates. Suggest a pair only when the amounts agree and the date difference fits the chosen window. Otherwise, report the difference.
4. Among remaining unblocked rows, suggest only unique exact date/amount/description pairs. Conflicting nonblank references prevent a suggestion.
5. Preserve every remaining row as an exception. Show up to ten candidate IDs, with the full candidate count, for equal amounts within the date window in the same account/currency. These candidates may themselves have review flags.

No row can be suggested in more than one pair. Equal transaction totals alone do not establish reconciliation.

## Fictional demo: expected results

The two files in `samples/` contain entirely fictional transactions. They are also embedded in the standalone HTML file.

| Result | Expected |
|---|---:|
| Bank rows / ledger rows | 10 / 10 |
| Suggested pairs | 4 |
| Bank exceptions / ledger exceptions | 6 / 6 |
| Potential duplicate rows | 2 |
| Operating USD bank transaction total | 6,579.50 |
| Operating USD ledger transaction total | 7,419.50 |
| Operating USD bank minus ledger | -840.00 |

The remaining totals are Operating EUR `300.00 / 300.00` and Savings USD `300.00 / 0.00`. These are transaction totals, not statement closing balances. The test suite checks the figures against the sample files.

## Tests and development

The application is deliberately contained in one HTML file so it works directly from disk. Edit the marked `reconciliation-core`, `sample-data`, and `application-ui` script blocks in that file. The tests extract and execute the **same core** shipped to users.

Install Node.js 22 or newer to run the tests; no npm packages are required:

```sh
node --test tests/reconciliation.test.cjs
```

Tests cover exact cents, invalid dates/CSV, duplicates, ambiguous matches, sign mismatches, account/currency isolation, source-row conservation, exports, formula-prefix protection, and the sample results. GitHub Actions runs the suite on pushes and pull requests.

## Scope and limitations

This is a transaction comparison aid. It does not implement statement opening/closing balance reconciliation, three-way trust reconciliation, grouped/split settlements, bank feeds, automatic journal entries, or an audit trail of user approvals. An unmatched row is an item to investigate, not proof of an accounting error. A duplicate flag is a review prompt, not proof that a row should be removed. Matching suggestions can be wrong even when the rules agree.

Potential future work: configurable CSV column mapping, reviewer decisions with an exportable log, split-payment review, and opening/closing balance checks. These are ideas, not completed features.

## Contributing and licence

Useful accounting examples, reproducible bugs, accessibility improvements, documentation, and well-tested fixes are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md). Use fictional data in all public submissions.

Maintained by Ehtisham Ul Haq / APEX Accounting & Solutions. The initial implementation was developed with AI assistance. It is published for transparent review and improvement; no independent review is claimed.

MIT licensed. See [LICENSE](LICENSE).
