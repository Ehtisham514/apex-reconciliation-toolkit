"""Auditable finance models. Decimal arithmetic, explicit assumptions, no investment advice."""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Sequence

def D(value):
    try:
        x = Decimal(str(value))
    except (InvalidOperation, ValueError) as e:
        raise ValueError("Invalid numeric input") from e
    if not x.is_finite():
        raise ValueError("Non-finite numeric input")
    return x

def ratio(numerator, denominator):
    den = D(denominator)
    return None if den == 0 else D(numerator) / den

@dataclass(frozen=True)
class ConstructionLine:
    quantity: Decimal
    unit_cost: Decimal
    labor_hours: Decimal = Decimal("0")
    hourly_rate: Decimal = Decimal("0")
    waste_rate: Decimal = Decimal("0")
    def cost(self):
        if min(self.quantity, self.unit_cost, self.labor_hours, self.hourly_rate, self.waste_rate) < 0:
            raise ValueError("Negative inputs not supported")
        return self.quantity * self.unit_cost * (1 + self.waste_rate) + self.labor_hours * self.hourly_rate

def construction_estimate(lines: Sequence[ConstructionLine], overhead_rate="0", contingency_rate="0", margin="0"):
    base = sum((x.cost() for x in lines), Decimal("0"))
    overhead, contingency, target_margin = map(D, (overhead_rate, contingency_rate, margin))
    if not (0 <= overhead and 0 <= contingency and 0 <= target_margin < 1):
        raise ValueError("Rates must be nonnegative; margin must be below 1")
    total_cost = base * (1 + overhead + contingency)
    bid = total_cost / (1 - target_margin)
    return {"direct_cost": base, "overhead": base * overhead, "contingency": base * contingency,
            "total_cost": total_cost, "bid_price": bid, "gross_profit": bid - total_cost}

def earned_value(budget_at_completion, planned_value, earned_value, actual_cost):
    bac, pv, ev, ac = map(D, (budget_at_completion, planned_value, earned_value, actual_cost))
    if min(bac, pv, ev, ac) < 0:
        raise ValueError("Negative EVM amounts not supported")
    cpi, spi = ratio(ev, ac), ratio(ev, pv)
    eac = None if cpi is None or cpi == 0 else bac / cpi
    return {"cost_variance": ev-ac, "schedule_variance": ev-pv, "cpi": cpi, "spi": spi,
            "estimate_at_completion": eac, "variance_at_completion": None if eac is None else bac-eac}

def cash_forecast(opening_cash, weekly_receipts, weekly_payments, minimum_cash="0"):
    if len(weekly_receipts) != len(weekly_payments):
        raise ValueError("Receipts and payments must have equal lengths")
    cash, floor = D(opening_cash), D(minimum_cash)
    result = []
    for i, (receipts, payments) in enumerate(zip(weekly_receipts, weekly_payments), 1):
        start = cash
        cash += D(receipts) - D(payments)
        result.append({"week": i, "opening": start, "receipts": D(receipts), "payments": D(payments),
                       "closing": cash, "funding_gap": max(floor-cash, D(0))})
    return result

def dcf(free_cash_flows, discount_rate, terminal_growth, net_debt="0", midyear=False):
    flows = [D(x) for x in free_cash_flows]
    r, g, debt = D(discount_rate), D(terminal_growth), D(net_debt)
    if not flows or r <= g or r <= -1 or g <= -1:
        raise ValueError("Requires cash flows and discount rate > terminal growth > -100%")
    discounted = [f / (1+r) ** (D(i)- (D("0.5") if midyear else D(0))) for i,f in enumerate(flows,1)]
    terminal = flows[-1] * (1+g) / (r-g)
    pv_terminal = terminal / (1+r) ** (D(len(flows)) - (D("0.5") if midyear else D(0)))
    enterprise_value = sum(discounted, D(0)) + pv_terminal
    return {"pv_forecast": sum(discounted, D(0)), "terminal_value": terminal,
            "pv_terminal": pv_terminal, "enterprise_value": enterprise_value,
            "equity_value": enterprise_value - debt, "terminal_value_share": ratio(pv_terminal, enterprise_value)}

def acquisition_case(target_ebitda, purchase_multiple, debt_financing, debt_interest_rate,
                     synergies="0", integration_cost="0", tax_rate="0"):
    ebitda, multiple, debt, rate, syn, integration, tax = map(
        D, (target_ebitda, purchase_multiple, debt_financing, debt_interest_rate, synergies, integration_cost, tax_rate))
    if min(ebitda, multiple, debt, rate, integration) < 0 or not 0 <= tax <= 1:
        raise ValueError("Invalid acquisition assumptions")
    price = ebitda * multiple
    if debt > price:
        raise ValueError("Debt financing exceeds purchase price")
    interest = debt * rate
    return {"purchase_price": price, "equity_financing": price-debt,
            "incremental_ebitda": ebitda+syn,
            "first_year_pre_tax_contribution": ebitda+syn-interest-integration,
            "illustrative_after_tax_contribution": (ebitda+syn-interest-integration)*(1-tax),
            "interest_coverage": ratio(ebitda+syn, interest)}
