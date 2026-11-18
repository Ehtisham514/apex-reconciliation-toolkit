# Start here

APEX is a collection of accounting tools, financial calculation models and editable working papers maintained by Ehtisham Ul Haq / APEX Accounting & Solutions. Choose a workflow below, then test it with the fictional examples before entering your own data.

## Choose your role

| I am… | Start with | Useful next step |
|---|---|---|
| An accountant or bookkeeper | [Bank-versus-ledger reconciliation](../apex-reconcile.html) and [monthly close checklist](../templates/month_end_close.csv) | Review open items, intercompany transfers and supporting evidence in the [accounting workbench](../tools/accounting-workbench.html). |
| A business owner | [Weekly cash plan](../templates/weekly_cash_plan.csv) and [management report](../templates/management_report.md) | Use the [Finance Lab](../financial_intelligence/RUN_ME.md) to examine cash and pricing assumptions. |
| A property accountant | [Trust balance working paper](../templates/trust_reconciliation.csv) and [beneficiary detail](../templates/trust_client_balances.csv) | Check balances in the workbench and review intercompany funding separately. |
| A construction company | [Estimate inputs](../templates/construction_estimate.csv) and [change-order register](../templates/change_orders.csv) | Compare pricing, contingency and cost-to-complete assumptions in the Finance Lab. |
| A controller or finance team | [Account mapping](../templates/chart_of_accounts_mapping.csv), [close workflow](WORKFLOWS.md) and [policy decisions](ACCOUNTING_POLICIES.md) | Process larger exports with the [ledger data engine](DATA_ENGINE.md), then review exceptions. |
| Evaluating a purchase or sale | [Deal assumptions](../templates/deal_assumptions.csv) and [diligence requests](../templates/ma_due_diligence.csv) | Run the Finance Lab's DCF and acquisition screening models. |

## Open a tool

### Browser tools

Download and extract the repository, then open `index.html` in a modern browser. The hub links to the standalone reconciliation tool and accounting workbench. Their calculations run in the browser. Read each tool's scope and data limits before uploading a file.

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
