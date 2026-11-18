# Worked fictional examples

These examples demonstrate the calculations and review questions. **They are not client engagements, testimonials, business performance claims or independently audited results.** All amounts and parties are fictional.

## 1. Receivables: find the open balance before forecasting receipts

Open [ar_open_items.csv](../templates/ar_open_items.csv) in the accounting workbench and choose `2026-11-19` as the as-of date.

| Invoice | Original | Applied | Open | Due date | Position at the as-of date |
|---|---:|---:|---:|---|---|
| DEMO_AR001 | 1,200.00 | 200.00 | 1,000.00 | 2026-10-01 | 49 days overdue |
| DEMO_AR002 | 2,500.00 | 0.00 | 2,500.00 | 2026-11-19 | Due today |
| DEMO_AR003 | 800.00 | 0.00 | 800.00 | 2026-11-24 | Not yet due |
| DEMO_AR004 | 500.00 | 500.00 | 0.00 | 2026-08-31 | Fully applied |

All amounts are USD for `DEMO_ENTITY`. Total open balance is `4,300.00`, calculated as `1,000 + 2,500 + 800 + 0`. The first invoice belongs in the 31–60 days overdue band. The payment dates in a cash forecast still need separate assumptions; the aging calculation does not predict collection.

## 2. Intercompany: balanced cash and an ambiguous reference

Use [intercompany_transfers.csv](../templates/intercompany_transfers.csv) with a one-day or wider matching window.

- `DEMO_TRANSFER_01`: parent cash out of `1,000` and property cash in of `1,000` on the next day. Reciprocal entities, the same reference and opposite amounts support a suggested pair.
- `DEMO_TRANSFER_02`: parent cash out of `250` without a reciprocal row in the example. Investigate whether the other export is incomplete or the entry has a different reference, date or classification.
- `DEMO_TRANSFER_03`: one outflow of `100` and two inflows of `100` with the same reference. The group is ambiguous. Do not silently choose a receipt or delete a row.

The signed total is `-150 USD`; see the [template control calculation](../templates/README.md). Cash pairing does not determine whether the underlying transaction is a loan, reimbursement or contribution.

## 3. Trust cash: three balances agree, detail still matters

The [trust working paper](../templates/trust_reconciliation.csv) contains:

| Item | USD |
|---|---:|
| Bank statement balance | 12,500.00 |
| Add deposits in transit | 1,000.00 |
| Less outstanding payments | (500.00) |
| Adjusted bank cash | 13,000.00 |
| Book cash | 13,000.00 |
| Beneficiary/client liabilities | 13,000.00 |

Adjusted bank cash is `12,500 + 1,000 - 500 = 13,000`. The two beneficiary balances in [the supporting detail](../templates/trust_client_balances.csv) total `8,000 + 5,000 = 13,000`. Each difference is `0.00`. The next review is the evidence for timing items, completeness of beneficiaries and permitted use of the funds. The arithmetic is one control, not a compliance conclusion.

## 4. Construction: distinguish margin from markup

The three lines in [construction_estimate.csv](../templates/construction_estimate.csv) give a direct cost of `6,213.80 USD`:

- Floor finish: `100 × 25 × 1.05 + 60 × 20 = 3,825.00`.
- Paint: `80 × 12 × 1.03 + 40 × 20 = 1,788.80`.
- Site preparation: `30 × 20 = 600.00`.

For a deliberately simplified cost of `1,000` and a target margin of `20%`, bid price is `1,000 / (1 - 0.20) = 1,250`. Profit is `250`, and `250 / 1,250 = 20%`. Adding a 20% markup instead would give `1,200`, with margin `200 / 1,200 ≈ 16.67%`. The Finance Lab uses target margin; complete the cost scope before relying on the price.

## 5. Acquisition: a transparent first screen

The base column in [deal_assumptions.csv](../templates/deal_assumptions.csv) supplies annual target EBITDA `100,000 USD`, a `5×` multiple, acquisition debt `200,000`, annual interest `10%`, annual synergies `20,000`, and first-year integration cost `10,000`.

| Calculation | USD |
|---|---:|
| Simplified purchase price: 100,000 × 5 | 500,000 |
| Equity funding before other uses: 500,000 − 200,000 | 300,000 |
| Annual interest: 200,000 × 10% | 20,000 |
| Illustrative first-year contribution: 100,000 + 20,000 − 20,000 − 10,000 | 90,000 |

The final figure is a simplified contribution measure. It is not net income, free cash flow, EPS accretion or investment return. Depreciation, amortization, taxes, debt principal, purchase accounting, financing fees and working-capital needs can materially change a complete deal case. Use the [diligence checklist](../templates/ma_due_diligence.csv) to identify what remains to be established.

## Reproduce the examples

Keep the supplied files unchanged and test copies when changing inputs. For the browser tools, compare each exported result to the source file and calculation shown here. For the Python models, follow the documented test and launch commands in [RUN_ME.md](../financial_intelligence/RUN_ME.md). Example control totals are calculated from the checked-in fictional inputs; they are not a claim that every possible real-world case has been validated.
