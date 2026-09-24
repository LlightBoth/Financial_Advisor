import pytest
from flask import session, render_template_string
from app import create_app
from app.utils.i18n import (
    SUPPORTED_LANGUAGES,
    DEFAULT_LANGUAGE,
    get_locale,
    translate,
    _,
)
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
# 1. Translation Unit Tests
# ==============================================================================

def test_supported_and_default_languages():
    assert "en" in SUPPORTED_LANGUAGES
    assert "km" in SUPPORTED_LANGUAGES
    assert "kh" not in SUPPORTED_LANGUAGES
    assert "khmer" not in SUPPORTED_LANGUAGES
    assert DEFAULT_LANGUAGE == "en"


def test_english_translation(app):
    with app.test_request_context():
        # Default is English
        assert _("app.name") == "Financial Consultant"
        assert _("nav.dashboard") == "Dashboard"
        assert _("nav.income") == "Income"
        assert _("nav.expense") == "Expense"
        assert _("common.save") == "Save"
        assert _("common.cancel") == "Cancel"
        assert translate("nav.plans", "en") == "Plans"


def test_khmer_translation(app):
    with app.test_request_context():
        assert translate("app.name", "km") == "ប្រព័ន្ធប្រឹក្សាហិរញ្ញវត្ថុ"
        assert translate("nav.dashboard", "km") == "ផ្ទាំងគ្រប់គ្រង"
        assert translate("nav.income", "km") == "ចំណូល"
        assert translate("nav.expense", "km") == "ចំណាយ"
        assert translate("common.monthly_income", "km") == "ចំណូលប្រចាំខែ"
        assert translate("common.monthly_expense", "km") == "ចំណាយប្រចាំខែ"
        assert translate("common.savings", "km") == "ប្រាក់សន្សំ"
        assert translate("common.recommendation", "km") == "អនុសាសន៍"


def test_missing_khmer_falls_back_to_english(app, monkeypatch):
    """
    If a key exists in en.json but is missing in km.json,
    it must fall back to the English translation.
    """
    import app.utils.i18n as i18n_module
    with app.test_request_context():
        monkeypatch.setitem(i18n_module._translations["en"], "test.only_in_en", "English Value")
        monkeypatch.delitem(i18n_module._translations["km"], "test.only_in_en", raising=False)
        
        result = translate("test.only_in_en", "km")
        assert result == "English Value"


def test_missing_key_falls_back_to_original_key(app):
    """
    If a key is missing from both km.json and en.json,
    it must safely fall back to returning the key itself.
    """
    with app.test_request_context():
        missing_key = "nonexistent.translation.key.123"
        assert translate(missing_key, "en") == missing_key
        assert translate(missing_key, "km") == missing_key
        assert _(missing_key) == missing_key


def test_translation_never_raises_on_invalid_types_or_files(app):
    """
    translate() should safely handle None, non-strings, or file reading exceptions.
    """
    with app.test_request_context():
        assert translate(None, "en") == ""
        assert translate("", "en") == ""
        assert translate(12345, "en") == "12345"


# ==============================================================================
# 2. Language Switcher Route Tests
# ==============================================================================

def test_set_language_en_success(client):
    response = client.get("/set-language/en")
    assert response.status_code == 302
    with client.session_transaction() as sess:
        assert sess.get("lang") == "en"


def test_set_language_km_success(client):
    response = client.get("/set-language/km")
    assert response.status_code == 302
    with client.session_transaction() as sess:
        assert sess.get("lang") == "km"


def test_invalid_language_returns_400(client):
    invalid_codes = ["fr", "kh", "khmer", "KH", "es", "zh", "anything", "123", "en_US"]
    for code in invalid_codes:
        response = client.get(f"/set-language/{code}")
        assert response.status_code == 400, f"Expected 400 for language '{code}', got {response.status_code}"


def test_session_persistence(client, app):
    # Set to km
    client.get("/set-language/km")
    with client.session_transaction() as sess:
        assert sess["lang"] == "km"

    # Context in request reflects km
    with client:
        client.get("/")
        assert get_locale() == "km"
        assert _("nav.dashboard") == "ផ្ទាំងគ្រប់គ្រង"

    # Switch back to en
    client.get("/set-language/en")
    with client.session_transaction() as sess:
        assert sess["lang"] == "en"

    with client:
        client.get("/")
        assert get_locale() == "en"
        assert _("nav.dashboard") == "Dashboard"


# ==============================================================================
# 3. Unicode and Khmer Character Integrity Tests
# ==============================================================================

def test_khmer_unicode_strings(app):
    required_khmer_strings = [
        ("app.name", "ប្រព័ន្ធប្រឹក្សាហិរញ្ញវត្ថុ"),
        ("nav.dashboard", "ផ្ទាំងគ្រប់គ្រង"),
        ("common.monthly_income", "ចំណូលប្រចាំខែ"),
        ("common.monthly_expense", "ចំណាយប្រចាំខែ"),
        ("common.savings", "ប្រាក់សន្សំ"),
        ("common.recommendation", "អនុសាសន៍"),
    ]
    with app.test_request_context():
        for key, expected_khmer in required_khmer_strings:
            translated = translate(key, "km")
            assert translated == expected_khmer
            # Verify proper UTF-8 encoding and round-trip
            utf8_bytes = translated.encode("utf-8")
            assert utf8_bytes.decode("utf-8") == expected_khmer


# ==============================================================================
# 4. Open Redirect and Referrer Security Tests
# ==============================================================================

def test_safe_internal_referrer_redirect(client):
    # Referrer on the same application host
    headers = {"Referer": "http://localhost/dashboards/emp"}
    response = client.get("/set-language/km", headers=headers)
    assert response.status_code == 302
    assert response.location == "http://localhost/dashboards/emp"


def test_safe_relative_path_referrer(client):
    headers = {"Referer": "/auth/login"}
    response = client.get("/set-language/km", headers=headers)
    assert response.status_code == 302
    assert response.location == "/auth/login" or response.location == "http://localhost/auth/login"


def test_external_referrer_blocked_to_safe_fallback(client):
    # Malicious external referrer
    malicious_referrers = [
        "http://evil.com/phishing",
        "https://attacker.org/steal",
        "//attacker.com",
        "javascript:alert(1)",
        "http://localhost.attacker.com/bypass",
    ]
    for bad_ref in malicious_referrers:
        headers = {"Referer": bad_ref}
        response = client.get("/set-language/km", headers=headers)
        assert response.status_code == 302
        # Redirect location MUST NOT be the attacker URL
        assert "attacker" not in response.location
        assert "evil.com" not in response.location
        assert "javascript" not in response.location
        # Must fall back to safe internal endpoint
        assert response.location.endswith("/") or response.location.endswith("/auth/login") or response.location == "/"


def test_missing_referrer_redirects_to_fallback(client):
    response = client.get("/set-language/km")
    assert response.status_code == 302
    assert response.location.endswith("/") or response.location == "/"


# ==============================================================================
# 5. Jinja Template Context Integration Tests
# ==============================================================================

def test_jinja_globals_and_context(app):
    with app.test_request_context():
        # Check that Jinja environment has _, translate, get_locale, SUPPORTED_LANGUAGES
        assert "_" in app.jinja_env.globals
        assert "translate" in app.jinja_env.globals
        assert "get_locale" in app.jinja_env.globals
        assert "SUPPORTED_LANGUAGES" in app.jinja_env.globals

        # Render string with Flask context processor
        rendered_en = render_template_string("{{ _('nav.dashboard') }} | {{ current_lang }}")
        assert "Dashboard | en" in rendered_en

    with app.test_request_context():
        session["lang"] = "km"
        rendered_km = render_template_string("{{ _('nav.dashboard') }} | {{ current_lang }}")
        assert "ផ្ទាំងគ្រប់គ្រង | km" in rendered_km


def test_accept_language_header_detection(app):
    with app.test_request_context(headers={"Accept-Language": "km,en;q=0.9"}):
        assert get_locale() == "km"
        assert _("nav.dashboard") == "ផ្ទាំងគ្រប់គ្រង"

    with app.test_request_context(headers={"Accept-Language": "en-US,en;q=0.8"}):
        assert get_locale() == "en"
        assert _("nav.dashboard") == "Dashboard"


def test_layout_templates_render_without_syntax_errors(app):
    """Verify that layouts compile and render with current_lang dynamically."""
    with app.test_request_context():
        session["lang"] = "km"
        rendered = render_template_string('<html lang="{{ current_lang }}"><meta charset="utf-8"><body>{{ _("app.name") }}</body></html>')
        assert '<html lang="km">' in rendered
        assert '<meta charset="utf-8">' in rendered
        assert "ប្រព័ន្ធប្រឹក្សាហិរញ្ញវត្ថុ" in rendered

