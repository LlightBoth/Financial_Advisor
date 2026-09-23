import pytest
import re
import json
from datetime import date
from flask import session
from app import create_app
from app.models import User, Role, Plan, Income, Expense
from app.security.token import Token
from extension import db
from config import Config
from sqlalchemy.pool import StaticPool


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool,
    }
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-dashboard-secret-key"


@pytest.fixture(name="app")
def fixture_app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture(name="client")
def fixture_client(app):
    return app.test_client()


def create_and_login_user(app, client, username="client_test", email="client_test@example.com"):
    """Deterministic, isolated test user creation for controlled test execution."""
    with app.app_context():
        role_user = Role.query.filter_by(name="user").first()
        if not role_user:
            role_user = Role(name="user", description="Regular Client")
            db.session.add(role_user)
            db.session.commit()

        user = User(username=username, email=email, full_name="Test Client User")
        user.set_password("TestSecret123!")
        user.roles.append(role_user)
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
# 1. English Dashboard Localization Tests
# ==============================================================================

def test_client_dashboard_renders_english(app, client):
    """Verify that English dashboard renders all expected UI text and no raw translation keys."""
    create_and_login_user(app, client)

    response = client.get("/dashboards/")
    assert response.status_code == 200
    html = response.data.decode("utf-8")

    # Document & Layout Attributes
    assert 'lang="en"' in html
    assert "fonts.css" in html

    # Header Banner
    assert "Financial Intelligence" in html
    assert "Real-time performance metrics" in html
    assert "savings tracking" in html
    assert "AI Advisory Scan" in html

    # Metric Cards
    assert "Live" in html
    assert "Total Balance Saving" in html
    assert "Rate" in html
    assert "Income Growth" in html
    assert "Score" in html
    assert "Risk Profile Status" in html

    # Chart Cards
    assert "Weekly Cashflow Trend" in html
    assert "7-Day Analysis" in html
    assert "Income vs Expense" in html
    assert "Ratio" in html

    # Milestone Cards
    assert "Savings Milestones" in html
    assert "Target Strategy Pacing" in html
    assert "Daily Milestones" in html
    assert "Check off today" in html
    assert "contributions" in html

    # Safe I18N Object in JavaScript
    match = re.search(r'const\s+I18N\s*=\s*(\{.*?\});', html, re.DOTALL)
    assert match is not None, "const I18N not found in rendered dashboard HTML"
    i18n_data = json.loads(match.group(1))
    assert i18n_data["day"] == "Day"
    assert i18n_data["val"] == "Val"
    assert i18n_data["income"] == "Income"
    assert i18n_data["expense"] == "Expenses"
    assert i18n_data["days"]["Mon"] == "Mon"
    assert i18n_data["days"]["Sun"] == "Sun"

    # Ensure no raw translation keys leaked into rendered HTML text
    assert "{{ _(" not in html
    assert "dashboard.financial_intelligence" not in html
    assert "dashboard.total_balance_saving" not in html


# ==============================================================================
# 2. Khmer Dashboard Localization Tests
# ==============================================================================

def test_client_dashboard_renders_khmer(app, client):
    """Verify that Khmer dashboard renders authentic Khmer translations and proper attributes."""
    create_and_login_user(app, client)

    # Set session language to Khmer
    with client.session_transaction() as sess:
        sess["lang"] = "km"

    response = client.get("/dashboards/")
    assert response.status_code == 200
    html = response.data.decode("utf-8")

    # Document & Layout Attributes
    assert 'lang="km"' in html
    assert "fonts.css" in html

    # Header Banner in Khmer
    assert "ព័ត៌មានឆ្លាតវៃហិរញ្ញវត្ថុ" in html
    assert "ម៉ែត្រិកវាស់វែងដំណើរការ និងការតាមដានការសន្សំតាមពេលវេលាជាក់ស្តែង" in html
    assert "ស្កេនការប្រឹក្សា AI" in html

    # Metric Cards in Khmer
    assert "ផ្សាយផ្ទាល់" in html
    assert "សមតុល្យសន្សំសរុប" in html
    assert "អត្រា" in html
    assert "កំណើនចំណូល" in html
    assert "ពិន្ទុ" in html
    assert "ស្ថានភាពហានិភ័យ" in html

    # Chart Cards in Khmer
    assert "និន្នាការចរន្តសាច់ប្រាក់ប្រចាំសប្តាហ៍" in html
    assert "ការវិភាគ ៧ ថ្ងៃ" in html
    assert "ចំណូល និងចំណាយ" in html
    assert "សមាមាត្រ" in html

    # Milestone Cards in Khmer
    assert "គោលដៅសន្សំ" in html
    assert "ដំណើរការយុទ្ធសាស្ត្រគោលដៅ" in html
    assert "កិច្ចការប្រចាំថ្ងៃ" in html
    assert "កត់ត្រាការរួមចំណែកថ្ងៃនេះ" in html

    # Safe I18N Object in JavaScript contains Khmer labels
    match = re.search(r'const\s+I18N\s*=\s*(\{.*?\});', html, re.DOTALL)
    assert match is not None, "const I18N not found in rendered dashboard HTML"
    i18n_data = json.loads(match.group(1))
    assert i18n_data["day"] == "ថ្ងៃ"
    assert i18n_data["val"] == "តម្លៃ"
    assert i18n_data["income"] == "ចំណូល"
    assert i18n_data["expense"] == "ចំណាយ"
    assert i18n_data["days"]["Mon"] == "ច័ន្ទ"
    assert i18n_data["days"]["Sun"] == "អាទិត្យ"

    # Ensure no raw translation keys leaked
    assert "{{ _(" not in html
    assert "dashboard.financial_intelligence" not in html
    assert "dashboard.total_balance_saving" not in html


# ==============================================================================
# 3. Language Switching & Session Persistence
# ==============================================================================

def test_language_switch_preserves_auth_and_session(app, client):
    """Test switching English -> Khmer -> English while preserving auth and route."""
    create_and_login_user(app, client)

    # 1. Start in English
    res_en = client.get("/dashboards/")
    assert res_en.status_code == 200
    assert 'lang="en"' in res_en.data.decode("utf-8")

    # 2. Switch to Khmer
    res_switch_km = client.get("/set-language/km?next=/dashboards/")
    assert res_switch_km.status_code == 302
    assert "/dashboards/" in res_switch_km.headers.get("Location", "")

    # 3. View dashboard in Khmer — user must still be authenticated
    res_km = client.get("/dashboards/")
    assert res_km.status_code == 200
    html_km = res_km.data.decode("utf-8")
    assert 'lang="km"' in html_km
    assert "ព័ត៌មានឆ្លាតវៃហិរញ្ញវត្ថុ" in html_km

    # 4. Switch back to English
    res_switch_en = client.get("/set-language/en?next=/dashboards/")
    assert res_switch_en.status_code == 302

    # 5. View dashboard in English again
    res_en_again = client.get("/dashboards/")
    assert res_en_again.status_code == 200
    html_en_again = res_en_again.data.decode("utf-8")
    assert 'lang="en"' in html_en_again
    assert "Financial Intelligence" in html_en_again


# ==============================================================================
# 4. Financial Data Preservation Verification
# ==============================================================================

def test_financial_values_preserved_across_languages(app, client):
    """Ensure that financial amounts and calculations are identical in both languages."""
    user_id = create_and_login_user(app, client)

    with app.app_context():
        user = db.session.get(User, user_id)
        # Seed test financial records
        inc = Income(
            amount=2500.0,
            category="Salary",
            description="Monthly Salary",
            income_date=date.today(),
        )
        exp = Expense(
            amount=1200.0,
            category="Housing",
            description="Rent",
            expense_date=date.today(),
        )
        inc.users.append(user)
        exp.users.append(user)
        db.session.add_all([inc, exp])
        db.session.commit()

    # Fetch in English
    with client.session_transaction() as sess:
        sess["lang"] = "en"
    res_en = client.get("/dashboards/")
    assert res_en.status_code == 200
    html_en = res_en.data.decode("utf-8")

    # Fetch in Khmer
    with client.session_transaction() as sess:
        sess["lang"] = "km"
    res_km = client.get("/dashboards/")
    assert res_km.status_code == 200
    html_km = res_km.data.decode("utf-8")

    # Expected values: sum_saving = 2500 - 1200 = 1300.00
    # sum_saving_rate = (1300 / 2500) * 100 = 52.00%
    expected_saving_str = "$1,300.00"
    expected_rate_str = "52.00%"

    assert expected_saving_str in html_en, f"English dashboard missing {expected_saving_str}"
    assert expected_saving_str in html_km, f"Khmer dashboard missing {expected_saving_str}"

    assert expected_rate_str in html_en, f"English dashboard missing {expected_rate_str}"
    assert expected_rate_str in html_km, f"Khmer dashboard missing {expected_rate_str}"

    # Extract all monetary values with regex and verify strict equality
    money_pattern = r'\$[\d,]+\.\d{2}'
    en_monetary = re.findall(money_pattern, html_en)
    km_monetary = re.findall(money_pattern, html_km)

    assert en_monetary == km_monetary, f"Financial values differ between languages: {en_monetary} != {km_monetary}"


# ==============================================================================
# 5. JavaScript I18N Object & Injection Safety
# ==============================================================================

def test_javascript_i18n_dictionary_safety(app, client):
    """Verify that JavaScript I18N dictionary is safely serialized without code injection."""
    create_and_login_user(app, client)

    response = client.get("/dashboards/")
    html = response.data.decode("utf-8")

    # Extract JSON between 'const I18N = ' and ';'
    match = re.search(r'const\s+I18N\s*=\s*(\{.*?\});', html, re.DOTALL)
    assert match is not None, "const I18N dictionary not found in rendered dashboard HTML"

    i18n_json_str = match.group(1)
    i18n_data = json.loads(i18n_json_str)

    assert "income" in i18n_data
    assert "expense" in i18n_data
    assert "days" in i18n_data
    assert "Mon" in i18n_data["days"]
    assert "Sun" in i18n_data["days"]


# ==============================================================================
# 6. Client Layout Navigation Localization
# ==============================================================================

def test_client_layout_navigation_localized(app, client):
    """Verify that clientBase layout sidebar and alerts are translated properly."""
    create_and_login_user(app, client)

    # English Layout
    with client.session_transaction() as sess:
        sess["lang"] = "en"
    res_en = client.get("/dashboards/")
    html_en = res_en.data.decode("utf-8")
    assert "MAIN MENU" in html_en
    assert "Recent Alerts" in html_en
    assert "Complete Daily Tasks" in html_en

    # Khmer Layout
    with client.session_transaction() as sess:
        sess["lang"] = "km"
    res_km = client.get("/dashboards/")
    html_km = res_km.data.decode("utf-8")
    assert "ម៉ឺនុយមេ" in html_km
    assert "ការជូនដំណឹងថ្មីៗ" in html_km
    assert "បំពេញកិច្ចការប្រចាំថ្ងៃ" in html_km
