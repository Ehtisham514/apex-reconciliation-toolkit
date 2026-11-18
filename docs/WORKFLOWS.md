# Accounting workflows

These are suggested operating workflows for the tools in this repository. They are not a universal accounting policy or a replacement for the company's approval procedures. Use the entity's reporting framework, contracts, source records and qualified advisers where those determine the treatment.

## 1. Reconcile bank and ledger transactions

**Inputs:** matching account, currency and reporting period; bank export; ledger export; opening/closing balances retained separately.

1. Preserve original exports and record the extraction dates.
2. Normalize the working copies to the [reconciliation tool](../apex-reconcile.html) schema. Positive amounts represent money in and negative amounts money out on both sides.
3. Confirm counts and transaction totals before matching. Check that an export does not contain a hidden date filter or duplicate download.
4. Run the match and examine suggested pairs, duplicate flags, reference conflicts and unmatched rows.
5. Check source documents before deciding whether an item is a timing difference, a duplicate, a classification issue or an error.
6. Record proposed corrections in a private review log. Obtain the applicable approval and post in the accounting system.
7. Export fresh records and rerun. Tie opening cash plus net activity to closing cash in a separate balance reconciliation.

**Output:** reviewed matches, dated exceptions with owners, and separately supported closing balances. The transaction tool alone does not establish a completed statement balance reconciliation.

## 2. Complete a monthly close

Use the [close checklist](../templates/month_end_close.csv). Adjust the illustrative day offsets and tasks to the business.

- Agree scope, reporting basis, currency and the cutoff date first.
- Collect cash, receivables, payables, payroll, debt, fixed-asset, inventory/project and intercompany support as applicable.
- Reconcile balance-sheet accounts to their schedules and review revenue/cost cutoff using approved policies.
- Track unresolved items with amounts, age, evidence, owner and due date. An incomplete schedule remains incomplete even if the total appears reasonable.
- Review changes from the prior period and budget, then prepare the [management report](../templates/management_report.md).
- Record reviewer decisions and archive the approved version with its source exports and adjustment log.

**Output:** a close package whose figures can be traced to records and whose remaining limitations are visible.

## 3. Review receivables and payables

Use separate [AR](../templates/ar_open_items.csv) and [AP](../templates/ap_open_items.csv) runs in the [accounting workbench](../tools/accounting-workbench.html).

1. Export open invoices and applied payments/credits as of a fixed date.
2. Tie open balances to the ledger control account for each entity and currency.
3. Confirm dates and amounts. A report for an earlier date must exclude later invoices and later payments.
4. Review due-date aging. Investigate disputes, unallocated credits, unapplied cash and items that remain overdue.
5. Add expected receipt/payment dates in a separate cash plan. Due-date aging and cash timing answer different questions.

**Output:** an aging analysis and a prioritized review list. The calculator does not determine collectability, authorize payment or send reminders.

## 4. Review property and trust cash

Use [trust reconciliation](../templates/trust_reconciliation.csv) with [beneficiary detail](../templates/trust_client_balances.csv).

1. Choose one bank account, reporting date and currency.
2. List deposits in transit and outstanding payments individually, with source references and dates.
3. Compare adjusted statement cash with book cash and the total client/beneficiary liabilities.
4. Review individual beneficiary balances, not only the aggregate. Investigate negative balances and amounts without a supported owner.
5. Keep operating-company cash, client funds and restricted funds separately identifiable. Confirm permitted treatment under the applicable agreement and local requirements.
6. Record findings and obtain review before any corrective entries or transfers.

**Output:** an arithmetic comparison plus a supported exception list. Three equal totals alone cannot establish completeness, correct ownership or compliance with trust-account rules.

## 5. Review intercompany funding

Use [intercompany_transfers.csv](../templates/intercompany_transfers.csv) in the workbench.

1. Record each entity's cash side with its counterparty and transfer reference.
2. Compare reciprocal entries using reference, currency, amount and the configured date window.
3. Investigate missing sides, repeated references, bank fees, timing differences and mismatched counterparties.
4. Confirm the underlying purpose: loan, repayment, capital contribution, expense reimbursement or another supported transaction. Matching cash does not determine the accounting classification.
5. Reconcile the resulting intercompany receivable/payable balances independently. Approve any group reporting elimination under the consolidation policy.

**Output:** proposed transfer pairs and unresolved entries with evidence. No automatic journals or consolidation eliminations are produced.

## 6. Price and monitor a construction project

Use [estimate inputs](../templates/construction_estimate.csv), [change orders](../templates/change_orders.csv) and the [Finance Lab](../financial_intelligence/RUN_ME.md).

1. Define scope, quantities, units and exclusions. Date supplier and subcontractor quotations.
2. Build material/labor costs and add the other project costs explicitly. Distinguish waste, overhead, contingency and profit assumptions.
3. Select a target margin and review the implied bid. Do not substitute markup for margin.
4. Separate approved changes from pending proposals. Document the effect on cost, schedule and contract value.
5. Refresh actual cost and cost-to-complete assumptions. Avoid double-counting remaining commitments inside both committed cost and another remaining-cost estimate.
6. Examine a downside case such as price increases, delayed collections or additional hours before making a financing or bid decision.

**Output:** a pricing and project-review calculation with explicit assumptions. The tool does not verify quantities, certify estimates or provide a jurisdiction-specific cost database.

## 7. Screen an acquisition

Use [deal assumptions](../templates/deal_assumptions.csv), [diligence requests](../templates/ma_due_diligence.csv) and the Finance Lab.

1. Define the transaction perimeter, valuation date, currency and purchase-price basis.
2. Obtain support for historical earnings, cash, debt, working capital and proposed adjustments.
3. Build operating and cash-flow assumptions. Label cost savings, implementation costs and timing separately.
4. Select a consistent valuation method. For DCF, document the free-cash-flow basis, discount rate, terminal method and net-debt bridge.
5. Examine sensitivities. A calculated equity value is conditional on the entered assumptions and omitted transaction features.
6. Reconcile financing sources and uses outside the simplified screen when fees, refinancing, cash acquired or other transaction adjustments apply.
7. Resolve material financial, commercial, legal and tax diligence before relying on a deal model.

**Output:** a transparent screening case and a diligence list. The current screen does not calculate a complete purchase-price allocation, GAAP/IFRS merger financials or full EPS accretion/dilution.

## Financial reporting references

The [SEC's introductory financial-statement guide](https://www.sec.gov/about/reports-publications/investorpubsbegfinstmtguide) distinguishes a balance-sheet snapshot from income and cash-flow reporting over a period. It is background reading, not the accounting policy for every entity. The [IFRS Foundation's IAS 7 overview](https://www.ifrs.org/issued-standards/list-of-standards/ias-7-statement-of-cash-flows/) explains the operating, investing and financing categories of cash-flow reporting. The weekly planning template is a management forecast; it does not claim to produce an IAS 7 statement.
