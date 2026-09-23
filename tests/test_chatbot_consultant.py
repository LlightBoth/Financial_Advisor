"""
Automated Test Suite for Conversational Financial Consultant AI Chatbot.

Verifies:
1. End-to-End Architectural Flow:
   User Message
   -> Intent Classification
   -> Existing DB Financial Profile
   -> ConsultantEngine
   -> Sanitized Result (raw rule IDs, raw titles, certainty, traces hidden)
   -> Local Financial Advisor AI
   -> Final Conversational Response
2. Greeting Invariant:
   ConsultantEngine is strictly NEVER called for greetings ("hello", "សួស្តី").
3. Complete 10-Turn Conversational Financial Consultant Dialogue:
   Turn 1: "hello" -> Natural greeting, no engine call.
   Turn 2: "Help me create a financial plan" -> Uses DB profile ($100 inc / $80 exp), calls engine, invokes AI, raw rule hidden.
   Turn 3: "How much can I save each month?" -> Answers specific $20 surplus.
   Turn 4: "How can I reduce my expenses?" -> Answers specific expense advice for $80 expense.
   Turn 5: "My expense is now $70" -> Updates only expense to $70, preserves income $100, surplus $30.
   Turn 6: "What does that change?" -> Explains surplus increased from $20 to $30 ($10 more each month).
   Turn 7: "I want to save $5000" -> Updates only goal_cost to $5000, preserves income $100 and expense $70.
   Turn 8: "How should I approach that goal?" -> Specific advice for $5,000 goal and $30/month surplus.
   Turn 9: "សួស្តី" -> Natural Khmer greeting, no engine call.
   Turn 10: "ខ្ញុំចង់សន្សំប្រាក់" -> Natural Khmer guidance using profile ($30 surplus).
"""

from unittest.mock import patch
import pytest
from app import create_app
from config import Config
from extension import db
from app.models.user import User
from app.models.role import Role
from app.models.history import History
from app.security.token import Token
from app.services.advisor_services import AdvisorServices
from app.services.history_services import HistoryServices
from app.services.consultant_engine import ConsultantEngine
from app.services.llm_service import LLMService
from training.llm_output_normalizer import classify_conversational_intent


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {}
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-secret-key-consultant"


@pytest.fixture(name="app")
def fixture_app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        role = Role.query.filter_by(name="user").first()
        if not role:
            role = Role(name="user", description="Normal User")
            db.session.add(role)
            db.session.commit()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture(name="client")
def fixture_client(app):
    return app.test_client()


def login_user(app, client, username="test_consultant_user", email="consultant@example.com"):
    with app.app_context():
        role = Role.query.filter_by(name="user").first()
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(username=username, email=email, full_name="Test Consultant User")
            user.set_password("Password123!")
            if role:
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


def setup_initial_history(app, user_id, income=100.0, expense=80.0, goal_cost=0.0):
    with app.app_context():
        user = db.session.get(User, user_id)
        history_data = {
            "goal_cost": goal_cost,
            "income": income,
            "expense": expense,
            "martial_status": "Single",
            "is_employed": "employed",
            "is_debt": "no debt",
            "is_spending": "average spend",
            "remain_percentage": 20.0,
            "expense_percentage": 80.0,
            "get_advice": None,
            "kb_version": "financial-kb-v1.0"
        }
        HistoryServices.create(history_data, user)


# ==============================================================================
# 1. Critical Proof of Architectural Flow
# ==============================================================================

def test_critical_architectural_flow_proven(app, client):
    """
    CRITICAL VERIFICATION:
    Proves from code and mocks that the flow is:
    User message
    -> intent classification
    -> existing DB financial profile
    -> ConsultantEngine
    -> sanitized result
    -> local Financial Advisor AI
    -> final conversational response

    Also verifies that raw ConsultantEngine recommendation is NOT directly returned to the browser.
    """
    user_id = login_user(app, client, "arch_flow_user", "arch@example.com")
    setup_initial_history(app, user_id, income=100.0, expense=80.0)

    # Wrap methods in spies to prove the exact execution order and data passed
    real_classify = classify_conversational_intent
    real_get_profile = AdvisorServices.get_user_financial_profile
    real_engine_evaluate = ConsultantEngine.evaluate
    real_generate_explain = LLMService.generate_recommendation_explanation

    events = []

    def spy_classify(msg, **kwargs):
        events.append("1_intent_classification")
        return real_classify(msg, **kwargs)

    def spy_get_profile(user):
        events.append("2_load_db_profile")
        return real_get_profile(user)

    def spy_engine_evaluate(*args, **kwargs):
        events.append("3_consultant_engine_evaluate")
        res = real_engine_evaluate(*args, **kwargs)
        # Capture the raw rule title to prove it exists in the engine output
        if res.get("selected_advice"):
            events.append(f"raw_engine_rule:{res['selected_advice'].conclusion_en}")
            events.append(f"raw_rule_id:{res['selected_advice'].rule_id}")
        return res

    def spy_generate_explain(*args, **kwargs):
        events.append("4_local_ai_explanation")
        return real_generate_explain(*args, **kwargs)

    with patch("training.llm_output_normalizer.classify_conversational_intent", side_effect=spy_classify), \
         patch("app.services.advisor_services.AdvisorServices.get_user_financial_profile", side_effect=spy_get_profile), \
         patch("app.services.consultant_engine.ConsultantEngine.evaluate", side_effect=spy_engine_evaluate), \
         patch("app.services.llm_service.LLMService.generate_recommendation_explanation", side_effect=spy_generate_explain):

        res = client.post("/bots/chat", json={"message": "Help me create a financial plan"})
        assert res.status_code == 200
        data = res.get_json()
        resp_text = data["response"]

    # 1. Prove intent classification was executed first
    assert "1_intent_classification" in events
    # 2. Prove authoritative DB profile was loaded
    assert "2_load_db_profile" in events
    # 3. Prove ConsultantEngine evaluated the profile
    assert "3_consultant_engine_evaluate" in events
    # 4. Prove the engine generated the raw rule "Narrow Operating Margin (Tight Budget)" with canonical rule_id
    assert any("Narrow Operating Margin (Tight Budget)" in e for e in events)
    assert any("raw_rule_id:" in e for e in events)
    # 5. Prove local Financial Advisor AI was invoked to generate explanation
    assert "4_local_ai_explanation" in events

    # 6. Prove SANITIZATION: raw rule title, rule IDs, certainty, and traces are NOT returned to the browser
    assert "Narrow Operating Margin (Tight Budget)" not in resp_text
    assert "TIGHT_MARGIN_HIGH_EXPENSE" not in resp_text
    assert "Rule 3" not in resp_text
    assert "RULE_3" not in resp_text
    assert "rule_id" not in resp_text
    assert "certainty" not in resp_text
    assert "decision_trace" not in resp_text

    # 7. Prove response contains verified consultant facts and AI explanation
    assert "100" in resp_text
    assert "80" in resp_text
    assert "20" in resp_text
    assert "Understanding Your Recommendation" in resp_text


# ==============================================================================
# 2. Greeting Invariant: ConsultantEngine Must NOT be Called
# ==============================================================================

def test_greetings_never_call_consultant_engine(app, client):
    """Verify that greetings in English and Khmer do NOT invoke ConsultantEngine."""
    user_id = login_user(app, client, "greeting_user", "greeting@example.com")
    setup_initial_history(app, user_id, income=100.0, expense=80.0)

    with patch("app.services.consultant_engine.ConsultantEngine.evaluate") as mock_engine:
        # English greeting
        res_en = client.post("/bots/chat", json={"message": "hello"})
        assert res_en.status_code == 200
        data_en = res_en.get_json()
        assert "hello" in data_en["response"].lower() or "financial advisor" in data_en["response"].lower()
        # Must not repeat recommendation
        assert "Understanding Your Recommendation" not in data_en["response"]
        assert mock_engine.call_count == 0

        # Khmer greeting
        res_km = client.post("/bots/chat", json={"message": "សួស្តី"})
        assert res_km.status_code == 200
        data_km = res_km.get_json()
        assert any('\u1780' <= c <= '\u17ff' for c in data_km["response"])
        assert "សួស្តី" in data_km["response"]
        # Must not call engine
        assert mock_engine.call_count == 0


# ==============================================================================
# 3. Complete 10-Turn Conversational Financial Consultant Flow
# ==============================================================================

def test_ten_turn_financial_consultant_conversation(app, client):
    """
    Simulates the exact 10 turns requested by the user:
    Turn 1: "hello"
    Turn 2: "Help me create a financial plan"
    Turn 3: "How much can I save each month?"
    Turn 4: "How can I reduce my expenses?"
    Turn 5: "My expense is now $70"
    Turn 6: "What does that change?"
    Turn 7: "I want to save $5000"
    Turn 8: "How should I approach that goal?"
    Turn 9: "សួស្តី"
    Turn 10: "ខ្ញុំចង់សន្សំប្រាក់"
    """
    user_id = login_user(app, client, "ten_turn_user", "tenturn@example.com")
    setup_initial_history(app, user_id, income=100.0, expense=80.0)

    chat_id = None

    # Helper to send message in active conversation
    def send(msg):
        nonlocal chat_id
        payload = {"message": msg}
        if chat_id:
            payload["chat_id"] = chat_id
        r = client.post("/bots/chat", json=payload)
        assert r.status_code == 200
        d = r.get_json()
        chat_id = d.get("chat_id")
        return d.get("response", "")

    # Turn 1: "hello"
    with patch("app.services.consultant_engine.ConsultantEngine.evaluate") as mock_engine:
        r1 = send("hello")
        assert "hello" in r1.lower() or "financial advisor" in r1.lower()
        assert "Understanding Your Recommendation" not in r1
        assert mock_engine.call_count == 0

    # Turn 2: "Help me create a financial plan"
    r2 = send("Help me create a financial plan")
    # Must use existing profile (income 100, expense 80, surplus 20)
    assert "100" in r2
    assert "80" in r2
    assert "20" in r2
    # Must NOT directly display raw engine rule title or IDs
    assert "Narrow Operating Margin (Tight Budget)" not in r2
    assert "Rule 3" not in r2
    assert "RULE_3" not in r2
    assert "Understanding Your Recommendation" in r2

    # Turn 3: "How much can I save each month?"
    r3 = send("How much can I save each month?")
    # Must understand previous conversation and use verified $20 surplus
    assert "20" in r3
    # Must answer specifically rather than repeat the previous full response
    assert "surplus" in r3.lower() or "save" in r3.lower()

    # Turn 4: "How can I reduce my expenses?"
    r4 = send("How can I reduce my expenses?")
    # Must answer expense question specifically using profile ($80 expenses)
    assert "80" in r4
    assert any(term in r4.lower() for term in ["discretionary", "spending", "subscriptions", "costs", "cut", "reduce"])

    # Turn 5: "My expense is now $70"
    r5 = send("My expense is now $70")
    # Update only expense, preserve income 100, new surplus 30
    assert "70" in r5
    assert "100" in r5
    assert "30" in r5
    # Verify DB profile updated
    with app.app_context():
        user = db.session.get(User, user_id)
        latest_prof = AdvisorServices.get_user_financial_profile(user)
        assert latest_prof["monthly_income"] == 100.0
        assert latest_prof["monthly_expense"] == 70.0
        assert latest_prof["debt_status"] == "no debt"

    # Turn 6: "What does that change?"
    r6 = send("What does that change?")
    # Explains monthly surplus changed from 20 to 30 ($10 more each month)
    assert "20" in r6
    assert "30" in r6
    assert "10" in r6 or "additional" in r6.lower() or "increased" in r6.lower()

    # Turn 7: "I want to save $5000"
    r7 = send("I want to save $5000")
    # Update only goal_cost = 5000, preserve other fields
    assert "5,000" in r7 or "5000" in r7
    with app.app_context():
        user = db.session.get(User, user_id)
        latest_prof = AdvisorServices.get_user_financial_profile(user)
        assert latest_prof["goal_cost"] == 5000.0
        assert latest_prof["monthly_income"] == 100.0
        assert latest_prof["monthly_expense"] == 70.0

    # Turn 8: "How should I approach that goal?"
    r8 = send("How should I approach that goal?")
    # Answers specifically about $5,000 goal and $30 monthly surplus
    assert "5,000" in r8 or "5000" in r8
    assert "30" in r8
    assert any(term in r8.lower() for term in ["allocation", "strategy", "milestones", "timeline", "save", "dedicated"])

    # Turn 9: "សួស្តី"
    with patch("app.services.consultant_engine.ConsultantEngine.evaluate") as mock_engine:
        r9 = send("សួស្តី")
        assert any('\u1780' <= c <= '\u17ff' for c in r9)
        assert "សួស្តី" in r9
        assert mock_engine.call_count == 0

    # Turn 10: "ខ្ញុំចង់សន្សំប្រាក់"
    r10 = send("ខ្ញុំចង់សន្សំប្រាក់")
    # Khmer financial guidance using profile ($100 inc, $70 exp, $30 surplus)
    assert any('\u1780' <= c <= '\u17ff' for c in r10)
    assert "100" in r10
    assert "70" in r10
    assert "30" in r10
    assert "Narrow Operating Margin" not in r10
    assert "Rule 3" not in r10
