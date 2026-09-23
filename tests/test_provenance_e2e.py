"""
End-to-End Audit & Hardening Regression Test Suite for Provenance Boundary Layer (Step 8I).

Covers all 15 audit verification requirements:
1. Explicit debt (debt_status='debt' remains explicit, not defaulted_legacy)
2. Explicit no debt (debt_status='no debt' remains explicit, not unknown)
3. Missing debt (unmentioned debt remains unknown, engine receives defaulted_legacy, decision_used_defaulted_field=True)
4. Explicit employment ('employed' / 'not employed' remains explicit)
5. Missing employment (unmentioned employment remains unknown, engine receives defaulted_legacy)
6. Zero income (explicit 0.0 remains valid, numeric, and explicit)
7. Missing income (remains null/unknown, never converted to 0.0, fails API validation as required)
8. Third-party income (spouse/partner income not silently assigned as user's explicit income)
9. Conflicting input (conflicting income or debt kept unknown, not silently resolved)
10. API provenance structure (authoritative schema validation)
11. Frontend/API compatibility (form-encoded and JSON requests work consistently)
12. Engine decision authority (PABL does not select rules; engine is sole authority)
13. No Phase-1 inferred values (inferred remains disabled in Phase 1)
14. Legacy HTML compatibility (AdvisorServices.get_advise returns legacy keys + provenance)
15. Protected-field tampering (client cannot override rule_id, priority, certainty, kb_version)
"""

import pytest
from app.services.provenance_boundary import (
    ProvenanceBoundaryLayer,
    ProvenanceState,
    BoundaryContext,
    SlotProvenance,
)
from app.services.advisor_services import AdvisorServices
from app.services.consultant_engine import ConsultantEngine, CANONICAL_KB_VERSION
from app.security.seed_rule_facts import CONSULTANT_RULES, seed_financial_system
from app import create_app
from extension import db
from config import Config
from sqlalchemy.pool import StaticPool


class E2EAuditTestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool,
    }
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-pabl-e2e-secret"


@pytest.fixture(name="app")
def fixture_app():
    app = create_app(E2EAuditTestConfig)
    with app.app_context():
        db.create_all()
        seed_financial_system()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture(name="client")
def fixture_client(app):
    return app.test_client()


@pytest.fixture(scope="module")
def standalone_rules():
    return [dict(r, kb_version=CANONICAL_KB_VERSION) for r in CONSULTANT_RULES]


# ==============================================================================
# 1. Case A — Explicit Debt
# ==============================================================================

def test_e2e_case_a_explicit_debt(client):
    """
    Case A: Input has explicit debt='debt'.
    Verify: debt_status provenance = explicit, is_defaulted = False, rule = SURPLUS_WITH_DEBT_SERVICING.
    """
    payload = {
        "monthly_income": 2000,
        "monthly_expense": 1500,
        "employment_status": "employed",
        "debt_status": "debt",
        "spending_habit": "average spend",
        "goal_cost": 0,
        "marital_status": "Single",
        "language": "en"
    }
    res = client.post("/api/consult", json=payload)
    assert res.status_code == 200
    data = res.get_json()

    # Provenance audit
    debt_slot = data["provenance"]["fields"]["debt_status"]
    assert debt_slot["provenance"] == "explicit"
    assert debt_slot["value"] == "debt"
    assert debt_slot["is_defaulted"] is False
    assert debt_slot["engine_state"] == "explicit"
    assert "debt_status" in data["provenance"]["explicit_fields"]
    assert "debt_status" not in data["provenance"]["defaulted_fields"]

    # Decision audit
    assert data["decision"]["rule_id"] == "SURPLUS_WITH_DEBT_SERVICING"


# ==============================================================================
# 2. Case B — Explicit No Debt
# ==============================================================================

def test_e2e_case_b_explicit_no_debt(client):
    """
    Case B: Input has explicit debt='no debt'.
    Verify: debt_status provenance = explicit, NOT unknown, NOT defaulted_legacy.
    """
    payload = {
        "monthly_income": 2000,
        "monthly_expense": 1500,
        "employment_status": "employed",
        "debt_status": "no debt",
        "spending_habit": "average spend",
        "goal_cost": 0,
        "marital_status": "Single",
        "language": "en"
    }
    res = client.post("/api/consult", json=payload)
    assert res.status_code == 200
    data = res.get_json()

    debt_slot = data["provenance"]["fields"]["debt_status"]
    assert debt_slot["provenance"] == "explicit"
    assert debt_slot["value"] == "no debt"
    assert debt_slot["is_defaulted"] is False
    assert "debt_status" not in data["provenance"]["unknown_fields"]
    assert "debt_status" not in data["provenance"]["defaulted_fields"]
    assert "debt_status" in data["provenance"]["explicit_fields"]


# ==============================================================================
# 3. Case C — Missing Debt
# ==============================================================================

def test_e2e_case_c_missing_debt(client):
    """
    Case C: Debt is omitted completely.
    Verify: original value remains null, provenance says unknown, engine receives legacy default,
    API does not claim user said 'no debt', decision_used_defaulted_field is True.
    """
    payload = {
        "monthly_income": 2000,
        "monthly_expense": 1500,
        "employment_status": "employed",
        "spending_habit": "average spend",
        "goal_cost": 0,
        "marital_status": "Single",
        "language": "en"
    }
    res = client.post("/api/consult", json=payload)
    assert res.status_code == 200
    data = res.get_json()

    debt_slot = data["provenance"]["fields"]["debt_status"]
    assert debt_slot["value"] is None
    assert debt_slot["original_value"] is None
    assert debt_slot["provenance"] == "unknown"
    assert debt_slot["engine_state"] == "defaulted_legacy"
    assert debt_slot["legacy_default"] == "no debt"
    assert debt_slot["is_defaulted"] is True

    # Audit list membership
    assert "debt_status" in data["provenance"]["unknown_fields"]
    assert "debt_status" in data["provenance"]["defaulted_fields"]
    assert "debt_status" not in data["provenance"]["explicit_fields"]

    # Rule selection used defaulted field
    assert data["provenance"]["decision_used_defaulted_field"] is True

    # Advisory caveat present
    assert any("zero active debt" in c.lower() for c in data["advisory_caveats"])


# ==============================================================================
# 4. Case D — Explicit Unemployment
# ==============================================================================

def test_e2e_case_d_explicit_unemployment(client):
    """
    Case D: Explicit employment_status='not employed'.
    Verify: provenance = explicit, value = 'not employed'.
    """
    payload = {
        "monthly_income": 0,
        "monthly_expense": 0,
        "employment_status": "not employed",
        "debt_status": "no debt"
    }
    res = client.post("/api/consult", json=payload)
    assert res.status_code == 200
    data = res.get_json()

    emp_slot = data["provenance"]["fields"]["employment_status"]
    assert emp_slot["provenance"] == "explicit"
    assert emp_slot["value"] == "not employed"
    assert emp_slot["is_defaulted"] is False
    assert "employment_status" in data["provenance"]["explicit_fields"]
    assert data["decision"]["rule_id"] == "INCOME_ZERO_UNEMPLOYED"


# ==============================================================================
# 5. Case E — Missing Employment
# ==============================================================================

def test_e2e_case_e_missing_employment(client):
    """
    Case E: Employment status omitted.
    Verify: value = null, provenance = unknown, engine_state = defaulted_legacy.
    User is not represented as explicitly unemployed.
    """
    payload = {
        "monthly_income": 3000,
        "monthly_expense": 1800,
        "debt_status": "no debt"
    }
    res = client.post("/api/consult", json=payload)
    assert res.status_code == 200
    data = res.get_json()

    emp_slot = data["provenance"]["fields"]["employment_status"]
    assert emp_slot["value"] is None
    assert emp_slot["provenance"] == "unknown"
    assert emp_slot["engine_state"] == "defaulted_legacy"
    assert emp_slot["is_defaulted"] is True
    assert "employment_status" in data["provenance"]["defaulted_fields"]
    assert "employment_status" not in data["provenance"]["explicit_fields"]


# ==============================================================================
# 6. Case F — Zero versus Missing Income
# ==============================================================================

def test_e2e_case_f_zero_income_preserved(client):
    """
    Case F.1: Explicit zero income.
    Verify: value=0.0, provenance=explicit, is_defaulted=False.
    """
    payload = {
        "monthly_income": 0,
        "monthly_expense": 500,
        "debt_status": "no debt"
    }
    res = client.post("/api/consult", json=payload)
    assert res.status_code == 200
    data = res.get_json()

    inc_slot = data["provenance"]["fields"]["monthly_income"]
    assert inc_slot["value"] == 0.0
    assert inc_slot["provenance"] == "explicit"
    assert inc_slot["is_defaulted"] is False


def test_e2e_case_f_missing_income_rejected(client):
    """
    Case F.2: Missing income.
    Verify: boundary tags missing income as unknown (not 0.0); API rejects with 400.
    """
    # Direct boundary check
    raw = {"monthly_expense": 500.0}
    ctx = ProvenanceBoundaryLayer.process(raw)
    assert ctx.fields["monthly_income"].value is None
    assert ctx.fields["monthly_income"].provenance == "unknown"
    assert ctx.fields["monthly_income"].value != 0.0

    # API boundary check
    res = client.post("/api/consult", json=raw)
    assert res.status_code == 400
    data = res.get_json()
    assert data["success"] is False
    assert "monthly_income" in data["error"]["fields"]


# ==============================================================================
# 7. Case G — Third-Party Income Protection
# ==============================================================================

def test_e2e_case_g_third_party_income_not_assigned_to_user():
    """
    Case G: Input represents third-party / spouse / partner income.
    Verify: system does NOT silently assign spouse's income to user's monthly_income.
    """
    # Test variant 1: spouse_income explicitly provided without user income
    raw1 = {
        "spouse_income": 3000.0,
        "monthly_expense": 1200.0,
        "debt_status": "no debt"
    }
    ctx1 = ProvenanceBoundaryLayer.process(raw1)
    assert ctx1.fields["monthly_income"].value is None
    assert ctx1.fields["monthly_income"].provenance == "unknown"
    assert "monthly_income" not in ctx1.explicit_fields

    # Test variant 2: metadata indicates entity is third-party
    raw2 = {
        "monthly_income": 3000.0,
        "monthly_expense": 1200.0,
        "metadata": {"is_third_party": True, "subject": "spouse"}
    }
    ctx2 = ProvenanceBoundaryLayer.process(raw2)
    assert ctx2.fields["monthly_income"].value is None
    assert ctx2.fields["monthly_income"].provenance == "unknown"
    assert "monthly_income" not in ctx2.explicit_fields


# ==============================================================================
# 8. Case H — Conflicting Information
# ==============================================================================

def test_e2e_case_h_conflicting_income_inputs():
    """
    Case H.1: User provides conflicting income statements (e.g. 2000 vs 1500).
    Verify: PABL does NOT silently resolve the conflict into a certain value;
    value remains None and provenance=unknown with conflict metadata.
    """
    raw = {
        "income": 2000.0,
        "monthly_income": 1500.0,
        "monthly_expense": 1000.0
    }
    ctx = ProvenanceBoundaryLayer.process(raw)

    inc_slot = ctx.fields["monthly_income"]
    assert inc_slot.value is None
    assert inc_slot.provenance == "unknown"
    assert inc_slot.source == "conflicting_inputs"
    assert ctx.conflicts_present is True
    assert any(c["field"] == "monthly_income" for c in ctx.conflicts)


def test_e2e_case_h_conflicting_debt_inputs():
    """
    Case H.2: Conflicting debt inputs (debt_status='debt' vs is_debt='no debt').
    Verify: kept unknown with conflict caveat, not resolved with false certainty.
    """
    raw = {
        "monthly_income": 3000.0,
        "monthly_expense": 1800.0,
        "debt_status": "debt",
        "is_debt": "no debt"
    }
    ctx = ProvenanceBoundaryLayer.process(raw)

    debt_slot = ctx.fields["debt_status"]
    assert debt_slot.value is None
    assert debt_slot.provenance == "unknown"
    assert debt_slot.source == "conflicting_inputs"
    assert ctx.conflicts_present is True
    assert any(c["field"] == "debt_status" for c in ctx.conflicts)


# ==============================================================================
# 9. API Truthfulness & Provenance Schema Conformance
# ==============================================================================

def test_e2e_api_truthfulness_and_schema(client):
    """
    Requirement 3 & 10: Inspect /api/consult response to verify complete provenance structure.
    """
    payload = {
        "monthly_income": 3000.0,
        "monthly_expense": 1800.0,
        "debt_status": None,
        "employment_status": "employed",
        "language": "en"
    }
    res = client.post("/api/consult", json=payload)
    assert res.status_code == 200
    data = res.get_json()

    prov = data["provenance"]
    assert "fields" in prov
    assert "explicit_fields" in prov
    assert "unknown_fields" in prov
    assert "defaulted_fields" in prov
    assert "assumptions_present" in prov
    assert "assumptions" in prov
    assert "conflicts_present" in prov
    assert "conflicts" in prov
    assert "decision_used_defaulted_field" in prov
    assert "advisory_caveats" in prov

    # Inferred must NOT be used in Phase 1
    for f, sp in prov["fields"].items():
        assert sp["provenance"] != "inferred"


# ==============================================================================
# 10. Engine Decision Authority
# ==============================================================================

def test_e2e_engine_decision_authority(client):
    """
    Requirement 12: Prove that PABL does NOT become an alternate rule engine.
    ConsultantEngine remains the sole decision authority.
    """
    payload = {
        "monthly_income": 1000.0,
        "monthly_expense": 900.0,
        "debt_status": "no debt"
    }
    res = client.post("/api/consult", json=payload)
    assert res.status_code == 200
    data = res.get_json()

    # Winning rule is selected strictly by ConsultantEngine hierarchy
    assert data["decision"]["rule_id"] == "TIGHT_MARGIN_HIGH_EXPENSE"
    assert data["decision"]["priority"] == 80
    assert data["decision"]["certainty"] == 0.70
    assert data["knowledge_base_version"] == CANONICAL_KB_VERSION


# ==============================================================================
# 11. Protected-Field Tampering Immunity
# ==============================================================================

def test_e2e_protected_field_tampering_immunity(client):
    """
    Requirement 15: Client attempts to inject fake rule_id, priority, certainty, or kb_version.
    Verify: ConsultantEngine ignores all client overrides and evaluates objectively.
    """
    payload = {
        "monthly_income": 1000.0,
        "monthly_expense": 900.0,
        "debt_status": "no debt",
        "rule_id": "FAKE_RULE_OVERRIDE",
        "priority": 999,
        "certainty": 1.0,
        "knowledge_base_version": "kb-hacked-v99",
        "is_active": False
    }
    res = client.post("/api/consult", json=payload)
    assert res.status_code == 200
    data = res.get_json()

    # Must ignore client injection
    assert data["decision"]["rule_id"] == "TIGHT_MARGIN_HIGH_EXPENSE"
    assert data["decision"]["priority"] == 80
    assert data["knowledge_base_version"] == CANONICAL_KB_VERSION


# ==============================================================================
# 12. Frontend & Legacy HTML Compatibility
# ==============================================================================

def test_e2e_legacy_html_service_compatibility(app):
    """
    Requirement 14: AdvisorServices.get_advise() used by HTML templates returns
    both legacy keys (get_advice, metrics, facts) AND enriched provenance.
    """
    with app.app_context():
        data = {
            "goal_cost": 1000.0,
            "income": 3000.0,
            "expense": 1800.0,
            "martial_status": "Single",
            "is_employed": "employed",
            "is_debt": "no debt",
            "is_spending": "average spend"
        }
        res = AdvisorServices.get_advise(data)

        # Legacy keys
        assert "get_advice" in res
        assert "metrics" in res
        assert "facts" in res
        assert "kb_version" in res
        assert res["get_advice"].rule_id == "BALANCED_BUDGET_BUFFER_BUILDING"

        # Enriched provenance
        assert "provenance" in res
        assert "advisory_caveats" in res


def test_e2e_form_encoded_post_compatibility(client):
    """
    Requirement 11: Form-encoded POST to /evaluate works seamlessly with PABL.
    """
    form_data = {
        "monthly_income": "3000",
        "monthly_expense": "1800",
        "debt_status": "no debt"
    }
    res = client.post("/evaluate", data=form_data)
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["decision"]["rule_id"] == "BALANCED_BUDGET_BUFFER_BUILDING"
    assert "provenance" in data


# ==============================================================================
# 13. Phase-1 Inferred Limitation Proof
# ==============================================================================

def test_e2e_phase1_inferred_limitation():
    """
    Requirement 13: Phase 1 strictly forbids automatic 'inferred' provenance.
    """
    raw = {
        "monthly_income": 5000.0,
        "monthly_expense": 2000.0
    }
    ctx = ProvenanceBoundaryLayer.process(raw)
    for field_name, sp in ctx.fields.items():
        assert sp.provenance != ProvenanceState.INFERRED
        assert sp.provenance in (ProvenanceState.EXPLICIT, ProvenanceState.UNKNOWN)
