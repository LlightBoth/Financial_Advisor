"""
Test Suite for Step 7I — Financial Consultant Integration & Competition Demo Hardening.

Verifies:
1. Advisor page loads with 200 OK and presents demo presets.
2. Demo 1 (Tight Margin: 1000/900/no debt) -> TIGHT_MARGIN_HIGH_EXPENSE.
3. Demo 2 (Deficit + Debt: 1000/1200/debt) -> DEFICIT_WITH_DEBT.
4. Demo 3 (Zero Income Safety: 0/500) -> HTTP 200, zero-division safe, ratios null.
5. Demo 4 (Stable Buffer: 1500/1000/no debt) -> Authoritative engine decision.
6. HTML form POST submission compatibility with explainability trace.
7. Zero-income HTML rendering (never renders raw 'null' or 'None').
8. Explainability decision trace human-readable elements.
9. English and Khmer deterministic decision invariance.
"""

import pytest
from app import create_app
from app.models import User, Role, History, Rule, Fact
from app.security.token import Token
from extension import db
from config import Config
from sqlalchemy.pool import StaticPool
from app.security.seed_rule_facts import seed_financial_system


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool,
    }
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-consultant-demo-secret"


@pytest.fixture(name="app")
def fixture_app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        seed_financial_system()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture(name="client")
def fixture_client(app):
    return app.test_client()


def create_and_login_user(app, client, username="demo_user", email="demo_user@example.com"):
    with app.app_context():
        role = Role.query.filter_by(name="user").first()
        if not role:
            role = Role(name="user", description="User")
            db.session.add(role)
            db.session.commit()
        user = User(username=username, email=email, full_name="Demo User")
        user.set_password("SecurePass123!")
        user.roles.append(role)
        db.session.add(user)
        db.session.commit()
        raw_token = Token.generate_refresh_token(user)
        user_id = user.id

    with client.session_transaction() as sess:
        sess["_user_id"] = str(user_id)
        sess["_fresh"] = True
    client.set_cookie(key="access_token", value="test_access_token")
    client.set_cookie(key="refresh_token", value=raw_token)
    return user_id


# ==============================================================================
# 1. Advisor Page Load & Demo Presets Availability
# ==============================================================================

def test_demo_page_loads(app, client):
    create_and_login_user(app, client)
    res = client.get("/advisors/")
    assert res.status_code == 200
    html = res.data.decode("utf-8")

    # Verify telemetry status with v1.0 exists
    assert "v1.0" in html

    # Verify wizard steps exist
    assert "advisor-step-1" in html
    assert "advisor-step-2" in html


# ==============================================================================
# 2. Demo 1 — Tight Margin
# ==============================================================================

def test_demo_1_tight_budget(client):
    payload = {
        "monthly_income": 1000.0,
        "monthly_expense": 900.0,
        "goal_cost": 1000.0,
        "employment_status": "employed",
        "debt_status": "no debt",
        "spending_habit": "average spend",
        "marital_status": "Single"
    }
    res = client.post("/api/consult", json=payload)
    assert res.status_code == 200
    data = res.get_json()

    assert data["success"] is True
    assert data["decision"]["rule_id"] == "TIGHT_MARGIN_HIGH_EXPENSE"
    assert data["decision"]["priority"] == 80
    assert data["metrics"]["net_cashflow"] == 100.0
    assert data["metrics"]["expense_ratio"] == 0.90
    assert data["metrics"]["surplus_ratio"] == 0.10
    assert data["decision_trace"]["selected_rule"] == "TIGHT_MARGIN_HIGH_EXPENSE"


# ==============================================================================
# 3. Demo 2 — Deficit + Debt
# ==============================================================================

def test_demo_2_deficit_with_debt(client):
    payload = {
        "monthly_income": 1000.0,
        "monthly_expense": 1200.0,
        "goal_cost": 1000.0,
        "employment_status": "employed",
        "debt_status": "debt",
        "spending_habit": "average spend",
        "marital_status": "Single"
    }
    res = client.post("/api/consult", json=payload)
    assert res.status_code == 200
    data = res.get_json()

    assert data["success"] is True
    assert data["decision"]["rule_id"] == "DEFICIT_WITH_DEBT"
    assert data["decision"]["priority"] == 100
    assert data["metrics"]["net_cashflow"] == -200.0
    assert data["decision_trace"]["selected_rule"] == "DEFICIT_WITH_DEBT"


# ==============================================================================
# 4. Demo 3 — Zero Income Safety
# ==============================================================================

def test_demo_3_zero_income_safety(client):
    payload = {
        "monthly_income": 0.0,
        "monthly_expense": 500.0,
        "goal_cost": 0.0,
        "employment_status": "not employed",
        "debt_status": "no debt",
        "spending_habit": "average spend",
        "marital_status": "Single"
    }
    res = client.post("/api/consult", json=payload)
    assert res.status_code == 200
    data = res.get_json()

    assert data["success"] is True
    assert data["metrics"]["monthly_income"] == 0.0
    assert data["metrics"]["monthly_expense"] == 500.0
    assert data["metrics"]["net_cashflow"] == -500.0
    # Zero division protection
    assert data["metrics"]["expense_ratio"] is None
    assert data["metrics"]["surplus_ratio"] is None
    assert data["decision"]["rule_id"] is not None
    assert "decision_trace" in data


# ==============================================================================
# 5. Demo 4 — Stable Buffer
# ==============================================================================

def test_demo_4_stable_buffer(client):
    payload = {
        "monthly_income": 1500.0,
        "monthly_expense": 1000.0,
        "goal_cost": 2000.0,
        "employment_status": "employed",
        "debt_status": "no debt",
        "spending_habit": "average spend",
        "marital_status": "Single"
    }
    res = client.post("/api/consult", json=payload)
    assert res.status_code == 200
    data = res.get_json()

    assert data["success"] is True
    assert data["metrics"]["net_cashflow"] == 500.0
    assert round(data["metrics"]["expense_ratio"], 2) == 0.67
    assert round(data["metrics"]["surplus_ratio"], 2) == 0.33
    assert data["metrics"]["natural_goal_months"] == 4.0
    assert data["decision"]["rule_id"] == "BALANCED_BUDGET_BUFFER_BUILDING"


# ==============================================================================
# 6. HTML Form POST Compatibility & Explainability Rendering
# ==============================================================================

def test_html_post_flow_renders_explainability(app, client):
    create_and_login_user(app, client)
    form_data = {
        "income": "1000",
        "expense": "900",
        "goal_cost": "1000",
        "martial_status": "Single",
        "employment_status": "employed",
        "debt_status": "no debt",
        "spending_habit": "average spend",
    }
    res = client.post("/advisors/", data=form_data)
    assert res.status_code == 200
    html = res.data.decode("utf-8")

    # Must contain results report and explainability section
    assert "results-report" in html
    assert "explainability-section" in html
    assert "Understanding Your Recommendation" in html or "ការយល់ដឹង" in html or "Why did the consultant recommend this?" in html or "ហេតុអ្វី" in html
    assert "$100.00" in html  # Net cash flow +$100.00


# ==============================================================================
# 7. Zero Income HTML Rendering (No raw nulls)
# ==============================================================================

def test_zero_income_html_rendering(app, client):
    create_and_login_user(app, client)
    form_data = {
        "income": "0",
        "expense": "500",
        "goal_cost": "0",
        "martial_status": "Single",
        "employment_status": "not employed",
        "debt_status": "no debt",
        "spending_habit": "average spend",
    }
    res = client.post("/advisors/", data=form_data)
    assert res.status_code == 200
    html = res.data.decode("utf-8")

    # Must NOT contain raw null or None in ratio displays
    assert "null%" not in html
    assert "None%" not in html
    # Must explain that ratio is not available because income is zero
    assert "Not available because monthly income is zero." in html or "មិនមានទេ" in html


# ==============================================================================
# 8. Explainability Trace Human-Readable Elements
# ==============================================================================

def test_explainability_trace_human_readable(client):
    payload = {
        "monthly_income": 1000.0,
        "monthly_expense": 900.0,
        "debt_status": "no debt"
    }
    res = client.post("/api/consult", json=payload)
    data = res.get_json()
    trace = data["decision_trace"]

    # Must contain factual selection reason, candidate rules, and conditions
    assert "Matched canonical rule" in trace["selection_reason"]
    assert len(trace["rule_evaluations"]) == 8
    first_eval = trace["rule_evaluations"][0]
    assert "condition_results" in first_eval
    assert "matched" in first_eval


# ==============================================================================
# 9. English / Khmer Decision Invariance
# ==============================================================================

def test_english_khmer_decision_invariance(client):
    payload_en = {
        "monthly_income": 1000.0,
        "monthly_expense": 1200.0,
        "debt_status": "debt",
        "language": "en"
    }
    payload_km = {
        "monthly_income": 1000.0,
        "monthly_expense": 1200.0,
        "debt_status": "debt",
        "language": "km"
    }
    res_en = client.post("/api/consult", json=payload_en)
    res_km = client.post("/api/consult", json=payload_km)

    data_en = res_en.get_json()
    data_km = res_km.get_json()

    # Identical decision
    assert data_en["decision"]["rule_id"] == data_km["decision"]["rule_id"] == "DEFICIT_WITH_DEBT"
    assert data_en["decision"]["priority"] == data_km["decision"]["priority"] == 100
    assert data_en["metrics"] == data_km["metrics"]
    assert data_en["facts"] == data_km["facts"]
    assert data_en["knowledge_base_version"] == data_km["knowledge_base_version"] == "financial-kb-v1.0"
