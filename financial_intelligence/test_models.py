from decimal import Decimal
from financial_intelligence.models import (
    D, ConstructionLine, construction_estimate, earned_value, cash_forecast, dcf, acquisition_case
)

def test_construction_margin_not_markup():
    x = construction_estimate([ConstructionLine(D(10), D(100))], margin="0.20")
    assert x["bid_price"] == D("1250")
    assert x["gross_profit"] == D("250")

def test_cash_13_weeks():
    x = cash_forecast("100", ["10"]*13, ["20"]*13, "50")
    assert len(x) == 13
    assert x[-1]["closing"] == D("-30")
    assert x[-1]["funding_gap"] == D("80")

def test_earned_value():
    x = earned_value(1000, 500, 400, 500)
    assert x["cpi"] == D("0.8")
    assert x["estimate_at_completion"] == D("1250")

def test_dcf_zero_growth_perpetuity():
    x = dcf([100], "0.10", "0")
    assert abs(x["enterprise_value"]-D("1000")) < D("0.000001")

def test_acquisition():
    x = acquisition_case(100, 5, 200, "0.1", synergies=20, integration_cost=10)
    assert x["purchase_price"] == 500
    assert x["first_year_pre_tax_contribution"] == 90

def test_zero_denominator():
    assert earned_value(100, 0, 0, 0)["cpi"] is None
