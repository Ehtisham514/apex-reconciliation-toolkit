# Start here: APEX project directory

Choose the type of work below. **Browser** opens an interactive tool. **Excel** opens a workbook you can copy. **Python** runs a model locally. **Templates** are editable working papers.

<a id="choose-your-role"></a>

| Area | Project | What you get | Open it |
|---|---|---|---|
| Bookkeeping and monthly close | Bank reconciliation | Match bank and ledger records and export items needing review. | [Browser](https://ehtisham514.github.io/apex-reconciliation-toolkit/apex-reconcile.html) |
| Bookkeeping and monthly close | Accounts receivable and payable | Age open invoices and inspect balances by entity and currency. | [Browser workbench](https://ehtisham514.github.io/apex-reconciliation-toolkit/tools/accounting-workbench.html) |
| Bookkeeping and monthly close | Timesheets and gross earnings | Count matching shifts once and flag partial overlaps. | [Browser](https://ehtisham514.github.io/apex-reconciliation-toolkit/tools/timesheet-review.html) |
| Bookkeeping and monthly close | Client questions | Ask the owner about unexplained payments and trace each answer to a reviewed accounting action. | [Question sheet, examples and private review log](../templates/client-questions/README.md) |
| Bookkeeping and monthly close | Close board | Assign owners, track due dates and record evidence references. | [Browser](https://ehtisham514.github.io/apex-reconciliation-toolkit/tools/close-board.html) |
| Property and construction | Rental property cash reconciliation | Follow a mortgage payment, a credit draw and a missing reserve receipt in a fictional close. | [Excel workbook and walkthrough](../templates/rental-property/README.md) |
| Property and construction | Trust and intercompany review | Compare client balances and inspect the two sides of transfers. | [Browser workbench](https://ehtisham514.github.io/apex-reconciliation-toolkit/tools/accounting-workbench.html) |
| Property and construction | Estimating and project control | Build a bid, calculate cost to complete and review project margin. | [Python model guide](../financial_intelligence/README.md#construction-and-earned-value) |
| Forecasting and valuation | 13-week cash forecast | Identify weeks when receipts fall short of payments and the cash reserve. | [Python guide](../financial_intelligence/RUN_ME.md) · [Weekly cash template](../templates/weekly_cash_plan.csv) |
| Forecasting and valuation | Integrated business forecast | Model five years of profit, balance sheet, cash flow and borrowing across three scenarios. | [Python model and inputs](../financial_intelligence/INTEGRATED_MODEL.md) |
| Forecasting and valuation | Operating projection, DCF and acquisition screen | Assess cash generation, valuation sensitivities, financing and synergies. | [Python model guide](../financial_intelligence/README.md#dcf-and-acquisition-screen) · [Diligence template](../templates/ma_due_diligence.csv) |
| Bank analysis | Four-bank financial model | Compare reported statements, model funding needs, stress capital and screen a share exchange. | [Browser](https://ehtisham514.github.io/apex-reconciliation-toolkit/financial_intelligence/bank-lab/) · [Source filings and results](../financial_intelligence/bank-lab/README.md) |
| Data and controls | Ledger data engine | Check import counts, duplicate rows and grouped totals on large transaction exports. | [Python guide and benchmark](DATA_ENGINE.md) |
| Data and controls | Working papers and reporting | Adapt schedules, account mappings, diligence requests and management reports. | [Templates](../templates/README.md) · [Workflow guides](WORKFLOWS.md) |

## Pick a portfolio example

- **For a property owner**, open the [rental workbook](../templates/rental-property/README.md) and follow transfer **TR-102**. The case shows why the books can disagree with the bank even when cash has reached the right account.
- **For a finance analyst**, open [the bank model](https://ehtisham514.github.io/apex-reconciliation-toolkit/financial_intelligence/bank-lab/) and select **Historical checks**. Compare the one-year net interest income forecast with the simpler prior-year benchmark and trace either result to its filings.
- **For a controller**, open the [integrated business forecast](../financial_intelligence/INTEGRATED_MODEL.md) to inspect which assumptions connect profit, debt and cash. The inputs start blank.

[Live hub](https://ehtisham514.github.io/apex-reconciliation-toolkit/) · [Detailed tool catalog](TOOL_CATALOG.md) · [Worked examples](CASE_STUDIES.md)

## Open a tool

### Browser tools

Open the [live hub](https://ehtisham514.github.io/apex-reconciliation-toolkit/), or go directly to [bank reconciliation](https://ehtisham514.github.io/apex-reconciliation-toolkit/apex-reconcile.html) or the [accounting workbench](https://ehtisham514.github.io/apex-reconciliation-toolkit/tools/accounting-workbench.html). Their calculations run in your browser without installation. Read each tool's scope and data limits before selecting a file.

For offline use:

1. Select **Code → Download ZIP** on the [repository page](https://github.com/Ehtisham514/apex-reconciliation-toolkit) and extract the folder.
2. Open `index.html` in a modern browser.
3. Choose a tool from the hub, or open `apex-reconcile.html` or `tools/accounting-workbench.html` directly.

### Python finance models

The Finance Lab needs a local Python environment and its documented dependencies. Follow [RUN_ME.md](../financial_intelligence/RUN_ME.md). GitHub's file viewer does not execute a Python dashboard. The command-line data engine is documented separately in [DATA_ENGINE.md](DATA_ENGINE.md).

### Templates

CSV templates open in spreadsheet editors. Markdown guides and the management report are editable text. The [template directory](../templates/README.md) explains field meanings, sign conventions and the fictional control totals. Templates do not contain automatic integrations or approval workflows.

## A useful first session

1. Open the reconciliation tool and load its built-in fictional sample.
2. Compare the sample result with the expected totals in the [tool documentation](RECONCILIATION.md).
3. Open the workbench and try the receivables, intercompany and trust examples from [templates](../templates/README.md).
4. Save an export locally and check its figures against the example's control totals.
5. Select one real workflow, agree the reporting date and sign convention, and work from private copies of the source exports.

## Know what the result means

A suggested match needs review. A flagged duplicate is not permission to delete a transaction. Equal totals do not establish completeness or correct classification. A projection expresses the entered assumptions; it is not a prediction of what will happen. A DCF or acquisition screen is a calculation aid with documented omissions.

The collection does not replace an accounting system, a complete consolidation platform, legal or tax advice, or regulated trust-account controls. It does not currently provide live bank feeds, production ERP integrations, automatic journal posting, multi-user permissions or enterprise service guarantees. Read the [tool catalog](TOOL_CATALOG.md) for the boundary of each component.

## Improve or adapt it

Use fictional or fully anonymized records in public examples and issues. Report the tool, input schema, expected result and reproducible steps. Keep real financial records, API keys and customer information out of the public repository.
