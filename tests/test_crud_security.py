import pytest
from datetime import date
from sqlalchemy.pool import StaticPool
from app import create_app
from extension import db
from app.models import User, Role, Plan, Income, Expense, History
from app.security.token import Token
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool,
    }
    WTF_CSRF_ENABLED = False


@pytest.fixture(name="app")
def fixture_app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


def setup_auth_client(app, user_id, raw_token):
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user_id)
        sess["_fresh"] = True
    client.set_cookie(key="access_token", value="test_access_token")
    client.set_cookie(key="refresh_token", value=raw_token)
    return client


def create_user_and_token(username, email):
    role_user = Role.query.filter_by(name="user").first()
    user = User(username=username, email=email, full_name=username.capitalize())
    user.set_password("Pass12345")
    user.roles.append(role_user)
    db.session.add(user)
    db.session.commit()
    raw_token = Token.generate_refresh_token(user)
    return user.id, raw_token


# --------------------------------------------------------------------------
# 1. Plan Ownership & IDOR Protection
# --------------------------------------------------------------------------
def test_plan_crud_ownership_and_idor(app):
    with app.app_context():
        u1_id, tok1 = create_user_and_token("plan_user1", "plan1@test.com")
        u2_id, tok2 = create_user_and_token("plan_user2", "plan2@test.com")

        u1 = db.session.get(User, u1_id)
        plan1 = Plan(
            goal="Buy Laptop",
            in_between=date(2026, 12, 31),
            goal_cost=1500.0,
            description="Tech upgrade",
        )
        plan1.users.append(u1)
        db.session.add(plan1)
        db.session.commit()
        plan1_id = plan1.id

    c1 = setup_auth_client(app, u1_id, tok1)
    c2 = setup_auth_client(app, u2_id, tok2)

    # User 1 accesses their own plan -> 200 OK
    res = c1.get(f"/plans/{plan1_id}")
    assert res.status_code == 200

    # User 2 attempts to View User 1's plan -> 404 Not Found (IDOR prevented)
    res_idor_view = c2.get(f"/plans/{plan1_id}")
    assert res_idor_view.status_code == 404

    # User 2 attempts to Edit User 1's plan -> 404 Not Found
    res_idor_edit = c2.post(f"/plans/{plan1_id}/edit", data={
        "goal": "Hacked Plan",
        "in_between": "2026-12-31",
        "goal_cost": 9999.0,
        "description": "Hacked",
    })
    assert res_idor_edit.status_code == 404

    # User 2 attempts to Delete User 1's plan -> 404 Not Found
    res_idor_del = c2.post(f"/plans/{plan1_id}/delete")
    assert res_idor_del.status_code == 404


# --------------------------------------------------------------------------
# 2. Income Ownership & IDOR Protection
# --------------------------------------------------------------------------
def test_income_crud_ownership_and_idor(app):
    with app.app_context():
        u1_id, tok1 = create_user_and_token("income_user1", "inc1@test.com")
        u2_id, tok2 = create_user_and_token("income_user2", "inc2@test.com")

        u1 = db.session.get(User, u1_id)
        income1 = Income(
            amount=3000.0,
            category="Salary",
            income_date=date(2026, 8, 1),
            description="Monthly salary",
        )
        income1.users.append(u1)
        db.session.add(income1)
        db.session.commit()
        income1_id = income1.id

    c1 = setup_auth_client(app, u1_id, tok1)
    c2 = setup_auth_client(app, u2_id, tok2)

    # User 1 accesses their income -> 200 OK
    res = c1.get(f"/incomes/{income1_id}")
    assert res.status_code == 200

    # User 2 attempts to View User 1's income -> 404 Not Found
    assert c2.get(f"/incomes/{income1_id}").status_code == 404

    # User 2 attempts to Edit User 1's income -> 404 Not Found
    assert c2.post(f"/incomes/{income1_id}/edit", data={
        "amount": 9999.0,
        "category": "Salary",
        "income_date": "2026-08-01",
    }).status_code == 404

    # User 2 attempts to Delete User 1's income -> 404 Not Found
    assert c2.post(f"/incomes/{income1_id}/delete").status_code == 404


# --------------------------------------------------------------------------
# 3. Expense Ownership & IDOR Protection
# --------------------------------------------------------------------------
def test_expense_crud_ownership_and_idor(app):
    with app.app_context():
        u1_id, tok1 = create_user_and_token("expense_user1", "exp1@test.com")
        u2_id, tok2 = create_user_and_token("expense_user2", "exp2@test.com")

        u1 = db.session.get(User, u1_id)
        expense1 = Expense(
            amount=50.0,
            category="Food",
            expense_date=date(2026, 8, 15),
            description="Groceries",
        )
        expense1.users.append(u1)
        db.session.add(expense1)
        db.session.commit()
        exp1_id = expense1.id

    c1 = setup_auth_client(app, u1_id, tok1)
    c2 = setup_auth_client(app, u2_id, tok2)

    # User 1 accesses their expense -> 200 OK
    res = c1.get(f"/expenses/{exp1_id}")
    assert res.status_code == 200

    # User 2 attempts to View User 1's expense -> 404 Not Found
    assert c2.get(f"/expenses/{exp1_id}").status_code == 404

    # User 2 attempts to Edit User 1's expense -> 404 Not Found
    assert c2.post(f"/expenses/{exp1_id}/edit", data={
        "amount": 100.0,
        "category": "Food",
        "expense_date": "2026-08-15",
    }).status_code == 404

    # User 2 attempts to Delete User 1's expense -> 404 Not Found
    assert c2.post(f"/expenses/{exp1_id}/delete").status_code == 404


# --------------------------------------------------------------------------
# 4. History Destructive Action on GET is Rejected (Method Not Allowed 405)
# --------------------------------------------------------------------------
def test_history_delete_all_rejects_get(app):
    with app.app_context():
        u_id, tok = create_user_and_token("hist_user", "hist@test.com")

    client = setup_auth_client(app, u_id, tok)

    # GET /histories/delete_all must return 405 Method Not Allowed (POST only)
    res_get = client.get("/histories/delete_all")
    assert res_get.status_code == 405

    # POST /histories/delete_all succeeds with redirect
    res_post = client.post("/histories/delete_all")
    assert res_post.status_code == 302


# --------------------------------------------------------------------------
# 5. Anonymous Access is Blocked / Redirected
# --------------------------------------------------------------------------
def test_anonymous_access_blocked(app):
    client = app.test_client()
    assert client.get("/plans/").status_code in (302, 401, 403)
    assert client.get("/incomes/").status_code in (302, 401, 403)
    assert client.get("/expenses/").status_code in (302, 401, 403)
    assert client.get("/histories/").status_code in (302, 401, 403)
