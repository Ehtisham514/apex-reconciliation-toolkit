# Decisions to agree before using the tools

This is a configuration guide, not a set of accounting policies that automatically applies to every company. Record the decisions below in the company's approved policy documents and adapt the workflow accordingly.

| Decision | Record explicitly | Why it affects the work |
|---|---|---|
| Reporting basis | Applicable framework, cash/accrual basis, fiscal year and reporting periods | Determines what the financial statements are intended to represent. |
| Entity scope | Legal entities, reporting units, ownership and approved consolidation scope | Prevents unrelated cash or balances from being combined. |
| Currency | Transaction currency, reporting currency and approved FX process | These tools do not silently translate currencies. |
| Source of record | Approved accounting system, bank statement and subledger sources | Establishes what each reconciliation is comparing. |
| Sign convention | Positive/negative amounts and treatment of debit/credit exports | A bank cash-flow sign is not automatically a trial-balance sign. |
| Cutoff | Time zone, reporting date and handling of later entries | Keeps source populations and comparisons consistent. |
| Adjustments | Required evidence, preparer, approver and posting rules | A tool suggestion must not become an unsupported journal. |
| Receivable credits | Applied credits, unapplied cash, disputes and overpayments | The simple aging input accepts nonnegative invoices with paid amounts no greater than invoice amounts. |
| Trust and restricted funds | Beneficiary ownership, permitted uses and applicable local requirements | Equal cash totals do not decide who may use the funds. |
| Intercompany | Agreements, counterparty codes, loan/equity/reimbursement treatment and settlement | Reciprocal cash entries do not establish classification or consolidation treatment. |
| Project costs | Cost codes, committed versus uncommitted costs, allocations and change approvals | Prevents scope omissions and double-counting of remaining costs. |
| Forecasts | Owner, version, scenario, receipt/payment timing and refresh frequency | Makes a forecast reproducible and distinguishes it from actuals. |
| Valuation | Method, date, currency, cash-flow basis and discount/terminal assumptions | Allows users to understand the specific calculation being performed. |
| Review | Reviewer authority, exception escalation and sign-off evidence | The applications do not implement a multi-user approval system. |
| Data handling | Access, retention, backup and public-sharing restrictions | Public GitHub files are not a place to store confidential client records. |

## Common distinctions to preserve

**Profit and cash.** An invoice, a collection and a bank deposit can occur in different periods. Payroll expense may differ from cash paid. Debt principal and owner contributions do not have the same meaning as operating income. The [SEC's financial-statement guide](https://www.sec.gov/about/reports-publications/investorpubsbegfinstmtguide) describes the distinct questions answered by income statements, cash-flow statements and balance sheets.

**Cash-flow classification.** The [IFRS Foundation's IAS 7 overview](https://www.ifrs.org/issued-standards/list-of-standards/ias-7-statement-of-cash-flows/) describes operating, investing and financing categories. Apply the requirements and effective standards relevant to the entity; this repository's templates do not certify a reporting framework or decide jurisdiction-specific classifications.

**Matching and approval.** The tools propose matches from defined rules. A matching date/reference/amount does not prove that a transaction was authorized, properly classified or complete.

**Forecasts and commitments.** A modeled receipt is not guaranteed collection. An assumed funding line is not an executed facility. A pending construction change is not approved contract revenue. Keep the evidence and status visible.

## Suggested private review record

For each adjustment or material assumption, retain a stable reference, source record, entity, currency, period, amount, explanation, preparer, reviewer, decision date and posting/version reference. Record rejected proposals as well as accepted ones. This is a suggested evidence structure; it is not a claim that the current applications provide an immutable audit log.

## When to stop the calculation

Stop and investigate a missing source, unknown currency, inconsistent sign, unresolved duplicate key, contradictory cutoff date or an unsupported amount before treating a result as complete. Missing information should remain visible rather than being converted to zero. Seek the relevant specialist when the result depends on a legal, tax, regulatory or professional judgment outside the tool's calculation scope.
