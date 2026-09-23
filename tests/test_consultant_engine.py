"""
Comprehensive Expert System Test Suite (Step 7E).

Verifies the Personal Financial Consultant Fact & Rule Engine against all requirements:
- Test A: Balanced Living (income=1000, expense=500, no debt)
- Test B: Tight Living / Paycheck-to-Paycheck (income=1000, expense=900, no debt)
- Test C: Deficit with Debt (income=1000, expense=1200, debt)
- Test D: Zero Income with Expenses (income=0, expense=500)
- Test E: Zero Expenses / 100% Surplus (income=500, expense=0)
- Boundary Tests: expense_ratio at 0.50, 0.80, 1.00, >1.00, and net_cashflow=0
- Certainty Regression Test: changing certainty does NOT change matching or priority selection
- Priority Regression Test: priority strictly resolves multi-rule matches
- Zero-Division Safety: income=0, expense=0
- Bilingual Output: English and Khmer
"""

import pytest
from app import create_app
from app.models import Rule, Fact
from app.services.consultant_metrics import calculate_metrics
from app.services.consultant_engine import ConsultantEngine, ConsultantAdviceResult
from app.services.advisor_services import AdvisorServices
from app.security.seed_rule_facts import seed_financial_system
from config import Config
from extension import db
from sqlalchemy.pool import StaticPool


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool,
    }
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-consultant-secret-key"


@pytest.fixture(name="app")
def fixture_app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        seed_financial_system()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


# ==============================================================================
# 1. Deterministic Financial Metrics Tests
# ==============================================================================

def test_metrics_test_a():
    """Test A: income = 1000, expense = 500, debt = no debt"""
    res = calculate_metrics(1000.0, 500.0, goal_cost=5000.0)
    assert res["net_cashflow"] == 500.0
    assert res["expense_ratio"] == 0.50
    assert res["surplus_ratio"] == 0.50
    assert res["natural_goal_months"] == 10.0  # 5000 / 500


def test_metrics_test_b():
    """Test B: income = 1000, expense = 900, debt = no debt"""
    res = calculate_metrics(1000.0, 900.0, goal_cost=1000.0)
    assert res["net_cashflow"] == 100.0
    assert res["expense_ratio"] == 0.90
    assert res["surplus_ratio"] == 0.10
    assert res["natural_goal_months"] == 10.0  # 1000 / 100


def test_metrics_test_c():
    """Test C: income = 1000, expense = 1200, debt = debt"""
    res = calculate_metrics(1000.0, 1200.0, goal_cost=1000.0)
    assert res["net_cashflow"] == -200.0
    assert res["expense_ratio"] == 1.20
    assert res["surplus_ratio"] == -0.20
    # Natural goal horizon cannot be funded from deficit
    assert res["natural_goal_months"] is None


def test_metrics_test_d_zero_income():
    """Test D: income = 0, expense = 500 (zero division safe)"""
    res = calculate_metrics(0.0, 500.0)
    assert res["net_cashflow"] == -500.0
    assert res["expense_ratio"] is None
    assert res["surplus_ratio"] is None
    assert res["natural_goal_months"] is None


def test_metrics_test_e_zero_expense():
    """Test E: income = 500, expense = 0"""
    res = calculate_metrics(500.0, 0.0)
    assert res["net_cashflow"] == 500.0
    assert res["expense_ratio"] == 0.0
    assert res["surplus_ratio"] == 1.0


def test_metrics_zero_income_zero_expense():
    """Test Boundary: income = 0, expense = 0 (zero division safe)"""
    res = calculate_metrics(0.0, 0.0)
    assert res["net_cashflow"] == 0.0
    assert res["expense_ratio"] is None
    assert res["surplus_ratio"] is None
    assert res["natural_goal_months"] is None


# ==============================================================================
# 2. Rule Engine End-to-End Scenarios (Tests A, B, C, D, E)
# ==============================================================================

def test_scenario_a_balanced_living(app):
    """
    Test A:
    income = 1000, expense = 500, no debt, employed.
    Expected: BALANCED_BUDGET_BUFFER_BUILDING (0.50 <= expense_ratio < 0.80)
    """
    with app.app_context():
        user_data = {
            "income": 1000.0,
            "expense": 500.0,
            "debt_status": "no debt",
            "employment_status": "employed",
            "spending_habit": "average spend",
            "goal_cost": 5000.0,
        }
        res = AdvisorServices.get_advise(user_data)
        rule = res["get_advice"]

        assert res["remain_percentage"] == 50.0
        assert res["expense_percentage"] == 50.0
        assert rule.rule_id == "BALANCED_BUDGET_BUFFER_BUILDING"
        assert rule.priority == 40
        assert rule.certainty == 0.85
        assert "Balanced Operating Budget" in rule.conclusion


def test_scenario_b_tight_living(app):
    """
    Test B:
    income = 1000, expense = 900, no debt, employed.
    Expected: TIGHT_MARGIN_HIGH_EXPENSE (expense_ratio >= 0.80, net_cashflow > 0)
    """
    with app.app_context():
        user_data = {
            "income": 1000.0,
            "expense": 900.0,
            "debt_status": "no debt",
            "employment_status": "employed",
            "spending_habit": "average spend",
        }
        res = AdvisorServices.get_advise(user_data)
        rule = res["get_advice"]

        assert res["remain_percentage"] == 10.0
        assert res["expense_percentage"] == 90.0
        assert rule.rule_id == "TIGHT_MARGIN_HIGH_EXPENSE"
        assert rule.priority == 80
        assert rule.certainty == 0.70
        assert "Narrow Operating Margin" in rule.conclusion


def test_scenario_c_deficit_with_debt(app):
    """
    Test C:
    income = 1000, expense = 1200, debt = debt, employed.
    Expected: DEFICIT_WITH_DEBT (net_cashflow < 0, debt_present == True)
    """
    with app.app_context():
        user_data = {
            "income": 1000.0,
            "expense": 1200.0,
            "debt_status": "debt",
            "employment_status": "employed",
            "spending_habit": "average spend",
        }
        res = AdvisorServices.get_advise(user_data)
        rule = res["get_advice"]

        assert res["remain_percentage"] == -20.0
        assert res["expense_percentage"] == 120.0
        assert rule.rule_id == "DEFICIT_WITH_DEBT"
        assert rule.priority == 100
        assert rule.certainty == 1.00
        assert "Active Debt Obligations" in rule.conclusion


def test_scenario_d_zero_income_with_expenses(app):
    """
    Test D:
    income = 0, expense = 500, not employed.
    Expected: No division-by-zero, no empty advice abort.
    Must match deficit/unemployed triage rule.
    """
    with app.app_context():
        user_data = {
            "income": 0.0,
            "expense": 500.0,
            "debt_status": "no debt",
            "employment_status": "not employed",
            "spending_habit": "average spend",
        }
        res = AdvisorServices.get_advise(user_data)
        rule = res["get_advice"]

        assert rule.advice != "No advice available"
        assert rule.conclusion != "No conclusion"
        assert rule.priority == 100
        assert rule.rule_id in ("INCOME_ZERO_UNEMPLOYED", "DEFICIT_NO_DEBT")


def test_scenario_e_zero_expenses_high_surplus(app):
    """
    Test E:
    income = 500, expense = 0, no debt, employed.
    Expected: FLEXIBLE_BUDGET_CAPITAL_GROWTH (expense_ratio < 0.50, net_cashflow > 0)
    """
    with app.app_context():
        user_data = {
            "income": 500.0,
            "expense": 0.0,
            "debt_status": "no debt",
            "employment_status": "employed",
            "spending_habit": "average spend",
        }
        res = AdvisorServices.get_advise(user_data)
        rule = res["get_advice"]

        assert res["remain_percentage"] == 100.0
        assert res["expense_percentage"] == 0.0
        assert rule.rule_id == "FLEXIBLE_BUDGET_CAPITAL_GROWTH"
        assert rule.priority == 20
        assert rule.certainty == 0.70


# ==============================================================================
# 3. Boundary Tests (0.50, 0.80, 1.00, >1.00, net_cashflow=0)
# ==============================================================================

def test_boundary_expense_ratio_50_percent(app):
    """Boundary at exactly 50% expense ratio: 0.50 <= expense_ratio < 0.80"""
    with app.app_context():
        user_data = {
            "income": 1000.0,
            "expense": 500.0,
            "debt_status": "no debt",
            "employment_status": "employed",
        }
        res = AdvisorServices.get_advise(user_data)
        assert res["get_advice"].rule_id == "BALANCED_BUDGET_BUFFER_BUILDING"


def test_boundary_expense_ratio_49_percent(app):
    """Boundary at 49.9% expense ratio: expense_ratio < 0.50"""
    with app.app_context():
        user_data = {
            "income": 1000.0,
            "expense": 499.0,
            "debt_status": "no debt",
            "employment_status": "employed",
        }
        res = AdvisorServices.get_advise(user_data)
        assert res["get_advice"].rule_id == "FLEXIBLE_BUDGET_CAPITAL_GROWTH"


def test_boundary_expense_ratio_80_percent(app):
    """Boundary at exactly 80% expense ratio: expense_ratio >= 0.80"""
    with app.app_context():
        user_data = {
            "income": 1000.0,
            "expense": 800.0,
            "debt_status": "no debt",
            "employment_status": "employed",
        }
        res = AdvisorServices.get_advise(user_data)
        assert res["get_advice"].rule_id == "TIGHT_MARGIN_HIGH_EXPENSE"


def test_boundary_expense_ratio_79_percent(app):
    """Boundary at 79.9% expense ratio: 0.50 <= expense_ratio < 0.80"""
    with app.app_context():
        user_data = {
            "income": 1000.0,
            "expense": 799.0,
            "debt_status": "no debt",
            "employment_status": "employed",
        }
        res = AdvisorServices.get_advise(user_data)
        assert res["get_advice"].rule_id == "BALANCED_BUDGET_BUFFER_BUILDING"


def test_boundary_break_even_net_cashflow_zero(app):
    """Boundary: net_cashflow == 0, expense_ratio = 1.00"""
    with app.app_context():
        user_data = {
            "income": 1000.0,
            "expense": 1000.0,
            "debt_status": "no debt",
            "employment_status": "employed",
        }
        res = AdvisorServices.get_advise(user_data)
        assert res["remain_percentage"] == 0.0
        assert res["expense_percentage"] == 100.0
        assert res["get_advice"].rule_id == "BREAK_EVEN_ZERO_MARGIN"
        assert res["get_advice"].priority == 80


def test_boundary_expense_ratio_greater_than_100_percent(app):
    """Boundary: expense_ratio > 1.00 (Operating Deficit, no debt)"""
    with app.app_context():
        user_data = {
            "income": 1000.0,
            "expense": 1500.0,
            "debt_status": "no debt",
            "employment_status": "employed",
        }
        res = AdvisorServices.get_advise(user_data)
        assert res["get_advice"].rule_id == "DEFICIT_NO_DEBT"
        assert res["get_advice"].priority == 100


# ==============================================================================
# 4. Certainty & Priority Regression Tests
# ==============================================================================

def test_certainty_regression_does_not_affect_matching(app):
    """
    CRITICAL INVARIANT:
    Changing Rule.certainty must NEVER change whether conditions match
    or which rule is selected by priority.
    """
    with app.app_context():
        user_data = {
            "income": 1000.0,
            "expense": 500.0,
            "debt_status": "no debt",
            "employment_status": "employed",
        }

        # Baseline evaluation
        baseline = AdvisorServices.get_advise(user_data)
        expected_rule_id = baseline["get_advice"].rule_id
        assert expected_rule_id == "BALANCED_BUDGET_BUFFER_BUILDING"

        # Modify certainty of the winning rule in the database to 0.10
        rule = Rule.query.filter_by(rule_id="BALANCED_BUDGET_BUFFER_BUILDING").first()
        rule.certainty = 0.10
        db.session.commit()

        # Re-evaluate
        after_low_certainty = AdvisorServices.get_advise(user_data)
        assert after_low_certainty["get_advice"].rule_id == "BALANCED_BUDGET_BUFFER_BUILDING"
        assert after_low_certainty["get_advice"].certainty == 0.10

        # Modify certainty to 0.99
        rule.certainty = 0.99
        db.session.commit()

        after_high_certainty = AdvisorServices.get_advise(user_data)
        assert after_high_certainty["get_advice"].rule_id == "BALANCED_BUDGET_BUFFER_BUILDING"
        assert after_high_certainty["get_advice"].certainty == 0.99


def test_priority_strictly_determines_selection():
    """
    CRITICAL INVARIANT:
    When two rules both match identical facts, the rule with higher priority
    MUST be selected, regardless of certainty values.
    """
    # Create two canonical matching rules:
    # Rule A: Priority 90, Certainty 0.30
    # Rule B: Priority 50, Certainty 0.95
    rule_a = {
        "rule_id": "DEFICIT_WITH_DEBT",
        "name": "Deficit Rule",
        "category": "TEST",
        "priority": 90,
        "certainty": 0.30,  # Lower certainty
        "kb_version": "financial-kb-v1.0",
        "conditions": [{"field": "income_positive", "operator": "==", "value": True}],
        "match_operator": "ALL",
        "conclusion": "High Priority Won",
        "advice": "High Priority Advice"
    }

    rule_b = {
        "rule_id": "DEFICIT_NO_DEBT",
        "name": "Deficit No Debt Rule",
        "category": "TEST",
        "priority": 50,
        "certainty": 0.95,  # Higher certainty
        "kb_version": "financial-kb-v1.0",
        "conditions": [{"field": "income_positive", "operator": "==", "value": True}],
        "match_operator": "ALL",
        "conclusion": "Low Priority Won",
        "advice": "Low Priority Advice"
    }

    facts = {"income_positive": True}
    winning, trace = ConsultantEngine.select_rule([rule_a, rule_b], facts)

    # Must select Rule A because priority 90 > priority 50, even though certainty 0.30 < 0.95
    assert winning is not None
    assert winning.rule_id == "DEFICIT_WITH_DEBT"
    assert winning.priority == 90
    assert winning.certainty == 0.30


def test_specificity_strictly_determines_selection():
    """
    When two canonical rules match with identical priority, the rule with more
    conditions (higher specificity) MUST be selected.
    """
    rule_a = {
        "rule_id": "DEFICIT_WITH_DEBT",
        "priority": 80,
        "certainty": 0.80,
        "kb_version": "financial-kb-v1.0",
        "conditions": [
            {"field": "income_positive", "operator": "==", "value": True},
            {"field": "cashflow_deficit", "operator": "==", "value": True},
        ],
        "match_operator": "ALL",
        "conclusion": "Specific Won",
        "advice": "Specific Advice"
    }
    rule_b = {
        "rule_id": "DEFICIT_NO_DEBT",
        "priority": 80,  # Equal priority
        "certainty": 0.80,
        "kb_version": "financial-kb-v1.0",
        "conditions": [
            {"field": "income_positive", "operator": "==", "value": True}
        ],
        "match_operator": "ALL",
        "conclusion": "General Won",
        "advice": "General Advice"
    }
    facts = {"income_positive": True, "cashflow_deficit": True}
    winning, trace = ConsultantEngine.select_rule([rule_a, rule_b], facts)
    assert winning is not None
    assert winning.rule_id == "DEFICIT_WITH_DEBT"


# ==============================================================================
# 5. Bilingual Support Tests (English and Khmer)
# ==============================================================================

def test_bilingual_english_output(app):
    """Verifies that English conclusions and advice are returned when lang='en'."""
    with app.app_context():
        user_data = {
            "income": 1000.0,
            "expense": 500.0,
            "debt_status": "no debt",
            "employment_status": "employed",
        }
        res = ConsultantEngine.evaluate(user_data, lang="en")
        advice = res["selected_advice"]

        assert "Balanced Operating Budget" in advice.conclusion
        assert "emergency reserve" in advice.advice


def test_bilingual_khmer_output(app):
    """Verifies that Khmer conclusions and advice are returned when lang='km'."""
    with app.app_context():
        user_data = {
            "income": 1000.0,
            "expense": 500.0,
            "debt_status": "no debt",
            "employment_status": "employed",
        }
        res = ConsultantEngine.evaluate(user_data, lang="km")
        advice = res["selected_advice"]

        # Khmer translation for BALANCED_BUDGET_BUFFER_BUILDING
        assert "ថវិកាប្រតិបត្តិការមានតុល្យភាព" in advice.conclusion
        assert "ការចំណាយប្រចាំថ្ងៃរបស់អ្នកមានតុល្យភាពល្អ" in advice.advice


# ==============================================================================
# 6. Knowledge References & Domain Boundary Tests
# ==============================================================================

def test_knowledge_references_present(app):
    """Verifies that Step 7D rules contain valid knowledge citations (K001-K014)."""
    with app.app_context():
        user_data = {
            "income": 1000.0,
            "expense": 1200.0,
            "debt_status": "debt",
            "employment_status": "employed",
        }
        res = ConsultantEngine.evaluate(user_data, lang="en")
        advice = res["selected_advice"]

        assert "K001" in advice.knowledge_refs
        assert "K002" in advice.knowledge_refs
        assert "K014" in advice.knowledge_refs


# ==============================================================================
# 7. Step 7F Legacy Rule Isolation & Knowledge Base Activation Tests
# ==============================================================================

def test_legacy_rule_isolation(app):
    """
    Verifies that legacy rules (rule_id is NULL, kb_version is NULL, is_active is False)
    are strictly excluded from ConsultantEngine.evaluate().
    """
    with app.app_context():
        # Insert an inactive legacy rule
        legacy_rule = Rule(
            name="Legacy Untagged Rule",
            conclusion="Legacy Untagged",
            advice="Legacy Untagged Advice",
            priority=100,
            certainty=1.00,
            is_active=False,
            kb_version=None,
            rule_id=None
        )
        db.session.add(legacy_rule)
        db.session.commit()

        user_data = {
            "income": 1000.0,
            "expense": 500.0,
            "debt_status": "no debt",
            "employment_status": "employed",
        }
        res = ConsultantEngine.evaluate(user_data)
        assert res["selected_advice"].rule_id == "BALANCED_BUDGET_BUFFER_BUILDING"
        assert res["selected_advice"].kb_version == "financial-kb-v1.0"
        # Verify the legacy rule was never evaluated in audit_trace
        trace_ids = [t["rule_id"] for t in res["audit_trace"]]
        assert f"RULE_{legacy_rule.id}" not in trace_ids
        assert legacy_rule.name not in trace_ids


def test_active_legacy_rule_rejection(app):
    """
    CRITICAL DEFENSE-IN-DEPTH:
    Even if someone manually sets is_active=True on a legacy rule,
    ConsultantEngine.evaluate() and select_rule() MUST reject it because:
    1. rule_id is not in CANONICAL_RULE_IDS
    2. kb_version is not 'financial-kb-v1.0'
    """
    with app.app_context():
        # Insert an active legacy rule (someone manually activated it)
        manually_activated = Rule(
            name="Manually Activated Legacy Rule",
            conclusion="Legacy Intrusion",
            advice="Legacy Intrusion Advice",
            priority=100,  # Highest priority
            certainty=1.00,
            is_active=True,  # Set to True!
            kb_version=None, # Missing canonical kb_version
            rule_id=None     # Missing canonical rule_id
        )
        db.session.add(manually_activated)
        db.session.commit()

        user_data = {
            "income": 1000.0,
            "expense": 500.0,
            "debt_status": "no debt",
            "employment_status": "employed",
        }
        # 1. Evaluate should not load or select the activated legacy rule
        res = ConsultantEngine.evaluate(user_data)
        assert res["selected_advice"].rule_id == "BALANCED_BUDGET_BUFFER_BUILDING"
        assert res["selected_advice"].rule_id != f"RULE_{manually_activated.id}"

        # 2. Even direct call to select_rule with the legacy rule must reject it
        winning, trace = ConsultantEngine.select_rule([manually_activated], {"income_positive": True})
        assert winning is None


def test_synthetic_legacy_rule_with_higher_priority_rejected():
    """
    Verifies that a synthetic legacy rule with higher priority (100) and certainty (1.00)
    is rejected in favor of a canonical rule with lower priority (40).
    """
    legacy_rule = {
        "rule_id": "LEGACY_UNAUTHORIZED_HIGH_PRIORITY",
        "name": "Legacy High Priority",
        "priority": 100,
        "certainty": 1.00,
        "is_active": True,
        "kb_version": None,  # NOT canonical
        "conditions": [{"field": "income_positive", "operator": "==", "value": True}],
        "match_operator": "ALL",
        "conclusion": "Legacy Won",
        "advice": "Legacy Advice"
    }

    canonical_rule = {
        "rule_id": "BALANCED_BUDGET_BUFFER_BUILDING",
        "name": "Balanced Operating Budget",
        "priority": 40,
        "certainty": 0.85,
        "is_active": True,
        "kb_version": "financial-kb-v1.0",
        "conditions": [{"field": "income_positive", "operator": "==", "value": True}],
        "match_operator": "ALL",
        "conclusion": "Canonical Won",
        "advice": "Canonical Advice"
    }

    facts = {"income_positive": True}
    winning, trace = ConsultantEngine.select_rule([legacy_rule, canonical_rule], facts)

    assert winning is not None
    assert winning.rule_id == "BALANCED_BUDGET_BUFFER_BUILDING"
    assert winning.priority == 40
    assert winning.kb_version == "financial-kb-v1.0"


def test_canonical_rule_conflict_handling():
    """
    Verifies deterministic priority conflict resolution between two matching canonical rules.
    """
    rule_high = {
        "rule_id": "BREAK_EVEN_ZERO_MARGIN",
        "name": "Break Even",
        "priority": 80,
        "certainty": 1.00,
        "is_active": True,
        "kb_version": "financial-kb-v1.0",
        "conditions": [{"field": "income_positive", "operator": "==", "value": True}],
        "match_operator": "ALL",
        "conclusion": "Break Even",
        "advice": "Break Even Advice"
    }

    rule_low = {
        "rule_id": "BALANCED_BUDGET_BUFFER_BUILDING",
        "name": "Buffer Building",
        "priority": 40,
        "certainty": 0.85,
        "is_active": True,
        "kb_version": "financial-kb-v1.0",
        "conditions": [{"field": "income_positive", "operator": "==", "value": True}],
        "match_operator": "ALL",
        "conclusion": "Buffer Building",
        "advice": "Buffer Building Advice"
    }

    facts = {"income_positive": True}
    winning, trace = ConsultantEngine.select_rule([rule_low, rule_high], facts)

    assert winning is not None
    assert winning.rule_id == "BREAK_EVEN_ZERO_MARGIN"
    assert winning.priority == 80


def test_seed_idempotency(app):
    """
    Verifies that calling seed_financial_system() repeatedly:
    1. Does not create duplicate rules or facts
    2. Maintains exact active/inactive status
    3. Keeps canonical kb_version tags
    """
    with app.app_context():
        # Run seed multiple times
        seed_financial_system()
        seed_financial_system()
        seed_financial_system()

        canonical_rules = Rule.query.filter(Rule.rule_id.isnot(None)).all()
        assert len(canonical_rules) == 8
        for r in canonical_rules:
            assert r.is_active is True
            assert r.kb_version == "financial-kb-v1.0"

        canonical_facts = Fact.query.filter(Fact.fact_key.isnot(None)).all()
        assert len(canonical_facts) == 13
        for f in canonical_facts:
            assert f.kb_version == "financial-kb-v1.0"


def test_history_compatibility_and_kb_version_propagation(app):
    """
    Verifies:
    1. Existing history records without kb_version are readable (nullable compatibility).
    2. New consultant execution persists kb_version='financial-kb-v1.0'.
    """
    from app.models.history import History
    from app.models.user import User
    from app.services.history_services import HistoryServices

    with app.app_context():
        # 1. Insert legacy history record without kb_version
        legacy_hist = History(
            goal_cost=1000.0,
            income=2000.0,
            expense=1000.0,
            remain_percentage=50.0,
            expense_percentage=50.0,
            get_advice="Legacy advice string",
            get_conclusion="Legacy conclusion",
            get_certainty=0.8,
            kb_version=None  # Legacy record
        )
        db.session.add(legacy_hist)
        db.session.commit()

        # Read back legacy record
        fetched_legacy = db.session.get(History, legacy_hist.id)
        assert fetched_legacy is not None
        assert fetched_legacy.kb_version is None
        assert fetched_legacy.income == 2000.0

        # 2. Create a test user and generate new history record via advisor pipeline
        test_user = User(
            username="test_history_user",
            full_name="Test User",
            email="test_hist@example.com",
            password_hash="hashed_pw"
        )
        db.session.add(test_user)
        db.session.commit()

        user_data = {
            "income": 1000.0,
            "expense": 500.0,
            "debt_status": "no debt",
            "employment_status": "employed",
            "spending_habit": "average spend",
            "goal_cost": 5000.0,
        }
        advise_data = AdvisorServices.persoal_analyse(user_data)
        new_hist = HistoryServices.create(advise_data, test_user)

        assert new_hist.kb_version == "financial-kb-v1.0"
        assert new_hist.income == 1000.0
        assert "Balanced Operating Budget" in new_hist.get_conclusion


def test_canonical_fact_isolation(app):
    """
    Verifies that Fact.query for canonical facts returns only the 13 canonical facts
    tagged with financial-kb-v1.0, and legacy facts remain excluded.
    """
    with app.app_context():
        # Insert a legacy fact with kb_version=None
        legacy_fact = Fact(
            tags="legacy_test_tag",
            description="Legacy fact for testing",
            type="boolean",
            value=True,
            kb_version=None,
            fact_key=None
        )
        db.session.add(legacy_fact)
        db.session.commit()

        canonical_facts = Fact.query.filter(Fact.kb_version == "financial-kb-v1.0").all()
        assert len(canonical_facts) == 13
        for f in canonical_facts:
            assert f.fact_key is not None
            assert f.tags != "legacy_test_tag"


# ==============================================================================
# 8. Step 7G Explainable Decision Trace Tests
# ==============================================================================

def test_trace_contains_all_metrics(app):
    """Proves calculated financial metrics appear in the decision trace."""
    with app.app_context():
        user_data = {
            "income": 1000.0,
            "expense": 500.0,
            "debt_status": "no debt",
            "employment_status": "employed",
            "goal_cost": 5000.0,
        }
        res = ConsultantEngine.evaluate(user_data)
        trace = res["decision_trace"]

        assert "metrics" in trace
        metrics = trace["metrics"]
        assert metrics["monthly_income"] == 1000.0
        assert metrics["monthly_expense"] == 500.0
        assert metrics["net_cashflow"] == 500.0
        assert metrics["expense_ratio"] == 0.50
        assert metrics["surplus_ratio"] == 0.50
        assert metrics["natural_goal_months"] == 10.0


def test_trace_contains_derived_facts(app):
    """Proves derived consultant facts appear in the decision trace."""
    with app.app_context():
        user_data = {
            "income": 1000.0,
            "expense": 500.0,
            "debt_status": "no debt",
            "employment_status": "employed",
        }
        res = ConsultantEngine.evaluate(user_data)
        trace = res["decision_trace"]

        assert "derived_facts" in trace
        facts = trace["derived_facts"]
        assert facts["income_positive"] is True
        assert facts["income_zero"] is False
        assert facts["cashflow_surplus"] is True
        assert facts["cashflow_deficit"] is False
        assert facts["debt_present"] is False
        assert facts["debt_free"] is True
        assert facts["expense_tier_balanced"] is True


def test_trace_candidate_rules_are_canonical_only(app):
    """Proves that only the 8 canonical consultant rules are candidate rules in the trace."""
    from app.services.consultant_engine import CANONICAL_RULE_IDS

    with app.app_context():
        user_data = {
            "income": 1000.0,
            "expense": 500.0,
            "debt_status": "no debt",
            "employment_status": "employed",
        }
        res = ConsultantEngine.evaluate(user_data)
        trace = res["decision_trace"]

        assert "candidate_rules" in trace
        assert len(trace["candidate_rules"]) == 8
        for r_id in trace["candidate_rules"]:
            assert r_id in CANONICAL_RULE_IDS


def test_trace_condition_evaluations_expose_actual_vs_expected(app):
    """Proves every evaluated condition exposes fact_key, operator, expected_value, actual_value, and matched."""
    with app.app_context():
        user_data = {
            "income": 1000.0,
            "expense": 500.0,
            "debt_status": "no debt",
            "employment_status": "employed",
        }
        res = ConsultantEngine.evaluate(user_data)
        trace = res["decision_trace"]

        assert "rule_evaluations" in trace
        for rule_eval in trace["rule_evaluations"]:
            assert "condition_results" in rule_eval
            for c in rule_eval["condition_results"]:
                assert "fact_key" in c
                assert "operator" in c
                assert "expected_value" in c
                assert "actual_value" in c
                assert "matched" in c
                assert isinstance(c["matched"], bool)


def test_trace_matched_and_rejected_rules_marked_correctly(app):
    """Proves matched rules are marked matched=True and rejected rules matched=False."""
    with app.app_context():
        user_data = {
            "income": 1000.0,
            "expense": 500.0,
            "debt_status": "no debt",
            "employment_status": "employed",
        }
        res = ConsultantEngine.evaluate(user_data)
        trace = res["decision_trace"]

        matched_rules = [r for r in trace["rule_evaluations"] if r["matched"]]
        rejected_rules = [r for r in trace["rule_evaluations"] if not r["matched"]]

        assert len(matched_rules) >= 1
        assert len(rejected_rules) >= 1

        matched_ids = [r["rule_id"] for r in matched_rules]
        assert "BALANCED_BUDGET_BUFFER_BUILDING" in matched_ids

        rejected_ids = [r["rule_id"] for r in rejected_rules]
        assert "DEFICIT_WITH_DEBT" in rejected_ids
        assert "BREAK_EVEN_ZERO_MARGIN" in rejected_ids


def test_trace_rejected_rules_contain_factual_failure_reasons(app):
    """Proves rejected rules contain factual deterministic failure reasons explaining what failed."""
    with app.app_context():
        user_data = {
            "income": 1000.0,
            "expense": 500.0,
            "debt_status": "no debt",
            "employment_status": "employed",
        }
        res = ConsultantEngine.evaluate(user_data)
        trace = res["decision_trace"]

        deficit_eval = next(r for r in trace["rule_evaluations"] if r["rule_id"] == "DEFICIT_WITH_DEBT")
        assert deficit_eval["matched"] is False
        assert deficit_eval["failure_reason"] is not None
        assert "net_cashflow < 0 was false" in deficit_eval["failure_reason"]
        assert "actual: 500.0" in deficit_eval["failure_reason"]

        break_even_eval = next(r for r in trace["rule_evaluations"] if r["rule_id"] == "BREAK_EVEN_ZERO_MARGIN")
        assert break_even_eval["matched"] is False
        assert "net_cashflow == 0 was false" in break_even_eval["failure_reason"]


def test_trace_selected_rule_and_deterministic_selection_reason(app):
    """Proves selected rule is included and selection reason reflects priority/specificity without subjective words."""
    with app.app_context():
        user_data = {
            "income": 1000.0,
            "expense": 900.0,
            "debt_status": "no debt",
            "employment_status": "employed",
        }
        res = ConsultantEngine.evaluate(user_data)
        trace = res["decision_trace"]

        assert trace["selected_rule"] == "TIGHT_MARGIN_HIGH_EXPENSE"
        reason = trace["selection_reason"]
        assert "Matched canonical rule" in reason
        assert "Priority = 80" in reason
        assert "Specificity = 3 conditions" in reason

        # Ensure no subjective phrasing
        for forbidden in ["best advice", "smartest rule", "most suitable", "ai decided", "intelligent"]:
            assert forbidden not in reason.lower()


def test_trace_superseded_rule_explains_priority_resolution():
    """
    Proves that when two rules match conditions, the losing rule's failure_reason
    states it was superseded by the higher-priority rule.
    """
    rule_high = {
        "rule_id": "BREAK_EVEN_ZERO_MARGIN",
        "name": "Break Even",
        "priority": 80,
        "certainty": 1.00,
        "is_active": True,
        "kb_version": "financial-kb-v1.0",
        "conditions": [{"field": "income_positive", "operator": "==", "value": True}],
        "match_operator": "ALL",
        "conclusion": "Break Even",
        "advice": "Advice"
    }

    rule_low = {
        "rule_id": "BALANCED_BUDGET_BUFFER_BUILDING",
        "name": "Buffer Building",
        "priority": 40,
        "certainty": 0.85,
        "is_active": True,
        "kb_version": "financial-kb-v1.0",
        "conditions": [{"field": "income_positive", "operator": "==", "value": True}],
        "match_operator": "ALL",
        "conclusion": "Buffer Building",
        "advice": "Advice"
    }

    facts = {"income_positive": True}
    winning, evaluations = ConsultantEngine.select_rule([rule_low, rule_high], facts)

    assert winning.rule_id == "BREAK_EVEN_ZERO_MARGIN"
    winning_eval = next(r for r in evaluations if r["rule_id"] == "BREAK_EVEN_ZERO_MARGIN")
    assert winning_eval["failure_reason"] is None

    losing_eval = next(r for r in evaluations if r["rule_id"] == "BALANCED_BUDGET_BUFFER_BUILDING")
    assert losing_eval["matched"] is True
    assert "superseded by higher-priority rule BREAK_EVEN_ZERO_MARGIN" in losing_eval["failure_reason"]
    assert "priority 80 > 40" in losing_eval["failure_reason"]


def test_trace_certainty_does_not_affect_selection_reason():
    """Proves that certainty is metadata only and does not influence selection or selection_reason."""
    rule_low_cert = {
        "rule_id": "DEFICIT_WITH_DEBT",
        "name": "Deficit With Debt",
        "priority": 100,
        "certainty": 0.10,  # Very low certainty!
        "is_active": True,
        "kb_version": "financial-kb-v1.0",
        "conditions": [{"field": "income_positive", "operator": "==", "value": True}],
        "match_operator": "ALL",
        "conclusion": "Deficit Won",
        "advice": "Advice"
    }

    rule_high_cert = {
        "rule_id": "DEFICIT_NO_DEBT",
        "name": "Deficit No Debt",
        "priority": 50,
        "certainty": 0.99,  # Very high certainty!
        "is_active": True,
        "kb_version": "financial-kb-v1.0",
        "conditions": [{"field": "income_positive", "operator": "==", "value": True}],
        "match_operator": "ALL",
        "conclusion": "Deficit No Debt",
        "advice": "Advice"
    }

    facts = {"income_positive": True}
    winning, evaluations = ConsultantEngine.select_rule([rule_low_cert, rule_high_cert], facts)

    assert winning.rule_id == "DEFICIT_WITH_DEBT"
    assert winning.priority == 100
    assert "Priority = 100" in winning.selection_reason
    assert "0.10" not in winning.selection_reason


def test_trace_bilingual_conclusion_and_advice(app):
    """Proves bilingual conclusion and advice remain populated in the decision trace."""
    with app.app_context():
        user_data = {
            "income": 1000.0,
            "expense": 500.0,
            "debt_status": "no debt",
            "employment_status": "employed",
        }
        res = ConsultantEngine.evaluate(user_data)
        trace = res["decision_trace"]

        assert trace["conclusion_en"] == "Balanced Operating Budget"
        assert trace["conclusion_km"] == "ថវិកាប្រតិបត្តិការមានតុល្យភាព"
        assert "emergency reserve" in trace["advice_en"]
        assert "ការចំណាយប្រចាំថ្ងៃរបស់អ្នកមានតុល្យភាពល្អ" in trace["advice_km"]


def test_trace_kb_version_propagation(app):
    """Proves financial-kb-v1.0 is propagated in the decision trace."""
    with app.app_context():
        user_data = {
            "income": 1000.0,
            "expense": 500.0,
            "debt_status": "no debt",
            "employment_status": "employed",
        }
        res = ConsultantEngine.evaluate(user_data)
        trace = res["decision_trace"]

        assert trace["knowledge_base_version"] == "financial-kb-v1.0"


def test_trace_manually_activated_legacy_rules_excluded(app):
    """Proves manually activated legacy rules never appear as candidate rules in the decision trace."""
    with app.app_context():
        # Insert a legacy rule with is_active=True
        intruder = Rule(
            name="Intruder Legacy Rule",
            conclusion="Intruder",
            advice="Intruder Advice",
            priority=100,
            certainty=1.00,
            is_active=True,   # Manually set to True!
            kb_version=None,  # Missing canonical kb_version
            rule_id=None      # Missing canonical rule_id
        )
        db.session.add(intruder)
        db.session.commit()

        user_data = {
            "income": 1000.0,
            "expense": 500.0,
            "debt_status": "no debt",
            "employment_status": "employed",
        }
        res = ConsultantEngine.evaluate(user_data)
        trace = res["decision_trace"]

        assert f"RULE_{intruder.id}" not in trace["candidate_rules"]
        eval_rule_ids = [r["rule_id"] for r in trace["rule_evaluations"]]
        assert f"RULE_{intruder.id}" not in eval_rule_ids
        assert intruder.name not in eval_rule_ids


def test_trace_exposed_via_advisor_services(app):
    """Proves AdvisorServices exposes the complete decision_trace in its return dicts."""
    with app.app_context():
        user_data = {
            "income": 1000.0,
            "expense": 500.0,
            "debt_status": "no debt",
            "employment_status": "employed",
            "spending_habit": "average spend",
            "goal_cost": 5000.0,
        }
        # 1. persoal_analyse
        pa_res = AdvisorServices.persoal_analyse(user_data)
        assert "decision_trace" in pa_res
        assert pa_res["decision_trace"]["selected_rule"] == "BALANCED_BUDGET_BUFFER_BUILDING"

        # 2. get_advise
        ga_res = AdvisorServices.get_advise(user_data)
        assert "decision_trace" in ga_res
        assert ga_res["decision_trace"]["selected_rule"] == "BALANCED_BUDGET_BUFFER_BUILDING"

        # 3. get_decision_trace
        direct_trace = AdvisorServices.get_decision_trace(user_data)
        assert direct_trace["knowledge_base_version"] == "financial-kb-v1.0"
        assert direct_trace["selected_rule"] == "BALANCED_BUDGET_BUFFER_BUILDING"


def test_trace_fallback_explanation_deterministic():
    """Proves deterministic explanation is provided when fallback is activated."""
    facts = {
        "monthly_income": 0.0,
        "monthly_expense": 500.0,
        "net_cashflow": -500.0,
        "expense_ratio": None,
        "surplus_ratio": None,
        "goal_cost": 0.0,
        "employment_status": "not employed",
        "debt_status": "no debt",
        "spending_habit": "average spend",
        "marital_status": "Single",
        "debt_present": False
    }
    user_data = {"income": 0.0, "expense": 500.0}
    # Pass empty rules list to trigger fallback
    res = ConsultantEngine.evaluate(user_data, rules=[])
    trace = res["decision_trace"]

    assert trace["selected_rule"] == "FALLBACK_DEFICIT"
    assert "Default deterministic financial triage fallback activated" in trace["selection_reason"]

