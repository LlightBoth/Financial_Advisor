import os
import re
import pytest
from flask import render_template_string
from app import create_app
from app.models import User, Role
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
    SECRET_KEY = "test-admin-font-secret-key"


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


def create_and_login_admin(app, client, username="admin_tester", email="admin_tester@example.com"):
    """Deterministic, isolated admin user for layout verification."""
    with app.app_context():
        role_admin = Role.query.filter_by(name="admin").first()
        if not role_admin:
            role_admin = Role(name="admin", description="System Administrator")
            db.session.add(role_admin)
            db.session.commit()

        admin = User(username=username, email=email, full_name="Admin Tester")
        admin.set_password("AdminSecurePassword123!")
        admin.roles.append(role_admin)
        db.session.add(admin)
        db.session.commit()

        raw_token = Token.generate_refresh_token(admin)
        admin_id = admin.id

    with client.session_transaction() as sess:
        sess["_user_id"] = str(admin_id)
        sess["_fresh"] = True
    client.set_cookie(key="access_token", value="test_access_token")
    client.set_cookie(key="refresh_token", value=raw_token)
    return admin_id


# ==============================================================================
# 1. Admin Layout References Centralized Font System
# ==============================================================================

def test_admin_base_layout_links_fonts_css_before_emp_css(app, client):
    """Admin layout (base.html) must load fonts.css before emp.css."""
    create_and_login_admin(app, client)

    with app.test_request_context():
        rendered = render_template_string(
            '{% extends "layouts/base.html" %}{% block content %}<h1>Admin Panel</h1>{% endblock %}'
        )
        assert "css/fonts.css" in rendered, "base.html must link fonts.css"
        assert "css/layout/emp.css" in rendered, "base.html must link emp.css"

        # Verify ordering: fonts.css MUST appear before emp.css
        fonts_idx = rendered.find("css/fonts.css")
        emp_idx = rendered.find("css/layout/emp.css")
        assert fonts_idx != -1 and emp_idx != -1
        assert fonts_idx < emp_idx, "fonts.css must be loaded prior to emp.css"


# ==============================================================================
# 2. fonts.css Exists and is Accessible
# ==============================================================================

def test_fonts_css_file_and_endpoint(client):
    """Verify fonts.css exists on disk and is served via HTTP 200."""
    res = client.get("/static/css/fonts.css")
    assert res.status_code == 200
    css = res.data.decode("utf-8")

    assert "--font-body" in css
    assert "--font-heading" in css
    assert "--font-khmer-body" in css
    assert "--font-khmer-heading" in css


# ==============================================================================
# 3. Existing Bundled Khmer Font Files Exist and are Served
# ==============================================================================

def test_bundled_khmer_font_files(client):
    """Verify local offline Khmer font assets exist and return HTTP 200 with non-empty binary."""
    khmer_fonts = [
        "KhmerOSBattambang-Regular.ttf",
        "KhmerOSBattambang-Bold.ttf",
        "KhmerOSSiemreap-Regular.ttf",
        "KhmerOSMuolLight.ttf",
        "NotoSansKhmer-Regular.ttf",
        "NotoSansKhmer-Bold.ttf",
    ]
    for font_name in khmer_fonts:
        res = client.get(f"/static/fonts/{font_name}")
        assert res.status_code == 200, f"Font {font_name} failed to load."
        assert len(res.data) > 10000, f"Font {font_name} binary is empty or corrupted."


# ==============================================================================
# 4. Admin CSS Inherits Font Variables Without Duplicate System
# ==============================================================================

def test_admin_css_uses_central_font_variables():
    """emp.css must use var(--font-body) and var(--font-heading) without conflicting fonts."""
    emp_path = os.path.join(os.path.dirname(__file__), "..", "app", "static", "css", "layout", "emp.css")
    assert os.path.isfile(emp_path), "emp.css must exist"

    with open(emp_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Must use central tokens
    assert "var(--font-body)" in content
    assert "var(--font-heading)" in content

    # Must NOT define a duplicate @font-face
    assert "@font-face" not in content, "emp.css must not define duplicate @font-face rules"

    # Must NOT have separate admin font imports
    assert "admin-font" not in content
    assert "employee-font" not in content


# ==============================================================================
# 5. Khmer Admin Pages Contain Correct Language Attribute
# ==============================================================================

def test_admin_pages_html_lang_attribute(app, client):
    """Admin base layout must dynamically render html[lang='en'] and html[lang='km']."""
    create_and_login_admin(app, client)

    # English admin page
    with app.test_request_context():
        from flask import session
        session["lang"] = "en"
        res_en = render_template_string('{% extends "layouts/base.html" %}{% block content %}{% endblock %}')
        assert '<html lang="en">' in res_en

    # Khmer admin page
    with app.test_request_context():
        from flask import session
        session["lang"] = "km"
        res_km = render_template_string('{% extends "layouts/base.html" %}{% block content %}{% endblock %}')
        assert '<html lang="km">' in res_km


# ==============================================================================
# 6. Zero Google Fonts or External Font CDNs
# ==============================================================================

def test_zero_google_fonts_in_admin_templates_and_css():
    """Ensure zero Google Fonts or external CDN font links exist in base.html and emp.css."""
    base_path = os.path.join(os.path.dirname(__file__), "..", "app", "templates", "layouts", "base.html")
    emp_path = os.path.join(os.path.dirname(__file__), "..", "app", "static", "css", "layout", "emp.css")

    with open(base_path, "r", encoding="utf-8") as f:
        base_html = f.read()

    with open(emp_path, "r", encoding="utf-8") as f:
        emp_css = f.read()

    forbidden_patterns = [
        "fonts.googleapis.com",
        "fonts.gstatic.com",
        "use.typekit.net",
        "cdnjs.cloudflare.com/ajax/libs/font",
    ]

    for pattern in forbidden_patterns:
        assert pattern not in base_html, f"base.html must not contain external font dependency: {pattern}"
        assert pattern not in emp_css, f"emp.css must not contain external font dependency: {pattern}"


# ==============================================================================
# 7. Zero Duplicate Font Files or Frameworks
# ==============================================================================

def test_single_centralized_font_directory():
    """Ensure no secondary font directories exist (e.g., admin_fonts, emp_fonts)."""
    static_dir = os.path.join(os.path.dirname(__file__), "..", "app", "static")
    subdirs = [d for d in os.listdir(static_dir) if os.path.isdir(os.path.join(static_dir, d))]

    assert "fonts" in subdirs, "Single central fonts directory must exist"
    for d in subdirs:
        if d != "fonts":
            assert "font" not in d.lower(), f"Unwanted secondary font directory found: {d}"
