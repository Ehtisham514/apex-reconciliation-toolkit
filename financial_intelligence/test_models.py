"""Hand-calculated finance controls, validation, and scale invariants."""
import pytest
from financial_intelligence.models import (
    D, ConstructionLine, construction_estimate, cost_to_complete, earned_value,
    cash_forecast, annual_projection, dcf, dcf_sensitivity, acquisition_case,
)


def near(value, expected, tolerance="0.00000001"):
    assert abs(value - D(expected)) <= D(tolerance)


def test_construction_margin_not_markup_and_additive_reserves():
    result = construction_estimate([ConstructionLine("10", "100")], "0.10", "0.05", "0.20")
    assert result["direct_cost"] == D(1000)
    assert result["total_cost"] == D(1150)
    assert result["bid_price"] == D("1437.50")
    assert result["gross_profit"] / result["bid_price"] == D("0.20")


def test_labor_is_total_hours_and_waste_only_affects_materials():
    assert ConstructionLine(10, 100, 5, 20, "0.10").cost() == D(1200)


@pytest.mark.parametrize("value", ["NaN", "Infinity", "-Infinity", "bad", None])
def test_invalid_numeric_inputs_rejected(value):
    with pytest.raises(ValueError):
        ConstructionLine(value, 10)


@pytest.mark.parametrize("rate", ["-0.01", "1", "1.2"])
def test_bid_margin_bounds(rate):
    with pytest.raises(ValueError):
        construction_estimate([ConstructionLine(1, 100)], margin=rate)


def test_construction_cost_to_complete_does_not_double_count_paid_commitments():
    result = cost_to_complete(1000, 400, 200, 100, approved_change_orders=100, contingency_rate="0.10")
    assert result["approved_contract_revenue"] == 1100
    assert result["estimate_to_complete"] == 330
    assert result["estimate_at_completion"] == 730
    assert result["forecast_profit"] == 370


def test_cost_to_complete_allows_approved_deduction_and_zero_revenue_ratio():
    result = cost_to_complete(1000, 50, 0, 0, approved_change_orders=-1000)
    assert result["forecast_profit"] == -50
    assert result["forecast_margin"] is None
    with pytest.raises(ValueError):
        cost_to_complete(1000, 50, 0, 0, approved_change_orders=-1001)


def test_cash_13_weeks_and_funding_gap_is_not_financing():
    rows = cash_forecast("100", ["10"] * 13, ["20"] * 13, "50")
    assert len(rows) == 13
    assert rows[0]["closing"] == 90
    assert rows[-1]["closing"] == -30
    assert rows[-1]["funding_gap"] == 80
    assert rows[-1]["closing"] == D(100) + sum(row["net_cash_flow"] for row in rows)


def test_variable_weekly_cash_and_negative_opening_balance():
    rows = cash_forecast(-10, [20, 30], [5, 50])
    assert [row["closing"] for row in rows] == [D(5), D(-15)]
    assert rows[1]["opening"] == rows[0]["closing"]


@pytest.mark.parametrize("receipts,payments,floor", [([-1], [0], 0), ([1], [-1], 0), ([1], [0], -1), ([], [], 0), ([1], [1, 2], 0)])
def test_cash_invalid_magnitudes_and_lengths(receipts, payments, floor):
    with pytest.raises(ValueError):
        cash_forecast(0, receipts, payments, floor)


def test_earned_value_and_undefined_startup_metrics():
    result = earned_value(1000, 500, 400, 500)
    assert result["cpi"] == D("0.8")
    assert result["spi"] == D("0.8")
    assert result["estimate_at_completion"] == 1250
    assert result["estimate_to_complete"] == 750
    assert result["variance_at_completion"] == -250
    assert earned_value(100, 0, 0, 0)["cpi"] is None
    assert earned_value(100, 0, 0, 0)["estimate_at_completion"] is None
    with pytest.raises(ValueError):
        earned_value(100, 110, 50, 50)


def test_projection_working_capital_and_cash_bridge():
    row = annual_projection(1000, ["0.10"], "0.40", "0.20", "0.02", "0.03", "0.10", "0.25")[0]
    # Revenue 1,100; COGS 660; OPEX 220; EBITDA 220; D&A 22;
    # EBIT 198; tax 49.50; capex 33; NWC change 10; FCFF 127.50.
    assert row["revenue"] == 1100
    assert row["ebitda"] == 220
    assert row["cash_tax"] == D("49.50")
    assert row["change_in_working_capital"] == 10
    assert row["free_cash_flow"] == D("127.50")


def test_projection_explicit_opening_nwc_and_loss_has_no_tax_refund():
    row = annual_projection(1000, [0], gross_margin="0.10", operating_cost_rate="0.20",
                            depreciation_rate=0, capex_rate=0, working_capital_rate="0.10",
                            tax_rate="0.25", opening_working_capital=0)[0]
    assert row["ebit"] == -100
    assert row["cash_tax"] == 0
    assert row["change_in_working_capital"] == 100
    assert row["free_cash_flow"] == -200


def test_projection_growth_compounds_from_each_prior_year():
    rows = annual_projection(1000, ["0.10", "-0.10"])
    assert [row["revenue"] for row in rows] == [D(1100), D(990)]
    with pytest.raises(ValueError):
        annual_projection(1000, [-1])


def test_dcf_zero_growth_perpetuity():
    near(dcf([100], "0.10", 0)["enterprise_value"], 1000)


def test_dcf_terminal_default_remains_at_year_end_when_forecast_is_midyear():
    normal = dcf([100], "0.10", 0)
    middle = dcf([100], "0.10", 0, midyear=True)
    near(middle["pv_terminal"], normal["pv_terminal"])
    assert middle["pv_forecast"] > normal["pv_forecast"]
    assert middle["terminal_discount_period"] == 1
    all_middle = dcf([100], "0.10", 0, midyear=True, terminal_timing="midyear")
    assert all_middle["terminal_discount_period"] == D("0.5")
    assert all_middle["pv_terminal"] > middle["pv_terminal"]


def test_dcf_net_cash_bridge_and_negative_flows_allowed():
    result = dcf([-20, 100], "0.10", "0.02", net_debt=-50)
    assert result["equity_value"] - result["enterprise_value"] == 50


@pytest.mark.parametrize("rate,growth", [("0.03", "0.03"), ("0.02", "0.03"), ("0.10", "-1"), ("NaN", "0.02")])
def test_dcf_invalid_rate_growth(rate, growth):
    with pytest.raises(ValueError):
        dcf([100], rate, growth)


def test_sensitivity_keeps_invalid_cells_visible():
    rows = dcf_sensitivity([100], ["0.03", "0.10"], ["0.02", "0.03"])
    assert len(rows) == 4
    assert rows[1]["status"] == "INVALID_RATE_GROWTH"
    assert rows[1]["enterprise_value"] is None
    assert rows[0]["enterprise_value"] > rows[2]["enterprise_value"]


def test_acquisition_no_tax_refund_and_explicit_interest():
    good = acquisition_case(100, 5, 200, "0.1", synergies=20, integration_cost=10, tax_rate="0.25")
    assert good["purchase_price"] == 500
    assert good["equity_financing"] == 300
    assert good["annual_interest"] == 20
    assert good["first_year_pre_tax_contribution"] == 90
    assert good["illustrative_after_tax_contribution"] == D("67.50")
    loss = acquisition_case(100, 5, 200, "0.1", integration_cost=200, tax_rate="0.25")
    assert loss["illustrative_after_tax_contribution"] == -120
    assert acquisition_case(100, 5, 0, 0)["interest_coverage"] is None


def test_acquisition_financing_cannot_exceed_proxy_price():
    with pytest.raises(ValueError):
        acquisition_case(100, 5, 501, "0.10")


def test_scaling_one_thousand_to_one_billion_keeps_economics_consistent():
    small = annual_projection(1000, ["0.10", "0.08", "0.05"])
    large = annual_projection(1_000_000_000, ["0.10", "0.08", "0.05"])
    for low, high in zip(small, large):
        assert high["free_cash_flow"] == low["free_cash_flow"] * 1_000_000
    small_dcf = dcf([row["free_cash_flow"] for row in small], "0.12", "0.02")
    large_dcf = dcf([row["free_cash_flow"] for row in large], "0.12", "0.02")
    near(large_dcf["enterprise_value"], small_dcf["enterprise_value"] * 1_000_000, "0.00001")
