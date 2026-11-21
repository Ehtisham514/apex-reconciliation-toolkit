# APEX Accounting & Finance Hub

![APEX Accounting & Finance Hub — practical tools for better financial decisions](assets/apex-banner.svg)

**Reconcile transactions. Plan cash. Review project costs. Evaluate financial scenarios.**

A practical, open-source workspace for accountants, business owners and finance teams, maintained by **Ehtisham Ul Haq / APEX Accounting & Solutions**. It brings the original APEX reconciliation tool together with accounting workbooks, browser utilities, financial models and documented review workflows.

[**Analyze the four U.S. banks**](https://ehtisham514.github.io/apex-reconciliation-toolkit/financial_intelligence/bank-lab/) · [**Open the live hub**](https://ehtisham514.github.io/apex-reconciliation-toolkit/) · [Start here](docs/START_HERE.md) · [Tool catalog](docs/TOOL_CATALOG.md) · [Templates](templates/README.md) · [Timesheet review](tools/timesheet-review.html) · [Close board](tools/close-board.html) · [Financial models](financial_intelligence/README.md) · [Integrated three-statement model](financial_intelligence/INTEGRATED_MODEL.md) · [Data engine](docs/DATA_ENGINE.md) · [Worked examples](docs/CASE_STUDIES.md)

**Release: v0.2.0 — public beta.** Tools support preparation, analysis and review. They do not post entries to accounting software or provide an audit opinion. The bank model uses public SEC filings. Training examples elsewhere in the hub use fictional figures.

**Rental property owners** · [Try the Excel cash reconciliation workbook](templates/rental-property/README.md). Follow a mortgage payment before rent arrives and trace a missing $300 reserve deposit in the fictional example.

## Choose your starting point

| You are… | Start with | What you can produce |
|---|---|---|
| A business owner | [Cash planning and management reporting](docs/WORKFLOWS.md) | A weekly cash plan, open-invoice review and a consistent management pack |
| A bookkeeper or accountant | [Month-end workflow](docs/START_HERE.md) | Reconciliation exceptions, close checklists and documented follow-up |
| A property or multi-entity finance team | [Accounting Workbench](https://ehtisham514.github.io/apex-reconciliation-toolkit/tools/accounting-workbench.html) · [Input guide](docs/WORKBENCH.md) | Receivables/payables aging, intercompany transfer review and trust-balance comparisons |
| A construction business | [Construction models](financial_intelligence/README.md) | Quantity-based estimates, target-margin bids and cost-to-complete scenarios |
| A financial analyst | [Finance Intelligence Lab](financial_intelligence/RUN_ME.md) | Driver-based projections, DCF sensitivities and acquisition screening |
| A team with large CSV files | [Disk-backed data engine](docs/DATA_ENGINE.md) | Validated ledger imports, duplicate review, control totals and grouped exports |

## Open the hub

1. [**Open the live Accounting & Finance Hub**](https://ehtisham514.github.io/apex-reconciliation-toolkit/).
2. Choose the [bank reconciliation tool](https://ehtisham514.github.io/apex-reconciliation-toolkit/apex-reconcile.html) or [accounting workbench](https://ehtisham514.github.io/apex-reconciliation-toolkit/tools/accounting-workbench.html).
3. Try a built-in fictional example, then follow the input guide for your own review.

The browser tools run their calculations in your browser without installation. The Python dashboard has a separate local setup below.

### Use the browser tools offline

1. Select **Code → Download ZIP** on GitHub and extract the folder.
2. Open **`index.html`** for the organized tool and template directory.
3. Open **`apex-reconcile.html`** or **`tools/accounting-workbench.html`** to use the browser tools. Start with their fictional examples.

The downloaded HTML files also run directly from your computer. GitHub's file viewer shows HTML source; use the live links above or open the downloaded files in a browser.

## Available tools

| Tool | Available now | How to use it |
|---|---|---|
| Bank ↔ ledger reconciliation | Exact-cents comparisons, account/currency separation, suggested pairs, duplicates and exceptions | [Open reconciliation tool](https://ehtisham514.github.io/apex-reconciliation-toolkit/apex-reconcile.html) · [Rules and CSV schema](docs/RECONCILIATION.md) |
| AR/AP aging | Due-date buckets, open balances and separate entity/currency totals | [Accounting Workbench](https://ehtisham514.github.io/apex-reconciliation-toolkit/tools/accounting-workbench.html) · [Input guide](docs/WORKBENCH.md) |
| Intercompany transfer review | Reciprocal entity/ref/currency checks, exact opposite amounts, exceptions for ambiguity | [Accounting Workbench](https://ehtisham514.github.io/apex-reconciliation-toolkit/tools/accounting-workbench.html) · [Input guide](docs/WORKBENCH.md) |
| Trust-balance comparison | Adjusted statement, book and client-liability balances with explicit differences | [Accounting Workbench](https://ehtisham514.github.io/apex-reconciliation-toolkit/tools/accounting-workbench.html) · [Input guide](docs/WORKBENCH.md) |
| Timesheet duplicate review | De-duplicates exact shifts across sources, flags partial overlaps and summarizes hours and gross USD earnings | [Open tool](https://ehtisham514.github.io/apex-reconciliation-toolkit/tools/timesheet-review.html) · [CSV template](templates/timesheet_entries.csv) · [Guide](docs/TIMESHEET_REVIEW.md) |
| Month-end close board | Tracks tasks by entity and period with owners, due dates, review statuses and evidence references | [Open tool](https://ehtisham514.github.io/apex-reconciliation-toolkit/tools/close-board.html) · [Blank checklist](templates/month_end_close_board.csv) · [Guide](docs/CLOSE_BOARD.md) |
| Construction analysis | Materials/labor/waste estimates, overhead, contingency, gross-margin bids, earned value and cost to complete | [Models and assumptions](financial_intelligence/README.md) |
| Cash forecasting | Editable weekly receipts/payments and funding-gap estimates | [Local dashboard](financial_intelligence/RUN_ME.md) |
| Integrated three-statement model | Five-year base, downside and upside projections linking P&L, balance sheet, cash flow and debt | [Model guide and blank inputs](financial_intelligence/INTEGRATED_MODEL.md) |
| Business projection and DCF | Annual driver assumptions, unlevered cash flow and valuation sensitivity | [Finance models](financial_intelligence/README.md) |
| Acquisition screening | Purchase multiple, financing, synergies and integration-cost contribution | [Finance models](financial_intelligence/README.md) |
| Large-file ledger analysis | Disk-backed deduplication, exact minor units, input validation and controlled exports | [Data engine and benchmark](docs/DATA_ENGINE.md) |

The acquisition screen is not an integrated merger, purchase-price-allocation or EPS accretion/dilution model. The intercompany tool reviews transfer pairs; it does not perform consolidated financial statements or elimination journals. The trust tool checks arithmetic and does not certify a legally compliant trust account.

## Templates you can adapt

[Browse the template library](templates/README.md) for month-end close, chart-of-accounts mapping, AR/AP open items, weekly cash planning, construction estimates, change orders, intercompany transfers, trust-balance schedules, M&A due diligence, deal assumptions and a management-report outline.

CSV files open in spreadsheet applications. They are plain inputs and registers unless explicitly identified as a tool import; they are not formula-driven Excel workbooks. Each template has field definitions and a stated purpose. Replace fictional rows before use.

## Run the financial dashboard

Use Python **3.11 or newer** from the repository root:

```sh
python -m pip install -r financial_intelligence/requirements-dashboard.txt
python -m streamlit run financial_intelligence/dashboard.py
```

The calculation and ledger-ingestion modules use the Python standard library; Streamlit is required only for the dashboard. Detailed commands and input conventions are in [RUN_ME.md](financial_intelligence/RUN_ME.md).

## Data size, money and review controls

The browser tools are for smaller reviews: **5,000 rows and 3 MiB per imported file**, with two decimal places. The Python engine uses disk-backed storage for larger files. The [reproducible benchmark](docs/DATA_ENGINE.md) records the environment, measured processing time, memory and control totals for a synthetic **1,000,000-row** input. A synthetic benchmark is not a service-level guarantee or evidence of deployment at an enterprise.

Monetary calculations use integer minor units or Python Decimal. Inputs must follow each tool's currency, unit and sign conventions. Results remain subject to source completeness, review of exceptions and the assumptions you select. See [accounting policies and scope](docs/ACCOUNTING_POLICIES.md).

## Verification and maintenance

```sh
node --test tests/*.test.cjs
python -m pytest financial_intelligence -q
python scripts/check_repository.py
```

[GitHub Actions](https://github.com/Ehtisham514/apex-reconciliation-toolkit/actions) runs the checks on changes. Browser tests execute the calculation code shipped inside the HTML files. Python tests cover the models, ingestion and Streamlit workspaces. [VALIDATION.md](docs/VALIDATION.md) records the verified release results and their limits.

Report reproducible bugs through [GitHub Issues](https://github.com/Ehtisham514/apex-reconciliation-toolkit/issues). Use fictional, minimized examples. For changes, see [CONTRIBUTING.md](CONTRIBUTING.md), [the changelog](CHANGELOG.md) and [the roadmap](docs/ROADMAP.md).

## Work with Ehtisham

For a property bookkeeping engagement, [view my rental reconciliation project on Upwork](https://www.upwork.com/freelancers/~019db478acf3ff1bda?p=2123159662781452288) or [see my bookkeeping services on Fiverr](https://www.fiverr.com/ehtisham_425).

## About this project

This is an accounting resource hub and a portfolio of practical tools. It is not a hosted ERP, accounting practice management system, bank connection, payroll/tax filing service or audited valuation service. Integrations with QuickBooks, Xero, Buildium and other platforms are not implemented. Professional requirements depend on your engagement and jurisdiction.

The implementation was developed with AI assistance and is published for transparent testing and improvement. No independent audit or third-party certification of the software is claimed. Licensed under [MIT](LICENSE).
