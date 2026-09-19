import pytest
from flask import session
from app import create_app
from app.forms.auth_forms import LoginForm, RegisterForm, ForgotPasswordForm
from app.models.user import User
from app.models.role import Role
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
    SECRET_KEY = "test-auth-secret-key"


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
# 1. Login Page Localization Tests
# ==============================================================================

def test_login_page_renders_english(client):
    response = client.get("/auth/login")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert 'lang="en"' in html
    assert "Sign In" in html
    assert "Welcome Back" in html
    assert "Email Address" in html
    assert "Password" in html
    assert "Remember me" in html
    assert "Forgot password?" in html
    assert "Create Account" in html


def test_login_page_renders_khmer(client):
    with client.session_transaction() as sess:
        sess["lang"] = "km"

    response = client.get("/auth/login")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert 'lang="km"' in html
    assert "ចូលគណនី" in html
    assert "សូមស្វាគមន៍ការត្រឡប់មកវិញ" in html
    assert "អាសយដ្ឋានអ៊ីមែល" in html
    assert "ពាក្យសម្ងាត់" in html
    assert "ចងចាំខ្ញុំ" in html
    assert "ភ្លេចពាក្យសម្ងាត់?" in html
    assert "បង្កើតគណនី" in html


# ==============================================================================
# 2. Register Page Localization Tests
# ==============================================================================

def test_register_page_renders_english(client):
    response = client.get("/auth/register")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert 'lang="en"' in html
    assert "Create Account" in html
    assert "Full Name" in html
    assert "Username" in html
    assert "Email Address" in html
    assert "Password" in html
    assert "Confirm Password" in html
    assert "Sign In" in html


def test_register_page_renders_khmer(client):
    with client.session_transaction() as sess:
        sess["lang"] = "km"

    response = client.get("/auth/register")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert 'lang="km"' in html
    assert "បង្កើតគណនី" in html
    assert "ឈ្មោះពេញ" in html
    assert "ឈ្មោះអ្នកប្រើប្រាស់" in html
    assert "អាសយដ្ឋានអ៊ីមែល" in html
    assert "ពាក្យសម្ងាត់" in html
    assert "បញ្ជាក់ពាក្យសម្ងាត់" in html
    assert "ចូលគណនី" in html


# ==============================================================================
# 3. Forgot Password Page Localization Tests
# ==============================================================================

def test_forgot_password_renders_english(client):
    response = client.get("/auth/forgot_password")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert 'lang="en"' in html
    assert "Reset Password" in html
    assert "Email Address" in html
    assert "Send Verification Code" in html
    assert "Back to Sign In" in html


def test_forgot_password_renders_khmer(client):
    with client.session_transaction() as sess:
        sess["lang"] = "km"

    response = client.get("/auth/forgot_password")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert 'lang="km"' in html
    assert "កំណត់ពាក្យសម្ងាត់ឡើងវិញ" in html
    assert "អាសយដ្ឋានអ៊ីមែល" in html
    assert "ផ្ញើលេខកូដផ្ទៀងផ្ទាត់" in html
    assert "ត្រឡប់ទៅចូលគណនី" in html


# ==============================================================================
# 4. Reset Password & Verify OTP Localization Tests
# ==============================================================================

def test_verify_otp_renders_english_and_khmer(client):
    # Setup reset session
    with client.session_transaction() as sess:
        sess["pending_user_email"] = "reset@example.com"
        sess["generated_otp"] = "123456"
        sess["otp_expiry"] = 9999999999
        sess["lang"] = "en"

    # English
    r_en = client.get("/auth/verify-otp")
    assert r_en.status_code == 200
    html_en = r_en.data.decode("utf-8")
    assert 'lang="en"' in html_en
    assert "Security Verification" in html_en
    assert "Verify & Continue" in html_en
    assert "Resend" in html_en

    # Khmer
    with client.session_transaction() as sess:
        sess["lang"] = "km"
    r_km = client.get("/auth/verify-otp")
    assert r_km.status_code == 200
    html_km = r_km.data.decode("utf-8")
    assert 'lang="km"' in html_km
    assert "ការផ្ទៀងផ្ទាត់សុវត្ថិភាព" in html_km
    assert "ផ្ទៀងផ្ទាត់ & បន្ត" in html_km
    assert "ផ្ញើម្តងទៀត" in html_km


def test_new_password_renders_english_and_khmer(client, app):
    with app.app_context():
        user = User(username="reset_user", email="reset_user@example.com", full_name="Reset User")
        user.set_password("OldPassword123")
        db.session.add(user)
        db.session.commit()

    # English
    with client.session_transaction() as sess:
        sess["pending_user_email"] = "reset_user@example.com"
        sess["otp_verified"] = True
        sess["lang"] = "en"

    r_en = client.get("/auth/reset-password")
    assert r_en.status_code == 200
    html_en = r_en.data.decode("utf-8")
    assert 'lang="en"' in html_en
    assert "Set New Password" in html_en
    assert "New Password" in html_en
    assert "Confirm Password" in html_en
    assert "At least 8 characters" in html_en

    # Khmer
    with client.session_transaction() as sess:
        sess["lang"] = "km"
    r_km = client.get("/auth/reset-password")
    assert r_km.status_code == 200
    html_km = r_km.data.decode("utf-8")
    assert 'lang="km"' in html_km
    assert "កំណត់ពាក្យសម្ងាត់ថ្មី" in html_km
    assert "ពាក្យសម្ងាត់ថ្មី" in html_km
    assert "បញ្ជាក់ពាក្យសម្ងាត់" in html_km
    assert "យ៉ាងតិច ៨ តួអក្សរ" in html_km


# ==============================================================================
# 5. Form Validation Localization Tests
# ==============================================================================

def test_login_form_validation_english(app):
    with app.test_request_context():
        form = LoginForm(email="", password="")
        form.validate()
        errors = [str(e) for e in form.email.errors]
        assert "This field is required." in errors
        assert str(form.email.label.text) == "Email"
        assert str(form.password.label.text) == "Password"


def test_login_form_validation_khmer(app):
    with app.test_request_context():
        session["lang"] = "km"
        form = LoginForm(email="", password="")
        form.validate()
        errors = [str(e) for e in form.email.errors]
        assert "សូមបំពេញប្រអប់នេះ។" in errors
        assert str(form.email.label.text) == "អ៊ីមែល"
        assert str(form.password.label.text) == "ពាក្យសម្ងាត់"


def test_register_form_validation_password_mismatch(app):
    # English
    with app.test_request_context():
        form_en = RegisterForm(
            username="testuser",
            full_name="Test User",
            email="test@example.com",
            password="Password123",
            confirm_password="DifferentPassword456",
        )
        form_en.validate()
        errors_en = [str(e) for e in form_en.confirm_password.errors]
        assert "Passwords must match." in errors_en

    # Khmer
    with app.test_request_context():
        session["lang"] = "km"
        form_km = RegisterForm(
            username="testuser",
            full_name="Test User",
            email="test@example.com",
            password="Password123",
            confirm_password="DifferentPassword456",
        )
        form_km.validate()
        errors_km = [str(e) for e in form_km.confirm_password.errors]
        assert "ពាក្យសម្ងាត់មិនត្រូវគ្នាទេ។" in errors_km


# ==============================================================================
# 6. Flash Message Localization Tests
# ==============================================================================

def test_login_failed_flash_message_english(client):
    response = client.post(
        "/auth/login",
        data={"email": "wrong@example.com", "password": "WrongPassword123"},
        follow_redirects=True,
    )
    html = response.data.decode("utf-8")
    assert "Invalid credentials" in html


def test_login_failed_flash_message_khmer(client):
    with client.session_transaction() as sess:
        sess["lang"] = "km"

    response = client.post(
        "/auth/login",
        data={"email": "wrong@example.com", "password": "WrongPassword123"},
        follow_redirects=True,
    )
    html = response.data.decode("utf-8")
    assert "ព័ត៌មានសម្ងាត់មិនត្រឹមត្រូវទេ" in html


def test_forgot_password_flash_message_english_and_khmer(client):
    # English
    r_en = client.post(
        "/auth/forgot_password",
        data={"email": "nonexistent@example.com"},
        follow_redirects=True,
    )
    html_en = r_en.data.decode("utf-8")
    assert "If an account exists with that email, a password reset code has been sent." in html_en

    # Khmer
    with client.session_transaction() as sess:
        sess["lang"] = "km"

    r_km = client.post(
        "/auth/forgot_password",
        data={"email": "nonexistent@example.com"},
        follow_redirects=True,
    )
    html_km = r_km.data.decode("utf-8")
    assert "ប្រសិនបើមានគណនីដែលប្រើអ៊ីមែលនោះ លេខកូដកំណត់ពាក្យសម្ងាត់ឡើងវិញត្រូវបានផ្ញើជូនហើយ។" in html_km


# ==============================================================================
# 7. Session Persistence and Language Switcher on Auth Pages
# ==============================================================================

def test_auth_language_switcher_and_session_persistence(client):
    # Navigate to login, switch to km
    client.get("/auth/login")
    r_switch = client.get("/set-language/km", headers={"Referer": "/auth/login"}, follow_redirects=True)
    assert r_switch.status_code == 200
    html_km = r_switch.data.decode("utf-8")
    assert 'lang="km"' in html_km
    assert "ចូលគណនី" in html_km

    # Navigate to register page: must stay in Khmer
    r_reg = client.get("/auth/register")
    assert r_reg.status_code == 200
    html_reg = r_reg.data.decode("utf-8")
    assert 'lang="km"' in html_reg
    assert "បង្កើតគណនី" in html_reg

    # Switch back to English
    r_en_switch = client.get("/set-language/en", headers={"Referer": "/auth/register"}, follow_redirects=True)
    assert r_en_switch.status_code == 200
    html_en = r_en_switch.data.decode("utf-8")
    assert 'lang="en"' in html_en
    assert "Create Account" in html_en
