"""Integrated five-year management-planning model.

Run from the repository root:
python financial_intelligence/integrated_model.py \
  --actuals financial_intelligence/integrated_model_actuals.json \
  --assumptions financial_intelligence/integrated_model_assumptions.csv \
  --output-dir output/integrated-model
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

SCENARIOS = ("base", "downside", "upside")
YEARS = 5
RATIO_FIELDS = (
    "cogs_pct_revenue",
    "operating_expense_pct_revenue",
    "capex_pct_revenue",
    "depreciation_pct_revenue",
    "tax_rate",
)
ASSUMPTION_FIELDS = (
    "revenue_growth",
    "cogs_pct_revenue",
    "operating_expense_pct_revenue",
    "capex_pct_revenue",
    "depreciation_pct_revenue",
    "ar_days",
    "inventory_days",
    "ap_days",
    "term_debt_rate",
    "revolver_rate",
    "tax_rate",
    "term_principal_repayment",
    "dividends",
)
AUDIT_FIELDS = (
    "source_reference",
    "source_date",
    "preparer",
    "reviewer",
    "review_status",
)
ZERO = Decimal("0")
ONE = Decimal("1")


def fail(message: str) -> None:
    raise ValueError(message)


def decimal_value(value: object, label: str) -> Decimal:
    if value is None or isinstance(value, bool) or str(value).strip() == "":
        fail(f"{label} is required.")
    try:
        result = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        fail(f"{label} must be a valid decimal number.")
    if not result.is_finite():
        fail(f"{label} must be finite.")
    return result


def money(value: Decimal, quantum: Decimal) -> Decimal:
    return value.quantize(quantum, rounding=ROUND_HALF_UP)


def nonnegative(value: Decimal, label: str) -> Decimal:
    if value < ZERO:
        fail(f"{label} cannot be negative.")
    return value


def load_actuals(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"Cannot read actuals JSON: {exc}")
    if not isinstance(data, dict):
        fail("Actuals file must contain a JSON object.")

    entity = str(data.get("entity_name", "")).strip()
    currency = str(data.get("currency", "")).strip().upper()
    if not entity:
        fail("entity_name is required.")
    if not re.fullmatch(r"[A-Z]{3}", currency):
        fail("currency must be a three-letter uppercase currency code.")
    try:
        base_year = int(data.get("base_year"))
        digits = int(data.get("minor_unit_digits"))
        years = int(data.get("forecast_years"))
    except (TypeError, ValueError):
        fail("base_year, minor_unit_digits and forecast_years must be integers.")
    if base_year < 1 or base_year > 9993:
        fail("base_year must allow five forecast years.")
    if years != YEARS:
        fail(f"forecast_years must be {YEARS} for this version.")
    if digits < 0 or digits > 4:
        fail("minor_unit_digits must be between 0 and 4.")
    quantum = Decimal(1).scaleb(-digits)

    try:
        floor = nonnegative(decimal_value(data.get("minimum_cash"), "minimum_cash"), "minimum_cash")
        limit = nonnegative(decimal_value(data.get("revolver_limit"), "revolver_limit"), "revolver_limit")
        actual_pl = data["base_year_income_statement"]
        opening = data["closing_base_year_balance_sheet"]
    except (KeyError, TypeError) as exc:
        fail(f"Missing actuals section or field: {exc}")
    if not isinstance(actual_pl, dict) or not isinstance(opening, dict):
        fail("base_year_income_statement and closing_base_year_balance_sheet must be JSON objects.")

    pl = {}
    for key in ("revenue", "cogs", "operating_expenses"):
        pl[key] = money(nonnegative(decimal_value(actual_pl.get(key), f"base_year_income_statement.{key}"), key), quantum)

    bs = {}
    bs_fields = (
        "cash",
        "accounts_receivable",
        "inventory",
        "net_ppe",
        "accounts_payable",
        "term_debt",
        "revolver",
        "share_capital",
        "retained_earnings",
    )
    for key in bs_fields:
        val = decimal_value(opening.get(key), f"closing_base_year_balance_sheet.{key}")
        if key != "retained_earnings":
            val = nonnegative(val, key)
        bs[key] = money(val, quantum)
    if bs["revolver"] > limit:
        fail("Opening revolver balance exceeds revolver_limit.")

    assets = money(bs["cash"] + bs["accounts_receivable"] + bs["inventory"] + bs["net_ppe"], quantum)
    liabilities_equity = money(
        bs["accounts_payable"] + bs["term_debt"] + bs["revolver"]
        + bs["share_capital"] + bs["retained_earnings"],
        quantum,
    )
    opening_difference = money(assets - liabilities_equity, quantum)
    if abs(opening_difference) > quantum:
        fail(
            "Closing base-year balance sheet does not balance: "
            f"assets less liabilities and equity = {opening_difference} {currency}. "
            "Correct the actuals; the model does not plug the difference."
        )

    return {
        "entity_name": entity,
        "currency": currency,
        "base_year": base_year,
        "minor_unit_digits": digits,
        "quantum": quantum,
        "minimum_cash": money(floor, quantum),
        "revolver_limit": money(limit, quantum),
        "pl": pl,
        "opening": bs,
        "opening_balance_check": opening_difference,
    }


def load_assumptions(path: Path, base_year: int, quantum: Decimal) -> dict:
    expected = {(scenario, offset) for scenario in SCENARIOS for offset in range(1, YEARS + 1)}
    found = {}
    try:
        handle = path.open(encoding="utf-8-sig", newline="")
    except OSError as exc:
        fail(f"Cannot read assumptions CSV: {exc}")
    with handle:
        reader = csv.DictReader(handle)
        needed = {"scenario", "year_offset", *ASSUMPTION_FIELDS, *AUDIT_FIELDS, "notes"}
        if reader.fieldnames is None or not needed.issubset(set(reader.fieldnames)):
            missing = sorted(needed - set(reader.fieldnames or []))
            fail("Assumptions CSV is missing columns: " + ", ".join(missing))
        for line, row in enumerate(reader, start=2):
            scenario = str(row.get("scenario", "")).strip().lower()
            try:
                offset = int(str(row.get("year_offset", "")).strip())
            except ValueError:
                fail(f"Row {line}: year_offset must be an integer from 1 to {YEARS}.")
            key = (scenario, offset)
            if key not in expected:
                fail(f"Row {line}: unexpected scenario/year_offset {key}.")
            if key in found:
                fail(f"Row {line}: duplicate assumptions for {scenario}, offset {offset}.")
            values = {}
            for field in ASSUMPTION_FIELDS:
                values[field] = decimal_value(row.get(field), f"row {line} {field}")
                if field in RATIO_FIELDS and not ZERO <= values[field] <= ONE:
                    fail(f"Row {line}: {field} must be between 0 and 1.")
                if field == "revenue_growth" and values[field] <= -ONE:
                    fail(f"Row {line}: revenue_growth must be greater than -1.")
                if field in ("ar_days", "inventory_days", "ap_days",
                             "term_debt_rate", "revolver_rate",
                             "term_principal_repayment", "dividends"):
                    nonnegative(values[field], f"row {line} {field}")
                values[field] = money(values[field], quantum) if field in (
                    "term_principal_repayment", "dividends"
                ) else values[field]
            for field in AUDIT_FIELDS:
                values[field] = str(row.get(field, "")).strip()
                if not values[field]:
                    fail(f"Row {line}: {field} is required for traceability.")
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", values["source_date"]):
                fail(f"Row {line}: source_date must use YYYY-MM-DD.")
            try:
                date.fromisoformat(values["source_date"])
            except ValueError:
                fail(f"Row {line}: source_date is not a valid calendar date.")
            values["review_status"] = values["review_status"].upper()
            if values["review_status"] not in ("DRAFT", "REVIEWED", "APPROVED"):
                fail(f"Row {line}: review_status must be DRAFT, REVIEWED or APPROVED.")
            if values["review_status"] == "APPROVED" and values["preparer"].casefold() == values["reviewer"].casefold():
                fail(f"Row {line}: an APPROVED assumption requires a reviewer different from the preparer.")
            values["notes"] = str(row.get("notes", "")).strip()
            values["year"] = base_year + offset
            values["scenario"] = scenario
            found[key] = values
    missing = sorted(expected - set(found))
    if missing:
        fail("Assumptions CSV must contain exactly one row for every scenario and forecast year. Missing: "
             + ", ".join(f"{s}/+{y}" for s, y in missing))
    return found


def project(actuals: dict, assumptions: dict, selected: str) -> tuple[list[dict], list[dict]]:
    q = actuals["quantum"]
    scenarios = SCENARIOS if selected == "all" else (selected,)
    forecasts, checks = [], []
    for scenario in scenarios:
        opening = dict(actuals["opening"])
        prior_revenue = actuals["pl"]["revenue"]
        for offset in range(1, YEARS + 1):
            a = assumptions[(scenario, offset)]
            year = a["year"]
            revenue = money(prior_revenue * (ONE + a["revenue_growth"]), q)
            cogs = money(revenue * a["cogs_pct_revenue"], q)
            gross_profit = money(revenue - cogs, q)
            opex = money(revenue * a["operating_expense_pct_revenue"], q)
            ebitda = money(gross_profit - opex, q)
            capex = money(revenue * a["capex_pct_revenue"], q)
            depreciation = money(revenue * a["depreciation_pct_revenue"], q)
            if depreciation > opening["net_ppe"] + capex:
                fail(f"{scenario} {year}: depreciation exceeds opening net PPE plus capex.")
            ebit = money(ebitda - depreciation, q)
            interest = money(
                opening["term_debt"] * a["term_debt_rate"]
                + opening["revolver"] * a["revolver_rate"],
                q,
            )
            pretax_income = money(ebit - interest, q)
            tax = money(max(pretax_income, ZERO) * a["tax_rate"], q)
            net_income = money(pretax_income - tax, q)

            ar = money(revenue * a["ar_days"] / Decimal(365), q)
            inventory = money(cogs * a["inventory_days"] / Decimal(365), q)
            ap = money(cogs * a["ap_days"] / Decimal(365), q)
            principal = money(a["term_principal_repayment"], q)
            dividend = money(a["dividends"], q)
            if principal > opening["term_debt"]:
                fail(f"{scenario} {year}: scheduled term-debt repayment exceeds opening term debt.")
            if depreciation > opening["net_ppe"] + capex:
                fail(f"{scenario} {year}: depreciation would make net PPE negative.")

            cfo = money(
                net_income + depreciation
                - (ar - opening["accounts_receivable"])
                - (inventory - opening["inventory"])
                + (ap - opening["accounts_payable"]),
                q,
            )
            cfi = money(-capex, q)
            term_close = money(opening["term_debt"] - principal, q)
            ppe_close = money(opening["net_ppe"] + capex - depreciation, q)
            retained_close = money(opening["retained_earnings"] + net_income - dividend, q)

            cash_before_revolver = money(
                opening["cash"] + cfo + cfi - principal - dividend,
                q,
            )
            draw = ZERO
            revolver_repayment = ZERO
            if cash_before_revolver < actuals["minimum_cash"]:
                need = actuals["minimum_cash"] - cash_before_revolver
                available = max(actuals["revolver_limit"] - opening["revolver"], ZERO)
                draw = money(min(need, available), q)
            elif cash_before_revolver > actuals["minimum_cash"] and opening["revolver"] > ZERO:
                excess = cash_before_revolver - actuals["minimum_cash"]
                revolver_repayment = money(min(excess, opening["revolver"]), q)

            revolver_close = money(opening["revolver"] + draw - revolver_repayment, q)
            cash_close = money(cash_before_revolver + draw - revolver_repayment, q)
            cff = money(draw - principal - revolver_repayment - dividend, q)
            cashflow_close = money(opening["cash"] + cfo + cfi + cff, q)
            cash_check = money(cash_close - cashflow_close, q)

            assets = money(cash_close + ar + inventory + ppe_close, q)
            liabilities_equity = money(
                ap + term_close + revolver_close
                + opening["share_capital"] + retained_close,
                q,
            )
            bs_check = money(assets - liabilities_equity, q)
            term_check = money(term_close - (opening["term_debt"] - principal), q)
            revolver_check = money(revolver_close - (opening["revolver"] + draw - revolver_repayment), q)
            ppe_check = money(ppe_close - (opening["net_ppe"] + capex - depreciation), q)
            retained_check = money(retained_close - (opening["retained_earnings"] + net_income - dividend), q)
            if any(abs(v) > q for v in (cash_check, bs_check, term_check, revolver_check, ppe_check, retained_check)):
                fail(f"{scenario} {year}: a linked-statement control failed; no output was written.")

            liquidity_shortfall = money(max(actuals["minimum_cash"] - cash_close, ZERO), q)
            forecasts.append({
                "entity_name": actuals["entity_name"],
                "scenario": scenario, "year": year, "currency": actuals["currency"],
                "revenue": revenue, "cogs": cogs, "gross_profit": gross_profit,
                "operating_expenses": opex, "ebitda": ebitda, "depreciation": depreciation,
                "ebit": ebit, "interest_expense": interest, "pretax_income": pretax_income,
                "income_tax_estimate": tax, "net_income": net_income,
                "accounts_receivable": ar, "inventory": inventory, "net_ppe": ppe_close,
                "cash": cash_close, "total_assets": assets, "accounts_payable": ap,
                "term_debt": term_close, "revolver": revolver_close,
                "share_capital": opening["share_capital"], "retained_earnings": retained_close,
                "total_liabilities_and_equity": liabilities_equity,
                "cash_from_operations": cfo, "capital_expenditure": capex,
                "cash_from_investing": cfi, "term_principal_repayment": principal,
                "revolver_draw": draw, "revolver_repayment": revolver_repayment,
                "dividends": dividend, "cash_from_financing": cff,
                "cashflow_ending_cash": cashflow_close,
                "revolver_available": money(actuals["revolver_limit"] - revolver_close, q),
                "liquidity_shortfall_to_minimum": liquidity_shortfall,
                **{"input_" + field: a[field] for field in ASSUMPTION_FIELDS},
                "assumption_source_reference": a["source_reference"],
                "assumption_source_date": a["source_date"],
                "assumption_preparer": a["preparer"],
                "assumption_reviewer": a["reviewer"],
                "assumption_review_status": a["review_status"],
                "assumption_notes": a["notes"],
            })
            checks.append({
                "scenario": scenario, "year": year,
                "currency": actuals["currency"],
                "balance_sheet_difference": bs_check,
                "cash_flow_difference": cash_check,
                "term_debt_rollforward_difference": term_check,
                "revolver_rollforward_difference": revolver_check,
                "net_ppe_rollforward_difference": ppe_check,
                "retained_earnings_rollforward_difference": retained_check,
                "core_controls": "PASS",
                "assumption_review_status": a["review_status"],
                "independent_approval": "YES" if a["review_status"] == "APPROVED" else "NO",
                "source_reference": a["source_reference"],
                "source_date": a["source_date"],
                "preparer": a["preparer"],
                "reviewer": a["reviewer"],
                "notes": a["notes"],
                "liquidity_floor": actuals["minimum_cash"],
                "liquidity_shortfall": liquidity_shortfall,
            })
            opening = {
                "cash": cash_close, "accounts_receivable": ar, "inventory": inventory,
                "net_ppe": ppe_close, "accounts_payable": ap, "term_debt": term_close,
                "revolver": revolver_close, "share_capital": opening["share_capital"],
                "retained_earnings": retained_close,
            }
            prior_revenue = revenue
    return forecasts, checks


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        fail(f"No output rows to write for {path.name}.")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow({
                key: format(value, "f") if isinstance(value, Decimal) else value
                for key, value in row.items()
            })


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the integrated five-year management-planning model.")
    parser.add_argument("--actuals", required=True, type=Path, help="Closing actuals JSON.")
    parser.add_argument("--assumptions", required=True, type=Path, help="Scenario assumptions CSV.")
    parser.add_argument("--output-dir", required=True, type=Path, help="Folder for forecast.csv and checks.csv.")
    parser.add_argument("--scenario", choices=(*SCENARIOS, "all"), default="all")
    args = parser.parse_args()
    try:
        actuals = load_actuals(args.actuals)
        assumptions = load_assumptions(args.assumptions, actuals["base_year"], actuals["quantum"])
        forecast, checks = project(actuals, assumptions, args.scenario)
        write_csv(args.output_dir / "forecast.csv", forecast)
        write_csv(args.output_dir / "checks.csv", checks)
    except (ValueError, OSError, KeyError) as exc:
        print(f"MODEL STOPPED: {exc}", file=sys.stderr)
        return 2
    print(f"Wrote {len(forecast)} forecast rows and {len(checks)} control rows to {args.output_dir}.")
    print(f"Entity: {actuals['entity_name']} | Currency: {actuals['currency']} | Scenario: {args.scenario}")
    print("Review checks.csv and the liquidity shortfall column before relying on results.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
