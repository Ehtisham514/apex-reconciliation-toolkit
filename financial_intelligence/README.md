# APEX Finance Lab

Practical planning models for construction contractors, business owners and accounting teams. Use the local dashboard to change assumptions and download results, or call the Python functions from your own workflow.

**Available now:** construction bidding, project cost-to-complete, earned-value checks, a 13-week cash plan, annual operating and cash-flow projections, an integrated three-statement planning model, DCF sensitivity, acquisition screening, and validated ledger aggregation. Existing dashboard examples use fictional assumptions. The integrated model starts with blank actuals and assumption templates.

[Run the dashboard](RUN_ME.md) · [Integrated model guide](INTEGRATED_MODEL.md) · [Integrated model code](integrated_model.py) · [Calculation code](models.py) · [Model tests](test_models.py) · [Dashboard tests](test_dashboard.py) · [Ledger engine](enterprise.py)

## Choose your question

| Question | Workspace / function | What you receive |
|---|---|---|
| What should we quote? | Construction bid / `construction_estimate` | Materials, total labor, waste, overhead, contingency and target-margin price |
| What will the project cost to finish? | Project forecast / `cost_to_complete` | Remaining commitments, uncommitted costs, contingency, EAC and forecast margin |
| Are we earning value efficiently? | Project forecast / `earned_value` | CV, SV, CPI, SPI, EAC, ETC and VAC |
| When could cash become tight? | 13-week cash / `cash_forecast` | A variable weekly schedule, minimum-reserve shortfalls and closing cash |
| How does growth affect cash generation? | Annual projection / `annual_projection` | Revenue, costs, EBITDA, EBIT, cash tax, working capital, capex and FCFF |
| How do operating assumptions flow through all three statements? | [Integrated model](INTEGRATED_MODEL.md) / integrated_model.py | Five-year scenario outputs, linked balance sheet and cash flow, debt schedules and control checks |
| How sensitive is value to assumptions? | DCF valuation / `dcf`, `dcf_sensitivity` | Enterprise value, net-debt bridge, terminal-value contribution and rate/growth grid |
| How does an acquisition affect contribution? | Acquisition screening / `acquisition_case` | EBITDA-based price proxy, new debt/equity funding, interest, synergies and integration costs |
| Is my ledger import complete? | Ledger data / `aggregate_csv` | Accepted/rejected row controls, exact totals, grouped preview and source hash |

## Start locally

Use Python **3.11 or newer** for the dashboard. The model calculations themselves use only Python's standard library. The dashboard dependencies are pinned to the versions used for verification.

```sh
python -m pip install -r financial_intelligence/requirements-dashboard.txt
python -m streamlit run financial_intelligence/dashboard.py
```

Open the local URL printed by Streamlit. Model inputs are entered as plain numbers without thousands separators. A reporting currency label applies to the entire analysis; it does not convert data.

### Example: estimate a bid

```python
from financial_intelligence.models import ConstructionLine, construction_estimate

result = construction_estimate(
    [ConstructionLine(quantity="10", unit_cost="100")],
    overhead_rate="0.10",
    contingency_rate="0.05",
    margin="0.20",
)
print(result["total_cost"])  # 1150.00
print(result["bid_price"])   # 1437.50
```

This example uses 1,000 of direct cost + 100 overhead + 50 contingency. The price is 1,150 ÷ (1 − 20%) = **1,437.50**. Both percentages apply to direct cost. Do not count indirect costs in the line items and again in overhead.

### Example: operating projection feeding valuation

```python
from financial_intelligence.models import annual_projection, dcf

forecast = annual_projection(
    base_revenue="1000000",
    growth_rates=["0.10", "0.08", "0.06", "0.04", "0.03"],
    gross_margin="0.40",
    operating_cost_rate="0.20",
    depreciation_rate="0.02",
    capex_rate="0.03",
    working_capital_rate="0.12",
    tax_rate="0.25",
)
value = dcf(
    [row["free_cash_flow"] for row in forecast],
    discount_rate="0.12",
    terminal_growth="0.03",
    net_debt="200000",
)
print(value["enterprise_value"])
print(value["equity_value"])
```

All rates and amounts above are fictional illustrations, not recommended assumptions.

## How the calculations work

### Construction and earned value

For an estimate line, material cost is `quantity × unit cost × (1 + waste rate)`. Labor cost is `total labor hours × hourly rate`. Waste is not applied to labor. The return key `gross_profit` is the bid less all included modeled costs, including selected overhead/contingency; it is not a prescribed financial-statement gross-profit classification.

The bottom-up project forecast uses:

- Approved revenue = original contract + approved signed change orders.
- ETC = remaining unincurred committed cost + remaining uncommitted cost + contingency on those remaining costs.
- EAC = actual incurred cost + ETC.
- Forecast margin = (approved revenue − EAC) ÷ approved revenue; undefined for zero revenue.

**Avoid double counting:** use only the unincurred remainder of commitments. Pending change orders are excluded until approved. Retention, revenue recognition, billing schedules and collection timing are not implemented by this calculation.

Earned-value formulas follow the [NASA EVM reference card](https://www.nasa.gov/wp-content/uploads/2018/06/nasa-evm-reference-card.pdf): CV = EV − AC; SV = EV − PV; CPI = EV / AC; SPI = EV / PV; EAC = BAC / CPI; ETC = EAC − AC; VAC = BAC − EAC. The model requires cumulative PV, EV and AC for the same scope and date; PV/EV cannot exceed BAC. Undefined startup ratios return `None`. EAC assumes current cost efficiency continues. SPI is not a predicted finish date. The [NASA tutorial](https://www.nasa.gov/ocfo/ppc-corner/evm/tutorial/) explains the underlying planned/earned/actual distinction.

### Cash and operating forecast

Weekly closing cash is `opening cash + receipts − payments`. Receipts and payments are entered as nonnegative magnitudes. A funding gap is `max(minimum cash − closing cash, 0)`. It is a point-in-time shortfall, **not** a borrowing drawdown and **not** a number to sum across weeks. No financing is automatically injected.

The annual projection is a transparent operating scenario. Revenue compounds using each year's growth rate; gross margin, operating expenses, depreciation, capex and operating working capital are driven by revenue. Opening working capital defaults to base-year revenue × working-capital rate, or you can supply the actual opening balance.

`FCFF = EBIT − cash tax + depreciation − capex − change in operating working capital`.

Tax is charged only on positive EBIT in the annual projection. Loss refunds, tax-loss carryforwards, jurisdictional adjustments and interest tax shields are not modeled. This is **not** an integrated income statement, balance sheet and cash-flow statement. It produces unlevered operating cash flows for planning and DCF inputs, not a financed bank-cash balance.

### DCF and acquisition screen

DCF uses a Gordon-growth terminal value: `final forecast FCFF × (1 + terminal growth) ÷ (discount rate − terminal growth)`. Discount rate must exceed terminal growth. Use FCFF with a matching cost of capital, as explained in [Aswath Damodaran's valuation material](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/lectures/val.html). Review sustainable growth and normalized terminal cash flow using his [terminal value discussion](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/valquestions/termvalapproaches.htm).

The default timing is explicit: forecast flows are at years 1 through N and terminal value is at year N. `midyear=True` moves explicit forecast flows to 0.5 through N−0.5, while terminal value stays at N. Only an explicit `terminal_timing="midyear"` also discounts terminal value at N−0.5; this assumes continuing cash flows use the midyear convention too. The dashboard uses year-end terminal value and labels the sensitivity grid as year-end. Negative cash-flow inputs are allowed, but a nonpositive final flow can make a perpetuity unsuitable; the dashboard flags it for review.

Equity value = enterprise value − net debt, where net debt means debt less excess cash. Other claims and adjustments require separate work. The sensitivity grid retains invalid rate/growth combinations as labelled empty cells instead of hiding them.

The acquisition screen treats EBITDA × purchase multiple as an **enterprise purchase-price proxy**. It subtracts new acquisition financing to show a simplified equity-funding amount. Target net debt/cash, fees, purchase accounting, debt amortization and working-capital adjustments are excluded. Its first-year contribution is EBITDA + EBITDA synergies − interest − integration cost. A simple tax charge is applied only to positive contribution. **This is not GAAP/IFRS net income, EPS accretion/dilution, a leveraged buyout model or a complete M&A valuation.**

## Ledger data and capacity

Ledger aggregation uses a separate disk-backed engine; read [the implementation](enterprise.py) for its input controls and local CLI options. The dashboard accepts CSV for convenience, but the browser upload holds that file in memory. Use local-file CLI ingestion for large datasets and full group/rejection exports. A truncated preview is explicitly identified.

The calculations are currency-neutral and the tests check that scaling annual revenue from **1,000 to 1,000,000,000** scales cash flow and value consistently. That verifies arithmetic behavior, **not** suitability for every billion-dollar business or unlimited data capacity. Such organizations may require audited models, integrations, access control and governance beyond this local toolkit.

## Validation

```sh
python -m pytest financial_intelligence/test_models.py financial_intelligence/test_dashboard.py -q
```

The model tests cover margin versus markup, construction scope, non-finite input rejection, cash continuity, negative cash and loss scenarios, EVM startup metrics, working-capital changes, terminal timing, sensitivity invalid cells, acquisition financing and the 1,000-to-1-billion scale check. AppTest executes all eight dashboard workspaces and verifies changed cash inputs and invalid DCF/non-finite inputs. [Streamlit documents AppTest here](https://docs.streamlit.io/develop/concepts/app-testing).

Results and assumptions can be downloaded as JSON; calculation outputs also have CSV exports. No client data is bundled. Run privately with your own data. Uploaded files are temporarily stored by the local process while being analyzed; there is no application account, multiuser authorization or external accounting-system integration.
