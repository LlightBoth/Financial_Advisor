import pytest
from flask import render_template_string, session
from app import create_app
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
    SECRET_KEY = "test-secret-key"


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


# ==============================================================================
# 1. Central Font CSS Delivery & Integrity
# ==============================================================================

def test_fonts_css_delivered(client):
    """Verify fonts.css is accessible and contains core typography definitions."""
    response = client.get("/static/css/fonts.css")
    assert response.status_code == 200
    css_content = response.data.decode("utf-8")

    # Verify @font-face declarations
    assert "@font-face" in css_content
    assert "Khmer OS Battambang" in css_content
    assert "Khmer OS Siemreap" in css_content
    assert "Khmer OS Muol Light" in css_content
    assert "Noto Sans Khmer" in css_content

    # Verify CSS variables
    assert "--font-khmer-body" in css_content
    assert "--font-khmer-heading" in css_content
    assert "--font-english-body" in css_content
    assert "--font-english-heading" in css_content
    assert "--font-body" in css_content
    assert "--font-heading" in css_content

    # Verify language-specific activations
    assert 'html[lang="km"]' in css_content
    assert "html[lang=\"en\"]" in css_content or "html," in css_content
    assert ".font-khmer" in css_content
    assert ".font-khmer-heading" in css_content
    assert ".font-english" in css_content

    # Verify zero external CDN URLs
    assert "fonts.googleapis.com" not in css_content
    assert "fonts.gstatic.com" not in css_content


def test_offline_font_files_served(client):
    """Verify all local font files can be fetched directly via HTTP 200."""
    required_fonts = [
        "KhmerOSBattambang-Regular.ttf",
        "KhmerOSBattambang-Bold.ttf",
        "KhmerOSSiemreap-Regular.ttf",
        "KhmerOSMuolLight.ttf",
        "NotoSansKhmer-Regular.ttf",
        "NotoSansKhmer-Bold.ttf",
    ]

    for font_filename in required_fonts:
        res = client.get(f"/static/fonts/{font_filename}")
        assert res.status_code == 200, f"Font file {font_filename} failed with status {res.status_code}"
        assert len(res.data) > 10000, f"Font file {font_filename} is suspiciously small: {len(res.data)} bytes"


# ==============================================================================
# 2. Layout Integration Tests
# ==============================================================================

def test_layouts_link_central_fonts_css(app):
    """Verify that base, clientBase, and authBase include fonts.css."""
    with app.test_request_context():
        client_rendered = render_template_string(
            '{% extends "layouts/clientBase.html" %}{% block content %}Test{% endblock %}'
        )
        assert 'fonts.css' in client_rendered

        auth_rendered = render_template_string(
            '{% extends "layouts/authBase.html" %}{% block content %}Test{% endblock %}'
        )
        assert 'fonts.css' in auth_rendered

        base_rendered = render_template_string(
            '{% extends "layouts/base.html" %}{% block content %}Test{% endblock %}'
        )
        assert 'fonts.css' in base_rendered


def test_auth_pages_include_fonts_and_proper_lang(client):
    """Verify rendered auth pages have fonts.css and html lang tag."""
    # English login
    res_en = client.get("/auth/login")
    assert res_en.status_code == 200
    html_en = res_en.data.decode("utf-8")
    assert 'fonts.css' in html_en
    assert 'lang="en"' in html_en

    # Khmer login via session
    with client.session_transaction() as sess:
        sess["lang"] = "km"
    res_km = client.get("/auth/login")
    assert res_km.status_code == 200
    html_km = res_km.data.decode("utf-8")
    assert 'fonts.css' in html_km
    assert 'lang="km"' in html_km
    assert "ចូលគណនី" in html_km
