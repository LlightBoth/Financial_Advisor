import pytest
import re
from datetime import date
from flask import session
from app import create_app
from app.models import User, Role, Income, Expense
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
    SECRET_KEY = "test-income-expense-secret-key"


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


def create_and_login_user(app, client, username="finance_client", email="finance_client@example.com"):
    """Deterministic, isolated test user creation for controlled test execution."""
    with app.app_context():
        role_user = Role.query.filter_by(name="user").first()
        if not role_user:
            role_user = Role(name="user", description="Regular Client")
            db.session.add(role_user)
            db.session.commit()

        user = User(username=username, email=email, full_name="Finance Client")
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
# 1. Income English & Khmer Rendering
# ==============================================================================

def test_income_index_renders_english(app, client):
    """Verify Income index renders English titles, metrics, and empty state."""
    create_and_login_user(app, client)

    with client.session_transaction() as sess:
        sess["lang"] = "en"

    response = client.get("/incomes/")
    assert response.status_code == 200
    html = response.data.decode("utf-8")

    assert 'lang="en"' in html
    assert "Income Streams" in html
    assert "Total Earned" in html
    assert "Transaction Logs" in html
    assert "Recurring Streams" in html
    assert "Add Income" in html
    assert "No Income Records Yet" in html
    assert "Add First Income" in html
    assert "{{ _(" not in html


def test_income_index_renders_khmer(app, client):
    """Verify Income index renders Khmer titles, metrics, and empty state."""
    create_and_login_user(app, client)

    with client.session_transaction() as sess:
        sess["lang"] = "km"

    response = client.get("/incomes/")
    assert response.status_code == 200
    html = response.data.decode("utf-8")

    assert 'lang="km"' in html
    assert "ប្រភពចំណូល" in html
    assert "ចំណូលសរុបដែលរកបាន" in html
    assert "កំណត់ត្រាប្រតិបត្តិការ" in html
    assert "ចំណូលកើតឡើងដដែលៗ" in html
    assert "បន្ថែមចំណូល" in html
    assert "មិនទាន់មានកំណត់ត្រាចំណូលនៅឡើយទេ" in html
    assert "បន្ថែមចំណូលដំបូង" in html
    assert "{{ _(" not in html


def test_income_table_and_detail_localization(app, client):
    """Verify Income table headers, categories, badges, and detail views in both languages."""
    user_id = create_and_login_user(app, client)

    with app.app_context():
        user = db.session.get(User, user_id)
        inc = Income(
            amount=2500.0,
            category="Salary",
            description="Monthly Base Salary",
            income_date=date(2026, 9, 1),
            recurring_period="Monthly"
        )
        inc.users.append(user)
        db.session.add(inc)
        db.session.commit()
        income_id = inc.id

    # English Table & Detail
    with client.session_transaction() as sess:
        sess["lang"] = "en"

    res_en = client.get("/incomes/")
    assert res_en.status_code == 200
    html_en = res_en.data.decode("utf-8")
    assert "Date" in html_en
    assert "Category" in html_en
    assert "Description" in html_en
    assert "Frequency" in html_en
    assert "Amount" in html_en
    assert "Salary" in html_en
    assert "Monthly" in html_en
    assert "+$2500.00" in html_en

    res_detail_en = client.get(f"/incomes/{income_id}")
    assert res_detail_en.status_code == 200
    html_detail_en = res_detail_en.data.decode("utf-8")
    assert "Income Overview" in html_detail_en
    assert "Total Amount" in html_detail_en
    assert "$2500.00" in html_detail_en

    # Khmer Table & Detail
    with client.session_transaction() as sess:
        sess["lang"] = "km"

    res_km = client.get("/incomes/")
    assert res_km.status_code == 200
    html_km = res_km.data.decode("utf-8")
    assert "កាលបរិច្ឆេទ" in html_km
    assert "ប្រភេទ" in html_km
    assert "ការពិពណ៌នា" in html_km
    assert "ភាពញឹកញាប់" in html_km
    assert "ចំនួនទឹកប្រាក់" in html_km
    assert "ប្រាក់បៀវត្សរ៍" in html_km
    assert "ប្រចាំខែ" in html_km
    assert "+$2500.00" in html_km

    res_detail_km = client.get(f"/incomes/{income_id}")
    assert res_detail_km.status_code == 200
    html_detail_km = res_detail_km.data.decode("utf-8")
    assert "ទិដ្ឋភាពទូទៅនៃចំណូល" in html_detail_km
    assert "ចំនួនទឹកប្រាក់សរុប" in html_detail_km
    assert "$2500.00" in html_detail_km


# ==============================================================================
# 2. Expense English & Khmer Rendering
# ==============================================================================

def test_expense_index_renders_english(app, client):
    """Verify Expense index renders English titles, metrics, and empty state."""
    create_and_login_user(app, client)

    with client.session_transaction() as sess:
        sess["lang"] = "en"

    response = client.get("/expenses/")
    assert response.status_code == 200
    html = response.data.decode("utf-8")

    assert 'lang="en"' in html
    assert "Expense Tracking" in html
    assert "Total Outlay" in html
    assert "Expense Records" in html
    assert "Recurring Fixed Costs" in html
    assert "Add Expense" in html
    assert "No Expense Records Yet" in html
    assert "Add First Expense" in html
    assert "{{ _(" not in html


def test_expense_index_renders_khmer(app, client):
    """Verify Expense index renders Khmer titles, metrics, and empty state."""
    create_and_login_user(app, client)

    with client.session_transaction() as sess:
        sess["lang"] = "km"

    response = client.get("/expenses/")
    assert response.status_code == 200
    html = response.data.decode("utf-8")

    assert 'lang="km"' in html
    assert "ការតាមដានចំណាយ" in html
    assert "ការចំណាយសរុប" in html
    assert "កំណត់ត្រាចំណាយ" in html
    assert "ចំណាយថេរកើតឡើងដដែលៗ" in html
    assert "បន្ថែមចំណាយ" in html
    assert "មិនទាន់មានកំណត់ត្រាចំណាយនៅឡើយទេ" in html
    assert "បន្ថែមចំណាយដំបូង" in html
    assert "{{ _(" not in html


def test_expense_table_and_detail_localization(app, client):
    """Verify Expense table headers, categories, badges, and detail views in both languages."""
    user_id = create_and_login_user(app, client)

    with app.app_context():
        user = db.session.get(User, user_id)
        exp = Expense(
            amount=350.0,
            category="Food",
            description="Grocery Shopping",
            expense_date=date(2026, 9, 2),
            recurring_period="Weekly"
        )
        exp.users.append(user)
        db.session.add(exp)
        db.session.commit()
        expense_id = exp.id

    # English Table & Detail
    with client.session_transaction() as sess:
        sess["lang"] = "en"

    res_en = client.get("/expenses/")
    assert res_en.status_code == 200
    html_en = res_en.data.decode("utf-8")
    assert "Date" in html_en
    assert "Category" in html_en
    assert "Food" in html_en
    assert "Weekly" in html_en
    assert "-$350.00" in html_en

    res_detail_en = client.get(f"/expenses/{expense_id}")
    assert res_detail_en.status_code == 200
    html_detail_en = res_detail_en.data.decode("utf-8")
    assert "Expense Overview" in html_detail_en
    assert "Total Amount" in html_detail_en
    assert "$350.00" in html_detail_en

    # Khmer Table & Detail
    with client.session_transaction() as sess:
        sess["lang"] = "km"

    res_km = client.get("/expenses/")
    assert res_km.status_code == 200
    html_km = res_km.data.decode("utf-8")
    assert "កាលបរិច្ឆេទ" in html_km
    assert "ប្រភេទ" in html_km
    assert "អាហារ" in html_km
    assert "ប្រចាំសប្តាហ៍" in html_km
    assert "-$350.00" in html_km

    res_detail_km = client.get(f"/expenses/{expense_id}")
    assert res_detail_km.status_code == 200
    html_detail_km = res_detail_km.data.decode("utf-8")
    assert "ទិដ្ឋភាពទូទៅនៃចំណាយ" in html_detail_km
    assert "ចំនួនទឹកប្រាក់សរុប" in html_detail_km
    assert "$350.00" in html_detail_km


# ==============================================================================
# 3. Financial Data Preservation Across Languages
# ==============================================================================

def test_financial_amounts_identical_in_en_and_km(app, client):
    """Ensure exact numeric values ($2,500.00, $1,200.00) are unchanged in both languages."""
    user_id = create_and_login_user(app, client)

    with app.app_context():
        user = db.session.get(User, user_id)
        inc = Income(
            amount=2500.50,
            category="Salary",
            description="Salary",
            income_date=date.today()
        )
        exp = Expense(
            amount=1200.75,
            category="Housing",
            description="Rent",
            expense_date=date.today()
        )
        inc.users.append(user)
        exp.users.append(user)
        db.session.add_all([inc, exp])
        db.session.commit()

    # Compare Income Index
    with client.session_transaction() as sess:
        sess["lang"] = "en"
    html_inc_en = client.get("/incomes/").data.decode("utf-8")

    with client.session_transaction() as sess:
        sess["lang"] = "km"
    html_inc_km = client.get("/incomes/").data.decode("utf-8")

    assert "$2500.50" in html_inc_en
    assert "$2500.50" in html_inc_km

    # Compare Expense Index
    with client.session_transaction() as sess:
        sess["lang"] = "en"
    html_exp_en = client.get("/expenses/").data.decode("utf-8")

    with client.session_transaction() as sess:
        sess["lang"] = "km"
    html_exp_km = client.get("/expenses/").data.decode("utf-8")

    assert "$1200.75" in html_exp_en
    assert "$1200.75" in html_exp_km


# ==============================================================================
# 4. Form Validation Localization
# ==============================================================================

def test_income_validation_messages_en_and_km(app, client):
    """Verify form validation errors are localized for Income in both EN and KM."""
    create_and_login_user(app, client)

    # 1. English validation errors
    with client.session_transaction() as sess:
        sess["lang"] = "en"

    res_en = client.post("/incomes/create", data={"amount": "", "income_date": ""})
    assert res_en.status_code == 200
    html_en = res_en.data.decode("utf-8")
    assert "This field is required." in html_en

    # Positive number validator
    res_pos_en = client.post("/incomes/create", data={"amount": "-10", "income_date": "2026-09-01", "category": "Salary"})
    assert res_pos_en.status_code == 200
    assert "Amount must be greater than 0." in res_pos_en.data.decode("utf-8")

    # 2. Khmer validation errors
    with client.session_transaction() as sess:
        sess["lang"] = "km"

    res_km = client.post("/incomes/create", data={"amount": "", "income_date": ""})
    assert res_km.status_code == 200
    html_km = res_km.data.decode("utf-8")
    assert "សូមបំពេញប្រអប់នេះ។" in html_km

    res_pos_km = client.post("/incomes/create", data={"amount": "-10", "income_date": "2026-09-01", "category": "Salary"})
    assert res_pos_km.status_code == 200
    assert "ចំនួនទឹកប្រាក់ត្រូវតែធំជាង ០។" in res_pos_km.data.decode("utf-8")


def test_expense_validation_messages_en_and_km(app, client):
    """Verify form validation errors are localized for Expense in both EN and KM."""
    create_and_login_user(app, client)

    # 1. English validation errors
    with client.session_transaction() as sess:
        sess["lang"] = "en"

    res_en = client.post("/expenses/create", data={"amount": "", "expense_date": ""})
    assert res_en.status_code == 200
    html_en = res_en.data.decode("utf-8")
    assert "This field is required." in html_en

    res_pos_en = client.post("/expenses/create", data={"amount": "-5", "expense_date": "2026-09-01", "category": "Food"})
    assert res_pos_en.status_code == 200
    assert "Amount must be greater than 0." in res_pos_en.data.decode("utf-8")

    # 2. Khmer validation errors
    with client.session_transaction() as sess:
        sess["lang"] = "km"

    res_km = client.post("/expenses/create", data={"amount": "", "expense_date": ""})
    assert res_km.status_code == 200
    html_km = res_km.data.decode("utf-8")
    assert "សូមបំពេញប្រអប់នេះ។" in html_km

    res_pos_km = client.post("/expenses/create", data={"amount": "-5", "expense_date": "2026-09-01", "category": "Food"})
    assert res_pos_km.status_code == 200
    assert "ចំនួនទឹកប្រាក់ត្រូវតែធំជាង ០។" in res_pos_km.data.decode("utf-8")


# ==============================================================================
# 5. Flash Message Localization & CRUD Regression
# ==============================================================================

def test_income_crud_and_flash_messages_en_and_km(app, client):
    """Verify Create, Read, Update, Delete for Income with localized flash messages."""
    user_id = create_and_login_user(app, client)

    # 1. Create Income in English
    with client.session_transaction() as sess:
        sess["lang"] = "en"

    create_res_en = client.post(
        "/incomes/create",
        data={
            "amount": "1800.00",
            "category": "Salary",
            "description": "Consulting Income",
            "income_date": "2026-09-10",
            "recurring_period": "Monthly"
        },
        follow_redirects=True
    )
    assert create_res_en.status_code == 200
    assert "Income &#39;$1800.00&#39; created successfully!" in create_res_en.data.decode("utf-8") or "Income '$1800.00' created successfully!" in create_res_en.data.decode("utf-8")

    # Find created income ID
    with app.app_context():
        inc = Income.query.filter_by(description="Consulting Income").first()
        assert inc is not None
        assert inc.amount == 1800.0
        income_id = inc.id

    # 2. Update Income in Khmer
    with client.session_transaction() as sess:
        sess["lang"] = "km"

    update_res_km = client.post(
        f"/incomes/{income_id}/edit",
        data={
            "amount": "2000.00",
            "category": "Salary",
            "description": "Consulting Income Updated",
            "income_date": "2026-09-10",
            "recurring_period": "Monthly"
        },
        follow_redirects=True
    )
    assert update_res_km.status_code == 200
    html_updated = update_res_km.data.decode("utf-8")
    assert "ចំណូល &#39;$2000.00&#39; ត្រូវបានធ្វើបច្ចុប្បន្នភាពដោយជោគជ័យ!" in html_updated or "ចំណូល '$2000.00' ត្រូវបានធ្វើបច្ចុប្បន្នភាពដោយជោគជ័យ!" in html_updated

    with app.app_context():
        inc_updated = db.session.get(Income, income_id)
        assert inc_updated.amount == 2000.0

    # 3. Delete Income in Khmer
    del_res_km = client.post(f"/incomes/{income_id}/delete", follow_redirects=True)
    assert del_res_km.status_code == 200
    assert "ចំណូលត្រូវបានលុបដោយជោគជ័យ!" in del_res_km.data.decode("utf-8")

    with app.app_context():
        assert db.session.get(Income, income_id) is None


def test_expense_crud_and_flash_messages_en_and_km(app, client):
    """Verify Create, Read, Update, Delete for Expense with localized flash messages."""
    user_id = create_and_login_user(app, client)

    # 1. Create Expense in Khmer
    with client.session_transaction() as sess:
        sess["lang"] = "km"

    create_res_km = client.post(
        "/expenses/create",
        data={
            "amount": "85.50",
            "category": "Food",
            "description": "Lunch with client",
            "expense_date": "2026-09-15",
            "recurring_period": ""
        },
        follow_redirects=True
    )
    assert create_res_km.status_code == 200
    html_km = create_res_km.data.decode("utf-8")
    assert "ចំណាយ &#39;$85.50&#39; ត្រូវបានបង្កើតដោយជោគជ័យ!" in html_km or "ចំណាយ '$85.50' ត្រូវបានបង្កើតដោយជោគជ័យ!" in html_km

    with app.app_context():
        exp = Expense.query.filter_by(description="Lunch with client").first()
        assert exp is not None
        assert exp.amount == 85.5
        expense_id = exp.id

    # 2. Update Expense in English
    with client.session_transaction() as sess:
        sess["lang"] = "en"

    update_res_en = client.post(
        f"/expenses/{expense_id}/edit",
        data={
            "amount": "95.00",
            "category": "Food",
            "description": "Lunch with client and team",
            "expense_date": "2026-09-15",
            "recurring_period": ""
        },
        follow_redirects=True
    )
    assert update_res_en.status_code == 200
    html_en = update_res_en.data.decode("utf-8")
    assert "Expense &#39;$95.00&#39; updated successfully!" in html_en or "Expense '$95.00' updated successfully!" in html_en

    # 3. Delete Confirmation Page renders properly in English and Khmer
    del_confirm_en = client.get(f"/expenses/{expense_id}/delete")
    assert del_confirm_en.status_code == 200
    assert "Confirm Delete" in del_confirm_en.data.decode("utf-8")

    with client.session_transaction() as sess:
        sess["lang"] = "km"
    del_confirm_km = client.get(f"/expenses/{expense_id}/delete")
    assert del_confirm_km.status_code == 200
    assert "បញ្ជាក់ការលុប" in del_confirm_km.data.decode("utf-8")

    # 4. Delete Expense in English
    with client.session_transaction() as sess:
        sess["lang"] = "en"

    del_res_en = client.post(f"/expenses/{expense_id}/delete", follow_redirects=True)
    assert del_res_en.status_code == 200
    assert "Expense deleted successfully!" in del_res_en.data.decode("utf-8")

    with app.app_context():
        assert db.session.get(Expense, expense_id) is None
