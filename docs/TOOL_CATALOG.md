# Tool catalog

Use this catalog to choose the right component and understand its output. A component being available here does not imply an independent audit, a regulatory certification or suitability for every business.

| Component | What it does | Runs where | Material boundary |
|---|---|---|---|
| [Bank financial analysis](../financial_intelligence/bank-lab/README.md) | Four-bank statements, funding forecasts, capital stress, equity valuation and merger screens. | Offline browser or Node.js | Public U.S. holding-company data and illustrative assumptions. |
| [Reconciliation tool](../apex-reconcile.html) | Compares bank and ledger transactions, suggests unambiguous pairs and exports exceptions. | Local browser | Exact rule-based suggestions; no journal posting. Account/currency isolation and documented row limits apply. |
| [Accounting workbench](../tools/accounting-workbench.html) | Checks trust balance arithmetic, ages invoices and reviews reciprocal intercompany transfer pairs. | Local browser | Does not perform full trust compliance, assess collectability, or post eliminations. |
| [Construction models](../financial_intelligence/README.md) | Builds direct cost, overhead, contingency and target-margin pricing, with project-performance calculations. | Local Python / Streamlit | Needs complete scope, units, quotations and reviewed assumptions. No local construction-cost database or certified estimate class. |
| [Cash forecasts](../financial_intelligence/README.md) | Rolls opening cash through receipts and payments and shows gaps below a minimum cash balance. | Local Python / Streamlit | Receipt/payment timing is supplied by the user. A funding gap is not committed financing. |
| [Annual operating projection](../financial_intelligence/README.md) | Projects operating drivers and unlevered free cash flow for valuation and scenario review. | Local Python / Streamlit | Not an integrated three-statement model. Drivers and working-capital/capital-spending assumptions need review. |
| [DCF and acquisition models](../financial_intelligence/README.md) | Calculates present values, enterprise-to-equity bridge and a simplified acquisition screen. | Local Python / Streamlit | Does not replace transaction diligence, purchase accounting or a complete integrated merger model. |
| [Ledger data engine](DATA_ENGINE.md) | Validates and aggregates transaction exports, retaining import counts and source identification. | Local command line | Read the exact schema, currency rules, benchmark environment and operating limits before a large import. |
| [Template library](../templates/README.md) | Provides working papers, import examples, checklists and report outlines. | Spreadsheet/text editor | Populated data is fictional. Manual templates do not execute calculations or synchronize with external systems. |
| [Workflow guides](WORKFLOWS.md) | Connects source preparation, calculations, exception review and approval. | Documentation | Suggested operating procedures; adapt to the entity's policies and jurisdiction. |

## Additional browser tools

| Tool | What it does | Guide |
|---|---|---|
| [Timesheet duplicate review](../tools/timesheet-review.html) | Counts exact cross-source duplicates once, flags overlaps and ambiguous repeats, and summarizes hours and gross USD earnings. | [Input format and limits](TIMESHEET_REVIEW.md) |
| [Month-end close board](../tools/close-board.html) | Tracks tasks by entity and period, with owners, due dates, status and evidence references. Data remains in browser local storage. | [Usage and data handling](CLOSE_BOARD.md) |

Both tools start blank and include no employee or business records. The timesheet tool does not calculate overtime or tax; the close board does not store evidence or enforce reviewer permissions.

## Integrated three-statement model

The [integrated planning model](../financial_intelligence/INTEGRATED_MODEL.md) creates five-year base, downside and upside projections for one entity and one reporting currency. It runs locally in Python, requires explicit source and review metadata for assumptions, checks linked statement roll-forwards, and stops rather than plug an unbalanced opening balance sheet. It is a management-planning model, not an institutional or regulatory model.

## How the pieces connect

Keep original exports in the company's private record system. Map them to the selected tool's schema in a working copy. Check row counts, date coverage and totals. Run the calculation. Review the exceptions and retain source references. Any correction belongs in the accounting system after the company's approval process; rerun the check from a fresh export afterward.

The data engine's transaction schema is distinct from the browser reconciliation schema and from the workbench's invoice/transfer schemas. Renaming a column without checking its meaning can reverse signs, omit accounts or double-count balances. Each component's documentation owns its input format.

## Choosing business scale

The amount of a business's revenue is not a processing-capacity measure. Choose a tool using transaction count, file size, number of entities/currencies, the required controls and the nature of the decision. Larger numbers in a calculator do not create enterprise governance. For measured ingestion performance, see [DATA_ENGINE.md](DATA_ENGINE.md); for each browser tool's limits, read its own instructions.

## What is outside this release

Live QuickBooks/Xero/Buildium connections, tax return preparation, payroll filing, automated payment execution, official financial-statement certification, a fully integrated three-statement M&A model, purchase-price allocation, production multi-tenant hosting and full statutory consolidation are outside the current release. The collection can support parts of those workflows through reviewed exports; it does not claim to perform them end to end.
