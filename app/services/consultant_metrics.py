"""
Personal Financial Consultant Metrics Layer (Step 7E).

Deterministic, mathematically pure financial calculations for personal financial consulting.
This module has zero side-effects, does not perform database access, and enforces strict
zero-division guards.
"""

from typing import Optional, Dict, Any


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
