# Accounting templates

Editable inputs and working papers for the [APEX Accounting & Finance Hub](../index.html). Every populated company, party, transaction, quote and financial assumption in this folder is **fictional**. Replace the examples before using a file for a business.

These CSV files contain values and headers, not hidden formulas. They can be opened in a spreadsheet editor. Import ID and account-code columns as text so leading zeros are preserved. Dates use `YYYY-MM-DD`, decimal points use `.`, and amount fields omit currency symbols and thousands separators. Keep copies of original source records separately.

## Rental property accounting

[Rental property cash reconciliation in Excel](rental-property/README.md) compares book and bank balances by account and flags unmatched transfers. The workbook includes a worked example and formulas for a monthly close.

## Choose a template

| Task | File | How to use it |
|---|---|---|
| Explain cash to an owner and hand over the books | [Cash report, payment planner and handover](../financial_intelligence/owner-cash/README.md) | Use the fictional owner case or inspect the separate historical check against BlackRock’s filed cash flows. |
| Ask a client about missing transaction details | [Client question pack](client-questions/README.md) | Send one short question per item and track the evidence and accounting decision in your private review log. |
| Organize the monthly close | [month_end_close.csv](month_end_close.csv) | Assign owners and reviewers. Attach evidence references. Replace the illustrative due-day offsets with your calendar. |
| Map accounting exports | [chart_of_accounts_mapping.csv](chart_of_accounts_mapping.csv) | Approve each entity's mapping to a common reporting structure. This is an example, not a universal chart of accounts. |
| Review receivables | [ar_open_items.csv](ar_open_items.csv) | Import into the workbench's aging tool. Enter an explicit reporting date. |
| Review payables | [ap_open_items.csv](ap_open_items.csv) | Use the same aging layout with supplier invoices. Keep AR and AP in separate runs. |
| Plan weekly cash | [weekly_cash_plan.csv](weekly_cash_plan.csv) | Replace 13 weeks of fictional receipts/payments. Roll closing cash into the next week's opening balance in your working model. |
| Prepare a construction estimate | [construction_estimate.csv](construction_estimate.csv) | Collect quantities, costs, hours and quote evidence. Use the Finance Lab or your own reviewed calculation sheet for totals. |
| Track construction changes | [change_orders.csv](change_orders.csv) | Distinguish pending proposals from approved contract changes. |
| Review intercompany transfers | [intercompany_transfers.csv](intercompany_transfers.csv) | Import into the workbench's intercompany tool. Review each proposed pair against both entities' records. |
| Check trust balances | [trust_reconciliation.csv](trust_reconciliation.csv) | Copy one account/date/currency into the workbench's trust balance checker. |
| Support beneficiary balances | [trust_client_balances.csv](trust_client_balances.csv) | Reconcile beneficiary detail to the client-liability total. Do not net unrelated beneficiaries to hide a deficit. |
| Record deal scenarios | [deal_assumptions.csv](deal_assumptions.csv) | Keep base, downside and upside inputs with evidence and reviewer status. These are fictional assumptions, not recommended rates or multiples. |
| Manage M&A diligence requests | [ma_due_diligence.csv](ma_due_diligence.csv) | Adapt the scope with financial, legal and tax advisers. Record findings and unresolved requests. |
| Write a management report | [management_report.md](management_report.md) | Present results, cash, exceptions and decisions with links to supporting schedules. |

The AR/AP and intercompany CSVs are application import formats. Other files are manual templates; their columns are not automatically imported by the Finance Lab or workbench.

## Field definitions and conventions

### Receivable and payable aging

Required headers: `id,party,invoice_date,due_date,amount,paid,currency,entity`.

- `id` is a stable, unique invoice ID for the uploaded file. `party` is the customer or supplier.
- `amount` is the original nonnegative invoice amount. `paid` is the nonnegative amount already applied, including approved credits if the source system reports them that way. `paid` must not exceed `amount`. Record unallocated credits separately rather than turning them into a negative invoice.
- Use no more than two decimal places. Do not combine currencies. The workbench groups by entity/currency.
- `invoice_date` is the date the invoice was issued; `due_date` is the contractual payment date. Investigate invoices with inconsistent dates before import.
- The as-of date determines aging. An invoice dated after that date is outside the reporting population. A future payment must not be included in `paid` for an earlier as-of report.
- The workbench calculates open balance as `amount - paid`. Its aging buckets are due-date based; an invoice due on the as-of date is current, not overdue.

For a fictional as-of date of `2026-11-19`, the AR file has `4,300.00 USD` outstanding: `(1,200 - 200) + 2,500 + 800 + (500 - 500)`. The AP file has `2,500.00 USD`: `(700 - 100) + 1,500 + 400`. These are source control totals, not cash collection forecasts.

### Intercompany transfers

Required headers: `id,date,entity,counterparty,reference,amount,currency`.

- `entity` identifies the entity whose cash entry this row represents; `counterparty` identifies the other entity.
- Positive `amount` means cash into that entity and negative `amount` means cash out. This is a cash sign convention, not a trial-balance debit/credit convention.
- Both sides should use the same transfer reference. Exact opposite amounts, reciprocal entities and the configured date window support a suggested pair.
- Repeated/ambiguous references need investigation. The tool does not select which duplicate to delete or post elimination journals.

The fictional file contains one intended pair for `DEMO_TRANSFER_01`, one unmatched outflow for `DEMO_TRANSFER_02`, and an ambiguous group for `DEMO_TRANSFER_03`. Its signed cash total is `-150.00 USD` because `(−1,000 + 1,000) − 250 + (−100 + 100 + 100) = −150`. A nonzero total prompts investigation; it does not by itself identify the missing or incorrect entry.

### Weekly cash

The week starts on the listed Monday. The first opening cash is a fictional `10,000 USD`; later opening balances are intentionally blank because they must link to the previous week's calculated closing cash. Never fill those blanks with zero merely to complete the table.

For each week: `closing cash = opening cash + customer receipts + other receipts + financing inflows - supplier payments - payroll and taxes - capital spending - debt service - owner distributions`. A funding gap is `max(minimum cash - closing cash, 0)`. Enter receipts and payment categories as nonnegative amounts. Borrowing appears in financing inflows; debt service includes the payment cash amount. Separate principal and interest in supporting debt schedules.

### Construction and changes

`waste_rate` is a decimal: `0.05` means 5%. For each line, direct cost is `quantity × material_unit_cost × (1 + waste_rate) + labor_hours × hourly_rate`. Units must agree with the supplier quote. Record tax, freight, equipment, subcontractors and other omitted scope in additional lines or a documented allowance before setting a bid. Do not assume that the supplied example includes every project cost.

The estimate's fictional direct cost is `6,213.80 USD`: floor finish `3,825.00`, paint `1,788.80`, site preparation `600.00`. Overhead, contingency and target margin are separate pricing assumptions in the Finance Lab. A margin rate is not the same as a markup rate.

In `change_orders.csv`, a blank approved amount means approval has not been recorded. It does not mean an approved zero-price variation. Only use approved changes in an approved contract-value total; show pending changes separately in scenarios.

### Trust balances

Use one bank account, reporting date and currency per check. Inputs are bank statement balance, deposits in transit, outstanding payments, book cash and beneficiary/client liabilities. Timing items require individual supporting records.

The fictional example gives adjusted bank cash of `12,500 + 1,000 - 500 = 13,000 USD`; book cash and beneficiary liabilities are also `13,000`. Beneficiary detail is `8,000 + 5,000 = 13,000`. Arithmetic agreement does not establish that all beneficiaries, restrictions or transactions are recorded correctly. The tool does not implement any jurisdiction's complete trust-account compliance requirements.

### Review fields

`NOT_STARTED`, `IN_PROGRESS`, `BLOCKED`, `READY_FOR_REVIEW`, `APPROVED` and `NOT_APPLICABLE` are suggested workflow statuses, not automated control outcomes. Record the reason for `NOT_APPLICABLE`. A task marked complete should include evidence, completion date and the required reviewer decision under your policy.

## Before sharing a completed file

Remove real bank identifiers, customer details and credentials from anything committed to a public repository. Keep financial records in the company's approved private system. Public examples should remain fictional.


## Blank browser-tool imports

- [Timesheet review CSV](timesheet_entries.csv) — header-only input for combining timekeeping exports. Read [the timesheet review guide](../docs/TIMESHEET_REVIEW.md) before importing.
- [Month-end close board CSV](month_end_close_board.csv) — header-only checklist import. Read [the close board guide](../docs/CLOSE_BOARD.md) for field and local-storage details.

These files contain no employee, client, business, or transaction records. Never commit real payroll or accounting records to a public repository.
