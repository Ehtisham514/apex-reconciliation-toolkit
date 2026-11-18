"""Local dashboard: python -m streamlit run financial_intelligence/dashboard.py."""
import csv
import io
import json
import tempfile
from decimal import Decimal
from pathlib import Path

import pandas as pd
import streamlit as st

try:
    from financial_intelligence.models import (
        D, ConstructionLine, construction_estimate, cost_to_complete, earned_value,
        cash_forecast, annual_projection, dcf, dcf_sensitivity, acquisition_case,
    )
    from financial_intelligence.enterprise import aggregate_csv
except ModuleNotFoundError as exc:
    if exc.name not in ("financial_intelligence", "financial_intelligence.models"):
        raise
    from models import (
        D, ConstructionLine, construction_estimate, cost_to_complete, earned_value,
        cash_forecast, annual_projection, dcf, dcf_sensitivity, acquisition_case,
    )
    from enterprise import aggregate_csv

st.set_page_config(page_title="APEX Finance Lab", page_icon="◈", layout="wide")
st.markdown("""<style>
[data-testid="stAppViewContainer"] {background:#f6f8fb;}
[data-testid="stSidebar"] {background:#10263c;}
[data-testid="stSidebar"] * {color:#edf3f8;}
[data-testid="stSidebar"] input {color:#172b43;}
[data-testid="stMetric"] {background:white;border:1px solid #dce4ec;border-radius:12px;padding:18px;}
.block-container {max-width:1280px;}
h1,h2,h3 {color:#10263c;}
</style>""", unsafe_allow_html=True)
st.title("APEX Finance Lab")
st.caption("Estimate costs. Plan cash. Review operating assumptions. Explore value.")
MODES = ["Overview", "Construction bid", "Project forecast", "13-week cash", "Annual projection",
         "DCF valuation", "Acquisition screening", "Ledger data"]
mode = st.sidebar.radio("Workspace", MODES, key="mode")
currency = st.sidebar.selectbox("Reporting currency", ["USD", "PKR", "GBP", "EUR", "AED", "Other"], key="currency")
if currency == "Other":
    currency = st.sidebar.text_input("Currency label", "Units", key="currency_label")[:12]
st.sidebar.caption("Currency is a display label. Keep every input in the same currency and scale; no FX conversion is performed.")
st.sidebar.markdown("[Documentation](https://github.com/Ehtisham514/apex-reconciliation-toolkit/tree/main/financial_intelligence)")


def amount(label, default, key, help=None):
    return D(st.text_input(label, str(default), key=key, help=help))


def percent(label, default, key, minimum=None, maximum=None):
    kwargs = {"value": float(default), "step": 0.5, "key": key}
    if minimum is not None:
        kwargs["min_value"] = float(minimum)
    if maximum is not None:
        kwargs["max_value"] = float(maximum)
    return D(st.number_input(label, **kwargs)) / 100


def fmt(value):
    return "Not defined" if value is None else f"{currency} {value:,.2f}"


def show_metrics(items):
    for column, (label, value) in zip(st.columns(len(items)), items):
        column.metric(label, fmt(value))


def export(result, filename, assumptions=None):
    bundle = {"currency": currency, "assumptions": assumptions or {}, "results": result}
    st.download_button("Download analysis (JSON)", json.dumps(bundle, indent=2, default=str),
                       filename + ".json", "application/json", key=filename + "_json")
    # Decimal strings preserve monetary precision; avoid spreadsheet formula cells.
    rows = result if isinstance(result, list) else [{"metric": key, "value": value} for key, value in result.items()]
    if rows:
        output = io.StringIO(newline="")
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            cleaned = {}
            for key, value in row.items():
                if isinstance(value, str) and value.startswith(("=", "+", "-", "@", "\t", "\r")):
                    value = "'" + value
                cleaned[key] = value
            writer.writerow(cleaned)
        st.download_button("Download results (CSV)", output.getvalue(), filename + ".csv", "text/csv", key=filename + "_csv")


def table(rows):
    # Keep displayed monetary values exact; use floats only for chart coordinates.
    return pd.DataFrame([{k: str(v) if isinstance(v, Decimal) else v for k, v in row.items()} for row in rows])


try:
    if mode == "Overview":
        st.subheader("Start with the question your business needs answered")
        st.markdown("""
| Workspace | Business question | Output |
|---|---|---|
| Construction bid | What should we quote at our target margin? | Direct cost, reserves and suggested price |
| Project forecast | What will this job cost to finish? | Cost to complete, final margin and EVM checks |
| 13-week cash | When might cash fall below our reserve? | Weekly cash path and peak funding shortfall |
| Annual projection | How do revenue and cost assumptions change cash generation? | Operating forecast and unlevered cash flows |
| DCF valuation | How sensitive is value to growth and the discount rate? | Enterprise/equity bridge and sensitivity grid |
| Acquisition screening | How do debt, synergies and integration affect contribution? | Simplified financing and contribution bridge |
| Ledger data | What totals and import exceptions exist in a CSV? | Validated grouped data and rejection report |
""")
        st.info("Every default is fictional demonstration data. Replace assumptions with your reviewed figures and download the result with its assumptions.")
        st.markdown("**How to use:** choose a workspace, select one reporting currency, review assumptions, and export the analysis. Amounts are entered as plain numbers without currency symbols or thousands separators.")
        st.caption("Planning models use Decimal arithmetic. This release is not a full accounting system, independently audited valuation, or jurisdiction-specific tax model.")

    elif mode == "Construction bid":
        st.subheader("Construction estimate & bid price")
        st.caption("Add material and labor lines. Labor hours mean total hours per line; waste applies to materials only.")
        edited = st.data_editor(pd.DataFrame([
            {"description": "Fictional materials and installation", "quantity": "100", "unit_cost": "120", "labor_hours": "50", "hourly_rate": "35", "waste_rate": "0.05"},
            {"description": "Fictional finishing", "quantity": "1", "unit_cost": "1200", "labor_hours": "20", "hourly_rate": "35", "waste_rate": "0"},
        ]), num_rows="dynamic", hide_index=True, key="estimate_lines", use_container_width=True)
        fields = ("quantity", "unit_cost", "labor_hours", "hourly_rate", "waste_rate")
        lines = [ConstructionLine(*(row[field] for field in fields)) for row in edited.to_dict("records")]
        left, center, right = st.columns(3)
        with left:
            overhead = percent("Overhead (% of direct cost)", 10, "bid_overhead", 0)
        with center:
            reserve = percent("Contingency (% of direct cost)", 8, "bid_reserve", 0)
        with right:
            margin = percent("Target gross margin (%)", 20, "bid_margin", 0, 99.9)
        result = construction_estimate(lines, overhead, reserve, margin)
        show_metrics([("Suggested bid", result["bid_price"]), ("Estimated cost", result["total_cost"]), ("Forecast gross profit", result["gross_profit"])])
        st.caption("Overhead and contingency are added separately to direct cost. Bid = total estimated cost ÷ (1 − target margin). Exclude indirect costs already included in line items.")
        st.dataframe(table([result]), hide_index=True, use_container_width=True)
        export(result, "construction_bid", {"lines": edited.to_dict("records"), "overhead_rate": overhead, "contingency_rate": reserve, "margin": margin})

    elif mode == "Project forecast":
        st.subheader("Cost to complete & project performance")
        left, right = st.columns(2)
        with left:
            contract = amount("Original contract revenue", "1000000", "job_contract")
            changes = amount("Approved change orders (+/−)", "50000", "job_changes")
            actual = amount("Actual costs incurred to date", "400000", "job_actual")
        with right:
            committed = amount("Remaining unincurred committed cost", "250000", "job_committed")
            uncommitted = amount("Remaining uncommitted cost estimate", "100000", "job_uncommitted")
            reserve = percent("Contingency on remaining cost (%)", 10, "job_reserve", 0)
        result = cost_to_complete(contract, actual, committed, uncommitted, changes, reserve)
        show_metrics([("Cost to complete", result["estimate_to_complete"]), ("Projected final cost", result["estimate_at_completion"]), ("Projected profit", result["forecast_profit"])])
        st.caption("Remaining commitments exclude amounts already included in actual costs. Pending change orders, retention and collection timing are not included.")
        with st.expander("Earned-value cross-check", expanded=False):
            bac = amount("Budget at completion (cost budget)", "800000", "evm_bac")
            pv = amount("Planned value at status date", "400000", "evm_pv")
            ev = amount("Earned value of completed work", "350000", "evm_ev")
            evm = earned_value(bac, pv, ev, actual)
            st.dataframe(table([evm]), hide_index=True, use_container_width=True)
            st.caption("EVM EAC assumes current cost efficiency continues. Compare it with the bottom-up forecast; investigate differences. SPI is not a predicted completion date.")
        export(result, "project_forecast", {"contract_value": contract, "approved_change_orders": changes, "actual_cost": actual, "remaining_committed_cost": committed, "remaining_uncommitted_cost": uncommitted, "contingency_rate": reserve})

    elif mode == "13-week cash":
        st.subheader("13-week liquidity plan")
        left, right = st.columns(2)
        with left:
            opening = amount("Opening cash", "100000", "cash_opening")
        with right:
            minimum = amount("Minimum cash reserve", "25000", "cash_minimum")
        schedule = st.data_editor(pd.DataFrame([{"week": week, "receipts": "30000", "payments": "35000"} for week in range(1, 14)]),
                                  disabled=["week"], hide_index=True, key="cash_schedule", use_container_width=True)
        receipts, payments = list(schedule["receipts"]), list(schedule["payments"])
        rows = cash_forecast(opening, receipts, payments, minimum)
        peak = max(row["funding_gap"] for row in rows)
        show_metrics([("Week 13 cash", rows[-1]["closing"]), ("Lowest cash balance", min(row["closing"] for row in rows)), ("Peak reserve shortfall", peak)])
        chart = pd.DataFrame({"Week": [row["week"] for row in rows], "Closing cash": [float(row["closing"]) for row in rows], "Minimum reserve": [float(minimum)] * len(rows)}).set_index("Week")
        st.line_chart(chart)
        st.caption("Receipts and payments are positive magnitudes. Funding gap is a weekly shortfall before financing; do not sum it across weeks.")
        st.dataframe(table(rows), hide_index=True, use_container_width=True)
        export(rows, "cash_forecast_13_weeks", {"opening_cash": opening, "minimum_cash": minimum, "weekly_receipts": receipts, "weekly_payments": payments})

    elif mode == "Annual projection":
        st.subheader("Annual operating & cash-flow projection")
        st.caption("A driver-based unlevered model. Enter one growth rate per forecast year, separated by commas.")
        left, middle, right = st.columns(3)
        with left:
            revenue = amount("Base-year revenue", "1000000", "projection_revenue")
            growth_text = st.text_input("Revenue growth rates (%)", "10,8,6,4,3", key="projection_growth")
            growth = [D(x.strip()) / 100 for x in growth_text.split(",")]
            gm = percent("Gross margin (%)", 40, "projection_gm", maximum=100)
        with middle:
            operating = percent("Operating costs / revenue (%)", 20, "projection_opex", 0)
            depreciation = percent("Depreciation / revenue (%)", 2, "projection_da", 0)
            capex = percent("Capex / revenue (%)", 3, "projection_capex", 0)
        with right:
            nwc = percent("Operating working capital / revenue (%)", 12, "projection_nwc")
            tax = percent("Cash tax on positive EBIT (%)", 25, "projection_tax", 0, 100)
            opening_nwc_text = st.text_input("Opening operating working capital (blank = base-year ratio)", "", key="projection_opening_nwc")
            opening_nwc = D(opening_nwc_text) if opening_nwc_text.strip() else None
        rows = annual_projection(revenue, growth, gm, operating, depreciation, capex, nwc, tax, opening_nwc)
        show_metrics([("Final-year revenue", rows[-1]["revenue"]), ("Final-year EBITDA", rows[-1]["ebitda"]), ("Final-year free cash flow", rows[-1]["free_cash_flow"])])
        st.line_chart(pd.DataFrame({"Year": [row["year"] for row in rows], "Revenue": [float(row["revenue"]) for row in rows], "Free cash flow": [float(row["free_cash_flow"]) for row in rows]}).set_index("Year"))
        st.dataframe(table(rows), hide_index=True, use_container_width=True)
        st.caption("FCFF = EBIT − cash tax + depreciation − capex − change in operating working capital. No borrowing, loss carryforwards, tax refunds or integrated balance sheet is modeled.")
        export(rows, "annual_projection", {"base_revenue": revenue, "growth_rates": growth, "gross_margin": gm, "operating_cost_rate": operating, "depreciation_rate": depreciation, "capex_rate": capex, "working_capital_rate": nwc, "tax_rate": tax, "opening_working_capital": opening_nwc})

    elif mode == "DCF valuation":
        st.subheader("DCF valuation & sensitivity")
        flow_text = st.text_input("Annual unlevered free cash flows (comma separated)", "100000,120000,140000,160000,180000", key="dcf_flows")
        flows = [D(x.strip()) for x in flow_text.split(",")]
        left, middle, right = st.columns(3)
        with left:
            rate = percent("Discount rate / WACC (%)", 12, "dcf_rate")
        with middle:
            growth = percent("Terminal growth (%)", 3, "dcf_growth")
        with right:
            debt = amount("Net debt (debt less excess cash)", "200000", "dcf_debt")
        midyear = st.checkbox("Discount explicit forecast cash flows at midyear", key="dcf_midyear")
        result = dcf(flows, rate, growth, debt, midyear=midyear)
        show_metrics([("Enterprise value", result["enterprise_value"]), ("Equity value", result["equity_value"]), ("PV of terminal value", result["pv_terminal"])])
        st.caption("Terminal value is at the end of the last forecast year. Midyear affects only the explicit forecast in this screen. Net debt is the sole equity adjustment; review other claims separately.")
        if flows[-1] <= 0:
            st.warning("The last forecast cash flow is nonpositive. A perpetuity based on it may not represent a viable continuing business; review normalization or another terminal approach.")
        if result["terminal_value_share"] is not None:
            st.write(f"Terminal value / enterprise value: {result['terminal_value_share']:.1%}")
        grid = dcf_sensitivity(flows, [rate - D("0.02"), rate, rate + D("0.02")], [growth - D("0.01"), growth, growth + D("0.01")], debt)
        st.markdown("**Year-end sensitivity — enterprise value**")
        sensitivity = pd.DataFrame([{"WACC": f"{row['discount_rate']:.1%}", "Growth": f"{row['terminal_growth']:.1%}", "Enterprise value": "Invalid" if row["enterprise_value"] is None else f"{row['enterprise_value']:,.2f}"} for row in grid])
        st.dataframe(sensitivity.pivot(index="WACC", columns="Growth", values="Enterprise value"), use_container_width=True)
        export(result, "dcf_valuation", {"free_cash_flows": flows, "discount_rate": rate, "terminal_growth": growth, "net_debt": debt, "midyear": midyear, "terminal_timing": "year_end"})
        export(grid, "dcf_sensitivity", {"discount_convention": "year_end", "free_cash_flows": flows, "net_debt": debt})

    elif mode == "Acquisition screening":
        st.subheader("Acquisition economics screen")
        left, right = st.columns(2)
        with left:
            ebitda = amount("Target normalized EBITDA", "500000", "deal_ebitda")
            multiple = amount("Enterprise value / EBITDA multiple", "5", "deal_multiple")
            debt = amount("New acquisition debt", "1000000", "deal_debt")
            rate = percent("Annual debt interest (%)", 8, "deal_rate", 0)
        with right:
            synergy = amount("Annual EBITDA synergies (+/−)", "100000", "deal_synergy")
            integration = amount("First-year integration costs", "150000", "deal_integration")
            tax = percent("Illustrative tax on positive contribution (%)", 25, "deal_tax", 0, 100)
        result = acquisition_case(ebitda, multiple, debt, rate, synergy, integration, tax)
        show_metrics([("Enterprise purchase-price proxy", result["purchase_price"]), ("Equity funding before adjustments", result["equity_financing"]), ("First-year contribution after illustrative tax", result["illustrative_after_tax_contribution"])])
        st.dataframe(table([result]), hide_index=True, use_container_width=True)
        st.caption("Contribution is not net income or EPS accretion. Target net debt, purchase accounting, depreciation, financing fees, debt amortization, working-capital adjustments and integration timing are excluded.")
        export(result, "acquisition_screen", {"target_ebitda": ebitda, "purchase_multiple": multiple, "debt_financing": debt, "debt_interest_rate": rate, "synergies": synergy, "integration_cost": integration, "tax_rate": tax})

    else:
        st.subheader("Validated ledger aggregation")
        st.caption("Schema: transaction_id,date,entity,project,account,amount,currency. This summarizes signed cash movements; it does not reconcile bank balances or eliminate intercompany entries.")
        upload = st.file_uploader("Upload a ledger CSV", type=["csv"], key="ledger_upload")
        st.info("The browser upload keeps the file in memory. For large files, use the local command-line ingestion workflow described in the documentation.")
        if upload is not None:
            with tempfile.TemporaryDirectory(prefix="apex-ledger-") as folder:
                path = Path(folder) / "upload.csv"
                upload.seek(0)
                with path.open("wb") as output:
                    for chunk in iter(lambda: upload.read(1024 * 1024), b""):
                        output.write(chunk)
                result = aggregate_csv(path, expected_currency=currency)
            columns = st.columns(2)
            columns[0].metric("Accepted rows", result["accepted_rows"])
            columns[1].metric("Rejected rows", result["rejected_rows"])
            st.dataframe(pd.DataFrame(result["totals"]), hide_index=True, use_container_width=True)
            if result.get("totals_truncated"):
                st.info("The group preview is truncated. Use the CLI totals export for every group.")
            if result.get("errors_truncated"):
                st.info("The rejected-row preview is truncated. Use the CLI rejection export for the complete report.")
            with st.expander("Import control totals"):
                st.json({key: result.get(key) for key in ("status", "records_read", "group_count", "cash_in", "cash_out", "net_amount", "checks", "sha256")})
            if result["errors"]:
                st.warning("Review rejected rows before relying on totals.")
                st.dataframe(pd.DataFrame(result["errors"]), hide_index=True, use_container_width=True)
            st.download_button("Download import report (JSON)", json.dumps(result, indent=2, default=str), "ledger_import_report.json", "application/json")
        else:
            st.markdown("Try `financial_intelligence/sample_ledger.csv` from the repository, or prepare a file using the schema above.")
except (ValueError, ArithmeticError, TypeError, KeyError) as exc:
    st.error(f"Check your inputs: {exc}")
    st.caption("No result was saved. Correct the value and the model will recalculate.")
