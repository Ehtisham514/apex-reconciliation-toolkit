"""Transparent, currency-neutral finance models using Decimal arithmetic.

Amounts must share a currency and scale. These are planning calculations, not a
posting engine or jurisdiction-specific financial statements. See README.md for
assumptions, formulas and primary references.
"""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, localcontext
from typing import Sequence

ZERO = Decimal("0")
ONE = Decimal("1")


def D(value):
    """Convert numeric input through its decimal string; reject NaN/infinity."""
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("Invalid numeric input") from exc
    if not result.is_finite():
        raise ValueError("Non-finite numeric input")
    return result


def nonnegative(value, name):
    result = D(value)
    if result < 0:
        raise ValueError(f"{name} must be nonnegative")
    return result


def ratio(numerator, denominator):
    numerator, denominator = D(numerator), D(denominator)
    return None if denominator == 0 else numerator / denominator


@dataclass(frozen=True)
class ConstructionLine:
    """One estimate line: quantity/material rate plus total labor hours/rate.

    Labor hours are total hours for this line, not hours per unit. Waste applies
    only to materials. Strings, integers and Decimals are accepted.
    """
    quantity: Decimal
    unit_cost: Decimal
    labor_hours: Decimal = ZERO
    hourly_rate: Decimal = ZERO
    waste_rate: Decimal = ZERO

    def __post_init__(self):
        for name in ("quantity", "unit_cost", "labor_hours", "hourly_rate", "waste_rate"):
            object.__setattr__(self, name, nonnegative(getattr(self, name), name))

    def cost(self):
        return self.quantity * self.unit_cost * (ONE + self.waste_rate) + self.labor_hours * self.hourly_rate


def construction_estimate(lines: Sequence[ConstructionLine], overhead_rate="0", contingency_rate="0", margin="0"):
    """Price a bid; both overhead and contingency are percentages of direct cost.

    ``margin`` is target profit / bid, not markup. Do not add the same indirect
    cost in line items and again in overhead.
    """
    if not lines:
        raise ValueError("At least one construction line is required")
    base = sum((line.cost() for line in lines), ZERO)
    overhead, contingency, target_margin = map(D, (overhead_rate, contingency_rate, margin))
    if not (overhead >= 0 and contingency >= 0 and 0 <= target_margin < 1):
        raise ValueError("Rates must be nonnegative; margin must be below 1")
    total_cost = base * (ONE + overhead + contingency)
    bid = total_cost / (ONE - target_margin)
    return {"direct_cost": base, "overhead": base * overhead, "contingency": base * contingency,
            "total_cost": total_cost, "bid_price": bid, "gross_profit": bid - total_cost,
            "target_margin": target_margin}


def cost_to_complete(contract_value, actual_cost, remaining_committed_cost, remaining_uncommitted_cost,
                     approved_change_orders="0", contingency_rate="0"):
    """Bottom-up forecast using unpaid/unincurred *remaining* commitments only.

    Approved change orders are signed additions/deductions to revenue. Pending
    variations are excluded. Retention, billing timing and cash flow are separate.
    """
    contract = nonnegative(contract_value, "Contract value")
    actual = nonnegative(actual_cost, "Actual cost")
    committed = nonnegative(remaining_committed_cost, "Remaining committed cost")
    uncommitted = nonnegative(remaining_uncommitted_cost, "Remaining uncommitted cost")
    change_orders = D(approved_change_orders)
    contingency = nonnegative(contingency_rate, "Contingency rate")
    revenue = contract + change_orders
    if revenue < 0:
        raise ValueError("Approved contract revenue cannot be negative")
    remaining = committed + uncommitted
    reserve = remaining * contingency
    estimated_total = actual + remaining + reserve
    profit = revenue - estimated_total
    return {"approved_contract_revenue": revenue, "actual_cost": actual,
            "remaining_committed_cost": committed, "remaining_uncommitted_cost": uncommitted,
            "remaining_contingency": reserve, "estimate_to_complete": remaining + reserve,
            "estimate_at_completion": estimated_total, "forecast_profit": profit,
            "forecast_margin": ratio(profit, revenue)}


def earned_value(budget_at_completion, planned_value, earned_value, actual_cost):
    """EVM: cumulative PV/EV/AC for the same scope and status date.

    EAC assumes current cost efficiency continues; SPI is not a finish-date
    forecast. Undefined ratios are returned as None, not fabricated zeros.
    """
    bac, pv, ev, ac = map(D, (budget_at_completion, planned_value, earned_value, actual_cost))
    if min(bac, pv, ev, ac) < 0 or pv > bac or ev > bac:
        raise ValueError("Values must be nonnegative; PV and EV cannot exceed BAC")
    cpi, spi = ratio(ev, ac), ratio(ev, pv)
    eac = None if cpi is None or cpi == 0 else bac / cpi
    return {"cost_variance": ev - ac, "schedule_variance": ev - pv, "cpi": cpi, "spi": spi,
            "estimate_at_completion": eac,
            "estimate_to_complete": None if eac is None else eac - ac,
            "variance_at_completion": None if eac is None else bac - eac}


def cash_forecast(opening_cash, weekly_receipts, weekly_payments, minimum_cash="0"):
    """Unfinanced cash path; receipts/payments are nonnegative cash magnitudes.

    Funding gap is a snapshot shortfall in each week, not a drawdown or an amount
    to sum across weeks. No borrowing is automatically added to cash.
    """
    if not weekly_receipts or len(weekly_receipts) != len(weekly_payments):
        raise ValueError("Receipts and payments must have equal nonzero lengths")
    cash, floor = D(opening_cash), nonnegative(minimum_cash, "Minimum cash")
    result = []
    for index, (receipts, payments) in enumerate(zip(weekly_receipts, weekly_payments), 1):
        receipts = nonnegative(receipts, "Receipts")
        payments = nonnegative(payments, "Payments")
        opening = cash
        cash += receipts - payments
        result.append({"week": index, "opening": opening, "receipts": receipts, "payments": payments,
                       "net_cash_flow": receipts - payments, "closing": cash,
                       "funding_gap": max(floor - cash, ZERO)})
    return result


def annual_projection(base_revenue, growth_rates, gross_margin="0.40", operating_cost_rate="0.20",
                      depreciation_rate="0.02", capex_rate="0.03", working_capital_rate="0.12",
                      tax_rate="0.25", opening_working_capital=None):
    """Driver-based unlevered annual operating / cash-flow projection.

    Revenue grows from the prior year; other drivers are percentages of revenue.
    Opening NWC defaults to base-year revenue times NWC rate. Taxes are applied
    only to positive EBIT: no loss refunds, NOL carryforwards or tax shield model.
    Not an integrated three-statement or debt-financed cash forecast.
    """
    revenue = nonnegative(base_revenue, "Base revenue")
    rates = [D(x) for x in growth_rates]
    if not rates or len(rates) > 100 or any(x <= -1 for x in rates):
        raise ValueError("Provide 1–100 growth rates, each greater than -100%")
    gm = D(gross_margin)
    operating = nonnegative(operating_cost_rate, "Operating cost rate")
    depreciation = nonnegative(depreciation_rate, "Depreciation rate")
    capex = nonnegative(capex_rate, "Capital expenditure rate")
    working_capital, tax = D(working_capital_rate), D(tax_rate)
    if gm > 1 or not 0 <= tax <= 1:
        raise ValueError("Gross margin cannot exceed 100%; tax rate must be 0–100%")
    nwc_previous = revenue * working_capital if opening_working_capital is None else D(opening_working_capital)
    rows = []
    for year, growth in enumerate(rates, 1):
        revenue *= ONE + growth
        cogs = revenue * (ONE - gm)
        opex = revenue * operating
        ebitda = revenue - cogs - opex
        da = revenue * depreciation
        ebit = ebitda - da
        cash_tax = max(ebit, ZERO) * tax
        capital_spending = revenue * capex
        nwc = revenue * working_capital
        delta_nwc = nwc - nwc_previous
        fcff = ebit - cash_tax + da - capital_spending - delta_nwc
        rows.append({"year": year, "revenue": revenue, "cost_of_sales": cogs,
                     "gross_profit": revenue - cogs, "operating_costs": opex, "ebitda": ebitda,
                     "depreciation": da, "ebit": ebit, "cash_tax": cash_tax,
                     "nopat": ebit - cash_tax, "capex": capital_spending,
                     "working_capital": nwc, "change_in_working_capital": delta_nwc,
                     "free_cash_flow": fcff})
        nwc_previous = nwc
    return rows


def dcf(free_cash_flows, discount_rate, terminal_growth, net_debt="0", midyear=False,
        terminal_timing="year_end"):
    """Discount annual unlevered FCFF using a matching cost of capital.

    Forecasts occur at years 1..N, or 0.5..N-0.5 if midyear=True. Gordon terminal
    value is at end of year N by default. Explicit terminal_timing='midyear'
    applies N-0.5, for an assumption of midyear continuing cash flows too.
    Net debt = debt less excess cash; other equity adjustments are not modeled.
    """
    flows = [D(x) for x in free_cash_flows]
    rate, growth, debt = map(D, (discount_rate, terminal_growth, net_debt))
    if not flows or len(flows) > 100 or rate <= growth or rate <= -1 or growth <= -1:
        raise ValueError("Requires 1–100 cash flows and discount rate > terminal growth > -100%")
    if terminal_timing not in ("year_end", "midyear") or (terminal_timing == "midyear" and not midyear):
        raise ValueError("Choose year_end terminal timing, or midyear with midyear=True")
    with localcontext() as context:
        context.prec = 40
        offset = D("0.5") if midyear else ZERO
        discounted = [flow / (ONE + rate) ** (D(year) - offset)
                      for year, flow in enumerate(flows, 1)]
        terminal = flows[-1] * (ONE + growth) / (rate - growth)
        terminal_period = D(len(flows)) - (D("0.5") if terminal_timing == "midyear" else ZERO)
        pv_terminal = terminal / (ONE + rate) ** terminal_period
        pv_forecast = sum(discounted, ZERO)
        enterprise = pv_forecast + pv_terminal
        return {"pv_forecast": pv_forecast, "terminal_value": terminal,
                "pv_terminal": pv_terminal, "enterprise_value": enterprise,
                "equity_value": enterprise - debt,
                "terminal_value_share": ratio(pv_terminal, enterprise),
                "terminal_discount_period": terminal_period}


def dcf_sensitivity(free_cash_flows, discount_rates, terminal_growth_rates, net_debt="0"):
    """Return every rate/growth combination; invalid rate<=growth cells are explicit."""
    flows = [D(x) for x in free_cash_flows]
    rates, growths = [D(x) for x in discount_rates], [D(x) for x in terminal_growth_rates]
    if not rates or not growths or len(rates) * len(growths) > 10000:
        raise ValueError("Provide a nonempty sensitivity grid of at most 10,000 cells")
    # Validate common assumptions before iterating; invalid cells remain visible.
    D(net_debt)
    if not flows or len(flows) > 100:
        raise ValueError("Provide 1–100 cash flows")
    rows = []
    for rate in rates:
        for growth in growths:
            row = {"discount_rate": rate, "terminal_growth": growth}
            if rate <= growth or rate <= -1 or growth <= -1:
                row.update({"enterprise_value": None, "equity_value": None, "status": "INVALID_RATE_GROWTH"})
            else:
                result = dcf(flows, rate, growth, net_debt)
                row.update({"enterprise_value": result["enterprise_value"],
                            "equity_value": result["equity_value"], "status": "VALID"})
            rows.append(row)
    return rows


def acquisition_case(target_ebitda, purchase_multiple, debt_financing, debt_interest_rate,
                     synergies="0", integration_cost="0", tax_rate="0"):
    """Simplified EBITDA acquisition screening, not EPS accretion or net income.

    Purchase price is an enterprise-value proxy. Debt here is new acquisition
    financing; target debt/cash, transaction fees and working-capital adjustments
    are excluded. No tax refund is assumed when contribution is negative.
    """
    ebitda, multiple, debt, rate, synergy, integration, tax = map(
        D, (target_ebitda, purchase_multiple, debt_financing, debt_interest_rate, synergies, integration_cost, tax_rate))
    if min(ebitda, multiple, debt, rate, integration) < 0 or not 0 <= tax <= 1:
        raise ValueError("Invalid acquisition assumptions")
    price = ebitda * multiple
    if debt > price:
        raise ValueError("Debt financing exceeds purchase price")
    interest = debt * rate
    contribution = ebitda + synergy - interest - integration
    tax_charge = max(contribution, ZERO) * tax
    return {"purchase_price": price, "equity_financing": price - debt,
            "incremental_ebitda": ebitda + synergy, "annual_interest": interest,
            "first_year_pre_tax_contribution": contribution,
            "illustrative_tax_charge": tax_charge,
            "illustrative_after_tax_contribution": contribution - tax_charge,
            "interest_coverage": ratio(ebitda + synergy, interest)}
