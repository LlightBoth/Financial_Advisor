"""
Tests for Template Semantic Audit & Annotation Dry Run (Step 8D).

Verifies:
1. All controlled templates can be audited without semantic errors.
2. Template IDs remain globally unique across all template families.
3. Dry-run dataset records strictly conform to the NLU schema contract.
4. The Null Invariant is strictly preserved (unknown != 0.0).
5. Explicit zero declarations are preserved as 0.0.
6. Annual, weekly, and hourly cadence ambiguity is not silently converted.
7. Third-party financial figures are not assigned to user slots.
8. Expected rule IDs are derived deterministically from ConsultantEngine.
9. Out-of-scope queries do not route to the financial decision engine.
"""

import json
import os
import pytest
from datasets.financial_nlu.audit_templates import (
    audit_all_templates,
    audit_single_template,
    audit_dry_run_dataset,
    CANONICAL_SLOT_KEYS,
    NUMERIC_SLOTS,
    ENUM_SLOTS,
    VALID_INTENTS,
    ENGINE_ROUTABLE_INTENTS,
    OUT_OF_SCOPE_INTENTS,
    STANDALONE_CANONICAL_RULES,
    DRY_RUN_FILE,
    TEMPLATES_DIR,
)
from app.services.consultant_engine import ConsultantEngine, CANONICAL_RULE_IDS


@pytest.fixture(scope="module")
def dry_run_records():
    """Fixture providing all dry-run records."""
    assert os.path.isfile(DRY_RUN_FILE), f"Dry-run file missing: {DRY_RUN_FILE}"
    records = []
    with open(DRY_RUN_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if line_str:
                records.append(json.loads(line_str))
    return records


# ──────────────────────────────────────────────────────────────
# 1. Template Auditing & Global Uniqueness
# ──────────────────────────────────────────────────────────────

def test_all_templates_can_be_audited():
    """All 60 controlled templates must pass semantic audit with 0 errors."""
    total, passed, failed, errors = audit_all_templates()
    assert total == 60, f"Expected 60 templates, found {total}"
    assert failed == 0, f"Audit failures found in templates: {errors}"
    assert len(errors) == 0


def test_template_ids_remain_unique():
    """Template IDs must be globally unique across all 8 template families."""
    seen = set()
    template_files = [f for f in os.listdir(TEMPLATES_DIR) if f.endswith(".json")]
    for fname in template_files:
        with open(os.path.join(TEMPLATES_DIR, fname), "r", encoding="utf-8") as f:
            templates = json.load(f)
        for tmpl in templates:
            tid = tmpl["template_id"]
            assert tid not in seen, f"Duplicate template_id found: {tid} in {fname}"
            seen.add(tid)
    assert len(seen) == 60


# ──────────────────────────────────────────────────────────────
# 2. Dry-Run Schema & Invariant Conformance
# ──────────────────────────────────────────────────────────────

def test_dry_run_records_count_and_schema(dry_run_records):
    """Dry-run file must contain <= 30 records and pass full audit."""
    assert 0 < len(dry_run_records) <= 30, f"Dry-run record count out of bounds: {len(dry_run_records)}"
    total, passed, failed, errors, findings = audit_dry_run_dataset(STANDALONE_CANONICAL_RULES)
    assert failed == 0, f"Dry-run records failed audit: {errors}"
    assert errors == []
    assert findings["null_safety"] == "PASS"
    assert findings["ambiguity"] == "PASS"
    assert findings["slot_spans"] == "PASS"
    assert findings["expected_rule_alignment"] == "PASS"
    assert findings["out_of_scope_classification"] == "PASS"


def test_null_values_are_preserved(dry_run_records):
    """Unknown or omitted information must remain null, never converted to 0.0."""
    # Find record with unknown expense (EN_MISSING_0001)
    missing_exp_recs = [r for r in dry_run_records if r.get("metadata", {}).get("ambiguity_type") == "expense_unknown"]
    assert len(missing_exp_recs) > 0
    for r in missing_exp_recs:
        assert r["slots"]["monthly_expense"] is None
        assert r["slots"]["monthly_expense"] != 0.0

    # Find record with all null (EN_MISSING_0002)
    all_null_recs = [r for r in dry_run_records if r.get("metadata", {}).get("ambiguity_type") == "all_null"]
    assert len(all_null_recs) > 0
    for r in all_null_recs:
        assert r["slots"]["monthly_income"] is None
        assert r["slots"]["monthly_expense"] is None


def test_explicit_zero_is_preserved(dry_run_records):
    """Explicitly stated zero income/expense must be preserved as 0.0."""
    zero_income_recs = [
        r for r in dry_run_records
        if r.get("metadata", {}).get("numerical_format") == "explicit_zero"
    ]
    assert len(zero_income_recs) >= 2, "Expected at least 2 explicit zero examples"
    for r in zero_income_recs:
        assert r["slots"]["monthly_income"] == 0.0


def test_ambiguity_cadence_not_converted(dry_run_records):
    """Annual or hourly cadence must NOT be converted to monthly values; slot must be null."""
    non_monthly_recs = [
        r for r in dry_run_records
        if r.get("metadata", {}).get("ambiguity_type") == "non_monthly_cadence"
    ]
    assert len(non_monthly_recs) >= 2, "Expected annual and hourly cadence examples"
    for r in non_monthly_recs:
        # User declared annual or hourly income, which must remain null
        assert r["slots"]["monthly_income"] is None


def test_third_party_financial_info_isolated(dry_run_records):
    """Third-party finances (e.g. brother's income) must not be assigned to user slots."""
    third_party_recs = [
        r for r in dry_run_records
        if r.get("metadata", {}).get("ambiguity_type") == "third_party_income"
    ]
    assert len(third_party_recs) >= 1
    for r in third_party_recs:
        # The brother earned 4500, user's monthly income must remain null
        assert r["slots"]["monthly_income"] is None
        assert r["slots"]["monthly_expense"] == 1200.0


def test_slot_spans_exact_character_slices(dry_run_records):
    """Slot spans must exactly slice input_text[start:end] == raw_text."""
    spans_tested = 0
    for r in dry_run_records:
        text = r["input_text"]
        for span in r.get("slot_spans", []):
            s = span["start"]
            e = span["end"]
            raw = span["raw_text"]
            assert text[s:e] == raw, (
                f"Span slice mismatch in {r['example_id']}: "
                f"expected {raw!r}, sliced {text[s:e]!r}"
            )
            spans_tested += 1
    assert spans_tested >= 15, f"Expected at least 15 span annotations, got {spans_tested}"


def test_expected_rule_ids_come_from_consultant_engine(dry_run_records):
    """Expected rule IDs must strictly match ConsultantEngine execution."""
    rules_evaluated = 0
    for r in dry_run_records:
        expected = r.get("expected_rule_id")
        slots = r["slots"]
        if expected is not None:
            assert expected in CANONICAL_RULE_IDS, f"Unknown rule ID: {expected}"
            engine_res = ConsultantEngine.evaluate(slots, rules=STANDALONE_CANONICAL_RULES)
            actual = engine_res["selected_advice"].rule_id
            assert actual == expected, (
                f"Record {r['example_id']} expected rule '{expected}', "
                f"but ConsultantEngine returned '{actual}'"
            )
            rules_evaluated += 1
        else:
            # Must be missing required info or non-routable intent
            is_incomplete = slots.get("monthly_income") is None or slots.get("monthly_expense") is None
            is_non_routable = r["intent"] not in ENGINE_ROUTABLE_INTENTS
            assert is_incomplete or is_non_routable, (
                f"Record {r['example_id']} has complete data and routable intent, "
                f"but expected_rule_id is null"
            )
    assert rules_evaluated >= 8, f"Expected at least 8 evaluated canonical rules, got {rules_evaluated}"


def test_out_of_scope_records_do_not_reach_engine(dry_run_records):
    """Out-of-scope and educational records must have expected_rule_id = null and all-null slots."""
    oos_recs = [r for r in dry_run_records if r["intent"] in OUT_OF_SCOPE_INTENTS]
    assert len(oos_recs) >= 4, "Expected at least 4 out-of-scope records (investment + loan)"

    for r in oos_recs:
        assert r["expected_rule_id"] is None
        for skey in CANONICAL_SLOT_KEYS:
            assert r["slots"][skey] is None

    edu_recs = [r for r in dry_run_records if r["intent"] == "financial_education"]
    assert len(edu_recs) >= 1
    for r in edu_recs:
        assert r["expected_rule_id"] is None
