"""
Test Suite for Step 7H — Financial Consultant API Contract & Validation Hardening.

Covers all 20 test requirements:
1. Valid consultant request (200 OK, full payload)
2. Missing required input (income/expense missing -> 400 VALIDATION_ERROR)
3. Negative income (income < 0 -> 400 VALIDATION_ERROR)
4. Negative expense (expense < 0 -> 400 VALIDATION_ERROR)
5. Negative goal cost (goal_cost < 0 -> 400 VALIDATION_ERROR)
6. Zero income (income == 0 -> 200 OK, expense_ratio=None, surplus_ratio=None, no ZeroDivisionError)
7. Zero expense (expense == 0 -> 200 OK, evaluated cleanly)
8. Language 'en' (English presentation)
9. Language 'km' (Khmer presentation)
10. Same decision for EN and KM (rule_id, metrics, facts, priority, certainty identical)
11. Stable response structure (all top-level fields present)
12. Knowledge base version 'financial-kb-v1.0' returned
13. Decision trace returned in response
14. Client cannot override rule ID (boundary protection)
15. Client cannot override priority (boundary protection)
16. Client cannot override certainty (boundary protection)
17. Client cannot override KB version (boundary protection)
18. Invalid enum values (rejected with clear 400 error)
19. Malformed request (invalid JSON / non-object payload -> 400 MALFORMED_REQUEST)
20. Backward compatibility with existing advisor services and HTML forms
"""

import json
import pytest
from app import create_app
from app.models import User, Role, History, Rule, Fact
from app.security.token import Token
from extension import db
from config import Config
from sqlalchemy.pool import StaticPool
from app.security.seed_rule_facts import seed_financial_system
from app.services.advisor_services import AdvisorServices


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool,
    }
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-consultant-api-secret"


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


def create_and_login_user(app, client, username="api_user", email="api_user@example.com"):
    with app.app_context():
        role = Role.query.filter_by(name="user").first()
        if not role:
            role = Role(name="user", description="User")
            db.session.add(role)
            db.session.commit()
        user = User(username=username, email=email, full_name="API User")
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
# 1. Valid Consultant Request
# ==============================================================================

def test_api_valid_consultant_request(client):
    payload = {
        "monthly_income": 1000.0,
        "monthly_expense": 900.0,
        "goal_cost": 1000.0,
        "employment_status": "employed",
        "debt_status": "no debt",
        "spending_habit": "average spend",
        "marital_status": "Single",
        "language": "en"
    }
    res = client.post("/api/consult", json=payload)
    assert res.status_code == 200
    data = res.get_json()

    assert data["success"] is True
    assert data["knowledge_base_version"] == "financial-kb-v1.0"
    assert data["decision"]["rule_id"] == "TIGHT_MARGIN_HIGH_EXPENSE"
    assert data["metrics"]["net_cashflow"] == 100.0
    assert data["metrics"]["expense_ratio"] == 0.90


def test_api_evaluate_alias_endpoint(client):
    """Test that the /evaluate alias endpoint routes to the exact same implementation."""
    payload = {
        "monthly_income": 1000.0,
        "monthly_expense": 900.0,
        "debt_status": "no debt"
    }
    res = client.post("/evaluate", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["decision"]["rule_id"] == "TIGHT_MARGIN_HIGH_EXPENSE"


def test_api_prefixed_endpoints(client):
    """Test that /advisors/api/consult and /advisors/evaluate both work."""
    payload = {
        "monthly_income": 1000.0,
        "monthly_expense": 900.0,
        "debt_status": "no debt"
    }
    res1 = client.post("/advisors/api/consult", json=payload)
    assert res1.status_code == 200
    assert res1.get_json()["success"] is True

    res2 = client.post("/advisors/evaluate", json=payload)
    assert res2.status_code == 200
    assert res2.get_json()["success"] is True


# ==============================================================================
# 2. Missing Required Input
# ==============================================================================

def test_api_missing_required_input(client):
    # Both missing
    res = client.post("/api/consult", json={})
    assert res.status_code == 400
    err = res.get_json()
    assert err["success"] is False
    assert err["error"]["code"] == "VALIDATION_ERROR"
    assert "monthly_income" in err["error"]["fields"]
    assert "monthly_expense" in err["error"]["fields"]

    # Income provided, expense missing
    res2 = client.post("/api/consult", json={"monthly_income": 1000.0})
    assert res2.status_code == 400
    err2 = res2.get_json()
    assert "monthly_expense" in err2["error"]["fields"]


# ==============================================================================
# 3. Negative Income
# ==============================================================================

def test_api_negative_income(client):
    payload = {
        "monthly_income": -500.0,
        "monthly_expense": 400.0
    }
    res = client.post("/api/consult", json=payload)
    assert res.status_code == 400
    err = res.get_json()
    assert err["success"] is False
    assert err["error"]["code"] == "VALIDATION_ERROR"
    assert "monthly_income" in err["error"]["fields"]
    assert "greater than or equal to 0" in err["error"]["fields"]["monthly_income"]


# ==============================================================================
# 4. Negative Expense
# ==============================================================================

def test_api_negative_expense(client):
    payload = {
        "monthly_income": 1000.0,
        "monthly_expense": -200.0
    }
    res = client.post("/api/consult", json=payload)
    assert res.status_code == 400
    err = res.get_json()
    assert err["success"] is False
    assert err["error"]["code"] == "VALIDATION_ERROR"
    assert "monthly_expense" in err["error"]["fields"]
    assert "greater than or equal to 0" in err["error"]["fields"]["monthly_expense"]


# ==============================================================================
# 5. Negative Goal Cost
# ==============================================================================

def test_api_negative_goal_cost(client):
    payload = {
        "monthly_income": 1000.0,
        "monthly_expense": 800.0,
        "goal_cost": -100.0
    }
    res = client.post("/api/consult", json=payload)
    assert res.status_code == 400
    err = res.get_json()
    assert err["success"] is False
    assert err["error"]["code"] == "VALIDATION_ERROR"
    assert "goal_cost" in err["error"]["fields"]
    assert "greater than or equal to 0" in err["error"]["fields"]["goal_cost"]


# ==============================================================================
# 6. Zero Income Behavior
# ==============================================================================

def test_api_zero_income_safety(client):
    payload = {
        "monthly_income": 0.0,
        "monthly_expense": 500.0,
        "employment_status": "not employed",
        "debt_status": "no debt"
    }
    res = client.post("/api/consult", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    # Zero income must safely set ratios to None without ZeroDivisionError
    assert data["metrics"]["monthly_income"] == 0.0
    assert data["metrics"]["expense_ratio"] is None
    assert data["metrics"]["surplus_ratio"] is None
    assert data["metrics"]["net_cashflow"] == -500.0
    assert data["decision"]["rule_id"] is not None
    assert "decision_trace" in data


# ==============================================================================
# 7. Zero Expense Behavior
# ==============================================================================

def test_api_zero_expense_safety(client):
    payload = {
        "monthly_income": 2000.0,
        "monthly_expense": 0.0,
        "debt_status": "no debt"
    }
    res = client.post("/api/consult", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["metrics"]["monthly_expense"] == 0.0
    assert data["metrics"]["expense_ratio"] == 0.0
    assert data["metrics"]["surplus_ratio"] == 1.0
    assert data["metrics"]["net_cashflow"] == 2000.0


# ==============================================================================
# 8. Language 'en'
# ==============================================================================

def test_api_language_en(client):
    payload = {
        "monthly_income": 1000.0,
        "monthly_expense": 900.0,
        "debt_status": "no debt",
        "language": "en"
    }
    res = client.post("/api/consult", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["conclusion"]["en"] != ""
    assert data["advice"]["en"] != ""


# ==============================================================================
# 9. Language 'km'
# ==============================================================================

def test_api_language_km(client):
    payload = {
        "monthly_income": 1000.0,
        "monthly_expense": 900.0,
        "debt_status": "no debt",
        "language": "km"
    }
    res = client.post("/api/consult", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["conclusion"]["km"] != ""
    assert data["advice"]["km"] != ""


# ==============================================================================
# 10. Same Decision for EN and KM
# ==============================================================================

def test_api_same_decision_for_en_and_km(client):
    payload_en = {
        "monthly_income": 1000.0,
        "monthly_expense": 900.0,
        "debt_status": "no debt",
        "language": "en"
    }
    payload_km = {
        "monthly_income": 1000.0,
        "monthly_expense": 900.0,
        "debt_status": "no debt",
        "language": "km"
    }
    res_en = client.post("/api/consult", json=payload_en)
    res_km = client.post("/api/consult", json=payload_km)

    data_en = res_en.get_json()
    data_km = res_km.get_json()

    # The underlying decision must be completely identical
    assert data_en["decision"]["rule_id"] == data_km["decision"]["rule_id"]
    assert data_en["decision"]["priority"] == data_km["decision"]["priority"]
    assert data_en["decision"]["certainty"] == data_km["decision"]["certainty"]
    assert data_en["metrics"] == data_km["metrics"]
    assert data_en["facts"] == data_km["facts"]
    assert data_en["knowledge_base_version"] == data_km["knowledge_base_version"]


# ==============================================================================
# 11. Stable Response Structure
# ==============================================================================

def test_api_stable_response_structure(client):
    payload = {
        "monthly_income": 1500.0,
        "monthly_expense": 1000.0,
        "debt_status": "no debt"
    }
    res = client.post("/api/consult", json=payload)
    assert res.status_code == 200
    data = res.get_json()

    expected_top_keys = {
        "success",
        "knowledge_base_version",
        "input",
        "metrics",
        "facts",
        "decision",
        "conclusion",
        "advice",
        "decision_trace"
    }
    assert expected_top_keys.issubset(set(data.keys()))

    expected_decision_keys = {"rule_id", "name", "category", "priority", "certainty", "selection_reason"}
    assert expected_decision_keys.issubset(set(data["decision"].keys()))

    expected_metrics_keys = {
        "monthly_income", "monthly_expense", "goal_cost",
        "net_cashflow", "expense_ratio", "surplus_ratio", "natural_goal_months"
    }
    assert expected_metrics_keys.issubset(set(data["metrics"].keys()))


# ==============================================================================
# 12. Knowledge Base Version 'financial-kb-v1.0'
# ==============================================================================

def test_api_kb_version_returned(client):
    payload = {"monthly_income": 1000.0, "monthly_expense": 800.0}
    res = client.post("/api/consult", json=payload)
    data = res.get_json()
    assert data["knowledge_base_version"] == "financial-kb-v1.0"
    assert data["decision_trace"]["knowledge_base_version"] == "financial-kb-v1.0"


# ==============================================================================
# 13. Decision Trace Returned
# ==============================================================================

def test_api_decision_trace_returned(client):
    payload = {"monthly_income": 1000.0, "monthly_expense": 900.0, "debt_status": "no debt"}
    res = client.post("/api/consult", json=payload)
    data = res.get_json()

    trace = data["decision_trace"]
    assert "candidate_rules" in trace
    assert "rule_evaluations" in trace
    assert "selected_rule" in trace
    assert "selection_reason" in trace
    assert len(trace["candidate_rules"]) == 8


# ==============================================================================
# 14. Client Cannot Override Rule ID (Boundary Protection)
# ==============================================================================

def test_api_client_cannot_override_rule_id(client):
    payload = {
        "monthly_income": 1000.0,
        "monthly_expense": 900.0,
        "debt_status": "no debt",
        "rule_id": "DEFICIT_WITH_DEBT"  # Attacking inference outcome
    }
    res = client.post("/api/consult", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    # Engine must deterministically select TIGHT_MARGIN_HIGH_EXPENSE based on financial facts
    assert data["decision"]["rule_id"] == "TIGHT_MARGIN_HIGH_EXPENSE"
    assert data["decision"]["rule_id"] != "DEFICIT_WITH_DEBT"


# ==============================================================================
# 15. Client Cannot Override Priority (Boundary Protection)
# ==============================================================================

def test_api_client_cannot_override_priority(client):
    payload = {
        "monthly_income": 1000.0,
        "monthly_expense": 900.0,
        "debt_status": "no debt",
        "priority": 99999
    }
    res = client.post("/api/consult", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    # Winning rule priority must remain the knowledge base priority (80)
    assert data["decision"]["priority"] == 80


# ==============================================================================
# 16. Client Cannot Override Certainty (Boundary Protection)
# ==============================================================================

def test_api_client_cannot_override_certainty(client):
    payload = {
        "monthly_income": 1000.0,
        "monthly_expense": 900.0,
        "debt_status": "no debt",
        "certainty": 1.00
    }
    res = client.post("/api/consult", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    # Winning rule certainty must remain the canonical metadata certainty (0.70)
    assert data["decision"]["certainty"] == 0.70


# ==============================================================================
# 17. Client Cannot Override KB Version (Boundary Protection)
# ==============================================================================

def test_api_client_cannot_override_kb_version(client):
    payload = {
        "monthly_income": 1000.0,
        "monthly_expense": 900.0,
        "debt_status": "no debt",
        "kb_version": "malicious-kb-v999.0"
    }
    res = client.post("/api/consult", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    # Knowledge base version must remain financial-kb-v1.0
    assert data["knowledge_base_version"] == "financial-kb-v1.0"
    assert data["decision_trace"]["knowledge_base_version"] == "financial-kb-v1.0"


# ==============================================================================
# 18. Invalid Enum Values
# ==============================================================================

def test_api_invalid_enum_values(client):
    # Invalid employment status
    res1 = client.post("/api/consult", json={
        "monthly_income": 1000.0,
        "monthly_expense": 900.0,
        "employment_status": "astronaut"
    })
    assert res1.status_code == 400
    assert "employment_status" in res1.get_json()["error"]["fields"]

    # Invalid debt status
    res2 = client.post("/api/consult", json={
        "monthly_income": 1000.0,
        "monthly_expense": 900.0,
        "debt_status": "infinite_debt"
    })
    assert res2.status_code == 400
    assert "debt_status" in res2.get_json()["error"]["fields"]

    # Invalid spending habit
    res3 = client.post("/api/consult", json={
        "monthly_income": 1000.0,
        "monthly_expense": 900.0,
        "spending_habit": "reckless"
    })
    assert res3.status_code == 400
    assert "spending_habit" in res3.get_json()["error"]["fields"]

    # Invalid marital status
    res4 = client.post("/api/consult", json={
        "monthly_income": 1000.0,
        "monthly_expense": 900.0,
        "marital_status": "complex"
    })
    assert res4.status_code == 400
    assert "marital_status" in res4.get_json()["error"]["fields"]

    # Invalid language
    res5 = client.post("/api/consult", json={
        "monthly_income": 1000.0,
        "monthly_expense": 900.0,
        "language": "es"
    })
    assert res5.status_code == 400
    assert "language" in res5.get_json()["error"]["fields"]


# ==============================================================================
# 19. Malformed Request
# ==============================================================================

def test_api_malformed_request(client):
    # Non-JSON content type with malformed body
    res = client.post(
        "/api/consult",
        data="{not valid json",
        content_type="application/json"
    )
    assert res.status_code == 400
    err = res.get_json()
    assert err["success"] is False
    assert err["error"]["code"] == "MALFORMED_REQUEST"

    # Non-dict JSON payload (e.g. array)
    res2 = client.post("/api/consult", json=[1, 2, 3])
    assert res2.status_code == 400
    err2 = res2.get_json()
    assert err2["error"]["code"] == "VALIDATION_ERROR"


# ==============================================================================
# 20. Backward Compatibility & Manual Cases A, B, C
# ==============================================================================

def test_api_backward_compatibility_aliases(client):
    """Test documented aliases: income, expense, is_debt, is_employed, is_spending, martial_status."""
    payload = {
        "income": 1000.0,
        "expense": 900.0,
        "is_employed": "yes",
        "is_debt": "active",
        "is_spending": "high",
        "martial_status": "Married",
        "lang": "en"
    }
    res = client.post("/api/consult", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["input"]["employment_status"] == "employed"
    assert data["input"]["debt_status"] == "debt"
    assert data["input"]["spending_habit"] == "big spend"
    assert data["input"]["marital_status"] == "Married"


def test_api_authenticated_user_saves_history(app, client):
    """Verifies that an authenticated consultation records into History."""
    user_id = create_and_login_user(app, client)
    payload = {
        "monthly_income": 1200.0,
        "monthly_expense": 800.0,
        "debt_status": "no debt"
    }
    res = client.post("/api/consult", json=payload)
    assert res.status_code == 200

    with app.app_context():
        user = db.session.get(User, user_id)
        assert len(user.histories) >= 1
        latest_hist = user.histories[-1]
        assert latest_hist.income == 1200.0
        assert latest_hist.expense == 800.0
        assert latest_hist.kb_version == "financial-kb-v1.0"


def test_manual_verification_case_a(client):
    """
    Case A:
    income = 1000, expense = 900, debt = 'no debt'
    Expected: TIGHT_MARGIN_HIGH_EXPENSE, HTTP 200, trace present.
    """
    payload = {
        "monthly_income": 1000,
        "monthly_expense": 900,
        "debt_status": "no debt"
    }
    res = client.post("/api/consult", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["metrics"]["net_cashflow"] == 100.0
    assert data["metrics"]["expense_ratio"] == 0.90
    assert data["decision"]["rule_id"] == "TIGHT_MARGIN_HIGH_EXPENSE"
    assert data["knowledge_base_version"] == "financial-kb-v1.0"
    assert "decision_trace" in data


def test_manual_verification_case_b(client):
    """
    Case B:
    income = 1000, expense = 1200, debt = 'active'
    Expected: DEFICIT_WITH_DEBT, HTTP 200, trace present.
    """
    payload = {
        "monthly_income": 1000,
        "monthly_expense": 1200,
        "debt_status": "active"
    }
    res = client.post("/api/consult", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["metrics"]["net_cashflow"] == -200.0
    assert data["decision"]["rule_id"] == "DEFICIT_WITH_DEBT"
    assert data["knowledge_base_version"] == "financial-kb-v1.0"
    assert "decision_trace" in data


def test_manual_verification_case_c(client):
    """
    Case C:
    income = 0, expense = 500
    Expected: HTTP 200, no division-by-zero, expense_ratio=null, surplus_ratio=null, trace present.
    """
    payload = {
        "monthly_income": 0,
        "monthly_expense": 500
    }
    res = client.post("/api/consult", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["metrics"]["monthly_income"] == 0.0
    assert data["metrics"]["monthly_expense"] == 500.0
    assert data["metrics"]["net_cashflow"] == -500.0
    assert data["metrics"]["expense_ratio"] is None
    assert data["metrics"]["surplus_ratio"] is None
    assert data["knowledge_base_version"] == "financial-kb-v1.0"
    assert "decision_trace" in data
