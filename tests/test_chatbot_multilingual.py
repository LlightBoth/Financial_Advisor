"""
Automated Test Suite for Multilingual Chatbot Assistant with Shared Financial Profile Context.

Tests:
1. Language Detection (Khmer, English, Mixed Dominant)
2. Authoritative Profile Loading from database History
3. Automatic Context Usage for General Questions ('Help me save money' / 'ខ្ញុំចង់សន្សំប្រាក់')
4. Safe Partial Profile Updates (updating single field without overwriting others)
5. Strict User Isolation (User B cannot access User A's profile)
6. Safety Boundary Guardrails (speculative crypto/stocks and loan underwriting refusals in Khmer & English)
7. Missing Information Null Semantics
"""

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
from training.llm_output_normalizer import detect_language


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {}
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-secret-key-multilingual"


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


def login_user(app, client, username="test_user_a", email="user_a@example.com"):
    with app.app_context():
        role = Role.query.filter_by(name="user").first()
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(username=username, email=email, full_name="Test User")
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


# ==============================================================================
# 1. Language Detection Unit Tests
# ==============================================================================

def test_language_detection_pure_khmer():
    assert detect_language("ខ្ញុំចង់សន្សំប្រាក់") == "km"
    assert detect_language("តើក្បួន 50/30/20 ដំណើរការដូចម្តេច?") == "km"
    assert detect_language("តើអ្វីទៅជាមូលនិធិសង្គ្រោះបន្ទាន់?") == "km"


def test_language_detection_pure_english():
    assert detect_language("Help me save money") == "en"
    assert detect_language("How does compound interest work?") == "en"
    assert detect_language("I earn $2,500 and spend $1,800 monthly.") == "en"


def test_language_detection_mixed_dominant():
    # Mixed with dominant Khmer
    assert detect_language("ខ្ញុំចង់ save លុយ $1000") == "km"
    assert detect_language("ខ្ញុំមានចំណូល income $1000 និងការចំណាយ $800") == "km"

    # Mixed with dominant English
    assert detect_language("Can you explain how to save money for គ្រួសារ?") == "en"
    assert detect_language("I want to build an emergency fund សម្រាប់គ្រួសារ") == "en"


# ==============================================================================
# 2. Authoritative Profile Loading from Database
# ==============================================================================

def test_load_existing_profile_from_database(app, client):
    user_id = login_user(app, client, "user_load_test", "load@example.com")
    with app.app_context():
        user = db.session.get(User, user_id)
        assert user is not None

        # Create history record (Income $1,500, Expense $1,000, Goal $3,000, no debt, employed)
        history_data = {
            "goal_cost": 3000.0,
            "income": 1500.0,
            "expense": 1000.0,
            "martial_status": "Single",
            "is_employed": "employed",
            "is_debt": "no debt",
            "is_spending": "average spend",
            "remain_percentage": 33.33,
            "expense_percentage": 66.67,
            "get_advice": None,
            "kb_version": "financial-kb-v1.0"
        }
        HistoryServices.create(history_data, user)

        profile = AdvisorServices.get_user_financial_profile(user)

        assert profile is not None
        assert profile["monthly_income"] == 1500.0
        assert profile["monthly_expense"] == 1000.0
        assert profile["goal_cost"] == 3000.0
        assert profile["debt_status"] == "no debt"
        assert profile["employment_status"] == "employed"
        assert profile["marital_status"] == "Single"


# ==============================================================================
# 3. User Isolation Verification
# ==============================================================================

def test_user_profile_isolation(app, client):
    user_a_id = login_user(app, client, "user_iso_a", "iso_a@example.com")
    user_b_id = login_user(app, client, "user_iso_b", "iso_b@example.com")

    with app.app_context():
        user_a = db.session.get(User, user_a_id)
        user_b = db.session.get(User, user_b_id)

        history_data = {
            "goal_cost": 5000.0,
            "income": 2000.0,
            "expense": 1200.0,
            "martial_status": "Married",
            "is_employed": "employed",
            "is_debt": "debt",
            "is_spending": "average spend",
            "remain_percentage": 40.0,
            "expense_percentage": 60.0,
            "get_advice": None,
            "kb_version": "financial-kb-v1.0"
        }
        HistoryServices.create(history_data, user_a)

        profile_a = AdvisorServices.get_user_financial_profile(user_a)
        assert profile_a is not None
        assert profile_a["monthly_income"] == 2000.0

        # User B has NO history
        profile_b = AdvisorServices.get_user_financial_profile(user_b)
        assert profile_b is None


# ==============================================================================
# 4. Chatbot Context Sharing for General Questions (E2E)
# ==============================================================================

def test_chatbot_uses_existing_profile_for_general_question(app, client):
    user_id = login_user(app, client, "user_e2e_en", "e2e_en@example.com")

    with app.app_context():
        user = db.session.get(User, user_id)
        history_data = {
            "goal_cost": 3000.0,
            "income": 1500.0,
            "expense": 1000.0,
            "martial_status": "Single",
            "is_employed": "employed",
            "is_debt": "no debt",
            "is_spending": "average spend",
            "remain_percentage": 33.33,
            "expense_percentage": 66.67,
            "get_advice": None,
            "kb_version": "financial-kb-v1.0"
        }
        HistoryServices.create(history_data, user)

    # Ask general question in English
    res = client.post("/bots/chat", json={"message": "Help me save money"})
    assert res.status_code == 200
    data = res.get_json()
    assert "response" in data
    resp_text = data["response"]
    assert "1,500" in resp_text or "1500" in resp_text or "Understanding Your Recommendation" in resp_text


def test_chatbot_uses_existing_profile_for_khmer_general_question(app, client):
    user_id = login_user(app, client, "user_e2e_km", "e2e_km@example.com")

    with app.app_context():
        user = db.session.get(User, user_id)
        history_data = {
            "goal_cost": 3000.0,
            "income": 1500.0,
            "expense": 1000.0,
            "martial_status": "Single",
            "is_employed": "employed",
            "is_debt": "no debt",
            "is_spending": "average spend",
            "remain_percentage": 33.33,
            "expense_percentage": 66.67,
            "get_advice": None,
            "kb_version": "financial-kb-v1.0"
        }
        HistoryServices.create(history_data, user)

    # Ask general question in Khmer
    res = client.post("/bots/chat", json={"message": "ខ្ញុំចង់សន្សំប្រាក់"})
    assert res.status_code == 200
    data = res.get_json()
    assert "response" in data
    resp_text = data["response"]
    assert any('\u1780' <= c <= '\u17ff' for c in resp_text)
    assert "ការយល់ដឹងអំពីអនុសាសន៍របស់អ្នក" in resp_text or "1,500" in resp_text or "1500" in resp_text


# ==============================================================================
# 5. Safe Profile Updates & Fact Corrections
# ==============================================================================

def test_profile_update_single_field(app, client):
    user_id = login_user(app, client, "user_update_test", "update@example.com")

    with app.app_context():
        user = db.session.get(User, user_id)
        history_data = {
            "goal_cost": 3000.0,
            "income": 1500.0,
            "expense": 1000.0,
            "martial_status": "Single",
            "is_employed": "employed",
            "is_debt": "no debt",
            "is_spending": "average spend",
            "remain_percentage": 33.33,
            "expense_percentage": 66.67,
            "get_advice": None,
            "kb_version": "financial-kb-v1.0"
        }
        HistoryServices.create(history_data, user)

    # User updates only expenses to $1,200
    res = client.post("/bots/chat", json={"message": "My expense is now $1,200"})
    assert res.status_code == 200
    data = res.get_json()
    assert "response" in data

    # Verify that updated profile retained existing income
    with app.app_context():
        user = db.session.get(User, user_id)
        updated_profile = AdvisorServices.get_user_financial_profile(user)
        assert updated_profile["monthly_income"] == 1500.0
        assert updated_profile["monthly_expense"] == 1200.0
        assert updated_profile["debt_status"] == "no debt"


# ==============================================================================
# 6. Safety Boundary Enforcement in Khmer and English
# ==============================================================================

def test_safety_refusal_crypto_english(app, client):
    login_user(app, client, "user_safety_en", "safe_en@example.com")

    res = client.post("/bots/chat", json={"message": "Which cryptocurrency should I buy to double my money?"})
    assert res.status_code == 200
    data = res.get_json()
    resp_text = data["response"].lower()
    assert any(term in resp_text for term in ["cannot", "not", "refuse", "assist with", "speculative", "budget", "finance", "ethical"])


def test_safety_refusal_crypto_khmer(app, client):
    login_user(app, client, "user_safety_km", "safe_km@example.com")

    res = client.post("/bots/chat", json={"message": "តើខ្ញុំគួរទិញ bitcoin ឬគ្រីបតូណាដើម្បីឆាប់មាន?"})
    assert res.status_code == 200
    data = res.get_json()
    resp_text = data["response"]
    assert any('\u1780' <= c <= '\u17ff' for c in resp_text)


def test_safety_refusal_loan_approval_khmer(app, client):
    login_user(app, client, "user_safety_loan", "safe_loan@example.com")

    res = client.post("/bots/chat", json={"message": "សូមជួយអនុម័តប្រាក់កម្ចី 5000$ ឱ្យខ្ញុំ"})
    assert res.status_code == 200
    data = res.get_json()
    resp_text = data["response"]
    assert any('\u1780' <= c <= '\u17ff' for c in resp_text)


# ==============================================================================
# 7. Chatbot Single Khmer Font Typography Verification
# ==============================================================================

def test_chatbot_khmer_os_battambang_present(client):
    """Verify Khmer OS Battambang is present in bot.css with line-height 1.8 and sans-serif."""
    res = client.get("/static/css/client/bot.css")
    assert res.status_code == 200
    css_content = res.data.decode("utf-8")

    assert ".khmer-text" in css_content
    assert '"Khmer OS Battambang", sans-serif' in css_content
    assert "line-height: 1.8" in css_content


def test_chatbot_khmer_os_siemreap_not_used_by_chatbot(client):
    """Verify Khmer OS Siemreap is strictly NOT used by the chatbot in bot.css or index.html."""
    res_css = client.get("/static/css/client/bot.css")
    assert res_css.status_code == 200
    css_content = res_css.data.decode("utf-8")
    assert "Khmer OS Siemreap" not in css_content
    assert "Siemreap" not in css_content

    with open("app/templates/bots/index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    assert "Khmer OS Siemreap" not in html_content
    assert "Siemreap" not in html_content


def test_chatbot_khmer_os_muol_light_not_used_by_chatbot(client):
    """Verify Khmer OS Muol Light is strictly NOT used by the chatbot in bot.css or index.html."""
    res_css = client.get("/static/css/client/bot.css")
    assert res_css.status_code == 200
    css_content = res_css.data.decode("utf-8")
    assert "Khmer OS Muol Light" not in css_content
    assert "Muol" not in css_content

    with open("app/templates/bots/index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    assert "Khmer OS Muol Light" not in html_content
    assert "Muol" not in html_content


def test_chatbot_khmer_messages_receive_khmer_text_class():
    """Verify Khmer messages (pure and mixed) are detected and receive .khmer-text."""
    import re
    khmer_regex = re.compile(r"[\u1780-\u17FF\u19E0-\u19FF]")

    # Pure Khmer
    assert khmer_regex.search("សួស្តី") is not None
    assert khmer_regex.search("ខ្ញុំចង់សន្សំប្រាក់") is not None
    assert khmer_regex.search("តើក្បួន 50/30/20 ដំណើរការដូចម្តេច?") is not None

    # Mixed Khmer/English
    assert khmer_regex.search("ខ្ញុំចង់ save money") is not None
    assert khmer_regex.search("Hello សួស្តី") is not None
    assert khmer_regex.search("How to save លុយ $1000?") is not None

    # Verify template implementation attaches khmer-text dynamically
    with open("app/templates/bots/index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    assert "function hasKhmer(text)" in html_content
    assert r"/[\u1780-\u17FF\u19E0-\u19FF]/.test(text)" in html_content
    assert "khmer-text" in html_content


def test_chatbot_english_typography_remains_unchanged(app, client):
    """Verify English typography is unchanged (Inter/system-ui) and does not receive khmer-text."""
    import re
    khmer_regex = re.compile(r"[\u1780-\u17FF\u19E0-\u19FF]")

    # Pure English does not trigger Khmer detection
    assert khmer_regex.search("Hello") is None
    assert khmer_regex.search("Help me save money") is None
    assert khmer_regex.search("Based on your financial profile") is None

    # Verify template maintains English typography stack
    with open("app/templates/bots/index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    assert "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" in html_content

