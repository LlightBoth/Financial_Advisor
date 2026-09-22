import pytest
from app import create_app
from extension import db
from app.models import User, Role, Permission
from app.security.token import Token
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


@pytest.fixture(name="app")
def fixture_app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(name="client")
def fixture_client(app):
    return app.test_client()


def login_user_client(client, user):
    raw_token = Token.generate_refresh_token(user)
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)
        sess["_fresh"] = True
    client.set_cookie("access_token", "test_access_token")
    client.set_cookie("refresh_token", raw_token)


# --------------------------------------------------------------------------
# Test 1: Helper functions in Jinja globals evaluate accurately
# --------------------------------------------------------------------------
def test_jinja_helpers(app):
    with app.app_context():
        # Retrieve pre-seeded roles or create test permission
        p_view = Permission(code="test:view", name="Test View", module="Test")
        r_admin = Role.query.filter_by(name="admin").first()
        r_editor = Role.query.filter_by(name="editor").first()
        r_user = Role.query.filter_by(name="user").first()
        r_editor.permissions.append(p_view)

        admin_user = User(username="admin1", email="a@test.com", full_name="Admin")
        admin_user.set_password("Pass123")
        admin_user.roles.append(r_admin)

        editor_user = User(username="editor1", email="e@test.com", full_name="Editor")
        editor_user.set_password("Pass123")
        editor_user.roles.append(r_editor)

        client_user = User(username="client1", email="c@test.com", full_name="Client")
        client_user.set_password("Pass123")
        client_user.roles.append(r_user)

        db.session.add_all([p_view, admin_user, editor_user, client_user])
        db.session.commit()

        user_has_role = app.jinja_env.globals["user_has_role"]
        user_has_permission = app.jinja_env.globals["user_has_permission"]

        # Admin checks
        assert user_has_role(admin_user, "admin") is True
        assert user_has_role(admin_user, "user") is False
        assert user_has_permission(admin_user, "test:view") is True  # Admin bypass

        # Editor checks
        assert user_has_role(editor_user, "editor") is True
        assert user_has_role(editor_user, "admin") is False
        assert user_has_permission(editor_user, "test:view") is True
        assert user_has_permission(editor_user, "test:delete") is False

        # Regular user checks
        assert user_has_role(client_user, "user") is True
        assert user_has_role(client_user, "admin") is False
        assert user_has_permission(client_user, "test:view") is False

        # Anonymous/None checks
        assert user_has_role(None, "admin") is False
        assert user_has_permission(None, "test:view") is False


# --------------------------------------------------------------------------
# Test 2: Admin navigation links rendered for admin
# --------------------------------------------------------------------------
def test_admin_sidebar_links_present_for_admin(client, app):
    with app.app_context():
        admin = User.query.filter_by(username="admin").first()
        login_user_client(client, admin)

    response = client.get("/dashboards/emp")
    assert response.status_code == 200
    html = response.data.decode("utf-8")

    # Admin should see management links
    assert "href=\"/users/\"" in html or "Users" in html
    assert "href=\"/roles/\"" in html or "Roles" in html
    assert "href=\"/permissions/\"" in html or "Permissions" in html


# --------------------------------------------------------------------------
# Test 3: Admin navigation links NOT rendered for regular client
# --------------------------------------------------------------------------
def test_admin_sidebar_links_absent_for_regular_user(client, app):
    with app.app_context():
        regular_role = Role.query.filter_by(name="user").first()
        user = User(
            username="normal_user",
            email="normal@test.com",
            full_name="Normal User",
        )
        user.set_password("Pass123")
        user.roles.append(regular_role)
        db.session.add(user)
        db.session.commit()

        login_user_client(client, user)

    response = client.get("/dashboards/")
    assert response.status_code == 200
    html = response.data.decode("utf-8")

    # Regular user client dashboard should NOT show Employee link in sidebar
    assert "href=\"/dashboards/emp\"" not in html
    assert "href=\"/users/\"" not in html
    assert "href=\"/roles/\"" not in html
    assert "href=\"/permissions/\"" not in html


# --------------------------------------------------------------------------
# Test 4: Logged-out guest does not see authenticated/admin UI
# --------------------------------------------------------------------------
def test_logged_out_user_renders_clean_login(client):
    response = client.get("/auth/login")
    assert response.status_code == 200
    html = response.data.decode("utf-8")

    # No internal admin navigation leaked
    assert "href=\"/dashboards/emp\"" not in html
    assert "href=\"/users/\"" not in html
    assert "href=\"/roles/\"" not in html
    assert "href=\"/permissions/\"" not in html
