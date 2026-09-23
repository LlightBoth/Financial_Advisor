"""
Template Semantic Audit and Annotation Dry Run Utility (Step 8D).

Authoritative audit tool for the Financial Advisor NLU Dataset:
1. Semantically audits all controlled templates in datasets/financial_nlu/templates/*.json.
2. Validates the annotation dry run dataset in datasets/financial_nlu/raw/annotation_dry_run.jsonl.
3. Verifies slot values, null safety, ambiguity preservation, and slot spans.
4. Validates expected rule IDs against ConsultantValidator -> ConsultantMetrics -> ConsultantEngine.
5. Emits the official audit report to datasets/financial_nlu/reports/step8d_template_audit_report.json.

Guarantees:
- Pure audit & verification only.
- No ML frameworks, no model creation, no external APIs.
- Production expert engine logic and database schema remain untouched.
"""

import json
import os
import sys
from typing import Dict, Any, List, Optional, Tuple, Set

# Add workspace root to sys.path to allow imports from app
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from app.services.consultant_engine import ConsultantEngine, CANONICAL_KB_VERSION, CANONICAL_RULE_IDS
from app.services.consultant_validator import ConsultantInputValidator
from app.services.consultant_metrics import calculate_metrics
from app.security.seed_rule_facts import CONSULTANT_RULES

# ──────────────────────────────────────────────────────────────
# Canonical Taxonomies & Contract Invariants
# ──────────────────────────────────────────────────────────────

CANONICAL_SLOT_KEYS = frozenset([
    "monthly_income",
    "monthly_expense",
    "employment_status",
    "debt_status",
    "spending_habit",
    "goal_cost",
    "marital_status",
])

NUMERIC_SLOTS = frozenset(["monthly_income", "monthly_expense", "goal_cost"])

ENUM_SLOTS = {
    "employment_status": frozenset(["employed", "not employed"]),
    "debt_status": frozenset(["debt", "no debt"]),
    "spending_habit": frozenset(["average spend", "big spend"]),
    "marital_status": frozenset(["Single", "Married"]),
}

VALID_INTENTS = frozenset([
    "financial_consultation",
    "budget_analysis",
    "cashflow_question",
    "savings_question",
    "debt_management",
    "financial_goal",
    "financial_education",
    "out_of_scope_investment",
    "out_of_scope_loan",
])

ENGINE_ROUTABLE_INTENTS = frozenset([
    "financial_consultation",
    "budget_analysis",
    "cashflow_question",
    "savings_question",
    "debt_management",
    "financial_goal",
])

OUT_OF_SCOPE_INTENTS = frozenset([
    "out_of_scope_investment",
    "out_of_scope_loan",
])

VALID_TEMPLATE_FAMILIES = frozenset([
    "TF_BUDGET",
    "TF_CASHFLOW",
    "TF_DEBT",
    "TF_SAVINGS",
    "TF_EMPLOYMENT",
    "TF_HOUSEHOLD",
    "TF_MISSING_INFO",
    "TF_OUT_OF_SCOPE",
])

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
RAW_DIR = os.path.join(BASE_DIR, "raw")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
DRY_RUN_FILE = os.path.join(RAW_DIR, "annotation_dry_run.jsonl")
REPORT_FILE = os.path.join(REPORTS_DIR, "step8d_template_audit_report.json")

# In-memory canonical rules with kb_version for deterministic standalone evaluation
STANDALONE_CANONICAL_RULES = [
    dict(r, kb_version=CANONICAL_KB_VERSION) for r in CONSULTANT_RULES
]


# ──────────────────────────────────────────────────────────────
# 1. Template Semantic Audit
# ──────────────────────────────────────────────────────────────

def audit_single_template(tmpl: Dict[str, Any], filename: str) -> List[str]:
    """
    Semantically audits a single template definition.
    Returns a list of error strings (empty if passed).
    """
    errors: List[str] = []
    tid = tmpl.get("template_id", "<MISSING_ID>")

    # Required fields
    required_keys = [
        "template_id", "template_family", "intent", "text_pattern",
        "required_slots", "optional_slots", "language", "source_type",
        "concept_source", "ambiguity_policy"
    ]
    for key in required_keys:
        if key not in tmpl:
            errors.append(f"Template {tid} missing required key '{key}'")

    # Template family
    family = tmpl.get("template_family")
    if family not in VALID_TEMPLATE_FAMILIES:
        errors.append(f"Template {tid} has invalid template_family: '{family}'")

    # Intent
    intent = tmpl.get("intent")
    if intent not in VALID_INTENTS:
        errors.append(f"Template {tid} has invalid intent: '{intent}'")

    # Language must be English only
    lang = tmpl.get("language")
    if lang != "en":
        errors.append(f"Template {tid} language must be 'en', found: '{lang}'")

    # Required and optional slots
    req_slots = tmpl.get("required_slots", [])
    opt_slots = tmpl.get("optional_slots", [])
    for s in req_slots:
        if s not in CANONICAL_SLOT_KEYS:
            errors.append(f"Template {tid} has non-canonical required slot: '{s}'")
    for s in opt_slots:
        if s not in CANONICAL_SLOT_KEYS:
            errors.append(f"Template {tid} has non-canonical optional slot: '{s}'")

    # Ambiguity policy must exist
    ambiguity_policy = tmpl.get("ambiguity_policy")
    if not ambiguity_policy:
        errors.append(f"Template {tid} is missing 'ambiguity_policy'")

    # Out-of-scope templates must use out_of_scope intents
    if family == "TF_OUT_OF_SCOPE":
        if intent not in OUT_OF_SCOPE_INTENTS:
            errors.append(f"Out-of-scope template {tid} has non-OOS intent: '{intent}'")
        expected_slots = tmpl.get("expected_slot_behavior", {})
        if expected_slots:
            for skey, sval in expected_slots.items():
                if sval is not None:
                    errors.append(f"Out-of-scope template {tid} must have null slot for '{skey}', got: {sval}")

    # Missing information templates check
    if family == "TF_MISSING_INFO":
        expected_slots = tmpl.get("expected_slot_behavior", {})
        policy = tmpl.get("ambiguity_policy")
        # Missing-info templates must not assign zero to missing fields (only explicit_zero policy may have 0)
        if policy in ("all_null", "expense_unknown", "vague_commitment", "non_monthly_cadence", "third_party_income", "education_only"):
            if expected_slots.get("monthly_income") == 0:
                errors.append(f"Template {tid} with policy '{policy}' incorrectly assigned 0 to monthly_income instead of null")
            if expected_slots.get("monthly_expense") == 0:
                errors.append(f"Template {tid} with policy '{policy}' incorrectly assigned 0 to monthly_expense instead of null")

        # Annual/weekly/hourly cadence must not be silently converted
        if policy == "non_monthly_cadence":
            if expected_slots.get("monthly_income") is not None:
                errors.append(f"Template {tid} with non_monthly_cadence must leave monthly_income as null")

        # Third-party income must not be extracted as user's income
        if policy == "third_party_income":
            if expected_slots.get("monthly_income") is not None:
                errors.append(f"Template {tid} with third_party_income must not assign third-party amount to user monthly_income")

    # Protection against model artifact claims
    model_keywords = ["model_name", "checkpoint", "weights", "lora", "pretrained", "fine_tuned"]
    for kw in model_keywords:
        if kw in tmpl:
            errors.append(f"Template {tid} illegally contains model artifact field: '{kw}'")

    # Protected decision-control fields check
    for pcf in ConsultantInputValidator.PROTECTED_CONTROL_FIELDS:
        if pcf in tmpl:
            errors.append(f"Template {tid} illegally contains protected control field: '{pcf}'")

    return errors


def audit_all_templates() -> Tuple[int, int, int, List[str]]:
    """
    Audits all templates in datasets/financial_nlu/templates/*.json.
    Returns: (total_audited, passed_count, failed_count, error_list)
    """
    all_errors: List[str] = []
    seen_ids: Set[str] = set()
    total_audited = 0
    passed_count = 0

    template_files = sorted([f for f in os.listdir(TEMPLATES_DIR) if f.endswith(".json")])
    for fname in template_files:
        fpath = os.path.join(TEMPLATES_DIR, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                templates = json.load(f)
        except Exception as e:
            all_errors.append(f"File {fname} is not valid JSON: {str(e)}")
            continue

        if not isinstance(templates, list):
            all_errors.append(f"File {fname} does not contain a JSON array")
            continue

        for tmpl in templates:
            total_audited += 1
            tid = tmpl.get("template_id")
            if not tid:
                all_errors.append(f"File {fname}: Template missing template_id")
                continue
            if tid in seen_ids:
                all_errors.append(f"Duplicate template_id across files: '{tid}'")
            seen_ids.add(tid)

            tmpl_errors = audit_single_template(tmpl, fname)
            if tmpl_errors:
                all_errors.extend(tmpl_errors)
            else:
                passed_count += 1

    failed_count = total_audited - passed_count
    return total_audited, passed_count, failed_count, all_errors


# ──────────────────────────────────────────────────────────────
# 2. Dry-Run Dataset Audit & Validation
# ──────────────────────────────────────────────────────────────

def audit_single_dry_run_record(
    rec: Dict[str, Any],
    line_num: int,
    rules: List[Dict[str, Any]]
) -> Tuple[List[str], Dict[str, Any]]:
    """
    Audits a single dry-run record against:
    - Schema compliance
    - Slot and null invariants
    - Slot spans precision
    - Expected rule calculation via ConsultantEngine
    Returns: (error_list, audit_metadata)
    """
    errors: List[str] = []
    meta: Dict[str, Any] = {
        "example_id": rec.get("example_id", f"LINE_{line_num}"),
        "null_safety_ok": True,
        "ambiguity_ok": True,
        "spans_ok": True,
        "rule_alignment_ok": True,
        "oos_ok": True,
    }

    eid = rec.get("example_id", f"LINE_{line_num}")

    # Top-level required keys
    required_top = [
        "example_id", "template_id", "template_family", "language",
        "split", "input_text", "intent", "slots", "expected_rule_id",
        "validation_status", "source_type", "concept_source", "metadata"
    ]
    for key in required_top:
        if key not in rec:
            errors.append(f"Record {eid} missing required top-level field '{key}'")

    # Language must be English
    if rec.get("language") != "en":
        errors.append(f"Record {eid} language must be 'en'")

    # Split
    if rec.get("split") not in ("train", "val", "test", "unassigned"):
        errors.append(f"Record {eid} has invalid split: {rec.get('split')}")

    # Intent
    intent = rec.get("intent")
    if intent not in VALID_INTENTS:
        errors.append(f"Record {eid} has invalid intent: {intent}")

    # Slots dictionary
    slots = rec.get("slots", {})
    if not isinstance(slots, dict):
        errors.append(f"Record {eid} 'slots' must be a dictionary")
        return errors, meta

    # All 7 keys must exist
    for skey in CANONICAL_SLOT_KEYS:
        if skey not in slots:
            errors.append(f"Record {eid} slots missing canonical key '{skey}'")
            meta["null_safety_ok"] = False

    # Numeric slots validation
    for nkey in NUMERIC_SLOTS:
        val = slots.get(nkey)
        if val is not None:
            if not isinstance(val, (int, float)) or isinstance(val, bool):
                errors.append(f"Record {eid} slot '{nkey}' must be a number or null, got: {type(val)}")
            elif val < 0.0:
                errors.append(f"Record {eid} slot '{nkey}' cannot be negative: {val}")

    # Enum slots validation
    for ckey, valid_vals in ENUM_SLOTS.items():
        val = slots.get(ckey)
        if val is not None:
            if val not in valid_vals:
                errors.append(f"Record {eid} slot '{ckey}' has invalid enum value: '{val}'")

    # Check null safety: unknown != 0.0
    rec_meta = rec.get("metadata", {})
    ambiguity_type = rec_meta.get("ambiguity_type")
    if ambiguity_type in ("all_null", "expense_unknown", "vague_commitment", "education_only", "out_of_scope"):
        if ambiguity_type == "expense_unknown" and slots.get("monthly_expense") is not None:
            errors.append(f"Record {eid} has expense_unknown ambiguity but monthly_expense is not null")
            meta["null_safety_ok"] = False
        elif ambiguity_type == "all_null" and (slots.get("monthly_income") is not None or slots.get("monthly_expense") is not None):
            errors.append(f"Record {eid} has all_null ambiguity but has non-null income/expense")
            meta["null_safety_ok"] = False

    # Ambiguity check: non-monthly cadence & third party finances
    if ambiguity_type == "non_monthly_cadence":
        if slots.get("monthly_income") is not None:
            errors.append(f"Record {eid} has non-monthly cadence; monthly_income must be null (no silent conversion)")
            meta["ambiguity_ok"] = False
    elif ambiguity_type == "range_ambiguity":
        if slots.get("monthly_income") is not None:
            errors.append(f"Record {eid} has range conflict; monthly_income must be null")
            meta["ambiguity_ok"] = False
    elif ambiguity_type == "third_party_income":
        if slots.get("monthly_income") is not None:
            errors.append(f"Record {eid} has third_party_income; user's monthly_income must be null")
            meta["ambiguity_ok"] = False

    # Out of scope classification
    if intent in OUT_OF_SCOPE_INTENTS:
        meta["oos_ok"] = True
        for skey in CANONICAL_SLOT_KEYS:
            if slots.get(skey) is not None:
                errors.append(f"Record {eid} is out-of-scope ({intent}); slot '{skey}' must be null")
                meta["oos_ok"] = False
        if rec.get("expected_rule_id") is not None:
            errors.append(f"Record {eid} is out-of-scope; expected_rule_id must be null")
            meta["oos_ok"] = False

    # Educational query check
    if intent == "financial_education":
        if rec.get("expected_rule_id") is not None:
            errors.append(f"Record {eid} is financial_education; expected_rule_id must be null")

    # Slot Spans Validation
    input_text = rec.get("input_text", "")
    slot_spans = rec.get("slot_spans", [])
    if slot_spans:
        for span in slot_spans:
            s_slot = span.get("slot")
            start = span.get("start")
            end = span.get("end")
            raw = span.get("raw_text")
            s_val = span.get("value")

            if s_slot not in CANONICAL_SLOT_KEYS:
                errors.append(f"Record {eid} slot span references invalid slot '{s_slot}'")
                meta["spans_ok"] = False
            if not isinstance(start, int) or not isinstance(end, int) or start < 0 or end > len(input_text) or start >= end:
                errors.append(f"Record {eid} span offsets [{start}:{end}] are invalid for text length {len(input_text)}")
                meta["spans_ok"] = False
                continue

            extracted_slice = input_text[start:end]
            if extracted_slice != raw:
                errors.append(f"Record {eid} span text mismatch: input_text[{start}:{end}] is '{extracted_slice}', raw_text is '{raw}'")
                meta["spans_ok"] = False

            # Spans must not refer to another person's information
            if ambiguity_type == "third_party_income" and s_slot == "monthly_income":
                errors.append(f"Record {eid} span illegally extracts third-party income as user slot")
                meta["spans_ok"] = False

    # Expected Rule ID Validation
    expected_rule_id = rec.get("expected_rule_id")
    monthly_income = slots.get("monthly_income")
    monthly_expense = slots.get("monthly_expense")

    if monthly_income is not None and monthly_expense is not None and intent in ENGINE_ROUTABLE_INTENTS:
        # Run through ConsultantValidator -> ConsultantMetrics -> ConsultantEngine
        norm_dict, val_err = ConsultantInputValidator.validate(slots, default_lang="en")
        if val_err:
            errors.append(f"Record {eid} ConsultantInputValidator error: {val_err}")
            meta["rule_alignment_ok"] = False
        else:
            engine_res = ConsultantEngine.evaluate(norm_dict, rules=rules)
            selected_rule = engine_res["selected_advice"].rule_id
            if expected_rule_id != selected_rule:
                errors.append(f"Record {eid} expected_rule_id mismatch: annotated '{expected_rule_id}' != engine '{selected_rule}'")
                meta["rule_alignment_ok"] = False
            if expected_rule_id not in CANONICAL_RULE_IDS:
                errors.append(f"Record {eid} expected_rule_id '{expected_rule_id}' is not in CANONICAL_RULE_IDS")
                meta["rule_alignment_ok"] = False
    else:
        # Expected rule ID must be null if required numeric info is missing or intent is non-routable
        if expected_rule_id is not None:
            errors.append(f"Record {eid} has incomplete data or non-routable intent ({intent}), expected_rule_id must be null")
            meta["rule_alignment_ok"] = False

    return errors, meta


def audit_dry_run_dataset(rules: List[Dict[str, Any]]) -> Tuple[int, int, int, List[str], Dict[str, Any]]:
    """
    Audits the raw dry-run file at datasets/financial_nlu/raw/annotation_dry_run.jsonl.
    Returns: (total_records, passed_records, failed_records, error_list, summary_findings)
    """
    all_errors: List[str] = []
    total_records = 0
    passed_records = 0
    record_metas = []

    if not os.path.isfile(DRY_RUN_FILE):
        all_errors.append(f"Dry-run file not found: {DRY_RUN_FILE}")
        return 0, 0, 0, all_errors, {}

    with open(DRY_RUN_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    total_records = len(lines)
    if total_records > 30:
        all_errors.append(f"Dry-run dataset exceeds 30 records limit: {total_records} records found")

    seen_eids: Set[str] = set()

    for idx, line in enumerate(lines, start=1):
        line_str = line.strip()
        if not line_str:
            continue
        try:
            rec = json.loads(line_str)
        except Exception as e:
            all_errors.append(f"Line {idx} is not valid JSON: {str(e)}")
            continue

        eid = rec.get("example_id")
        if eid in seen_eids:
            all_errors.append(f"Duplicate example_id: '{eid}'")
        seen_eids.add(eid)

        rec_errors, meta = audit_single_dry_run_record(rec, idx, rules)
        record_metas.append(meta)
        if rec_errors:
            all_errors.extend(rec_errors)
        else:
            passed_records += 1

    failed_records = total_records - passed_records

    # Aggregated findings
    summary_findings = {
        "null_safety": "PASS" if all(m.get("null_safety_ok") for m in record_metas) else "FAIL",
        "ambiguity": "PASS" if all(m.get("ambiguity_ok") for m in record_metas) else "FAIL",
        "slot_spans": "PASS" if all(m.get("spans_ok") for m in record_metas) else "FAIL",
        "expected_rule_alignment": "PASS" if all(m.get("rule_alignment_ok") for m in record_metas) else "FAIL",
        "out_of_scope_classification": "PASS" if all(m.get("oos_ok") for m in record_metas) else "FAIL",
    }

    return total_records, passed_records, failed_records, all_errors, summary_findings


# ──────────────────────────────────────────────────────────────
# 3. Report Generation & CLI Runner
# ──────────────────────────────────────────────────────────────

def run_step8d_audit(output_report: bool = True) -> Dict[str, Any]:
    """
    Executes full Step 8D template semantic audit and dry-run dataset audit.
    Writes JSON report and returns audit summary dictionary.
    """
    # 1. Audit templates
    t_total, t_pass, t_fail, t_errors = audit_all_templates()

    # 2. Audit dry run dataset
    d_total, d_pass, d_fail, d_errors, findings = audit_dry_run_dataset(STANDALONE_CANONICAL_RULES)

    all_errors = t_errors + d_errors

    report = {
        "audit_version": "step8d_v1.0",
        "kb_version": CANONICAL_KB_VERSION,
        "language_scope": "en",
        "templates": {
            "total_audited": t_total,
            "passed": t_pass,
            "failed": t_fail,
            "status": "PASS" if t_fail == 0 else "FAIL",
            "errors": t_errors,
        },
        "dry_run_dataset": {
            "file": "datasets/financial_nlu/raw/annotation_dry_run.jsonl",
            "total_records": d_total,
            "passed": d_pass,
            "failed": d_fail,
            "status": "PASS" if d_fail == 0 else "FAIL",
            "errors": d_errors,
        },
        "findings": {
            "null_safety": findings.get("null_safety", "UNKNOWN"),
            "ambiguity": findings.get("ambiguity", "UNKNOWN"),
            "slot_spans": findings.get("slot_spans", "UNKNOWN"),
            "expected_rule_alignment": findings.get("expected_rule_alignment", "UNKNOWN"),
            "out_of_scope_classification": findings.get("out_of_scope_classification", "UNKNOWN"),
        },
        "total_errors": len(all_errors),
        "overall_status": "PASS" if len(all_errors) == 0 else "FAIL"
    }

    if output_report:
        os.makedirs(REPORTS_DIR, exist_ok=True)
        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

    return report


def main():
    print("=" * 70)
    print("STEP 8D: TEMPLATE SEMANTIC AUDIT & ANNOTATION DRY RUN")
    print("=" * 70)

    report = run_step8d_audit(output_report=True)

    print(f"\n[1/2] Controlled Template Semantic Audit:")
    print(f"  Total templates: {report['templates']['total_audited']}")
    print(f"  Passed:          {report['templates']['passed']}")
    print(f"  Failed:          {report['templates']['failed']}")
    print(f"  Status:          {report['templates']['status']}")
    if report['templates']['errors']:
        for e in report['templates']['errors']:
            print(f"    - ERROR: {e}")

    print(f"\n[2/2] Dry-Run Dataset Audit (raw/annotation_dry_run.jsonl):")
    print(f"  Total records:   {report['dry_run_dataset']['total_records']}")
    print(f"  Passed:          {report['dry_run_dataset']['passed']}")
    print(f"  Failed:          {report['dry_run_dataset']['failed']}")
    print(f"  Status:          {report['dry_run_dataset']['status']}")
    if report['dry_run_dataset']['errors']:
        for e in report['dry_run_dataset']['errors']:
            print(f"    - ERROR: {e}")

    print(f"\n[Findings Breakdown]:")
    print(f"  Null-Safety Check:         {report['findings']['null_safety']}")
    print(f"  Ambiguity Check:           {report['findings']['ambiguity']}")
    print(f"  Slot-Span Check:           {report['findings']['slot_spans']}")
    print(f"  Expected-Rule Alignment:   {report['findings']['expected_rule_alignment']}")
    print(f"  Out-Of-Scope Refusals:     {report['findings']['out_of_scope_classification']}")

    print("=" * 70)
    print(f"REPORT SAVED TO: {REPORT_FILE}")
    print(f"OVERALL STATUS:  {report['overall_status']}")
    print("=" * 70)

    if report["overall_status"] != "PASS":
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
