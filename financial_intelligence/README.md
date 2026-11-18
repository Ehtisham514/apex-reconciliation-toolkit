# Financial Intelligence Models — experimental module

A transparent, **illustrative calculation engine** for construction estimating, earned-value management, 13-week cash forecasts, discounted cash flow (DCF) valuation and acquisition scenario analysis.

**Status:** Prototype on a feature branch. Not production-ready, audited, or a substitute for professional valuation, tax, legal, or engineering advice. No external customer data is included.

## Capabilities

- Construction quantity × unit-cost estimates, labor, waste, overhead, contingency, and **target gross margin** (not confused with markup)
- Earned value: CV, SV, CPI, SPI, EAC and VAC
- Weekly liquidity: opening and closing cash, receipts, disbursements, minimum-cash funding gaps
- DCF: forecast present value, Gordon-growth terminal value, net debt to equity bridge, mid-year convention option
- Acquisition screening: EBITDA multiple, financing mix, interest burden, synergies, one-time integration cost and illustrative contribution

## Quick start

Python 3.10+; no third-party runtime dependencies.

```python
from decimal import Decimal as D
from financial_intelligence.models import ConstructionLine, construction_estimate, dcf

project = construction_estimate(
    [ConstructionLine(D("100"), D("120"), D("50"), D("35"), D("0.05"))],
    overhead_rate="0.10", contingency_rate="0.08", margin="0.20"
)
print(project)
print(dcf([100000, 120000, 135000], "0.12", "0.03", net_debt="250000"))
```

Run tests: `python -m pytest financial_intelligence/test_models.py` (requires pytest).

## Important limitations

- Inputs must use consistent currency and units; no FX, inflation escalation, tax jurisdiction, or calendar normalization yet.
- Acquisition contribution is **not** GAAP/IFRS net income or EPS accretion/dilution: depreciation, amortization, financing fees, purchase accounting, working capital and debt amortization are not modeled.
- DCF requires analyst-reviewed assumptions and a consistent free-cash-flow/discount-rate basis. The simple terminal-value model can dominate the valuation.
- EAC assumes current CPI continues; it is not an independently verified cost-to-complete estimate.
- Construction estimates are not calibrated to a local cost database or an AACE estimate class.
- Large-data ingestion, database persistence, access control, multi-tenant security, audit trails and user interfaces are **planned, not implemented**.

## Enterprise roadmap

1. Import validated CSV/Parquet with schemas, currency/units, error reports and duplicate detection.
2. Store large transaction and project tables in partitioned DuckDB/PostgreSQL, with batch aggregation, reconciliation and versioned assumptions.
3. Build scenario engines (base/upside/downside), Monte Carlo risk simulation, sensitivity tornadoes, and cash runway stress testing.
4. Add construction WBS, schedule-based cash flow, change orders, committed costs, retention and estimate-at-completion overrides.
5. Add M&A integrated three-statement forecasts, working-capital adjustments, debt schedule, purchase-price allocation, synergies and deal IRR.
6. Add role-based access, encrypted storage, audit events, performance tests and exports.

No claim is made that this prototype can currently process millions of rows or serve billion-dollar companies. Those are scalability design targets requiring benchmarking and controls.
