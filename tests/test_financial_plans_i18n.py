import pytest
from datetime import date
from app import create_app
from app.models import User, Role, Plan
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
    SECRET_KEY = "test-financial-plans-secret-key"


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


def create_and_login_user(app, client, username="plan_tester", email="plan_tester@example.com"):
    """Deterministic, isolated test user creation for controlled test execution."""
    with app.app_context():
        role_user = Role.query.filter_by(name="user").first()
        if not role_user:
            role_user = Role(name="user", description="Regular Client")
            db.session.add(role_user)
            db.session.commit()

        user = User(username=username, email=email, full_name="Plan Tester")
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


# ==============================================================================
# 1. English Rendering Tests
# ==============================================================================

def test_plans_index_renders_english(app, client):
    """Verify Plan list renders in English with proper title, labels, and empty state."""
    create_and_login_user(app, client)

    with client.session_transaction() as sess:
        sess["lang"] = "en"

    response = client.get("/plans/")
    assert response.status_code == 200
    html = response.data.decode("utf-8")

    assert 'lang="en"' in html
    assert "Savings Milestones &amp; Plans" in html or "Savings Milestones & Plans" in html
    assert "Track and project your long-term wealth targets." in html
    assert "Create New Plan" in html
    assert "No Plans Active" in html
    assert "Get Started" in html
    assert "{{ _(" not in html


def test_plans_create_renders_english(app, client):
    """Verify Plan create page renders in English."""
    create_and_login_user(app, client)

    with client.session_transaction() as sess:
        sess["lang"] = "en"

    response = client.get("/plans/create")
    assert response.status_code == 200
    html = response.data.decode("utf-8")

    assert 'lang="en"' in html
    assert "Create Your Strategy" in html
    assert "Strategy Framework" in html
    assert "Enter the core details of your financial goal" in html
    assert "Real-time Tracking" in html
    assert "Secure Data" in html
    assert "Flexible Edits" in html
    assert "Save Plan" in html
    assert "{{ _(" not in html


def test_plans_edit_renders_english(app, client):
    """Verify Plan edit page renders in English."""
    user_id = create_and_login_user(app, client)

    with app.app_context():
        user = db.session.get(User, user_id)
        plan = Plan(
            goal="Retirement Fund",
            in_between=date(2035, 12, 31),
            goal_cost=50000.0,
            description="Long-term nest egg",
            value=False
        )
        plan.users.append(user)
        db.session.add(plan)
        db.session.commit()
        plan_id = plan.id

    with client.session_transaction() as sess:
        sess["lang"] = "en"

    response = client.get(f"/plans/{plan_id}/edit")
    assert response.status_code == 200
    html = response.data.decode("utf-8")

    assert 'lang="en"' in html
    assert "Update Your Strategy" in html
    assert "Strategy Framework" in html
    assert "Retirement Fund" in html
    assert "Save Plan" in html
    assert "{{ _(" not in html


def test_plans_detail_renders_english(app, client):
    """Verify Plan detail page renders in English."""
    user_id = create_and_login_user(app, client)

    with app.app_context():
        user = db.session.get(User, user_id)
        plan = Plan(
            goal="Emergency Fund",
            in_between=date(2028, 6, 30),
            goal_cost=10000.0,
            description="Six months of living expenses",
            value=True
        )
        plan.users.append(user)
        db.session.add(plan)
        db.session.commit()
        plan_id = plan.id

    with client.session_transaction() as sess:
        sess["lang"] = "en"

    response = client.get(f"/plans/{plan_id}")
    assert response.status_code == 200
    html = response.data.decode("utf-8")

    assert 'lang="en"' in html
    assert "Plan Overview" in html
    assert "Record ID:" in html
    assert "Completed" in html
    assert "Goal Cost" in html
    assert "$10000.00" in html
    assert "Goal" in html
    assert "Emergency Fund" in html
    assert "In-Between Steps / Details" in html
    assert "Created:" in html
    assert "Last updated:" in html
    assert "{{ _(" not in html


def test_plans_delete_confirm_renders_english(app, client):
    """Verify Plan delete confirmation renders in English."""
    user_id = create_and_login_user(app, client)

    with app.app_context():
        user = db.session.get(User, user_id)
        plan = Plan(
            goal="Car Purchase",
            in_between=date(2027, 1, 1),
            goal_cost=15000.0,
            description="Electric vehicle down payment",
            value=False
        )
        plan.users.append(user)
        db.session.add(plan)
        db.session.commit()
        plan_id = plan.id

    with client.session_transaction() as sess:
        sess["lang"] = "en"

    response = client.get(f"/plans/{plan_id}/delete")
    assert response.status_code == 200
    html = response.data.decode("utf-8")

    assert 'lang="en"' in html
    assert "Confirm Delete" in html
    assert "Are you sure you want to delete this Plan?" in html
    assert "Cancel" in html
    assert "{{ _(" not in html


# ==============================================================================
# 2. Khmer Rendering Tests
# ==============================================================================

def test_plans_index_renders_khmer(app, client):
    """Verify Plan list renders in Khmer with proper titles, labels, and empty state."""
    create_and_login_user(app, client)

    with client.session_transaction() as sess:
        sess["lang"] = "km"

    response = client.get("/plans/")
    assert response.status_code == 200
    html = response.data.decode("utf-8")

    assert 'lang="km"' in html
    assert "គោលដៅសន្សំ និងផែនការ" in html
    assert "តាមដាន និងព្យាករណ៍គោលដៅទ្រព្យសម្បត្តិរយៈពេលវែងរបស់អ្នក។" in html
    assert "បង្កើតផែនការថ្មី" in html
    assert "មិនមានផែនការសកម្មទេ" in html
    assert "ចាប់ផ្តើម" in html
    assert "{{ _(" not in html


def test_plans_create_renders_khmer(app, client):
    """Verify Plan create page renders in Khmer."""
    create_and_login_user(app, client)

    with client.session_transaction() as sess:
        sess["lang"] = "km"

    response = client.get("/plans/create")
    assert response.status_code == 200
    html = response.data.decode("utf-8")

    assert 'lang="km"' in html
    assert "បង្កើតយុទ្ធសាស្ត្ររបស់អ្នក" in html
    assert "ក្របខ័ណ្ឌយុទ្ធសាស្ត្រ" in html
    assert "បញ្ចូលព័ត៌មានលម្អិតស្នូលនៃគោលដៅហិរញ្ញវត្ថុរបស់អ្នក" in html
    assert "ការតាមដានពេលវេលាជាក់ស្តែង" in html
    assert "ទិន្នន័យមានសុវត្ថិភាព" in html
    assert "ការកែសម្រួលដោយបត់បែន" in html
    assert "រក្សាទុកផែនការ" in html
    assert "{{ _(" not in html


def test_plans_edit_renders_khmer(app, client):
    """Verify Plan edit page renders in Khmer."""
    user_id = create_and_login_user(app, client)

    with app.app_context():
        user = db.session.get(User, user_id)
        plan = Plan(
            goal="ផ្ទះថ្មី",
            in_between=date(2030, 5, 1),
            goal_cost=80000.0,
            description="ទិញផ្ទះ",
            value=False
        )
        plan.users.append(user)
        db.session.add(plan)
        db.session.commit()
        plan_id = plan.id

    with client.session_transaction() as sess:
        sess["lang"] = "km"

    response = client.get(f"/plans/{plan_id}/edit")
    assert response.status_code == 200
    html = response.data.decode("utf-8")

    assert 'lang="km"' in html
    assert "ធ្វើបច្ចុប្បន្នភាពយុទ្ធសាស្ត្ររបស់អ្នក" in html
    assert "ក្របខ័ណ្ឌយុទ្ធសាស្ត្រ" in html
    assert "រក្សាទុកផែនការ" in html
    assert "{{ _(" not in html


def test_plans_detail_renders_khmer(app, client):
    """Verify Plan detail page renders in Khmer."""
    user_id = create_and_login_user(app, client)

    with app.app_context():
        user = db.session.get(User, user_id)
        plan = Plan(
            goal="ទិញរថយន្ត",
            in_between=date(2027, 8, 15),
            goal_cost=25000.0,
            description="រថយន្តគ្រួសារ",
            value=True
        )
        plan.users.append(user)
        db.session.add(plan)
        db.session.commit()
        plan_id = plan.id

    with client.session_transaction() as sess:
        sess["lang"] = "km"

    response = client.get(f"/plans/{plan_id}")
    assert response.status_code == 200
    html = response.data.decode("utf-8")

    assert 'lang="km"' in html
    assert "ទិដ្ឋភាពទូទៅនៃផែនការ" in html
    assert "លេខសម្គាល់កំណត់ត្រា" in html
    assert "បានបញ្ចប់" in html
    assert "ការចំណាយលើគោលដៅ" in html
    assert "$25000.00" in html
    assert "គោលដៅ" in html
    assert "ជំហានពាក់កណ្តាល / ព័ត៌មានលម្អិត" in html
    assert "បានបង្កើត" in html
    assert "បានធ្វើបច្ចុប្បន្នភាពចុងក្រោយ" in html
    assert "{{ _(" not in html


def test_plans_delete_confirm_renders_khmer(app, client):
    """Verify Plan delete confirmation renders in Khmer."""
    user_id = create_and_login_user(app, client)

    with app.app_context():
        user = db.session.get(User, user_id)
        plan = Plan(
            goal="ដំណើរកម្សាន្ត",
            in_between=date(2026, 11, 20),
            goal_cost=3000.0,
            description="ដំណើរកម្សាន្តទៅជប៉ុន",
            value=False
        )
        plan.users.append(user)
        db.session.add(plan)
        db.session.commit()
        plan_id = plan.id

    with client.session_transaction() as sess:
        sess["lang"] = "km"

    response = client.get(f"/plans/{plan_id}/delete")
    assert response.status_code == 200
    html = response.data.decode("utf-8")

    assert 'lang="km"' in html
    assert "បញ្ជាក់ការលុប" in html
    assert "តើអ្នកប្រាកដជាចង់លុបផែនការនេះមែនទេ?" in html
    assert "បោះបង់" in html
    assert "{{ _(" not in html


# ==============================================================================
# 3. Language Switching Tests
# ==============================================================================

def test_language_switching_on_plans(app, client):
    """Verify switching between English and Khmer retains route and updates content."""
    user_id = create_and_login_user(app, client)

    with app.app_context():
        user = db.session.get(User, user_id)
        plan = Plan(
            goal="College Fund",
            in_between=date(2032, 9, 1),
            goal_cost=40000.0,
            description="University savings",
            value=True
        )
        plan.users.append(user)
        db.session.add(plan)
        db.session.commit()
        plan_id = plan.id

    # Switch to Khmer
    switch_res = client.get("/set-language/km", headers={"Referer": "/plans/"}, follow_redirects=True)
    assert switch_res.status_code == 200
    html_km = switch_res.data.decode("utf-8")
    assert 'lang="km"' in html_km
    assert "គោលដៅសន្សំ និងផែនការ" in html_km
    assert "ថវិកាគោលដៅ" in html_km

    # Switch back to English
    switch_en_res = client.get("/set-language/en", headers={"Referer": "/plans/"}, follow_redirects=True)
    assert switch_en_res.status_code == 200
    html_en = switch_en_res.data.decode("utf-8")
    assert 'lang="en"' in html_en
    assert "Savings Milestones &amp; Plans" in html_en or "Savings Milestones & Plans" in html_en
    assert "Target Budget" in html_en


# ==============================================================================
# 4. Financial Value & Status Preservation Tests
# ==============================================================================

def test_financial_value_preservation(app, client):
    """Verify numerical goal cost and dates are identical across languages."""
    user_id = create_and_login_user(app, client)

    with app.app_context():
        user = db.session.get(User, user_id)
        plan = Plan(
            goal="Home Expansion",
            in_between=date(2029, 4, 15),
            goal_cost=18500.50,
            description="Add second floor bedroom",
            value=False
        )
        plan.users.append(user)
        db.session.add(plan)
        db.session.commit()
        plan_id = plan.id

    # View in English
    with client.session_transaction() as sess:
        sess["lang"] = "en"
    res_en = client.get(f"/plans/{plan_id}")
    html_en = res_en.data.decode("utf-8")
    assert "$18500.50" in html_en
    assert "2029-04-15" in html_en or "Apr 15, 2029" in html_en

    # View in Khmer
    with client.session_transaction() as sess:
        sess["lang"] = "km"
    res_km = client.get(f"/plans/{plan_id}")
    html_km = res_km.data.decode("utf-8")
    assert "$18500.50" in html_km
    assert "2029-04-15" in html_km or "Apr 15, 2029" in html_km


def test_status_display_localization_and_db_preservation(app, client):
    """Verify internal plan.value (boolean) is preserved while display text translates."""
    user_id = create_and_login_user(app, client)

    with app.app_context():
        user = db.session.get(User, user_id)
        completed_plan = Plan(
            goal="Emergency Fund",
            in_between=date(2025, 12, 31),
            goal_cost=5000.0,
            description="Safety net",
            value=True
        )
        completed_plan.users.append(user)

        incompleted_plan = Plan(
            goal="New Laptop",
            in_between=date(2026, 6, 30),
            goal_cost=2000.0,
            description="Upgrade computer",
            value=False
        )
        incompleted_plan.users.append(user)

        db.session.add_all([completed_plan, incompleted_plan])
        db.session.commit()
        p1_id, p2_id = completed_plan.id, incompleted_plan.id

    # English check
    with client.session_transaction() as sess:
        sess["lang"] = "en"
    en_p1 = client.get(f"/plans/{p1_id}").data.decode("utf-8")
    en_p2 = client.get(f"/plans/{p2_id}").data.decode("utf-8")
    assert "Completed" in en_p1
    assert "Incompleted" in en_p2

    # Khmer check
    with client.session_transaction() as sess:
        sess["lang"] = "km"
    km_p1 = client.get(f"/plans/{p1_id}").data.decode("utf-8")
    km_p2 = client.get(f"/plans/{p2_id}").data.decode("utf-8")
    assert "បានបញ្ចប់" in km_p1
    assert "មិនទាន់បញ្ចប់" in km_p2

    # Verify DB values are still pristine booleans
    with app.app_context():
        p1_db = db.session.get(Plan, p1_id)
        p2_db = db.session.get(Plan, p2_id)
        assert p1_db.value is True
        assert p2_db.value is False


# ==============================================================================
# 5. Form Validation Tests
# ==============================================================================

def test_plan_validation_english(app, client):
    """Verify validation messages in English for missing required fields and negative budget."""
    create_and_login_user(app, client)

    with client.session_transaction() as sess:
        sess["lang"] = "en"

    # Post invalid data: negative cost and missing goal
    response = client.post("/plans/create", data={
        "goal": "",
        "in_between": "2028-01-01",
        "goal_cost": "-100",
        "description": "Invalid plan",
        "value": "y"
    })
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "This field is required." in html
    assert "Estimated budget must be greater than 0." in html


def test_plan_validation_khmer(app, client):
    """Verify validation messages in Khmer for missing required fields and negative budget."""
    create_and_login_user(app, client)

    with client.session_transaction() as sess:
        sess["lang"] = "km"

    # Post invalid data: negative cost and missing goal
    response = client.post("/plans/create", data={
        "goal": "",
        "in_between": "2028-01-01",
        "goal_cost": "-100",
        "description": "Invalid plan",
        "value": "y"
    })
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "សូមបំពេញប្រអប់នេះ។" in html
    assert "ថវិកាប៉ាន់ស្មានត្រូវតែធំជាង ០។" in html


# ==============================================================================
# 6. Flash Messages & Full CRUD Regression
# ==============================================================================

def test_plan_crud_english(app, client):
    """Verify full CRUD lifecycle and flash messages in English."""
    user_id = create_and_login_user(app, client)

    with client.session_transaction() as sess:
        sess["lang"] = "en"

    # 1. CREATE
    create_res = client.post("/plans/create", data={
        "goal": "Wedding Fund",
        "in_between": "2027-10-15",
        "goal_cost": "12000.00",
        "description": "Ceremony and reception",
        "value": "y"
    }, follow_redirects=True)
    assert create_res.status_code == 200
    create_html = create_res.data.decode("utf-8")
    assert "Plan &#39;Wedding Fund&#39; created successfully!" in create_html or "Plan 'Wedding Fund' created successfully!" in create_html

    # Verify created in DB
    with app.app_context():
        plan = Plan.query.filter(Plan.goal == "Wedding Fund", Plan.users.any(id=user_id)).first()
        assert plan is not None
        assert plan.goal_cost == 12000.00
        assert plan.value is True
        plan_id = plan.id

    # 2. READ
    read_res = client.get(f"/plans/{plan_id}")
    assert read_res.status_code == 200
    assert "Wedding Fund" in read_res.data.decode("utf-8")

    # 3. UPDATE
    update_res = client.post(f"/plans/{plan_id}/edit", data={
        "goal": "Grand Wedding Fund",
        "in_between": "2027-11-20",
        "goal_cost": "15000.00",
        "description": "Upgraded venue",
        "value": "y"
    }, follow_redirects=True)
    assert update_res.status_code == 200
    update_html = update_res.data.decode("utf-8")
    assert "Plan &#39;Grand Wedding Fund&#39; updated successfully!" in update_html or "Plan 'Grand Wedding Fund' updated successfully!" in update_html

    with app.app_context():
        plan = db.session.get(Plan, plan_id)
        assert plan.goal == "Grand Wedding Fund"
        assert plan.goal_cost == 15000.00

    # 4. DELETE
    delete_res = client.post(f"/plans/{plan_id}/delete", data={}, follow_redirects=True)
    assert delete_res.status_code == 200
    delete_html = delete_res.data.decode("utf-8")
    assert "Plan deleted successfully!" in delete_html

    with app.app_context():
        deleted = db.session.get(Plan, plan_id)
        assert deleted is None


def test_plan_crud_khmer(app, client):
    """Verify full CRUD lifecycle and flash messages in Khmer."""
    user_id = create_and_login_user(app, client)

    with client.session_transaction() as sess:
        sess["lang"] = "km"

    # 1. CREATE
    create_res = client.post("/plans/create", data={
        "goal": "មូលនិធិអាពាហ៍ពិពាហ៍",
        "in_between": "2027-10-15",
        "goal_cost": "12000.00",
        "description": "ការរៀបចំពិធីមង្គលការ",
        "value": "y"
    }, follow_redirects=True)
    assert create_res.status_code == 200
    create_html = create_res.data.decode("utf-8")
    assert "ផែនការ &#39;មូលនិធិអាពាហ៍ពិពាហ៍&#39; ត្រូវបានបង្កើតដោយជោគជ័យ!" in create_html or "ផែនការ 'មូលនិធិអាពាហ៍ពិពាហ៍' ត្រូវបានបង្កើតដោយជោគជ័យ!" in create_html

    # Verify created in DB
    with app.app_context():
        plan = Plan.query.filter(Plan.goal == "មូលនិធិអាពាហ៍ពិពាហ៍", Plan.users.any(id=user_id)).first()
        assert plan is not None
        assert plan.goal_cost == 12000.00
        plan_id = plan.id

    # 2. READ
    read_res = client.get(f"/plans/{plan_id}")
    assert read_res.status_code == 200
    assert "មូលនិធិអាពាហ៍ពិពាហ៍" in read_res.data.decode("utf-8")

    # 3. UPDATE
    update_res = client.post(f"/plans/{plan_id}/edit", data={
        "goal": "មូលនិធិអាពាហ៍ពិពាហ៍ធំ",
        "in_between": "2027-11-20",
        "goal_cost": "16000.00",
        "description": "ទីតាំងធំទូលាយជាងមុន",
        "value": "y"
    }, follow_redirects=True)
    assert update_res.status_code == 200
    update_html = update_res.data.decode("utf-8")
    assert "ផែនការ &#39;មូលនិធិអាពាហ៍ពិពាហ៍ធំ&#39; ត្រូវបានធ្វើបច្ចុប្បន្នភាពដោយជោគជ័យ!" in update_html or "ផែនការ 'មូលនិធិអាពាហ៍ពិពាហ៍ធំ' ត្រូវបានធ្វើបច្ចុប្បន្នភាពដោយជោគជ័យ!" in update_html

    with app.app_context():
        plan = db.session.get(Plan, plan_id)
        assert plan.goal == "មូលនិធិអាពាហ៍ពិពាហ៍ធំ"
        assert plan.goal_cost == 16000.00

    # 4. DELETE
    delete_res = client.post(f"/plans/{plan_id}/delete", data={}, follow_redirects=True)
    assert delete_res.status_code == 200
    delete_html = delete_res.data.decode("utf-8")
    assert "ផែនការត្រូវបានលុបដោយជោគជ័យ!" in delete_html

    with app.app_context():
        deleted = db.session.get(Plan, plan_id)
        assert deleted is None
