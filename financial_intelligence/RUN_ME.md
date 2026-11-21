# Run APEX Finance Lab

**U.S. bank analysis.** Open [the bank model](https://ehtisham514.github.io/apex-reconciliation-toolkit/financial_intelligence/bank-lab/) in a browser or run `python financial_intelligence/integrated_model.py bank --output-dir bank-results` from the repository root (Node.js 18+). [Sources and results](bank-lab/README.md).

## 1. Download and install

Download the repository ZIP and extract it, or clone the repository. Open a terminal in its top-level folder. Use Python **3.11+**.

```sh
python -m venv .venv
```

Activate the environment:

```sh
# macOS / Linux
source .venv/bin/activate
```

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Then install and run:

```sh
python -m pip install -r financial_intelligence/requirements-dashboard.txt
python -m streamlit run financial_intelligence/dashboard.py
```

Open the local URL printed by Streamlit. Keep the terminal running while you use the dashboard. Press Ctrl+C in the terminal to stop it.

## 2. Choose a workspace

- **Construction bid:** add estimate lines and price a target-margin bid.
- **Project forecast:** enter incurred costs and remaining commitments to forecast final profitability.
- **13-week cash:** edit each week's receipts and payments to inspect cash shortfalls.
- **Annual projection:** change revenue growth, costs, capex and working-capital assumptions.
- **DCF valuation:** inspect value and sensitivity to the discount rate and terminal growth.
- **Acquisition screening:** compare price, financing, synergies and integration contribution.
- **Ledger data:** try `financial_intelligence/sample_ledger.csv`, then prepare your own data using the displayed schema.

Amounts are plain numbers without currency symbols or thousands separators. Percent controls are labelled in percent; rate columns in editable tables use decimal rates, for example `0.05` means 5%. Keep every amount in one currency and unit scale. The reporting-currency selector changes labels only.

Every default is fictional. Review the [model assumptions](README.md) before applying your data. Download JSON to preserve results with assumptions, or CSV for the calculation tables. Ledger reports download as JSON; use the CLI for large files and complete CSV exports.

## 3. Validate the calculations

```sh
python -m pytest financial_intelligence -q
```

The model suite includes hand-calculated control examples and scale checks. The dashboard suite uses Streamlit AppTest. Passing these tests does not establish suitability for every accounting policy, tax jurisdiction or transaction.

## Troubleshooting

| Issue | Action |
|---|---|
| `streamlit` or `pytest` cannot be found | Activate the environment and install the requirements. Prefer the `python -m ...` commands above. |
| Python version is unsupported | Use Python 3.11 or newer. |
| A numeric input is rejected | Remove separators/symbols and provide a finite number. Follow the sign convention shown for the workspace. |
| DCF discount rate must exceed growth | Review the assumptions; the perpetual-growth formula is undefined or unsuitable when rate ≤ growth. |
| CSV rows are rejected | Inspect the import report. Dates, unique transaction IDs, currency and two-decimal amounts must match the schema. |
| The ledger group preview is truncated | Use the CLI to export all groups and rejected rows. |
| A very large upload is slow | Use the local-file command-line engine. Browser upload itself retains the source in memory. |

## Data handling

Run locally or in a deployment you control. The ledger upload is written to a temporary folder during analysis and removed when the request finishes. The dashboard is not a multiuser accounting system: it does not provide user accounts, role permissions, ERP posting or a durable approval audit trail. Browser/client software and downloaded reports remain outside the application's control.


## Run the integrated three-statement model

Use the blank actuals and assumptions templates, then follow [the model guide](INTEGRATED_MODEL.md). The model has no sample business data.

    python financial_intelligence/integrated_model.py --actuals financial_intelligence/integrated_model_actuals.template.json --assumptions financial_intelligence/integrated_model_assumptions.template.csv --output-dir output/integrated-model

