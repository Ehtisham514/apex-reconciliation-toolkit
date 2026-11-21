# Cash decisions for owners and bookkeepers

[Download the Excel workbook](https://github.com/Ehtisham514/apex-reconciliation-toolkit/raw/refs/heads/main/financial_intelligence/owner-cash/Owner-Cash-and-Handover.xlsx) · [Read the one-page owner example](Owner-Cash-Example.pdf)

Juniper Workshop earned $12,000 in October, yet its cash balance fell from $20,000 to $16,000. The workbook lets an owner follow the difference to the books, then see whether next week’s payments leave enough cash for payroll. Juniper Workshop and its records are fictional. The separate BlackRock worksheet uses public historical figures.

| If you want to… | Start on | What to look for |
|---|---|---|
| Explain why profit and cash differ | Cash report | $12,000 profit + $1,000 noncash adjustments − $4,000 net working-capital use = $9,000 operating cash. Equipment used $8,000 and financing used $5,000. Cash fell $4,000. |
| Reconcile the result | Close inputs | The ending bank statement of $16,500 + $500 in transit − $1,000 outstanding = $16,000. The ledger and the cash bridge each independently close at $16,000. |
| Decide what can be paid this week | Weekly payments | The tightest day is Friday. The base case leaves $4,900 above reserve after all scheduled payments. |
| Stress a late receipt | Week inputs | Change the eligible receipt delay from 0 to 3 days. Friday’s $1,900 low is $3,100 below the $5,000 reserve before that day’s receipt clears. Reset the delay to 0 to restore the example. |
| Take over a set of books | Handover | Assign the 13 requests, collect evidence, and record a reviewer. Open items prevent a ready status. |

## Use your own records

1. Download a private working copy. Replace the blue example cells, including source references and the month’s reporting entity. Use a single entity, currency (USD) and consistent cash perimeter for each run. Keep client evidence and completed workpapers in your private records.
2. On **Close inputs**, use accrual net income, signed operating-balance changes and cash-only investing and financing schedules. Support any “other” amount with an itemized bridge. Account separately for noncash acquisitions, disposals and reclassifications when calculating working-capital changes. Use the reconciled prior closing balance as opening cash. Review both ending differences to the cent.
3. On **Week inputs**, start from the actual bank balance at the beginning of day one. Deduct all restricted or unavailable money included in that balance. Add the operating reserve separately. Include uncleared or overdue payments in the schedule on the date cash may leave, including day one when appropriate. Avoid counting them twice.
4. Enter up to **30** dated receipts and payments for the next seven calendar days. Compare the original-date schedule with independent weekly register totals in rows 46–47. An incomplete row, duplicate ID, mismatched register total or missing review acknowledgment suppresses the planner’s figures. If you have more than 30 items, use documented batch totals with a private itemized register or expand and revalidate the model. To connect the [13-week forecast](../../templates/weekly_cash_plan.csv), compare category totals for the selected week and support each amount with its expected clearing date.
5. On **Weekly payments**, each day’s payments clear before its receipts. Additional cash available equals the lowest pre-receipt balance across the seven days, less the reserve, floored at zero. A separate line reports any shortfall. Confirm expected receipts, restrictions and outstanding obligations before approving a payment.
6. On **Handover**, replace the example roles with named people. Mark an item verified or inapplicable only after recording support or rationale, a due date and a separate reviewer. Retain approvals in the system where access and sign-offs are controlled.

## Historical validation

The **BlackRock filing** tab reproduces the three annual columns of the consolidated cash-flow statement in USD millions. Five checks per year independently rebuild the operating, investing and financing subtotals, net change and closing balance. All 15 differences are zero in the published example. Cash in this statement includes cash equivalents and restricted cash. The annual figures also reflect consolidated sponsored investment products. The weekly planner uses its own opening balance, restrictions and payment dates.

| USD millions | FY 2025 | FY 2024 | FY 2023 |
|---|---:|---:|---:|
| Operating cash flow | 3,927 | 4,956 | 4,165 |
| Investing cash flow | (4,418) | (3,004) | (959) |
| Financing cash flow | (1,127) | 2,236 | (1,992) |
| Currency effect | 329 | (162) | 106 |
| Change in cash | (1,289) | 4,026 | 1,320 |
| Closing cash | 11,490 | 12,779 | 8,753 |

Source: [BlackRock, Inc. FY2025 Form 10-K, Consolidated Statements of Cash Flows, page F-8](https://www.sec.gov/Archives/edgar/data/2012383/000119312526071966/blk-20251231.htm).

## Reproduce the example checks

Download the workbook and [verification script](verify_example.py) to the same folder and run `python verify_example.py` using Python 3. The script reads the saved example, checks the three historical years, recomputes both weekly scenarios and compares the on-time daily balances with the saved Excel results.

The workbook supports analysis and handover. It has no macros, payment execution, bank connection, identity verification or approval enforcement. An institution evaluating production use would need to validate its own data mappings, access controls and operating procedures. The BlackRock case illustrates historical arithmetic. BlackRock’s approval or use of this workbook has not been established.
