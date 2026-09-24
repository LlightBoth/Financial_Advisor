"""
Tests verifying Option 1:
Authoritative User Financial Profile loaded from live Income and Expense tracker tables,
superseding legacy History table.
"""

import pytest
from datetime import date
from app import create_app
from config import Config
from extension import db
from app.models.user import User
from app.models.role import Role
from app.models.income import Income
from app.models.expense import Expense
from app.models.plan import Plan
from app.models.history import History
from app.services.advisor_services import AdvisorServices
from app.services.income_services import IncomeServices
from app.services.expense_services import ExpenseServices
from app.services.history_services import HistoryServices


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {}
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-tracker-priority-key"


@pytest.fixture(name="app")
def fixture_app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        role = Role.query.filter_by(name="user").first()
        if not role:
            role = Role(name="user", description="User")
            db.session.add(role)
            db.session.commit()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


def test_tracker_tables_supersede_stale_history(app):
    """
    Given a user with:
      - Old History: Income=$2500, Expense=$2000
      - Live Incomes: $500 (Salary)
      - Live Expenses: $120 (Food)
      - Live Plan: $12,000 (Goal)
    Verify AdvisorServices.get_user_financial_profile returns:
      - monthly_income: 500.0
      - monthly_expense: 120.0
      - goal_cost: 12000.0
    """
    with app.app_context():
        user = User(username="tracker_user", full_name="Tracker User", email="tracker@example.com")
        user.set_password("Password123!")
        db.session.add(user)
        db.session.commit()

        # 1. Create stale History record
        stale_history = {
            "goal_cost": 500.0,
            "income": 2500.0,
            "expense": 2000.0,
            "martial_status": "Married",
            "is_employed": "employed",
            "is_debt": "no debt",
            "is_spending": "average spend",
            "remain_percentage": 20.0,
            "expense_percentage": 80.0,
            "get_advice": None,
            "kb_version": "financial-kb-v1.0"
        }
        HistoryServices.create(stale_history, user)

        # 2. Add Live Income
        inc = Income(
            amount=500.0,
            category="Salary",
            income_date=date.today(),
            description="Monthly Paycheck"
        )
        inc.users.append(user)
        db.session.add(inc)

        # 3. Add Live Expense
        exp = Expense(
            amount=120.0,
            category="Food",
            expense_date=date.today(),
            description="Groceries"
        )
        exp.users.append(user)
        db.session.add(exp)

        # 4. Add Live Plan
        plan = Plan(
            goal="Buy Car",
            goal_cost=12000.0,
            in_between=date.today(),
            marital_status="Single",
            employment_status="employed",
            debt_status="no debt",
            spending_habit="average spend"
        )
        plan.users.append(user)
        db.session.add(plan)
        db.session.commit()

        # 5. Fetch profile
        profile = AdvisorServices.get_user_financial_profile(user)
        assert profile is not None
        assert profile["monthly_income"] == 500.0
        assert profile["monthly_expense"] == 120.0
        assert profile["goal_cost"] == 12000.0
        assert profile["marital_status"] == "Single"
        assert profile["employment_status"] == "employed"
        assert profile["debt_status"] == "no debt"


def test_tracker_fallback_to_history_when_no_tracker_data(app):
    """
    If a user has 0 tracker entries, it gracefully falls back to legacy History.
    """
    with app.app_context():
        user = User(username="legacy_user", full_name="Legacy User", email="legacy@example.com")
        user.set_password("Password123!")
        db.session.add(user)
        db.session.commit()

        legacy_history = {
            "goal_cost": 300.0,
            "income": 1000.0,
            "expense": 750.0,
            "martial_status": "Single",
            "is_employed": "employed",
            "is_debt": "debt",
            "is_spending": "big spend",
            "remain_percentage": 25.0,
            "expense_percentage": 75.0,
            "get_advice": None,
            "kb_version": "financial-kb-v1.0"
        }
        HistoryServices.create(legacy_history, user)

        profile = AdvisorServices.get_user_financial_profile(user)
        assert profile is not None
        assert profile["monthly_income"] == 1000.0
        assert profile["monthly_expense"] == 750.0
        assert profile["goal_cost"] == 300.0
        assert profile["debt_status"] == "debt"
        assert profile["spending_habit"] == "big spend"


def test_adding_new_expense_immediately_updates_profile(app):
    """
    Verify that adding a new expense record in the tracker table immediately updates
    the profile loaded by AdvisorServices without any reliance on History.
    """
    with app.app_context():
        user = User(username="live_update_user", full_name="Live User", email="live@example.com")
        user.set_password("Password123!")
        db.session.add(user)
        db.session.commit()

        # Step 1: Add initial income ($1,000) and expense ($200)
        inc = Income(amount=1000.0, category="Salary", income_date=date.today())
        inc.users.append(user)
        exp1 = Expense(amount=200.0, category="Food", expense_date=date.today())
        exp1.users.append(user)
        db.session.add_all([inc, exp1])
        db.session.commit()

        p1 = AdvisorServices.get_user_financial_profile(user)
        assert p1["monthly_income"] == 1000.0
        assert p1["monthly_expense"] == 200.0

        # Step 2: User logs another expense ($50)
        exp2 = Expense(amount=50.0, category="Entertainment", expense_date=date.today())
        exp2.users.append(user)
        db.session.add(exp2)
        db.session.commit()

        # Step 3: AdvisorServices profile immediately reflects $250 total expense
        p2 = AdvisorServices.get_user_financial_profile(user)
        assert p2["monthly_income"] == 1000.0
        assert p2["monthly_expense"] == 250.0
        # No History records were ever created
        assert History.query.filter(History.users.any(id=user.id)).count() == 0


def test_chat_session_override_preserves_dialogue(app):
    """
    Verify that if a user in chat modifies their expense to $70,
    the active session cache (without _history_id) is respected during the dialogue.
    """
    with app.test_request_context():
        from flask import session as flask_session
        user = User(username="dialogue_user", full_name="Dialogue User", email="dialogue@example.com")
        user.set_password("Password123!")
        db.session.add(user)
        db.session.commit()

        # Add tracker income $100, expense $80
        inc = Income(amount=100.0, category="Salary", income_date=date.today())
        inc.users.append(user)
        exp = Expense(amount=80.0, category="Food", expense_date=date.today())
        exp.users.append(user)
        db.session.add_all([inc, exp])
        db.session.commit()

        # Baseline profile before chat override
        base = AdvisorServices.get_user_financial_profile(user)
        assert base["monthly_expense"] == 80.0

        # Simulate in-chat conversational override: user said "My expense is now $70"
        flask_session["advisor_profile"] = {
            "monthly_income": 100.0,
            "monthly_expense": 70.0,
            "goal_cost": 0.0,
            "marital_status": "Single",
            "employment_status": "employed",
            "debt_status": "no debt",
            "spending_habit": "average spend",
            "_user_id": user.id,
            "_is_conversational_override": True,
        }

        # Profile in chat dialogue now sees the override ($70)
        chat_prof = AdvisorServices.get_user_financial_profile(user)
        assert chat_prof["monthly_expense"] == 70.0

