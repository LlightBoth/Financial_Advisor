"""
Step 2B — Extended Financial Metrics Deterministic Test Suite.

Verifies:
1. Basic surplus calculations
2. Deficit handling
3. Zero-income division safety
4. Emergency fund months (essential expense only, not legacy)
5. Legacy expense semantics (legacy ≠ essential)
6. Debt service ratio
7. Unknown debt propagation
8. Explicit zero debt payment
9. Negative cashflow goal timeline
10. Metric-level status (CALCULATED vs UNKNOWN)
11. Legacy 7-field compatibility (rule selection unchanged)
12. Full regression (run via pytest tests/ -v)

Also verifies:
- UNKNOWN ≠ 0 (first-class unknown handling)
- Secondary income UNKNOWN propagation
- MetricEntry structure
"""

import pytest
from app.services.consultant_metrics import (
    calculate_metrics,
    calculate_extended_metrics,
    MetricEntry,
)
from app.services.consultant_engine import ConsultantEngine, CANONICAL_KB_VERSION
from app.security.seed_rule_facts import CONSULTANT_RULES


@pytest.fixture(scope="module")
def standalone_rules():
    """Provides canonical rules with explicit kb_version for standalone evaluation."""
    return [dict(r, kb_version=CANONICAL_KB_VERSION) for r in CONSULTANT_RULES]


# ==============================================================================
# Test 1 — Basic Surplus
# ==============================================================================

def test_extended_basic_surplus():
    """income=2000, expense=1500 → net=500, expense_ratio=0.75, surplus_ratio=0.25"""
    result = calculate_extended_metrics(
        legacy_monthly_income=2000,
        legacy_monthly_expense=1500,
    )
    assert result["net_monthly_cashflow"].value == 500.0
    assert result["net_monthly_cashflow"].status == "CALCULATED"
    assert result["expense_ratio"].value == 0.75
    assert result["expense_ratio"].status == "CALCULATED"
    assert result["surplus_ratio"].value == 0.25
    assert result["surplus_ratio"].status == "CALCULATED"


# ==============================================================================
# Test 2 — Deficit
# ==============================================================================

def test_extended_deficit():
    """income=1500, expense=2000 → net=-500, expense_ratio>1, surplus_ratio<0"""
    result = calculate_extended_metrics(
        legacy_monthly_income=1500,
        legacy_monthly_expense=2000,
    )
    assert result["net_monthly_cashflow"].value == -500.0
    assert result["net_monthly_cashflow"].status == "CALCULATED"
    # 2000 / 1500 = 1.3333
    assert result["expense_ratio"].value is not None
    assert result["expense_ratio"].value > 1.0
    assert result["expense_ratio"].status == "CALCULATED"
    # -500 / 1500 = -0.3333
    assert result["surplus_ratio"].value is not None
    assert result["surplus_ratio"].value < 0
    assert result["surplus_ratio"].status == "CALCULATED"


# ==============================================================================
# Test 3 — Zero Income (no division by zero)
# ==============================================================================

def test_extended_zero_income():
    """income=0, expense=500 → net=-500, ratios=null (NOT_APPLICABLE)"""
    result = calculate_extended_metrics(
        legacy_monthly_income=0,
        legacy_monthly_expense=500,
    )
    assert result["net_monthly_cashflow"].value == -500.0
    assert result["net_monthly_cashflow"].status == "CALCULATED"
    # Ratios with zero income: NOT_APPLICABLE (not division-by-zero)
    assert result["expense_ratio"].value is None
    assert result["expense_ratio"].status == "NOT_APPLICABLE"
    assert result["surplus_ratio"].value is None
    assert result["surplus_ratio"].status == "NOT_APPLICABLE"


# ==============================================================================
# Test 4 — Emergency Fund Months
# ==============================================================================

def test_extended_emergency_fund():
    """emergency=3000, essential=1000 → 3.0 months"""
    result = calculate_extended_metrics(
        legacy_monthly_income=3000,
        essential_monthly_expense=1000,
        discretionary_monthly_expense=500,
        current_emergency_savings=3000,
    )
    assert result["emergency_fund_months"].value == 3.0
    assert result["emergency_fund_months"].status == "CALCULATED"
    assert "essential_monthly_expense" in result["emergency_fund_months"].inputs
    assert "current_emergency_savings" in result["emergency_fund_months"].inputs


# ==============================================================================
# Test 5 — Legacy Expense Semantics
#
# CRITICAL: legacy_monthly_expense = total, NOT essential.
# emergency_fund_months must remain UNKNOWN when only legacy expense is provided.
# ==============================================================================

def test_extended_legacy_expense_not_essential():
    """legacy_expense=1200, essential=UNKNOWN → total=1200, essential=UNKNOWN, emergency=UNKNOWN"""
    result = calculate_extended_metrics(
        legacy_monthly_income=2000,
        legacy_monthly_expense=1200,
    )
    # Total expense uses legacy value
    assert result["total_monthly_expense"].value == 1200.0
    assert result["total_monthly_expense"].status == "CALCULATED"
    # Essential expense is UNKNOWN (legacy is NOT essential)
    assert result["essential_monthly_expense"].value is None
    assert result["essential_monthly_expense"].status == "UNKNOWN"
    # Emergency fund requires essential expense → UNKNOWN
    assert result["emergency_fund_months"].value is None
    assert result["emergency_fund_months"].status == "UNKNOWN"


# ==============================================================================
# Test 6 — Debt Service Ratio
# ==============================================================================

def test_extended_debt_service_ratio():
    """income=2000, debt_payment=300 → debt_service_ratio=0.15"""
    result = calculate_extended_metrics(
        legacy_monthly_income=2000,
        legacy_monthly_expense=1500,
        monthly_debt_payment=300,
    )
    assert result["debt_service_ratio"].value == 0.15
    assert result["debt_service_ratio"].status == "CALCULATED"


# ==============================================================================
# Test 7 — Unknown Debt
# ==============================================================================

def test_extended_unknown_debt():
    """monthly_debt_payment=None → debt_service_ratio=UNKNOWN"""
    result = calculate_extended_metrics(
        legacy_monthly_income=2000,
        legacy_monthly_expense=1500,
        monthly_debt_payment=None,
    )
    assert result["debt_service_ratio"].value is None
    assert result["debt_service_ratio"].status == "UNKNOWN"


# ==============================================================================
# Test 8 — Explicit Zero Debt Payment
#
# Explicit zero is NOT UNKNOWN. It means the user confirmed zero debt payment.
# ==============================================================================

def test_extended_explicit_zero_debt_payment():
    """monthly_debt_payment=0 → debt_service_ratio=0.0 (CALCULATED, not UNKNOWN)"""
    result = calculate_extended_metrics(
        legacy_monthly_income=2000,
        legacy_monthly_expense=1500,
        monthly_debt_payment=0,
    )
    assert result["debt_service_ratio"].value == 0.0
    assert result["debt_service_ratio"].status == "CALCULATED"


# ==============================================================================
# Test 9 — Negative Cashflow Goal
# ==============================================================================

def test_extended_negative_cashflow_goal():
    """net_cashflow<0, goal>0 → natural_goal_months=UNKNOWN"""
    result = calculate_extended_metrics(
        legacy_monthly_income=1000,
        legacy_monthly_expense=1500,
        goal_cost=5000,
    )
    assert result["natural_goal_months"].value is None
    assert result["natural_goal_months"].status == "UNKNOWN"


# ==============================================================================
# Test 10 — Metric-Level Status (CALCULATED vs UNKNOWN)
#
# This is metric-level calculation metadata, NOT PABL slot provenance.
# ==============================================================================

def test_extended_metric_status():
    """Calculated metrics → CALCULATED; missing inputs → UNKNOWN"""
    result = calculate_extended_metrics(
        legacy_monthly_income=2000,
        legacy_monthly_expense=1000,
        monthly_debt_payment=200,
        goal_cost=5000,
    )
    # Calculated metrics
    assert result["total_monthly_income"].status == "CALCULATED"
    assert result["total_monthly_expense"].status == "CALCULATED"
    assert result["net_monthly_cashflow"].status == "CALCULATED"
    assert result["expense_ratio"].status == "CALCULATED"
    assert result["surplus_ratio"].status == "CALCULATED"
    assert result["debt_service_ratio"].status == "CALCULATED"
    assert result["natural_goal_months"].status == "CALCULATED"
    # Unknown metrics (essential expense and emergency savings not provided)
    assert result["essential_monthly_expense"].status == "UNKNOWN"
    assert result["discretionary_monthly_expense"].status == "UNKNOWN"
    assert result["emergency_fund_months"].status == "UNKNOWN"


# ==============================================================================
# Test 11 — Legacy Compatibility (rule selection unchanged)
#
# Verifies that the legacy calculate_metrics() function and ConsultantEngine
# continue producing identical rule selections for all canonical scenarios.
# ==============================================================================

def test_legacy_rule_selection_unchanged(standalone_rules):
    """Legacy 7-field payloads must still select the same canonical rules."""
    # Scenario A: Balanced Budget (expense_ratio 0.50)
    user_a = {
        "income": 1000.0, "expense": 500.0,
        "debt_status": "no debt", "employment_status": "employed",
        "spending_habit": "average spend", "goal_cost": 5000.0,
    }
    eval_a = ConsultantEngine.evaluate(user_a, rules=standalone_rules)
    assert eval_a["selected_advice"].rule_id == "BALANCED_BUDGET_BUFFER_BUILDING"

    # Scenario B: Tight Margin (expense_ratio 0.90)
    user_b = {
        "income": 1000.0, "expense": 900.0,
        "debt_status": "no debt", "employment_status": "employed",
        "spending_habit": "average spend",
    }
    eval_b = ConsultantEngine.evaluate(user_b, rules=standalone_rules)
    assert eval_b["selected_advice"].rule_id == "TIGHT_MARGIN_HIGH_EXPENSE"

    # Scenario C: Deficit With Debt
    user_c = {
        "income": 1000.0, "expense": 1200.0,
        "debt_status": "debt", "employment_status": "employed",
        "spending_habit": "average spend",
    }
    eval_c = ConsultantEngine.evaluate(user_c, rules=standalone_rules)
    assert eval_c["selected_advice"].rule_id == "DEFICIT_WITH_DEBT"

    # Scenario D: Zero Income Unemployed
    # Both DEFICIT_NO_DEBT and INCOME_ZERO_UNEMPLOYED match at priority 100.
    # Deterministic ordering resolves the tie — either is acceptable.
    user_d = {
        "income": 0.0, "expense": 500.0,
        "debt_status": "no debt", "employment_status": "not employed",
    }
    eval_d = ConsultantEngine.evaluate(user_d, rules=standalone_rules)
    assert eval_d["selected_advice"].rule_id in (
        "INCOME_ZERO_UNEMPLOYED", "DEFICIT_NO_DEBT"
    )
    assert eval_d["selected_advice"].priority == 100

    # Scenario E: Flexible Budget (expense_ratio < 0.50)
    user_e = {
        "income": 1000.0, "expense": 400.0,
        "debt_status": "no debt", "employment_status": "employed",
        "spending_habit": "average spend",
    }
    eval_e = ConsultantEngine.evaluate(user_e, rules=standalone_rules)
    assert eval_e["selected_advice"].rule_id == "FLEXIBLE_BUDGET_CAPITAL_GROWTH"

    # Verify legacy calculate_metrics() is unchanged
    m = calculate_metrics(1000.0, 500.0, goal_cost=5000.0)
    assert m["net_cashflow"] == 500.0
    assert m["expense_ratio"] == 0.50
    assert m["surplus_ratio"] == 0.50
    assert m["natural_goal_months"] == 10.0


# ==============================================================================
# Additional Tests: UNKNOWN ≠ 0, Secondary Income, MetricEntry Structure
# ==============================================================================

def test_unknown_is_not_zero():
    """UNKNOWN (None) must never be coerced to zero."""
    # All inputs UNKNOWN
    result = calculate_extended_metrics()
    assert result["total_monthly_income"].value is None
    assert result["total_monthly_income"].status == "UNKNOWN"
    assert result["total_monthly_expense"].value is None
    assert result["total_monthly_expense"].status == "UNKNOWN"
    assert result["net_monthly_cashflow"].value is None
    assert result["net_monthly_cashflow"].status == "UNKNOWN"
    assert result["expense_ratio"].value is None
    assert result["expense_ratio"].status == "UNKNOWN"
    assert result["surplus_ratio"].value is None
    assert result["surplus_ratio"].status == "UNKNOWN"
    assert result["debt_service_ratio"].value is None
    assert result["debt_service_ratio"].status == "UNKNOWN"
    assert result["emergency_fund_months"].value is None
    assert result["emergency_fund_months"].status == "UNKNOWN"
    assert result["natural_goal_months"].value is None
    assert result["natural_goal_months"].status == "UNKNOWN"


def test_secondary_income_unknown_propagation():
    """
    secondary_monthly_income=None means UNKNOWN (not zero).
    total_monthly_income is UNKNOWN when primary alone is provided
    (Step 2A does not define absent secondary income as known zero).
    """
    result = calculate_extended_metrics(
        primary_monthly_income=2000,
        secondary_monthly_income=None,
    )
    assert result["total_monthly_income"].value is None
    assert result["total_monthly_income"].status == "UNKNOWN"


def test_secondary_income_explicit_zero():
    """secondary_monthly_income=0 (explicit zero) → total = primary + 0."""
    result = calculate_extended_metrics(
        primary_monthly_income=2000,
        secondary_monthly_income=0,
    )
    assert result["total_monthly_income"].value == 2000.0
    assert result["total_monthly_income"].status == "CALCULATED"


def test_primary_and_secondary_income():
    """Both primary and secondary known → total = sum."""
    result = calculate_extended_metrics(
        primary_monthly_income=1000,
        secondary_monthly_income=200,
        legacy_monthly_expense=900,
    )
    assert result["total_monthly_income"].value == 1200.0
    assert result["total_monthly_income"].status == "CALCULATED"
    assert result["net_monthly_cashflow"].value == 300.0


def test_metric_entry_structure():
    """MetricEntry is a NamedTuple with (value, status, inputs, formula)."""
    result = calculate_extended_metrics(
        legacy_monthly_income=2000,
        legacy_monthly_expense=1000,
    )
    entry = result["net_monthly_cashflow"]
    assert isinstance(entry, MetricEntry)
    assert isinstance(entry, tuple)
    assert hasattr(entry, "value")
    assert hasattr(entry, "status")
    assert hasattr(entry, "inputs")
    assert hasattr(entry, "formula")
    assert entry.value == 1000.0
    assert entry.status == "CALCULATED"
    assert isinstance(entry.inputs, list)
    assert isinstance(entry.formula, str)


def test_essential_discretionary_expense_breakdown():
    """Both essential and discretionary known → total = sum, emergency fund works."""
    result = calculate_extended_metrics(
        legacy_monthly_income=3000,
        essential_monthly_expense=800,
        discretionary_monthly_expense=400,
        current_emergency_savings=2400,
    )
    assert result["total_monthly_expense"].value == 1200.0
    assert result["essential_monthly_expense"].value == 800.0
    assert result["discretionary_monthly_expense"].value == 400.0
    assert result["emergency_fund_months"].value == 3.0  # 2400 / 800


def test_legacy_calculate_metrics_unchanged():
    """
    Verifies the legacy calculate_metrics() function signature and behavior
    are completely preserved.
    """
    # Test A: income=1000, expense=500, goal=5000
    res = calculate_metrics(1000.0, 500.0, goal_cost=5000.0)
    assert res["monthly_income"] == 1000.0
    assert res["monthly_expense"] == 500.0
    assert res["goal_cost"] == 5000.0
    assert res["net_cashflow"] == 500.0
    assert res["expense_ratio"] == 0.50
    assert res["surplus_ratio"] == 0.50
    assert res["natural_goal_months"] == 10.0

    # Test B: zero income (no division by zero)
    res2 = calculate_metrics(0.0, 500.0)
    assert res2["net_cashflow"] == -500.0
    assert res2["expense_ratio"] is None
    assert res2["surplus_ratio"] is None
    assert res2["natural_goal_months"] is None

    # Test C: None income → 0.0 (legacy behavior, unchanged)
    res3 = calculate_metrics(None, 100.0)
    assert res3["monthly_income"] == 0.0
    assert res3["net_cashflow"] == -100.0

    # Test D: negative clamping (legacy behavior, unchanged)
    res4 = calculate_metrics(-500.0, 100.0)
    assert res4["monthly_income"] == 0.0
