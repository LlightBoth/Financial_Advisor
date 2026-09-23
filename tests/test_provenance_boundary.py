"""
Focused Regression Tests for Provenance-Aware Boundary Layer (PABL) - Step 8H.

Verifies and proves:
1. Explicit debt: 'debt' remains explicit.
2. Explicit no debt: 'no debt' remains explicit.
3. Missing debt: remains unknown in provenance even if engine receives legacy default.
4. Explicit employed: 'employed' remains explicit.
5. Explicit not employed: 'not employed' remains explicit.
6. Missing employment: remains unknown in provenance even if legacy default is used.
7. Explicit zero income: remains numeric zero and explicit when source metadata supports it.
8. Missing income: remains null/unknown and is never converted to zero.
9. Third-party income: is not incorrectly marked as user's explicit income.
10. Existing HTML/API compatibility: existing endpoints return expected structures.
11. Deterministic engine authority: NLU/provenance layer does not select rules directly.
12. No financial decision changes: complete-input cases continue selecting same canonical rules.
13. No silent inferred values: Phase 1 does not mark unknown values as inferred.
14. Structured output schema: validates fields, explicit_fields, unknown_fields, defaulted_fields, assumptions.
15. Advisory caveats: structured metadata generated when defaulted fields are evaluated.
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
from app.services.consultant_validator import ConsultantInputValidator
from app.security.seed_rule_facts import CONSULTANT_RULES, seed_financial_system
from app import create_app
from extension import db
from config import Config
from sqlalchemy.pool import StaticPool


class BoundaryTestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool,
    }
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-pabl-secret"


@pytest.fixture(name="app")
def fixture_app():
    app = create_app(BoundaryTestConfig)
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
# Requirement 1 & 2: Explicit Debt ("debt" vs "no debt")
# ==============================================================================

def test_pabl_explicit_debt_remains_explicit():
    """Requirement 1: Proves that explicit 'debt' is marked as explicit with value 'debt'."""
    raw = {"monthly_income": 3000.0, "monthly_expense": 1800.0, "debt_status": "debt"}
    ctx = ProvenanceBoundaryLayer.process(raw)

    sp = ctx.fields["debt_status"]
    assert sp.provenance == ProvenanceState.EXPLICIT
    assert sp.value == "debt"
    assert sp.is_explicit is True
    assert sp.is_unknown is False
    assert "debt_status" in ctx.explicit_fields
    assert "debt_status" not in ctx.defaulted_fields
    assert ctx.legacy_payload["debt_status"] == "debt"


def test_pabl_explicit_no_debt_remains_explicit():
    """Requirement 2: Proves that explicit 'no debt' is marked as explicit with value 'no debt'."""
    raw = {"monthly_income": 3000.0, "monthly_expense": 1800.0, "debt_status": "no debt"}
    ctx = ProvenanceBoundaryLayer.process(raw)

    sp = ctx.fields["debt_status"]
    assert sp.provenance == ProvenanceState.EXPLICIT
    assert sp.value == "no debt"
    assert sp.is_explicit is True
    assert sp.is_unknown is False
    assert "debt_status" in ctx.explicit_fields
    assert "debt_status" not in ctx.defaulted_fields
    assert ctx.legacy_payload["debt_status"] == "no debt"


# ==============================================================================
# Requirement 3: Missing Debt (Unknown in Provenance, Defaulted in Legacy)
# ==============================================================================

def test_pabl_missing_debt_remains_unknown_with_legacy_default():
    """
    Requirement 3: Proves that missing debt remains value=None and provenance='unknown',
    while legacy_payload receives 'no debt' marked as a defaulted legacy field.
    """
    raw = {"monthly_income": 3000.0, "monthly_expense": 1800.0, "debt_status": None}
    ctx = ProvenanceBoundaryLayer.process(raw)

    sp = ctx.fields["debt_status"]
    assert sp.provenance == ProvenanceState.UNKNOWN
    assert sp.value is None
    assert sp.is_unknown is True
    assert sp.is_explicit is False
    assert sp.legacy_default == "no debt"

    # Present in unknown and defaulted lists
    assert "debt_status" in ctx.unknown_fields
    assert "debt_status" in ctx.defaulted_fields
    assert "debt_status" not in ctx.explicit_fields

    # Legacy engine receives required default
    assert ctx.legacy_payload["debt_status"] == "no debt"

    # Assumptions indicate debt assumption
    assert ctx.assumptions_present is True
    debt_assumptions = [a for a in ctx.assumptions if a["field"] == "debt_status"]
    assert len(debt_assumptions) == 1
    assert debt_assumptions[0]["assumed_value"] == "no debt"


# ==============================================================================
# Requirement 4 & 5: Explicit Employment ("employed" vs "not employed")
# ==============================================================================

def test_pabl_explicit_employed_remains_explicit():
    """Requirement 4: Proves that explicit 'employed' is marked as explicit."""
    raw = {"monthly_income": 2000.0, "monthly_expense": 1500.0, "employment_status": "employed"}
    ctx = ProvenanceBoundaryLayer.process(raw)

    sp = ctx.fields["employment_status"]
    assert sp.provenance == ProvenanceState.EXPLICIT
    assert sp.value == "employed"
    assert sp.is_explicit is True
    assert "employment_status" in ctx.explicit_fields
    assert "employment_status" not in ctx.defaulted_fields


def test_pabl_explicit_not_employed_remains_explicit():
    """Requirement 5: Proves that explicit 'not employed' is marked as explicit."""
    raw = {"monthly_income": 0.0, "monthly_expense": 0.0, "employment_status": "not employed"}
    ctx = ProvenanceBoundaryLayer.process(raw)

    sp = ctx.fields["employment_status"]
    assert sp.provenance == ProvenanceState.EXPLICIT
    assert sp.value == "not employed"
    assert sp.is_explicit is True
    assert "employment_status" in ctx.explicit_fields
    assert "employment_status" not in ctx.defaulted_fields


# ==============================================================================
# Requirement 6: Missing Employment (Unknown in Provenance, Defaulted in Legacy)
# ==============================================================================

def test_pabl_missing_employment_remains_unknown_with_legacy_default():
    """
    Requirement 6: Proves that missing employment remains value=None and provenance='unknown',
    while legacy payload receives 'not employed'.
    """
    raw = {"monthly_income": 3000.0, "monthly_expense": 1800.0}
    ctx = ProvenanceBoundaryLayer.process(raw)

    sp = ctx.fields["employment_status"]
    assert sp.provenance == ProvenanceState.UNKNOWN
    assert sp.value is None
    assert sp.legacy_default == "not employed"
    assert "employment_status" in ctx.unknown_fields
    assert "employment_status" in ctx.defaulted_fields
    assert ctx.legacy_payload["employment_status"] == "not employed"


# ==============================================================================
# Requirement 7 & 8: Income Semantics (Explicit Zero vs Missing/Unknown)
# ==============================================================================

def test_pabl_explicit_zero_income_preserved():
    """Requirement 7: Proves that explicit zero income remains numeric 0.0 and explicit."""
    raw = {"monthly_income": 0.0, "monthly_expense": 500.0}
    ctx = ProvenanceBoundaryLayer.process(raw)

    sp = ctx.fields["monthly_income"]
    assert sp.provenance == ProvenanceState.EXPLICIT
    assert sp.value == 0.0
    assert isinstance(sp.value, float)
    assert sp.is_explicit is True
    assert "monthly_income" in ctx.explicit_fields
    assert "monthly_income" not in ctx.unknown_fields


def test_pabl_missing_income_remains_null_and_unknown():
    """Requirement 8: Proves that missing income is null/unknown and NEVER converted to zero."""
    raw = {"monthly_expense": 500.0}
    ctx = ProvenanceBoundaryLayer.process(raw)

    sp = ctx.fields["monthly_income"]
    assert sp.provenance == ProvenanceState.UNKNOWN
    assert sp.value is None
    assert sp.value != 0.0
    assert sp.is_unknown is True
    assert "monthly_income" in ctx.unknown_fields


# ==============================================================================
# Requirement 9: Third-Party Income Protection
# ==============================================================================

def test_pabl_third_party_income_not_assigned_as_user_explicit_income():
    """
    Requirement 9: Proves that income explicitly attributed to a third party or partner
    is NOT assigned as the user's explicit income.
    """
    raw = {
        "monthly_income": None,
        "third_party_income": 5000.0,
        "monthly_expense": 1500.0,
        "metadata": {"is_third_party": True},
    }
    ctx = ProvenanceBoundaryLayer.process(raw)

    sp = ctx.fields["monthly_income"]
    assert sp.provenance == ProvenanceState.UNKNOWN
    assert sp.value is None
    assert "monthly_income" not in ctx.explicit_fields


# ==============================================================================
# Requirement 10: Existing HTML / API Compatibility
# ==============================================================================

def test_pabl_api_compatibility_and_provenance_structure(client):
    """
    Requirement 10: Proves that existing API endpoints return 200 OK, include the
    new provenance section, and preserve all legacy fields without regression.
    """
    payload = {
        "monthly_income": 3000.0,
        "monthly_expense": 1800.0,
        "debt_status": "no debt",
        "language": "en"
    }
    res = client.post("/api/consult", json=payload)
    assert res.status_code == 200
    data = res.get_json()

    # Legacy contract preserved
    assert data["success"] is True
    assert data["knowledge_base_version"] == "financial-kb-v1.0"
    assert "decision" in data
    assert "metrics" in data
    assert "facts" in data
    assert "decision_trace" in data

    # Provenance section present
    assert "provenance" in data
    prov = data["provenance"]
    assert "fields" in prov
    assert "explicit_fields" in prov
    assert "unknown_fields" in prov
    assert "defaulted_fields" in prov
    assert "assumptions_present" in prov
    assert "decision_used_defaulted_field" in prov

    # Decision trace enriched with provenance
    assert "provenance" in data["decision_trace"]


# ==============================================================================
# Requirement 11: Deterministic Engine Authority
# ==============================================================================

def test_pabl_deterministic_engine_authority(standalone_rules):
    """
    Requirement 11: Proves that ProvenanceBoundaryLayer does not select rules directly.
    ConsultantEngine.select_rule remains the sole authority.
    """
    raw = {"monthly_income": 3000.0, "monthly_expense": 1800.0, "debt_status": None}
    ctx = ProvenanceBoundaryLayer.process(raw)

    # ProvenanceBoundaryLayer has no rule selection result
    assert not hasattr(ctx, "selected_rule")
    assert not hasattr(ctx, "rule_id")

    # ConsultantEngine is the sole entity evaluating the payload
    eval_result = ConsultantEngine.evaluate(ctx.legacy_payload, rules=standalone_rules)
    assert eval_result["selected_advice"] is not None
    assert eval_result["selected_advice"].rule_id == "BALANCED_BUDGET_BUFFER_BUILDING"


# ==============================================================================
# Requirement 12: No Financial Decision Changes
# ==============================================================================

def test_pabl_no_financial_decision_changes_on_complete_inputs(client):
    """
    Requirement 12: Proves that complete-input cases select the exact same canonical
    rule IDs before and after PABL integration.
    """
    cases = [
        ({"monthly_income": 1000.0, "monthly_expense": 900.0, "debt_status": "no debt"}, "TIGHT_MARGIN_HIGH_EXPENSE"),
        ({"monthly_income": 3000.0, "monthly_expense": 1800.0, "debt_status": "no debt"}, "BALANCED_BUDGET_BUFFER_BUILDING"),
        ({"monthly_income": 5000.0, "monthly_expense": 1800.0, "debt_status": "no debt"}, "FLEXIBLE_BUDGET_CAPITAL_GROWTH"),
        ({"monthly_income": 3000.0, "monthly_expense": 2000.0, "debt_status": "debt"}, "SURPLUS_WITH_DEBT_SERVICING"),
        ({"monthly_income": 2000.0, "monthly_expense": 2600.0, "debt_status": "debt"}, "DEFICIT_WITH_DEBT"),
        ({"monthly_income": 1500.0, "monthly_expense": 1900.0, "debt_status": "no debt"}, "DEFICIT_NO_DEBT"),
        ({"monthly_income": 2400.0, "monthly_expense": 2400.0, "debt_status": "no debt"}, "BREAK_EVEN_ZERO_MARGIN"),
        ({"monthly_income": 0.0, "monthly_expense": 0.0, "employment_status": "not employed", "debt_status": "no debt"}, "INCOME_ZERO_UNEMPLOYED"),
    ]
    for payload, expected_rule in cases:
        res = client.post("/api/consult", json=payload)
        assert res.status_code == 200
        data = res.get_json()
        assert data["decision"]["rule_id"] == expected_rule, (
            f"Expected {expected_rule} for payload {payload}, got {data['decision']['rule_id']}"
        )


# ==============================================================================
# Requirement 13: No Silent Inferred Values in Phase 1
# ==============================================================================

def test_pabl_no_silent_inferred_values():
    """
    Requirement 13: Proves that Phase 1 never automatically assigns provenance='inferred'.
    All unmentioned fields must be 'unknown'.
    """
    raw = {"monthly_income": 4000.0, "monthly_expense": 2000.0}
    ctx = ProvenanceBoundaryLayer.process(raw)

    for field_name, sp in ctx.fields.items():
        assert sp.provenance != ProvenanceState.INFERRED, (
            f"Field {field_name} must not be inferred in Phase 1"
        )
        assert sp.provenance in (ProvenanceState.EXPLICIT, ProvenanceState.UNKNOWN)


# ==============================================================================
# Requirement 14: Structured Output Schema Conformance
# ==============================================================================

def test_pabl_structured_output_schema_conformance():
    """
    Validates that to_dict() produces the exact required structure documented in Step 8G/8H.
    """
    raw = {
        "monthly_income": 3000.0,
        "monthly_expense": 1800.0,
        "debt_status": None,
        "employment_status": None,
    }
    ctx = ProvenanceBoundaryLayer.process(raw)
    out = ctx.to_dict(decision_used_defaulted_field=True)

    # Check top-level keys
    required_keys = {
        "fields",
        "explicit_fields",
        "unknown_fields",
        "defaulted_fields",
        "assumptions_present",
        "assumptions",
        "decision_used_defaulted_field",
        "advisory_caveats",
    }
    assert required_keys.issubset(set(out.keys()))

    # Check field objects
    debt_field = out["fields"]["debt_status"]
    assert debt_field["value"] is None
    assert debt_field["provenance"] == "unknown"
    assert debt_field["legacy_default"] == "no debt"

    income_field = out["fields"]["monthly_income"]
    assert income_field["value"] == 3000.0
    assert income_field["provenance"] == "explicit"

    # Check assumptions list
    assert out["assumptions_present"] is True
    assert out["decision_used_defaulted_field"] is True
    assert any(a["field"] == "debt_status" for a in out["assumptions"])


# ==============================================================================
# Requirement 15: Advisory Caveats Generation
# ==============================================================================

def test_pabl_advisory_caveats_for_unmentioned_debt():
    """
    Proves that unmentioned debt triggers safe advisory caveats explaining the assumption.
    """
    raw = {"monthly_income": 3000.0, "monthly_expense": 1800.0}
    ctx = ProvenanceBoundaryLayer.process(raw)

    caveats_en = ctx.get_caveat_messages("en")
    assert len(caveats_en) >= 1
    assert any("zero active debt" in c.lower() for c in caveats_en)

    caveats_km = ctx.get_caveat_messages("km")
    assert len(caveats_km) >= 1
    assert any("បំណុល" in c for c in caveats_km)
