import pytest
from sqlalchemy.pool import StaticPool
from app import create_app
from extension import db
from app.models import User, Role, Permission, Plan
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


def create_user_with_role(username, email, role_name):
    role = Role.query.filter_by(name=role_name).first()
    if not role:
        role = Role(name=role_name, descriptions=f"{role_name.capitalize()} Role")
        db.session.add(role)
        db.session.commit()
    user = User(username=username, email=email, full_name=username.capitalize())
    user.set_password("Admin123")
    user.roles.append(role)
    db.session.add(user)
    db.session.commit()
    raw_token = Token.generate_refresh_token(user)
    return user.id, raw_token


def test_role_has_permission(app):
    with app.app_context():
        p1 = Permission(code="user.create", name="Create User", module="User")
        p2 = Permission(code="user.delete", name="Delete User", module="User")
        r = Role(name="manager", descriptions="Manager Role")
        r.permissions.extend([p1, p2])
        db.session.add_all([p1, p2, r])
        db.session.commit()

        assert r.has_permission("user.create") is True
        assert r.has_permission("user.delete") is True
        assert r.has_permission("user.update") is False


def test_user_get_permission_codes_deduplication(app):
    with app.app_context():
        p1 = Permission(code="report.view", name="View Report", module="Report")
        r1 = Role(name="viewer", descriptions="Viewer")
        r2 = Role(name="auditor", descriptions="Auditor")
        r1.permissions.append(p1)
        r2.permissions.append(p1)

        u = User(username="multi_role", email="mr@test.com", full_name="Multi Role")
        u.set_password("Pass12345")
        u.roles.extend([r1, r2])
        db.session.add_all([p1, r1, r2, u])
        db.session.commit()

        perm_codes = u.get_permission_codes()
        assert isinstance(perm_codes, set)
        assert len(perm_codes) == 1
        assert "report.view" in perm_codes


@pytest.mark.parametrize("method,url", [
    ("get", "/users/"),
    ("get", "/users/1"),
    ("get", "/users/create"),
    ("post", "/users/create"),
    ("get", "/users/1/edit"),
    ("post", "/users/1/edit"),
    ("get", "/users/1/delete"),
    ("post", "/users/1/delete"),
])
def test_non_admin_blocked_from_user_routes(app, method, url):
    with app.app_context():
        u_id, tok = create_user_with_role("reg_user", "reg@test.com", "user")

    client = setup_auth_client(app, u_id, tok)
    resp = getattr(client, method)(url)
    assert resp.status_code == 403


def test_non_admin_blocked_from_emp_dashboard(app):
    with app.app_context():
        u_id, tok = create_user_with_role("reg_user_emp", "reg_emp@test.com", "user")

    client = setup_auth_client(app, u_id, tok)
    resp = client.get("/dashboards/emp")
    assert resp.status_code == 403


def test_admin_access_allowed(app):
    with app.app_context():
        admin_id, tok = create_user_with_role("admin_tester", "admin_tester@test.com", "admin")

    client = setup_auth_client(app, admin_id, tok)
    resp = client.get("/users/")
    assert resp.status_code == 200


def test_models_without_usermixin():
    assert not hasattr(Role, "is_authenticated") or not hasattr(Role, "get_id")
    assert not hasattr(Permission, "is_authenticated") or not hasattr(Permission, "get_id")
    assert not hasattr(Plan, "is_authenticated") or not hasattr(Plan, "get_id")
    assert hasattr(User, "is_authenticated") and hasattr(User, "get_id")
