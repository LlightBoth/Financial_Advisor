"""
Personal Financial Consultant Metrics Layer (Step 7E / Step 2B).

Deterministic, mathematically pure financial calculations for personal financial consulting.
This module has zero side-effects, does not perform database access, and enforces strict
zero-division guards.

Step 7E: calculate_metrics() — Legacy 3-argument interface used by ConsultantEngine.
Step 2B: calculate_extended_metrics() — Extended professional financial indicators
         with first-class UNKNOWN handling and metric-level calculation metadata.
"""

from typing import Optional, Dict, Any, List, NamedTuple


def calculate_metrics(
    monthly_income: float,
    monthly_expense: float,
    goal_cost: float = 0.0
) -> Dict[str, Any]:
    """
    Computes core financial consultant metrics.

    Formulas:
        net_cashflow = monthly_income - monthly_expense
        expense_ratio = monthly_expense / monthly_income (when monthly_income > 0 else None)
        surplus_ratio = net_cashflow / monthly_income (when monthly_income > 0 else None)
        natural_goal_months = goal_cost / net_cashflow (when net_cashflow > 0 and goal_cost > 0 else None)

    Mathematical Guarantees:
        - Zero division is impossible.
        - Negative income is treated safely as zero inflow.
        - Natural goal horizon is an objective projection assuming 100% surplus allocation,
          not an arbitrary feasibility verdict.
    """
    # Defensive casting
    income = float(monthly_income) if monthly_income is not None else 0.0
    expense = float(monthly_expense) if monthly_expense is not None else 0.0
    goal = float(goal_cost) if goal_cost is not None else 0.0

    # Ensure non-negative boundary for inputs
    if income < 0.0:
        income = 0.0
    if expense < 0.0:
        expense = 0.0
    if goal < 0.0:
        goal = 0.0

    # 1. Net Cash Flow: Income - Expense
    net_cashflow = income - expense

    # 2. Operating Expense Ratio
    if income > 0.0:
        expense_ratio: Optional[float] = expense / income
    else:
        expense_ratio = None

    # 3. Operating Surplus Ratio: (Income - Expense) / Income == 1.0 - expense_ratio
    if income > 0.0:
        surplus_ratio: Optional[float] = net_cashflow / income
    else:
        surplus_ratio = None

    # 4. Natural Goal Horizon (months): goal_cost / net_cashflow
    if net_cashflow > 0.0 and goal > 0.0:
        natural_goal_months: Optional[float] = goal / net_cashflow
    elif goal == 0.0 and net_cashflow > 0.0:
        natural_goal_months = 0.0
    else:
        natural_goal_months = None

    return {
        "monthly_income": income,
        "monthly_expense": expense,
        "goal_cost": goal,
        "net_cashflow": round(net_cashflow, 4),
        "expense_ratio": round(expense_ratio, 4) if expense_ratio is not None else None,
        "surplus_ratio": round(surplus_ratio, 4) if surplus_ratio is not None else None,
        "natural_goal_months": round(natural_goal_months, 2) if natural_goal_months is not None else None,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Step 2B: Extended Financial Metrics
# ══════════════════════════════════════════════════════════════════════════════


class MetricEntry(NamedTuple):
    """
    Structured result for a single calculated financial metric.

    This is metric-level calculation metadata, NOT Provenance-Aware Boundary
    Layer (PABL) slot provenance. MetricEntry identifies whether a value was
    computed from known inputs or is unknown due to missing information.

    Statuses:
        CALCULATED     — Value was computed from known inputs.
        UNKNOWN        — One or more required inputs are missing (None).
        NOT_APPLICABLE — Metric cannot be meaningfully computed (e.g., ratio
                         with zero denominator, or negative cashflow for goal).
    """
    value: Optional[float]
    status: str  # "CALCULATED", "UNKNOWN", "NOT_APPLICABLE"
    inputs: List[str]
    formula: str


def _is_known(value: Any) -> bool:
    """Returns True if value is a known numeric value (including explicit zero)."""
    return value is not None


def _safe_float(value: Any) -> Optional[float]:
    """Converts value to float if known, returns None if UNKNOWN (None)."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def calculate_extended_metrics(
    *,
    primary_monthly_income: Optional[float] = None,
    secondary_monthly_income: Optional[float] = None,
    legacy_monthly_income: Optional[float] = None,
    essential_monthly_expense: Optional[float] = None,
    discretionary_monthly_expense: Optional[float] = None,
    legacy_monthly_expense: Optional[float] = None,
    monthly_debt_payment: Optional[float] = None,
    current_emergency_savings: Optional[float] = None,
    goal_cost: Optional[float] = None,
) -> Dict[str, MetricEntry]:
    """
    Extended Financial Metrics (Step 2B).

    Computes professional financial indicators from the canonical data contract
    with first-class UNKNOWN handling. Each metric is returned as a MetricEntry
    with its value, calculation status, input fields, and formula.

    UNKNOWN (None) vs Explicit Zero (0):
        - None means the system does not know the value. It is never coerced to 0.
        - 0 means the user explicitly provided zero. It produces valid calculations.

    Legacy Expense Semantics:
        - legacy_monthly_expense represents total monthly expense from the 7-field
          contract. It is NEVER reinterpreted as essential_monthly_expense.
        - emergency_fund_months requires known essential_monthly_expense, not
          legacy total.

    Secondary Income Semantics:
        - secondary_monthly_income=None means UNKNOWN (not zero).
        - The Step 2A canonical contract does not define absent secondary income
          as known zero.
        - total_monthly_income is UNKNOWN when secondary_monthly_income is None
          UNLESS legacy_monthly_income is provided as a known total.

    Income Resolution Priority:
        1. primary + secondary (when both known)
        2. legacy_monthly_income (fallback total)
        3. UNKNOWN

    Expense Resolution Priority:
        1. essential + discretionary (when both known)
        2. legacy_monthly_expense (fallback total)
        3. UNKNOWN

    This function has zero side-effects: no database, no HTTP, no LLM, no
    global state.

    Returns:
        Dict[str, MetricEntry] where each key is a metric name and each value
        is a MetricEntry(value, status, inputs, formula).
    """
    results: Dict[str, MetricEntry] = {}

    # Safe float conversions (preserving None as UNKNOWN)
    p_income = _safe_float(primary_monthly_income)
    s_income = _safe_float(secondary_monthly_income)
    l_income = _safe_float(legacy_monthly_income)
    e_expense = _safe_float(essential_monthly_expense)
    d_expense = _safe_float(discretionary_monthly_expense)
    l_expense = _safe_float(legacy_monthly_expense)
    debt_pay = _safe_float(monthly_debt_payment)
    emerg_sav = _safe_float(current_emergency_savings)
    goal = _safe_float(goal_cost)

    # ─────────────────────────────────────────────────────────────
    # 1. Total Monthly Income
    # ─────────────────────────────────────────────────────────────
    total_income: Optional[float] = None

    if _is_known(p_income) and _is_known(s_income):
        # Both primary and secondary are known (including explicit zero)
        total_income = p_income + s_income
        results["total_monthly_income"] = MetricEntry(
            value=round(total_income, 4),
            status="CALCULATED",
            inputs=["primary_monthly_income", "secondary_monthly_income"],
            formula="primary_monthly_income + secondary_monthly_income",
        )
    elif _is_known(l_income):
        # Legacy total income provided as a known value
        total_income = l_income
        results["total_monthly_income"] = MetricEntry(
            value=round(total_income, 4),
            status="CALCULATED",
            inputs=["legacy_monthly_income"],
            formula="legacy_monthly_income",
        )
    else:
        # Cannot determine total: primary alone + unknown secondary = UNKNOWN
        # (Step 2A contract does not define absent secondary income as known zero)
        results["total_monthly_income"] = MetricEntry(
            value=None,
            status="UNKNOWN",
            inputs=[],
            formula="insufficient inputs",
        )

    # ─────────────────────────────────────────────────────────────
    # 2. Total Monthly Expense
    # ─────────────────────────────────────────────────────────────
    total_expense: Optional[float] = None
    essential_known = _is_known(e_expense)

    if _is_known(e_expense) and _is_known(d_expense):
        # Both essential and discretionary known
        total_expense = e_expense + d_expense
        results["total_monthly_expense"] = MetricEntry(
            value=round(total_expense, 4),
            status="CALCULATED",
            inputs=["essential_monthly_expense", "discretionary_monthly_expense"],
            formula="essential_monthly_expense + discretionary_monthly_expense",
        )
    elif _is_known(l_expense):
        # Legacy total expense as fallback (NOT essential expense)
        total_expense = l_expense
        results["total_monthly_expense"] = MetricEntry(
            value=round(total_expense, 4),
            status="CALCULATED",
            inputs=["legacy_monthly_expense"],
            formula="legacy_monthly_expense",
        )
    else:
        results["total_monthly_expense"] = MetricEntry(
            value=None,
            status="UNKNOWN",
            inputs=[],
            formula="insufficient inputs",
        )

    # Essential and discretionary sub-metrics (passthrough, not reinterpreted)
    results["essential_monthly_expense"] = MetricEntry(
        value=round(e_expense, 4) if essential_known else None,
        status="CALCULATED" if essential_known else "UNKNOWN",
        inputs=["essential_monthly_expense"] if essential_known else [],
        formula="essential_monthly_expense" if essential_known else "not provided",
    )
    results["discretionary_monthly_expense"] = MetricEntry(
        value=round(d_expense, 4) if _is_known(d_expense) else None,
        status="CALCULATED" if _is_known(d_expense) else "UNKNOWN",
        inputs=["discretionary_monthly_expense"] if _is_known(d_expense) else [],
        formula="discretionary_monthly_expense" if _is_known(d_expense) else "not provided",
    )

    # ─────────────────────────────────────────────────────────────
    # 3. Net Monthly Cash Flow
    # ─────────────────────────────────────────────────────────────
    net_cashflow: Optional[float] = None

    if _is_known(total_income) and _is_known(total_expense):
        net_cashflow = total_income - total_expense
        results["net_monthly_cashflow"] = MetricEntry(
            value=round(net_cashflow, 4),
            status="CALCULATED",
            inputs=["total_monthly_income", "total_monthly_expense"],
            formula="total_monthly_income - total_monthly_expense",
        )
    else:
        results["net_monthly_cashflow"] = MetricEntry(
            value=None,
            status="UNKNOWN",
            inputs=[],
            formula="total_monthly_income - total_monthly_expense (inputs UNKNOWN)",
        )

    # ─────────────────────────────────────────────────────────────
    # 4. Expense Ratio
    # ─────────────────────────────────────────────────────────────
    if not _is_known(total_expense) or not _is_known(total_income):
        results["expense_ratio"] = MetricEntry(
            value=None,
            status="UNKNOWN",
            inputs=[],
            formula="total_monthly_expense / total_monthly_income (inputs UNKNOWN)",
        )
    elif total_income == 0:
        results["expense_ratio"] = MetricEntry(
            value=None,
            status="NOT_APPLICABLE",
            inputs=["total_monthly_income"],
            formula="total_monthly_expense / total_monthly_income (income is zero)",
        )
    else:
        results["expense_ratio"] = MetricEntry(
            value=round(total_expense / total_income, 4),
            status="CALCULATED",
            inputs=["total_monthly_expense", "total_monthly_income"],
            formula="total_monthly_expense / total_monthly_income",
        )

    # ─────────────────────────────────────────────────────────────
    # 5. Surplus Ratio
    # ─────────────────────────────────────────────────────────────
    if not _is_known(net_cashflow) or not _is_known(total_income):
        results["surplus_ratio"] = MetricEntry(
            value=None,
            status="UNKNOWN",
            inputs=[],
            formula="net_monthly_cashflow / total_monthly_income (inputs UNKNOWN)",
        )
    elif total_income == 0:
        results["surplus_ratio"] = MetricEntry(
            value=None,
            status="NOT_APPLICABLE",
            inputs=["total_monthly_income"],
            formula="net_monthly_cashflow / total_monthly_income (income is zero)",
        )
    else:
        results["surplus_ratio"] = MetricEntry(
            value=round(net_cashflow / total_income, 4),
            status="CALCULATED",
            inputs=["net_monthly_cashflow", "total_monthly_income"],
            formula="net_monthly_cashflow / total_monthly_income",
        )

    # ─────────────────────────────────────────────────────────────
    # 6. Debt Service Ratio
    # ─────────────────────────────────────────────────────────────
    if not _is_known(debt_pay):
        results["debt_service_ratio"] = MetricEntry(
            value=None,
            status="UNKNOWN",
            inputs=[],
            formula="monthly_debt_payment / total_monthly_income (debt payment UNKNOWN)",
        )
    elif not _is_known(total_income):
        results["debt_service_ratio"] = MetricEntry(
            value=None,
            status="UNKNOWN",
            inputs=["monthly_debt_payment"],
            formula="monthly_debt_payment / total_monthly_income (income UNKNOWN)",
        )
    elif total_income == 0:
        results["debt_service_ratio"] = MetricEntry(
            value=None,
            status="NOT_APPLICABLE",
            inputs=["monthly_debt_payment", "total_monthly_income"],
            formula="monthly_debt_payment / total_monthly_income (income is zero)",
        )
    else:
        results["debt_service_ratio"] = MetricEntry(
            value=round(debt_pay / total_income, 4),
            status="CALCULATED",
            inputs=["monthly_debt_payment", "total_monthly_income"],
            formula="monthly_debt_payment / total_monthly_income",
        )

    # ─────────────────────────────────────────────────────────────
    # 7. Emergency Fund Months
    #
    # CRITICAL: Uses ONLY known essential_monthly_expense.
    # Legacy total expense is NEVER used as essential expense.
    # ─────────────────────────────────────────────────────────────
    if not _is_known(emerg_sav) or not essential_known:
        missing = []
        if not _is_known(emerg_sav):
            missing.append("current_emergency_savings")
        if not essential_known:
            missing.append("essential_monthly_expense")
        results["emergency_fund_months"] = MetricEntry(
            value=None,
            status="UNKNOWN",
            inputs=[],
            formula=f"current_emergency_savings / essential_monthly_expense "
                    f"({', '.join(missing)} UNKNOWN)",
        )
    elif e_expense == 0:
        results["emergency_fund_months"] = MetricEntry(
            value=None,
            status="NOT_APPLICABLE",
            inputs=["current_emergency_savings", "essential_monthly_expense"],
            formula="current_emergency_savings / essential_monthly_expense "
                    "(essential expense is zero)",
        )
    else:
        results["emergency_fund_months"] = MetricEntry(
            value=round(emerg_sav / e_expense, 2),
            status="CALCULATED",
            inputs=["current_emergency_savings", "essential_monthly_expense"],
            formula="current_emergency_savings / essential_monthly_expense",
        )

    # ─────────────────────────────────────────────────────────────
    # 8. Natural Goal Months
    #
    # Matches the legacy calculate_metrics() behavior:
    #   - goal > 0, cashflow > 0: goal / cashflow
    #   - goal == 0, cashflow > 0: 0.0 (already achieved)
    #   - cashflow <= 0: NOT_APPLICABLE (cannot fund)
    # ─────────────────────────────────────────────────────────────
    if not _is_known(goal) or not _is_known(net_cashflow):
        results["natural_goal_months"] = MetricEntry(
            value=None,
            status="UNKNOWN",
            inputs=[],
            formula="goal_cost / net_monthly_cashflow (inputs UNKNOWN)",
        )
    elif net_cashflow > 0 and goal > 0:
        results["natural_goal_months"] = MetricEntry(
            value=round(goal / net_cashflow, 2),
            status="CALCULATED",
            inputs=["goal_cost", "net_monthly_cashflow"],
            formula="goal_cost / net_monthly_cashflow",
        )
    elif net_cashflow > 0 and goal == 0:
        results["natural_goal_months"] = MetricEntry(
            value=0.0,
            status="CALCULATED",
            inputs=["goal_cost"],
            formula="goal_cost is zero (already achieved)",
        )
    else:
        # net_cashflow <= 0: cannot fund goal from deficit or break-even
        results["natural_goal_months"] = MetricEntry(
            value=None,
            status="NOT_APPLICABLE",
            inputs=["goal_cost", "net_monthly_cashflow"],
            formula="goal_cost / net_monthly_cashflow (cashflow is zero or negative)",
        )

    return results
