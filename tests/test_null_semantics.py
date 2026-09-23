"""
Focused Regression Tests for Null Semantics and Validator Boundaries (Step 8F).

Verifies and proves:
1. ConsultantInputValidator normalizes null and missing debt_status to 'no debt'.
2. ConsultantInputValidator preserves explicit 'debt' and explicit 'no debt'.
3. Unknown debt and explicit 'no debt' produce identical engine facts in financial-kb-v1.0.
4. Unknown debt and explicit 'no debt' produce identical rule selections and decision traces.
5. ConsultantInputValidator normalizes null and missing employment_status to 'not employed'.
6. The NLU dry-run dataset maintains strict null safety (unmentioned debt is null, not 'no debt').
7. The NLU dry-run dataset assigns 'no debt' only when textual evidence explicitly states it.

Strict Invariant:
Tests document and prove existing production behavior without modifying any production logic.
"""

import json
import os
import pytest
from app.services.consultant_validator import ConsultantInputValidator
from app.services.consultant_engine import ConsultantEngine, CANONICAL_KB_VERSION
from app.security.seed_rule_facts import CONSULTANT_RULES


@pytest.fixture(scope="module")
def standalone_rules():
    """Provides canonical rules with explicit kb_version for standalone evaluation."""
    return [dict(r, kb_version=CANONICAL_KB_VERSION) for r in CONSULTANT_RULES]


@pytest.fixture(scope="module")
def dry_run_records():
    """Loads all 22 records from the NLU dry-run file."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    fpath = os.path.join(base_dir, "datasets", "financial_nlu", "raw", "annotation_dry_run.jsonl")
    records = []
    with open(fpath, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line.strip()))
    return records


# ──────────────────────────────────────────────────────────────
# 1. Validator Normalization Behavior Tests
# ──────────────────────────────────────────────────────────────

def test_validator_normalizes_null_debt_to_no_debt():
    """Proves that passing debt_status=None to ConsultantInputValidator results in 'no debt'."""
    raw = {"monthly_income": 3000.0, "monthly_expense": 1800.0, "debt_status": None}
    norm, err = ConsultantInputValidator.validate(raw)
    assert err is None
    assert norm["debt_status"] == "no debt"


def test_validator_normalizes_missing_debt_to_no_debt():
    """Proves that omitting debt_status entirely results in 'no debt'."""
    raw = {"monthly_income": 3000.0, "monthly_expense": 1800.0}
    norm, err = ConsultantInputValidator.validate(raw)
    assert err is None
    assert norm["debt_status"] == "no debt"


def test_validator_preserves_explicit_debt():
    """Proves that explicit 'debt' is preserved verbatim."""
    raw = {"monthly_income": 3000.0, "monthly_expense": 1800.0, "debt_status": "debt"}
    norm, err = ConsultantInputValidator.validate(raw)
    assert err is None
    assert norm["debt_status"] == "debt"


def test_validator_preserves_explicit_no_debt():
    """Proves that explicit 'no debt' is preserved verbatim."""
    raw = {"monthly_income": 3000.0, "monthly_expense": 1800.0, "debt_status": "no debt"}
    norm, err = ConsultantInputValidator.validate(raw)
    assert err is None
    assert norm["debt_status"] == "no debt"


def test_validator_normalizes_null_employment_to_not_employed():
    """Proves that employment_status=None normalizes to 'not employed'."""
    raw = {"monthly_income": 3000.0, "monthly_expense": 1800.0, "employment_status": None}
    norm, err = ConsultantInputValidator.validate(raw)
    assert err is None
    assert norm["employment_status"] == "not employed"


# ──────────────────────────────────────────────────────────────
# 2. Indistinguishability in ConsultantEngine Tests
# ──────────────────────────────────────────────────────────────

def test_unknown_and_explicit_no_debt_produce_identical_engine_facts(standalone_rules):
    """Proves that unknown debt status and explicit 'no debt' produce 100% identical fact namespaces."""
    raw_unknown = {"monthly_income": 3000.0, "monthly_expense": 1800.0, "debt_status": None}
    raw_explicit = {"monthly_income": 3000.0, "monthly_expense": 1800.0, "debt_status": "no debt"}

    norm_u, _ = ConsultantInputValidator.validate(raw_unknown)
    norm_e, _ = ConsultantInputValidator.validate(raw_explicit)

    eval_u = ConsultantEngine.evaluate(norm_u, rules=standalone_rules)
    eval_e = ConsultantEngine.evaluate(norm_e, rules=standalone_rules)

    assert eval_u["facts"] == eval_e["facts"]
    assert eval_u["facts"]["debt_present"] is False
    assert eval_u["facts"]["debt_free"] is True
    assert eval_u["facts"]["debt_status"] == "no debt"


def test_unknown_and_explicit_no_debt_produce_identical_rules(standalone_rules):
    """Proves that unknown debt status and explicit 'no debt' select the exact same canonical rule."""
    raw_unknown = {"monthly_income": 3000.0, "monthly_expense": 1800.0, "debt_status": None}
    raw_explicit = {"monthly_income": 3000.0, "monthly_expense": 1800.0, "debt_status": "no debt"}

    norm_u, _ = ConsultantInputValidator.validate(raw_unknown)
    norm_e, _ = ConsultantInputValidator.validate(raw_explicit)

    eval_u = ConsultantEngine.evaluate(norm_u, rules=standalone_rules)
    eval_e = ConsultantEngine.evaluate(norm_e, rules=standalone_rules)

    assert eval_u["selected_advice"].rule_id == "BALANCED_BUDGET_BUFFER_BUILDING"
    assert eval_e["selected_advice"].rule_id == "BALANCED_BUDGET_BUFFER_BUILDING"
    assert eval_u["selected_advice"].rule_id == eval_e["selected_advice"].rule_id


def test_unknown_and_explicit_no_debt_produce_identical_decision_traces(standalone_rules):
    """Proves that decision traces cannot distinguish between unmentioned debt and explicit 'no debt'."""
    raw_unknown = {"monthly_income": 3000.0, "monthly_expense": 1800.0, "debt_status": None}
    raw_explicit = {"monthly_income": 3000.0, "monthly_expense": 1800.0, "debt_status": "no debt"}

    norm_u, _ = ConsultantInputValidator.validate(raw_unknown)
    norm_e, _ = ConsultantInputValidator.validate(raw_explicit)

    eval_u = ConsultantEngine.evaluate(norm_u, rules=standalone_rules)
    eval_e = ConsultantEngine.evaluate(norm_e, rules=standalone_rules)

    assert eval_u["decision_trace"] == eval_e["decision_trace"]
    # Both report input_summary with 'no debt'
    assert eval_u["decision_trace"]["input_summary"]["debt_status"] == "no debt"
    assert eval_e["decision_trace"]["input_summary"]["debt_status"] == "no debt"


# ──────────────────────────────────────────────────────────────
# 3. NLU Dataset Null-Safety & Perception Integrity Tests
# ──────────────────────────────────────────────────────────────

def test_nlu_dry_run_dataset_maintains_null_for_unmentioned_debt(dry_run_records):
    """Proves that the NLU dataset keeps debt_status as null whenever debt is not mentioned."""
    unmentioned_debt_eids = [
        "EN_BUDGET_0001",
        "EN_BUDGET_0002",
        "EN_BUDGET_0003",
        "EN_CASHFLOW_0001",
        "EN_EMPLOYMENT_0001",
        "EN_SAVINGS_0001",
        "EN_HOUSEHOLD_0001",
    ]
    for r in dry_run_records:
        if r["example_id"] in unmentioned_debt_eids:
            assert r["slots"]["debt_status"] is None, (
                f"Record {r['example_id']} unmentioned debt must be null, "
                f"found: {r['slots']['debt_status']}"
            )


def test_nlu_dry_run_dataset_uses_no_debt_only_when_explicit(dry_run_records):
    """Proves that 'no debt' is assigned only when explicit textual evidence is present."""
    no_debt_records = [r for r in dry_run_records if r["slots"].get("debt_status") == "no debt"]
    # Only EN_DEBT_0002 has explicit 'no debt'
    assert len(no_debt_records) == 1
    rec = no_debt_records[0]
    assert rec["example_id"] == "EN_DEBT_0002"
    assert "no debt" in rec["input_text"].lower()
    # Verified span exists for 'no debt'
    span_slots = [s["slot"] for s in rec.get("slot_spans", [])]
    assert "debt_status" in span_slots
