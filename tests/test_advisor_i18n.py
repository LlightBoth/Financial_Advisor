import json
import pytest
from datetime import datetime
from app import create_app
from app.models import User, Role, History, Rule, Fact
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
    SECRET_KEY = "test-advisor-i18n-secret-key"


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


def create_and_login_user(app, client, username="advisor_tester", email="advisor_tester@example.com"):
    """Deterministic, isolated test user creation for controlled test execution."""
    with app.app_context():
        role_user = Role.query.filter_by(name="user").first()
        if not role_user:
            role_user = Role(name="user", description="Regular Client")
            db.session.add(role_user)
            db.session.commit()

        user = User(username=username, email=email, full_name="Advisor Tester")
        user.set_password("SecurePassword123!")
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


def seed_test_rule(app):
    """Seed a deterministic test rule for the expert system."""
    with app.app_context():
        rule = Rule(
            conclusion="Your financial situation is balanced and on track.",
            advice="Continue to maintain low debt and regular savings habits.",
            certainty=0.3
        )
        db.session.add(rule)
        db.session.commit()
        return rule.id


# ==============================================================================
# 1. AI Advisor Interface — English Localization
# ==============================================================================

def test_advisor_index_english(app, client):
    create_and_login_user(app, client)
    with client.session_transaction() as sess:
        sess["lang"] = "en"

    res = client.get("/advisors/")
    assert res.status_code == 200
    html = res.data.decode("utf-8")

    assert 'lang="en"' in html
    assert "AI Expert System" in html
    assert "Financial Baseline" in html
    assert "Target Milestone Goal ($)" in html
    assert "Monthly Income ($)" in html
    assert "Monthly Expense ($)" in html
    assert "Marital Status" in html
    assert "Single" in html
    assert "Married" in html
    assert "Behavioral Profile" in html
    assert "Execute Inference Analysis" in html
    assert "AI Advisor" in html


def test_advisor_submission_english(app, client):
    create_and_login_user(app, client)
    seed_test_rule(app)
    with client.session_transaction() as sess:
        sess["lang"] = "en"

    post_data = {
        "goal_cost": "10000.00",
        "income": "5000.00",
        "expense": "2000.00",
        "martial_status": "Single",
        "employment_status": "employed",
        "debt_status": "no debt",
        "spending_habit": "average spend",
    }
    res = client.post("/advisors/", data=post_data)
    assert res.status_code == 200
    html = res.data.decode("utf-8")

    assert "Expert System Analysis" in html
    assert "Savings Potential" in html
    assert "Expense Load" in html
    assert "Projected Horizon" in html
    assert "Certainty Factor (CF)" in html
    assert "Recalibrate Inference Scan" in html
    # Numerical values preserved
    assert "60.0%" in html  # savings potential: (5000 - 2000) / 5000 = 60%
    assert "40.0%" in html  # expense load: 2000 / 5000 = 40%


def test_advisor_analyse_page_english(app, client):
    create_and_login_user(app, client)
    with client.session_transaction() as sess:
        sess["lang"] = "en"

    # GET request without advice -> empty state
    res_get = client.get("/advisors/analyse")
    assert res_get.status_code == 200
    html_get = res_get.data.decode("utf-8")
    assert 'lang="en"' in html_get
    assert "Financial Analysis &amp; Advice" in html_get or "Financial Analysis & Advice" in html_get
    assert "Back to Dashboard" in html_get
    assert "No Advice Available" in html_get
    assert "Return to Dashboard" in html_get
    assert "No financial data yet" in html_get

    # POST request with financial data -> active recommendation
    res_post = client.post("/advisors/analyse", data={
        "income": "5000.00",
        "expense": "2000.00",
        "goal_cost": "10000.00",
        "martial_status": "Single",
        "employment_status": "employed",
        "debt_status": "no debt",
        "spending_habit": "average spend",
    })
    assert res_post.status_code == 200
    html_post = res_post.data.decode("utf-8")
    assert "Advisor Recommendation" in html_post
    assert "Calculated Metrics Overview" in html_post
    assert "Income vs. monthly expenses" in html_post
    assert "Analyzed Income" in html_post
    assert "Analyzed Expense" in html_post


# ==============================================================================
# 2. AI Advisor Interface — Khmer Localization
# ==============================================================================

def test_advisor_index_khmer(app, client):
    create_and_login_user(app, client)
    with client.session_transaction() as sess:
        sess["lang"] = "km"

    res = client.get("/advisors/")
    assert res.status_code == 200
    html = res.data.decode("utf-8")

    assert 'lang="km"' in html
    assert "ប្រព័ន្ធអ្នកជំនាញ AI" in html
    assert "មូលដ្ឋានហិរញ្ញវត្ថុ" in html
    assert "គោលដៅកំណត់សំខាន់ ($)" in html
    assert "ចំណូលប្រចាំខែ ($)" in html
    assert "ចំណាយប្រចាំខែ ($)" in html
    assert "ស្ថានភាពអាពាហ៍ពិពាហ៍" in html
    assert "នៅលីវ" in html
    assert "រៀបការរួច" in html
    assert "ទម្រង់ឥរិយាបថ" in html
    assert "ដំណើរការការវិភាគ" in html
    assert "ទីប្រឹក្សា AI" in html


def test_advisor_submission_khmer(app, client):
    create_and_login_user(app, client)
    seed_test_rule(app)
    with client.session_transaction() as sess:
        sess["lang"] = "km"

    post_data = {
        "goal_cost": "10000.00",
        "income": "5000.00",
        "expense": "2000.00",
        "martial_status": "Single",
        "employment_status": "employed",
        "debt_status": "no debt",
        "spending_habit": "average spend",
    }
    res = client.post("/advisors/", data=post_data)
    assert res.status_code == 200
    html = res.data.decode("utf-8")

    assert "ការវិភាគប្រព័ន្ធអ្នកជំនាញ" in html
    assert "សក្តានុពលសន្សំ" in html
    assert "បន្ទុកចំណាយ" in html
    assert "កត្តាប្រាកដប្រជា (CF)" in html
    assert "គណនាការស្កេនឡើងវិញ" in html
    # Numerical values precisely preserved
    assert "60.0%" in html
    assert "40.0%" in html


def test_advisor_analyse_page_khmer(app, client):
    create_and_login_user(app, client)
    with client.session_transaction() as sess:
        sess["lang"] = "km"

    # GET request
    res_get = client.get("/advisors/analyse")
    assert res_get.status_code == 200
    html_get = res_get.data.decode("utf-8")
    assert 'lang="km"' in html_get
    assert "ការវិភាគ និងដំបូន្មានហិរញ្ញវត្ថុ" in html_get
    assert "ត្រឡប់ទៅផ្ទាំងគ្រប់គ្រង" in html_get
    assert "មិនមានដំបូន្មានទេ" in html_get
    assert "I18N_ADVISOR" in html_get

    # POST request
    res_post = client.post("/advisors/analyse", data={
        "income": "5000.00",
        "expense": "2000.00",
        "goal_cost": "10000.00",
        "martial_status": "Single",
        "employment_status": "employed",
        "debt_status": "no debt",
        "spending_habit": "average spend",
    })
    assert res_post.status_code == 200
    html_post = res_post.data.decode("utf-8")
    assert "អនុសាសន៍ពីទីប្រឹក្សា" in html_post
    assert "ទិដ្ឋភាពទូទៅនៃរង្វាស់ដែលបានគណនា" in html_post
    assert "ចំណូលដែលបានវិភាគ" in html_post
    assert "ចំណាយដែលបានវិភាគ" in html_post


# ==============================================================================
# 3. History Module — English & Khmer
# ==============================================================================

def create_sample_history(app, user_id):
    with app.app_context():
        user = User.query.get(user_id)
        history = History(
            goal_cost=15000.00,
            income=4500.00,
            expense=1800.00,
            remain_percentage=60.0,
            expense_percentage=40.0,
            martial_status="married",
            is_employed=True,
            is_debt=False,
            is_spending=False,
            get_conclusion="Solid financial foundation.",
            get_advice="Maintain consistent savings rate.",
            created_at=datetime(2026, 9, 15, 10, 30)
        )
        history.users.append(user)
        db.session.add(history)
        db.session.commit()
        return history.id


def test_history_empty_state_english_and_khmer(app, client):
    create_and_login_user(app, client)

    # English empty state
    with client.session_transaction() as sess:
        sess["lang"] = "en"
    res_en = client.get("/histories/")
    assert res_en.status_code == 200
    html_en = res_en.data.decode("utf-8")
    assert "Inference History Archive" in html_en
    assert "No Inference Archive Found" in html_en
    assert "New Inference Scan" in html_en

    # Khmer empty state
    with client.session_transaction() as sess:
        sess["lang"] = "km"
    res_km = client.get("/histories/")
    assert res_km.status_code == 200
    html_km = res_km.data.decode("utf-8")
    assert "ប័ណ្ណសារប្រវត្តិវិភាគ" in html_km
    assert "រកមិនឃើញប័ណ្ណសារប្រវត្តិទេ" in html_km
    assert "ការស្កេនវិភាគថ្មី" in html_km


def test_history_list_and_detail_english(app, client):
    user_id = create_and_login_user(app, client)
    hist_id = create_sample_history(app, user_id)

    with client.session_transaction() as sess:
        sess["lang"] = "en"

    # Index with record
    res_idx = client.get("/histories/")
    assert res_idx.status_code == 200
    html_idx = res_idx.data.decode("utf-8")
    assert "Scan Ref" in html_idx
    assert f"#{hist_id}" in html_idx
    assert "Target Goal" in html_idx
    assert "$15,000.00" in html_idx
    assert "$4,500.00" in html_idx
    assert "Maintain consistent savings rate." in html_idx

    # Detail page
    res_dtl = client.get(f"/histories/{hist_id}")
    assert res_dtl.status_code == 200
    html_dtl = res_dtl.data.decode("utf-8")
    assert "Analysis Record" in html_dtl
    assert f"Reference ID: #{hist_id}" in html_dtl
    assert "Savings Potential" in html_dtl
    assert "Expense Load" in html_dtl
    assert "Monthly Income" in html_dtl
    assert "Strategic Roadmap" in html_dtl
    assert "Solid financial foundation." in html_dtl
    assert "Maintain consistent savings rate." in html_dtl
    assert "Delete Record" in html_dtl


def test_history_list_and_detail_khmer(app, client):
    user_id = create_and_login_user(app, client)
    hist_id = create_sample_history(app, user_id)

    with client.session_transaction() as sess:
        sess["lang"] = "km"

    # Index in Khmer
    res_idx = client.get("/histories/")
    assert res_idx.status_code == 200
    html_idx = res_idx.data.decode("utf-8")
    assert "លេខយោងស្កេន" in html_idx
    assert f"#{hist_id}" in html_idx
    assert "គោលដៅកំណត់" in html_idx
    assert "មូលដ្ឋានចំណូល" in html_idx
    assert "Maintain consistent savings rate." in html_idx
    # Numerical data intact
    assert "$15,000.00" in html_idx
    assert "$4,500.00" in html_idx

    # Detail in Khmer
    res_dtl = client.get(f"/histories/{hist_id}")
    assert res_dtl.status_code == 200
    html_dtl = res_dtl.data.decode("utf-8")
    assert "កំណត់ត្រាការវិភាគ" in html_dtl
    assert f"លេខយោង៖ #{hist_id}" in html_dtl
    assert "សក្តានុពលសន្សំ" in html_dtl
    assert "បន្ទុកចំណាយ" in html_dtl
    assert "ចំណូលប្រចាំខែ" in html_dtl
    assert "ផែនទីបង្ហាញផ្លូវយុទ្ធសាស្ត្រ" in html_dtl
    assert "លុបកំណត់ត្រា" in html_dtl
    # Values preserved
    assert "60.0%" in html_dtl
    assert "40.0%" in html_dtl
    assert "4,500" in html_dtl


def test_history_delete_flow_and_flash(app, client):
    user_id = create_and_login_user(app, client)
    hist_id = create_sample_history(app, user_id)

    # English delete confirm
    with client.session_transaction() as sess:
        sess["lang"] = "en"
    res_del_en = client.get(f"/histories/{hist_id}/delete")
    assert res_del_en.status_code == 200
    html_del_en = res_del_en.data.decode("utf-8")
    assert "Confirm Delete" in html_del_en
    assert "Are you sure you want to delete this history?" in html_del_en

    # Khmer delete confirm
    with client.session_transaction() as sess:
        sess["lang"] = "km"
    res_del_km = client.get(f"/histories/{hist_id}/delete")
    assert res_del_km.status_code == 200
    html_del_km = res_del_km.data.decode("utf-8")
    assert "បញ្ជាក់ការលុប" in html_del_km
    assert "តើអ្នកប្រាកដជាចង់លុបប្រវត្តិនេះមែនទេ?" in html_del_km

    # POST delete in Khmer -> check localized flash message
    res_post = client.post(f"/histories/{hist_id}/delete", follow_redirects=True)
    assert res_post.status_code == 200
    html_redirect = res_post.data.decode("utf-8")
    assert "កំណត់ត្រាប្រវត្តិត្រូវបានលុបដោយជោគជ័យ។" in html_redirect


# ==============================================================================
# 4. Language Switching & Value Integrity
# ==============================================================================

def test_language_switching_advisor_routes(app, client):
    user_id = create_and_login_user(app, client)

    # Switch to Khmer via route
    res_switch_km = client.get("/set-language/km", follow_redirects=True)
    assert res_switch_km.status_code == 200
    res_adv_km = client.get("/advisors/")
    html_km = res_adv_km.data.decode("utf-8")
    assert 'lang="km"' in html_km
    assert "ប្រព័ន្ធអ្នកជំនាញ AI" in html_km
    assert "មូលដ្ឋានហិរញ្ញវត្ថុ" in html_km

    # Switch back to English
    res_switch_en = client.get("/set-language/en", follow_redirects=True)
    assert res_switch_en.status_code == 200
    res_adv_en = client.get("/advisors/")
    html_en = res_adv_en.data.decode("utf-8")
    assert 'lang="en"' in html_en
    assert "AI Expert System" in html_en
    assert "Financial Baseline" in html_en


def test_financial_value_and_inference_preservation(app, client):
    """Ensure math, inference, percentages, and currencies are not altered by i18n."""
    user_id = create_and_login_user(app, client)

    data = {
        "goal_cost": "25000.00",
        "income": "5000.00",
        "expense": "1500.00",
        "martial_status": "Single",
        "employment_status": "employed",
        "debt_status": "no debt",
        "spending_habit": "average spend",
    }

    # Submit in EN
    with client.session_transaction() as sess:
        sess["lang"] = "en"
    res_en = client.post("/advisors/", data=data)
    assert res_en.status_code == 200
    html_en = res_en.data.decode("utf-8")

    # Submit in KM
    with client.session_transaction() as sess:
        sess["lang"] = "km"
    res_km = client.post("/advisors/", data=data)
    assert res_km.status_code == 200
    html_km = res_km.data.decode("utf-8")

    # Exact same calculations:
    # savings potential: (5000 - 1500) / 5000 = 70.0%
    # expense load: 1500 / 5000 = 30.0%
    assert "70.0%" in html_en and "70.0%" in html_km
    assert "30.0%" in html_en and "30.0%" in html_km


# ==============================================================================
# 5. Security Scoping & Authorization
# ==============================================================================

def test_unauthenticated_access_denied(client):
    res_adv = client.get("/advisors/")
    assert res_adv.status_code == 302
    assert "/auth/login" in res_adv.headers.get("Location", "")

    res_hist = client.get("/histories/")
    assert res_hist.status_code == 302
    assert "/auth/login" in res_hist.headers.get("Location", "")


def test_cross_user_history_isolation(app, client):
    """User B cannot view or delete User A's advisory history record."""
    user_a_id = create_and_login_user(app, client, username="user_a", email="user_a@example.com")
    hist_a_id = create_sample_history(app, user_a_id)

    # Login as User B
    client_b = app.test_client()
    user_b_id = create_and_login_user(app, client_b, username="user_b", email="user_b@example.com")

    # User B requests User A's history -> 404
    res_b_view = client_b.get(f"/histories/{hist_a_id}")
    assert res_b_view.status_code == 404

    res_b_delete = client_b.get(f"/histories/{hist_a_id}/delete")
    assert res_b_delete.status_code == 404
