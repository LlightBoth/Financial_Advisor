import re
import pytest
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
    SECRET_KEY = "test-landing-secret-key"


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


def test_landing_page_english(client):
    """Test landing page renders properly in default English."""
    client.get("/set-language/en")
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    # Document & Meta
    assert '<html lang="en"' in html
    assert "Smart Wealth Planning" in html

    # Navigation & Actions
    assert "Overview" in html
    assert "Features" in html
    assert "Advisory" in html
    assert "Security" in html
    assert "Sign In" in html
    assert "Get Started" in html

    # Hero & Mockup Preview
    assert "Smart Financial Planning" in html
    assert "Personal Wealth Advisory" in html
    assert "FINANCIAL HEALTH: OPTIMAL // ADVISORY: ACTIVE" in html
    assert "Total Net Savings" in html
    assert "Savings Goal Pacing" in html
    assert "Debt-to-Income Ratio" in html

    # Core Capabilities
    assert "Core Capabilities" in html
    assert "Everything You Need to Master Your Money" in html
    assert "Intelligent Advisory Engine" in html
    assert "Goal &amp; Milestone Tracking" in html or "Goal & Milestone Tracking" in html
    assert "Cashflow &amp; Expense Analytics" in html or "Cashflow & Expense Analytics" in html
    assert "Audit-Ready Transaction Ledger" in html

    # Showcase & CTA
    assert "STRATEGIC WEALTH MANAGEMENT" in html
    assert "Built for Confident Financial Decision-Making" in html
    assert "Bank-Level Security &amp; Privacy" in html or "Bank-Level Security & Privacy" in html
    assert "Personalized Advisory Insights" in html
    assert "Take Control of Your Financial Future" in html
    assert "Create Free Account" in html

    # Footer
    assert "System Status: Operational" in html
    assert "Platform" in html
    assert "Company" in html
    assert "Legal" in html
    assert "Access" in html
    assert "Global (EN-US)" in html
    assert "Back to Top" in html


def test_landing_page_khmer(client):
    """Test landing page renders properly in Khmer with complete translation."""
    client.get("/set-language/km")
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    # Document & Meta
    assert '<html lang="km"' in html
    assert "ការរៀបចំផែនការទ្រព្យសម្បត្តិឆ្លាតវៃ" in html

    # Navigation & Actions
    assert "ទិដ្ឋភាពទូទៅ" in html
    assert "មុខងារចម្បង" in html
    assert "ប្រឹក្សាហិរញ្ញវត្ថុ" in html
    assert "សុវត្ថិភាព" in html
    assert "ចូលគណនី" in html
    assert "ចាប់ផ្តើម" in html

    # Hero & Mockup Preview
    assert "ការរៀបចំផែនការហិរញ្ញវត្ថុឆ្លាតវៃ" in html
    assert "ការប្រឹក្សាទ្រព្យសម្បត្តិផ្ទាល់ខ្លួន" in html
    assert "សុខភាពហិរញ្ញវត្ថុ៖ ល្អប្រសើរ // ការប្រឹក្សា៖ សកម្ម" in html
    assert "ការសន្សំសុទ្ធសរុប" in html
    assert "ល្បឿនគោលដៅសន្សំ" in html
    assert "សមាមាត្របំណុលធៀបចំណូល" in html

    # Core Capabilities
    assert "សមត្ថភាពស្នូល" in html
    assert "អ្វីគ្រប់យ៉ាងដែលអ្នកត្រូវការដើម្បីគ្រប់គ្រងលុយកាក់" in html
    assert "ប្រព័ន្ធផ្តល់ដំបូន្មានឆ្លាតវៃ" in html
    assert "ការតាមដានគោលដៅ និងដំណាក់កាល" in html
    assert "ការវិភាគលំហូរសាច់ប្រាក់ និងចំណាយ" in html
    assert "សៀវភៅបញ្ជីប្រតិបត្តិការដែលអាចធ្វើសវនកម្មបាន" in html

    # Showcase & CTA
    assert "ការគ្រប់គ្រងទ្រព្យសម្បត្តិជាយុទ្ធសាស្ត្រ" in html
    assert "បង្កើតឡើងសម្រាប់ការសម្រេចចិត្តផ្នែកហិរញ្ញវត្ថុប្រកបដោយទំនុកចិត្ត" in html
    assert "សុវត្ថិភាព និងភាពឯកជនកម្រិតខ្ពស់" in html
    assert "ការយល់ដឹងស៊ីជម្រៅនៃការប្រឹក្សាផ្ទាល់ខ្លួន" in html
    assert "គ្រប់គ្រងអនាគតហិរញ្ញវត្ថុរបស់អ្នក" in html
    assert "បង្កើតគណនីឥតគិតថ្លៃ" in html

    # Footer
    assert "ស្ថានភាពប្រព័ន្ធ៖ ដំណើរការធម្មតា" in html
    assert "វេទិកា" in html
    assert "ក្រុមហ៊ុន" in html
    assert "ច្បាប់" in html
    assert "ការចូលប្រើ" in html
    assert "កម្ពុជា (KM)" in html
    assert "ត្រឡប់ទៅលើ" in html


def test_landing_no_unrendered_keys(client):
    """Ensure no untranslated raw translation keys are displayed."""
    for lang in ["en", "km"]:
        client.get(f"/set-language/{lang}")
        response = client.get("/")
        html = response.get_data(as_text=True)

        # Ignore literal asset filenames or JS syntax
        raw_keys = [
            k for k in re.findall(r"(?:nav|common|landing|advisor|history|plan|auth|settings|expense|income)\.[a-zA-Z0-9_]+", html)
            if k not in ("landing.css", "advisor.ai", "history.pushState")
        ]
        assert raw_keys == [], f"Found raw keys in {lang} landing: {raw_keys}"
