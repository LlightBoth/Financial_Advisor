"""
Regression Test Suite for Response-Quality Polish.

Verifies:
1. Khmer-only output:
   - When user writes in Khmer, response is 100% Khmer.
   - No English sections (e.g. "Understanding Your Recommendation") appended unless explicitly requested.
2. Surplus grounding:
   - For income $2,500 and expenses $1,800, never says "little room for savings".
   - Accurately states verified monthly surplus of $700.
3. Precise ratio language:
   - 72% expense ratio: expenses consume 72% of income (Khmer: ការចំណាយប្រើប្រាស់ ៧២% នៃប្រាក់ចំណូល).
   - 80% expense ratio: expenses consume exactly 80% of income (Khmer: ការចំណាយប្រើប្រាស់យ៉ាងជាក់លាក់ ៨០% នៃប្រាក់ចំណូល).
4. Zero debt advice for debt-free users:
   - Strictly no debt payoff or credit card repayment advice when user has no debt.
5. ConsultantEngine as sole authority:
   - All calculations and rule selections originate deterministically from ConsultantEngine.
"""

import re
import pytest
from app import create_app
from config import Config
from extension import db
from app.models.user import User
from app.models.role import Role
from app.security.token import Token
from app.services.advisor_services import AdvisorServices
from app.services.consultant_engine import ConsultantEngine
from app.services.llm_service import LLMService
from training.llm_output_normalizer import (
    normalize_and_verify_response,
    sanitize_khmer_only_response,
    sanitize_explanation_consistency,
    sanitize_no_debt_advice,
    detect_language
)


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {}
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-secret-response-quality"


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
        db.session.remove()
        db.drop_all()


@pytest.fixture(name="auth_client")
def fixture_auth_client(app):
    client = app.test_client()
    with app.app_context():
        user = User(
            username="quality_user",
            full_name="Quality Test User",
            email="quality@test.com"
        )
        user.set_password("Password123!")
        role = Role.query.filter_by(name="user").first()
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
    return client


# ==============================================================================
# 1. Khmer-Only Output Regression Tests
# ==============================================================================

def test_khmer_input_returns_fully_khmer_without_english_sections():
    """Verify that Khmer input produces a response without English sections or headers."""
    raw_response_with_leakage = (
        "ផ្អែកលើទិន្នន័យហិរញ្ញវត្ថុរបស់អ្នក (ចំណូល: $2,500/ខែ, ចំណាយ: $1,800/ខែ, សល់សុទ្ធ: $700/ខែ)៖\n\n"
        "ការចំណាយប្រចាំថ្ងៃរបស់អ្នកមានតុល្យភាពល្អ (ការចំណាយប្រើប្រាស់ ៧២% នៃប្រាក់ចំណូល)។ "
        "ប្រសិនបើអ្នកមិនទាន់មានប្រាក់បម្រុងបន្ទាន់ទេ សូមផ្តល់អាទិភាពដល់ការសន្សំប្រាក់សម្រាប់ ៣ ទៅ ៦ ខែនៃការចំណាយចាំបាច់។\n\n"
        "**Understanding Your Recommendation**:\n"
        "Your living costs consume most of your monthly income, leaving little room for immediate savings."
    )

    cleaned = sanitize_khmer_only_response(raw_response_with_leakage, user_input="ខ្ញុំចង់សន្សំប្រាក់", lang="km")

    # Assert no English header
    assert "Understanding Your Recommendation" not in cleaned
    assert "**Understanding Your Recommendation**" not in cleaned
    # Assert no English sentence left
    assert "Your living costs consume" not in cleaned
    # Assert Khmer content preserved
    assert "ការចំណាយប្រចាំថ្ងៃរបស់អ្នកមានតុល្យភាពល្អ" in cleaned


def test_khmer_response_replaces_english_explanation_with_khmer():
    """When header is Khmer but body was English, replace with verified Khmer explanation."""
    raw_response = (
        "ផ្អែកលើទិន្នន័យហិរញ្ញវត្ថុរបស់អ្នក៖\n\n"
        "ការចំណាយប្រចាំថ្ងៃរបស់អ្នកមានតុល្យភាពល្អ។\n\n"
        "**ការយល់ដឹងអំពីអនុសាសន៍របស់អ្នក**:\n"
        "Your monthly expenses are close to income, leaving limited savings capacity."
    )

    cleaned = sanitize_khmer_only_response(raw_response, user_input="ជួយរៀបចំផែនការ", lang="km")
    assert "Your monthly expenses" not in cleaned
    assert "**ការយល់ដឹងអំពីអនុសាសន៍របស់អ្នក**:" in cleaned
    assert "លំហូរសាច់ប្រាក់សុទ្ធប្រចាំខែរបស់អ្នកមានសញ្ញាវិជ្ជមាន" in cleaned


def test_english_allowed_only_when_user_explicitly_requests():
    """If user asks in Khmer but explicitly requests English, English is preserved."""
    raw_response = (
        "Based on your profile:\n\n"
        "**Understanding Your Recommendation**:\n"
        "You have a verified monthly surplus of $700."
    )
    result = sanitize_khmer_only_response(raw_response, user_input="សូមឆ្លើយជាភាសាអង់គ្លេស", lang="km")
    assert "Understanding Your Recommendation" in result


# ==============================================================================
# 2. Surplus Grounding Tests ($2,500 income / $1,800 expense -> verified $700)
# ==============================================================================

def test_surplus_grounding_rejects_little_room_for_savings():
    """For income $2,500 and expenses $1,800, do not say 'little room for savings'; state verified monthly surplus of $700."""
    hallucinated_text = (
        "Your expenses closely match your income, leaving little room for savings. "
        "Consider reviewing discretionary spending."
    )
    context = {
        "monthly_income": 2500.0,
        "monthly_expense": 1800.0,
        "net_cashflow": 700.0,
        "expense_ratio": 0.72,
        "debt_status": "no debt",
    }
    corrected = sanitize_explanation_consistency(hallucinated_text, context_profile=context, lang="en")

    assert "little room for savings" not in corrected.lower()
    assert "little room for immediate savings" not in corrected.lower()
    assert "verified monthly surplus of $700" in corrected


def test_surplus_grounding_end_to_end_normalizer():
    """Full normalization pipeline replaces 'limited savings capacity' with verified surplus."""
    raw_text = (
        "Financial Profile: Monthly Income: $2,500.00, Monthly Expense: $1,800.00. "
        "Your living costs consume most of your monthly income, leaving little room for immediate savings."
    )
    normalized = normalize_and_verify_response(
        raw_text,
        user_input="Help me create a financial plan.",
        context_profile={"monthly_income": 2500.0, "monthly_expense": 1800.0, "net_cashflow": 700.0, "debt_status": "no debt"},
        lang="en"
    )

    assert "little room for immediate savings" not in normalized.lower()
    assert "verified monthly surplus of $700" in normalized


# ==============================================================================
# 3. Precise Ratio Language Tests (72% and 80%)
# ==============================================================================

def test_precise_ratio_language_72_percent_en_and_km():
    """72% expense ratio: expenses consume 72% of income."""
    # English test
    generic_en = "Your living expenses are well-balanced (consuming between 50% and 80% of income)."
    context_72 = {
        "monthly_income": 2500.0,
        "monthly_expense": 1800.0,
        "expense_ratio": 0.72,
        "net_cashflow": 700.0,
    }
    refined_en = sanitize_explanation_consistency(generic_en, context_profile=context_72, lang="en")
    assert "expenses consume 72% of income" in refined_en
    assert "between 50% and 80%" not in refined_en

    # Khmer test
    generic_km = "ការចំណាយប្រចាំថ្ងៃរបស់អ្នកមានតុល្យភាពល្អ (ចន្លោះពី ៥០% ទៅ ៨០% នៃប្រាក់ចំណូល)។"
    refined_km = sanitize_explanation_consistency(generic_km, context_profile=context_72, lang="km")
    assert "ការចំណាយប្រើប្រាស់ ៧២% នៃប្រាក់ចំណូល" in refined_km
    assert "ចន្លោះពី ៥០% ទៅ ៨០%" not in refined_km


def test_precise_ratio_language_80_percent_en_and_km():
    """80% expense ratio: expenses consume exactly 80% of income."""
    # English test
    generic_en = "Operating cash flow is positive, but living costs consume 80% or more of income."
    context_80 = {
        "monthly_income": 2500.0,
        "monthly_expense": 2000.0,
        "expense_ratio": 0.80,
        "net_cashflow": 500.0,
    }
    refined_en = sanitize_explanation_consistency(generic_en, context_profile=context_80, lang="en")
    assert "expenses consume exactly 80% of income" in refined_en
    assert "80% or more" not in refined_en

    # Khmer test
    generic_km = "លំហូរសាច់ប្រាក់ប្រតិបត្តិការមានវិជ្ជមាន ប៉ុន្តែការចំណាយប្រចាំថ្ងៃស្រូបយក ៨០% ឬច្រើនជាងនេះនៃប្រាក់ចំណូល។"
    refined_km = sanitize_explanation_consistency(generic_km, context_profile=context_80, lang="km")
    assert "ការចំណាយប្រើប្រាស់យ៉ាងជាក់លាក់ ៨០% នៃប្រាក់ចំណូល" in refined_km
    assert "៨០% ឬច្រើនជាងនេះ" not in refined_km


# ==============================================================================
# 4. Zero Debt Advice for Debt-Free User Tests
# ==============================================================================

def test_zero_debt_advice_enforcement_for_debt_free_user():
    """Never invent debt advice for a debt-free user."""
    hallucinated_debt_advice_en = (
        "You have a $700 surplus. Consider allocating this extra cash toward structured debt payoff "
        "and paying off high-interest credit card balances if available."
    )
    cleaned_en = sanitize_no_debt_advice(hallucinated_debt_advice_en, is_debt_free=True)
    assert "debt payoff" not in cleaned_en.lower()
    assert "credit card" not in cleaned_en.lower()
    assert "emergency reserve" in cleaned_en.lower() or "savings" in cleaned_en.lower()

    hallucinated_debt_advice_km = (
        "អ្នកមានប្រាក់សល់ $700។ សូមពិចារណាបែងចែកប្រាក់នេះទៅកាន់ ការទូទាត់បំណុលដែលមានរចនាសម្ព័ន្ធ និងសងបំណុលកាតឥណទាន។"
    )
    cleaned_km = sanitize_no_debt_advice(hallucinated_debt_advice_km, is_debt_free=True)
    assert "សងបំណុល" not in cleaned_km
    assert "ការទូទាត់បំណុល" not in cleaned_km
    assert "មូលនិធិសង្គ្រោះបន្ទាន់" in cleaned_km or "ការកសាងប្រាក់សន្សំ" in cleaned_km


# ==============================================================================
# 5. ConsultantEngine as Sole Authority End-to-End Tests
# ==============================================================================

def test_consultant_engine_authority_72_and_80_percent(app):
    """ConsultantEngine is the sole authority for calculations and rule selection."""
    with app.app_context():
        # Case 1: Income $2,500, Expense $1,800
        profile_72 = {
            "income": 2500.0,
            "expense": 1800.0,
            "debt_status": "no debt",
            "employment_status": "employed",
        }
        res_72 = ConsultantEngine.evaluate(profile_72)
        assert res_72["metrics"]["net_cashflow"] == 700.0
        assert res_72["metrics"]["expense_ratio"] == 0.72
        assert res_72["metrics"]["surplus_ratio"] == 0.28
        assert res_72["selected_advice"].rule_id == "BALANCED_BUDGET_BUFFER_BUILDING"

        dto_72, _ = AdvisorServices.consult(profile_72, lang="en")
        assert dto_72["metrics"]["net_cashflow"] == 700.0
        assert "expenses consume 72% of income" in dto_72["advice"]["en"]

        # Case 2: Income $2,500, Expense $2,000
        profile_80 = {
            "income": 2500.0,
            "expense": 2000.0,
            "debt_status": "no debt",
            "employment_status": "employed",
        }
        res_80 = ConsultantEngine.evaluate(profile_80)
        assert res_80["metrics"]["net_cashflow"] == 500.0
        assert res_80["metrics"]["expense_ratio"] == 0.80
        assert res_80["metrics"]["surplus_ratio"] == 0.20
        assert res_80["selected_advice"].rule_id == "TIGHT_MARGIN_HIGH_EXPENSE"

        dto_80, _ = AdvisorServices.consult(profile_80, lang="en")
        assert dto_80["metrics"]["net_cashflow"] == 500.0
        assert "expenses consume exactly 80% of income" in dto_80["advice"]["en"]


# ==============================================================================
# 6. Chatbot Route Integration Tests
# ==============================================================================

def test_chatbot_khmer_turn_produces_khmer_without_english_sections(auth_client, app):
    """Chatbot /bot/send endpoint with Khmer input returns pure Khmer response."""
    with app.app_context():
        from app.models.history import History
        user = User.query.filter_by(email="quality@test.com").first()
        # Seed user profile: income $2,500, expense $1,800, no debt
        h = History(
            income=2500.0,
            expense=1800.0,
            goal_cost=5000.0,
            martial_status="Married",
            is_employed=True,
            is_debt=False,
            is_spending=True,
            remain_percentage=28.0,
            expense_percentage=72.0,
            get_advice="BALANCED_BUDGET_BUFFER_BUILDING"
        )
        h.users.append(user)
        db.session.add(h)
        db.session.commit()

    # Query in Khmer
    resp = auth_client.post("/bots/chat", json={"message": "ខ្ញុំចង់សន្សំប្រាក់"})
    assert resp.status_code == 200
    data = resp.get_json()
    ai_msg = data.get("response", "")

    # Assert no English headers
    assert "Understanding Your Recommendation" not in ai_msg
    assert "little room for savings" not in ai_msg.lower()
    # Assert Khmer content exists
    assert re.search(r"[\u1780-\u17ff]", ai_msg)
