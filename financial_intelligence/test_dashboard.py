"""AppTest exercises real dashboard code without requiring a browser session."""
from pathlib import Path
import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).with_name("dashboard.py"))


@pytest.mark.parametrize("mode", ["Overview", "Construction bid", "Project forecast", "13-week cash",
                                 "Annual projection", "DCF valuation", "Acquisition screening", "Ledger data"])
def test_each_workspace_renders(mode):
    app = AppTest.from_file(APP, default_timeout=20).run()
    app.radio(key="mode").set_value(mode).run()
    assert not app.exception, list(app.exception)
    assert not app.error, [error.value for error in app.error]
    if mode not in ("Overview", "Ledger data"):
        assert len(app.metric) >= 3


def test_cash_results_respond_to_inputs():
    app = AppTest.from_file(APP, default_timeout=20).run()
    app.radio(key="mode").set_value("13-week cash").run()
    app.text_input(key="cash_opening").set_value("1000").run()
    assert not app.exception
    assert app.metric[0].value == "USD -64,000.00"
    assert app.metric[2].value == "USD 89,000.00"


def test_dcf_rejects_invalid_growth_without_crashing():
    app = AppTest.from_file(APP, default_timeout=20).run()
    app.radio(key="mode").set_value("DCF valuation").run()
    app.number_input(key="dcf_growth").set_value(12.0).run()
    assert not app.exception
    assert len(app.error) == 1
    assert "discount rate > terminal growth" in app.error[0].value


def test_invalid_nonfinite_money_displays_validation():
    app = AppTest.from_file(APP, default_timeout=20).run()
    app.radio(key="mode").set_value("Annual projection").run()
    app.text_input(key="projection_revenue").set_value("NaN").run()
    assert not app.exception
    assert len(app.error) == 1
    assert "Non-finite" in app.error[0].value
