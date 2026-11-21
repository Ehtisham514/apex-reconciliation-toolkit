# U.S. bank financial analysis

[Open the interactive model](https://ehtisham514.github.io/apex-reconciliation-toolkit/financial_intelligence/bank-lab/) · [Download the standalone HTML](https://raw.githubusercontent.com/Ehtisham514/apex-reconciliation-toolkit/main/financial_intelligence/bank-lab/index.html) · [Run results](results/summary.json)

Compare JPMorgan Chase, Bank of America, Citigroup and Wells Fargo using their public consolidated holding-company statements. Start with **Statements**. Pick a bank and period to see the figures, their source and six independent arithmetic comparisons. **Peer comparison** puts the four banks side by side. The single HTML file also works when downloaded and opened offline. It has no external scripts, uploads, credentials or market-data connection.

## Try one decision

Open **Bank forecast**, select **JPMorgan Chase / FY 2025**, and change deposit growth. Each forecast year shows net loans, deposits, net interest income, earnings, and the additional wholesale funding needed to balance. The export includes assumptions alongside the outputs. **Valuation & stress** reprices funding and credit costs, stresses capital, and compares two common-equity valuation methods. **Merger screen** lets you change the target, exchange ratio and after-tax synergy. Inputs reset on reload.

## Coverage and evidence

| Analysis | Coverage | Evidence |
|---|---|---|
| Reported statements and controls | 172 original Forms 10-K and 10-Q. Four banks × 43 periods, from March 2016 to September 2026. Quarterly filings use three-, six- or nine-month year-to-date income and cash flows. Year-end filings use full-year flows. | [Filed figures, accessions and concept dictionary](filings.json) · [1,032 check results](results/checks.csv) |
| Capital and historical pricing | December 31, 2025 and September 30, 2026. Reported common book, tangible book, CET1, standardized RWA and average earning assets. Each period has its own capital, book and pricing source. | [Inputs and source links](anchors.json) |
| Three-year operating forecast | Four banks × two dates × three illustrative cases × three forecast years. | [72 forecast rows with drivers](results/forecasts.csv) |
| Equity valuation and stress | 24 cases. Five-year residual-income and dividend valuations, terminal value, sensitivity grid, credit/funding shocks and CET1 bridge. | [Cases and valuation cross-checks](results/scenarios.csv) |
| All-stock merger arithmetic | 24 ordered buyer/target/date combinations. Starting exchange ratios imply zero premium, with zero assumed synergy. | [Merger screens](results/mergers.csv) |
| Forecast accuracy | 32 one-year net-interest-income estimates, FY 2018–2025. Prior-year actuals and prior growth were available before each target year ended. | [Forecasts, actuals and source filings](results/backtest.csv) |

Six checks per filing compare assets with liabilities and equity, interest revenue less expense with net interest income, pre-tax earnings with its components, pre-tax earnings less tax with the relevant income line, closing cash with opening cash plus its reported change, and reported net cash movement with the filing’s cash-flow sections. All 1,032 differences were zero in USD millions in this release. The stated rounding tolerance is $1 million. Missing inputs produce **Unavailable**, and differences above tolerance produce **Review**. Optional fields can be blank even when these six controls pass.

The trend forecast repeats the previous annual growth rate in net interest income, bounded at ±15%. The flat forecast repeats the previous annual amount. Weighted absolute percentage error is the sum of absolute dollar errors divided by the sum of actual net interest income. Across all 32 observations, the trend model returned **9.30%** and the flat comparator **8.47%**. This replay scores the NII forecasting rules only. Each estimate becomes available when the prior annual filing is public, generally after the forecast year has started.

## Definitions and assumptions

- **Source selection.** Historical results preserve the original period's filing accession and publication date. Later comparative restatements can differ. Source tags identify consolidated facts by unit and exact dates. Where SEC Companyfacts omits an issuer extension or historical definition, the extractor reads the same accession's inline facts or its SEC-rendered statement workbook. Row locators name the sheet and the disclosed caption. [SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) · [Raw source URLs and hashes](source-manifest.json)
- **Cash and income.** Each cash bridge uses the filing's own definition, which changes over the historical window. Wells Fargo can present the total from three cash-flow sections. Citi’s provision subtotal can include benefits and claims. The tax bridge uses continuing income before attribution where applicable. Parent net income and common-shareholder income have separate lines.
- **Funding and earnings.** Starting annual margin is GAAP net interest income divided by average earning assets. Interim income is annualized by elapsed days. Forecast average earning assets change with average net loan growth. Fees and expenses grow at adjustable rates. Base provision uses period provision divided by period-end net loans. The historical effective tax rate applies to positive profits. The annualized difference between after-tax continuing profit and common income stays fixed. Preferred and noncontrolling distributions are simplified.
- **Forecast balance sheet.** Nonloan assets and other liabilities are held constant before liquidity or new funding. Loan growth less deposit growth and retained common earnings creates a cumulative funding requirement. A surplus builds liquid assets. New funding accrues interest from the following year. Required funding assumes availability at the chosen rate. The capital proxy adds retained common earnings to CET1 and changes RWA by incremental net loans times the chosen risk weight. Capital results depend on these assumptions.
- **Peer multiples.** Historical reference price divides BlackRock's reported 13F common-stock position value by reported shares for each common-stock CUSIP, excluding options. Source dollar/share totals are included. P/E uses full-year diluted EPS or FY plus current YTD minus prior YTD. Interim trailing EPS is approximate because diluted share counts vary. Each issuer defines tangible book value. Reported figures and 13F prices became public after the measurement date. [December 2025 13F](https://www.sec.gov/Archives/edgar/data/2012383/000201238326000920/0002012383-26-000920-index.htm) · [September 2026 13F](https://www.sec.gov/Archives/edgar/data/2012383/000201238326003985/0002012383-26-003985-index.html)
- **Equity valuation.** Opening book is common book value per share. Starting profitability uses trailing diluted EPS divided by closing book value as a proxy. ROE moves in five equal steps to the long-run assumption. Closing book equals opening book plus earnings less dividends. Terminal payout is consistent with terminal growth and ROE. The dividend and residual-income calculations use identical clean-surplus assumptions. Agreement checks the equations, while valuation still depends on the assumed returns, payout and discount rate. [Aswath Damodaran, *Valuing Financial Service Firms*](https://pages.stern.nyu.edu/~adamodar/pdfiles/papers/finfirm.pdf)
- **Stress and transactions.** The funding shock applies to total ending deposits; the credit shock applies to ending net loans. Both use the selected period length. The after-tax loss reduces CET1. The separate all-stock screen uses reported diluted share counts as a proxy and user-defined synergies. The historical deal panel gives a dated regional-bank precedent with the adviser’s comparison group. [First Horizon / Capital Bank Form S-4, pp. 74–75](https://www.sec.gov/Archives/edgar/data/36966/000093041317002422/c88663_s4.htm)

## Run locally

Open **index.html** in a browser, or run these commands from this folder using Node.js 18 or newer. The offline runner uses only built-in modules. Use a new destination for each run.

```sh
node checks.test.js
node run.js my-bank-results
```

The runner verifies the published input hashes and stages the CSVs before publishing an output directory. A failed required anchor check stops the scenarios. A historical difference above tolerance produces a nonzero exit and a report for review. To rebuild the standalone interface from the same inputs, run `node build.js`.

For source review, `source-manifest.json` records the cache path, direct EDGAR URL and SHA-256 of the raw files. To reproduce the statement extraction from those archived bytes, place them at the listed paths in a local folder and run `python extract.py /path/to/cache --out /path/to/rebuilt-filings.json` with lxml and openpyxl installed. Companyfacts URLs update over time. The checked-in normalized snapshot and its checksum support deterministic offline runs. Anchor values were transcribed from the linked tables, with the BlackRock numerator and share denominator preserved for recalculation.

## Scope for institutional review

This release covers public holding-company reporting, simplified bank forecasting, equity valuation and preliminary transaction screening. Desk-level deposit repricing, deposit runoff by maturity, intraday liquidity, securities duration and hedges, loan vintage loss models, full regulatory capital deductions, liquidity coverage and net stable funding ratios, deal purchase accounting, and transaction approvals require additional assumptions or data and dedicated validation. Historical reconciliation confirms arithmetic on filed amounts. It does not validate forward valuations, forecast accuracy for another institution, deal feasibility or adoption by a bank.
