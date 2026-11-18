# Accounting Workbench

Open [the Accounting Workbench](../tools/accounting-workbench.html) from an extracted copy of this repository in a modern browser with JavaScript BigInt support. It is a single HTML file with its calculation engine and interface embedded. No server or installation is required.

The workbench has three separate tasks. Each starts with a fictional example and produces a CSV report that can be checked against the supplied source rows. Use the [template guide](../templates/README.md) for the associated working papers.

## 1. Receivables and payables aging

Load an open-items CSV and select an as-of date. The required columns are:

```text
id,party,invoice_date,due_date,amount,paid,currency,entity
```

Dates must be valid `YYYY-MM-DD` calendar dates. `amount` and `paid` are nonnegative values with no more than two decimal places, and `paid` cannot exceed `amount`. The outstanding amount is `amount − paid`. Credits and overpayments are deliberately excluded from this schema and require separate working papers.

**The paid amount must already be correct at the selected as-of date.** This schema has no dated payment history, so it cannot rebuild historical aging from a current payment total.

| Bucket | Days after due date at the selected as-of date |
| --- | --- |
| Current | Not yet due, or due on the as-of date |
| 1–30 | 1 through 30 |
| 31–60 | 31 through 60 |
| 61–90 | 61 through 90 |
| 91+ | 91 or more |

Future invoice dates are excluded from the aging totals and retained in the detailed report as `FUTURE_INVOICE_EXCLUDED`. Fully paid items are retained as `SETTLED`. Other included items are marked `OPEN_REVIEW_REQUIRED`.

Totals remain separate by entity and currency. Entity labels are normalized for case and repeated whitespace. No exchange-rate conversion is performed, and the interface does not display a combined monetary total across currencies.

For the fictional receivables template at **19 November 2026**, the expected outstanding balance is **4,300.00 USD**: **3,300.00 Current** and **1,000.00 in 31–60 days**. There are three open items and one settled item. The detailed export preserves every source row, ID, physical line number, source amount, paid amount, inclusion status and bucket.

## 2. Intercompany transfer review

Required columns:

```text
id,date,entity,counterparty,reference,amount,currency
```

A negative amount means cash leaves `entity`; a positive amount means cash arrives at `entity`. Entity and counterparty labels are normalized for case and repeated whitespace. References must agree **exactly after trimming**, including case and punctuation. Currency labels are normalized to uppercase and must agree.

A suggested pair requires all of the following:

1. Exactly two rows share the entity pair, reference and currency.
2. Entity and counterparty are reciprocal; the two entities are different.
3. Amounts are nonzero, exactly equal and opposite.
4. The date difference fits the chosen window of zero through seven days.

Repeated-reference groups with more than two rows stay unresolved as a group. This conservative rule does not greedily choose one of several possible counterparts. Missing references, mismatched amounts, same-entity rows, nonreciprocal labels, zero values and out-of-window dates also require investigation.

Suggested rows are marked `PAIR_REVIEW_REQUIRED`; unresolved rows are marked `EXCEPTION_REVIEW_REQUIRED`. The tool neither posts due-to/due-from entries nor creates consolidation eliminations. Candidate lists are limited to ten IDs per unresolved row, while the full candidate count is shown.

Every source row is preserved exactly once in the all-row export. The control relationship is `2 × suggested pairs + unresolved rows = source rows`. The six-row fictional template produces **one suggested pair and four unresolved rows** at the default three-day window. Its aggregate signed movement is **−150.00 USD**, but the interface keeps entity totals separate; an overall zero would not prove that all transfers are complete.

## 3. Trust balance arithmetic

Enter one entity, trust-account label, date and currency, then supply:

- Statement closing balance.
- Deposits in transit, entered as a nonnegative amount.
- Outstanding payments, entered as a nonnegative amount.
- Book closing balance after reviewed adjustments.
- Total client liability from the client subledger for the same date and account.

The tool calculates:

```text
Adjusted bank = Statement balance + Deposits in transit − Outstanding payments
Bank-versus-books difference = Adjusted bank − Book balance
Books-versus-liability difference = Book balance − Total client liability
```

Agreement requires both differences to equal zero individually. Opposite differences cannot cancel to produce a false agreement. A matching result is labelled `ARITHMETIC_AGREEMENT_REVIEW_REQUIRED`; otherwise the result is `DIFFERENCE_TO_INVESTIGATE`.

The fictional example calculates `12,500 + 1,000 − 500 = 13,000`, compared with books of `13,000` and total client liability of `13,000` USD. Agreement checks arithmetic only. Each outstanding item, each client balance, evidence and cutoff completeness must be reviewed separately. The liability input is supplied by the user; this tool does not independently reconstruct the client subledger or establish jurisdiction-specific trust-account compliance.

## Shared data controls

- UTF-8 CSV, up to **5,000 data rows** and **3 MiB per browser file**.
- Required IDs are nonempty and unique within an imported file.
- At most 64 nonempty, unique header names after case/whitespace normalization.
- Monetary calculations use integer cents with JavaScript BigInt. Up to two decimal places; no rounding of excess precision. Per-input magnitude is limited to `9,999,999,999,999.99`.
- Signed decimal amounts and correctly grouped comma amounts are supported; quote comma-containing CSV fields. Parentheses represent negative amounts.
- Invalid imports fail visibly. There is no silent partial-row import.
- Tables paginate at 50 rows; exports include all report rows.
- Exported user text that could start a spreadsheet formula receives an apostrophe prefix. Numeric money columns retain their numeric signs.
- User values are rendered through `textContent`, with no HTML interpretation.

The workbench contains no external scripts, analytics, network requests or browser-storage writes. Selected CSV files remain in tab memory. **Clear all session data** clears its application state; closing the tab also ends the session. Downloaded reports stay on your device. Browser extensions and operating-system software remain outside the tool's control.

For larger files, use the [disk-backed Python ledger engine](DATA_ENGINE.md). Its aggregation function does not perform these workbench tasks; the million-row benchmark for that engine must not be attributed to browser aging or transfer matching.

## Verification

From the repository root, use Node.js 22 or newer:

```sh
node --test tests/workbench.test.cjs
```

The tests extract the calculation engine from the exact HTML file shipped to users. They cover aging boundaries, historical-snapshot limitations, future exclusions, partial payments, exact large amounts, separate currencies, transfer ambiguity and row conservation, trust differences, input limits and protected CSV exports. The embedded fictional demos are checked against the downloadable templates.

CSV/date/money helpers were adapted from this repository's MIT-licensed reconciliation core. No independent audit or professional certification of the software is claimed.
