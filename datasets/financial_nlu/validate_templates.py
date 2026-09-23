"""
Dataset Template Validation Utility (Step 8C).

Validates the controlled template JSON files against the canonical schema contract.
Uses only Python standard library — no ML dependencies.

Does NOT modify the production ConsultantEngine or any application code.
"""

import json
import os
import sys
from typing import List, Dict, Any, Set, Tuple


# ──────────────────────────────────────────────────────────────
# Canonical Constants (verified from app/services/consultant_engine.py
# and app/services/consultant_validator.py)
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

VALID_SOURCE_TYPES = frozenset([
    "synthetic_controlled_template",
    "synthetic_paraphrase",
    "human_authored",
    "human_reviewed",
])

VALID_CONCEPT_SOURCES_PREFIXES = ("original", "CFA_", "WILEY_")

CANONICAL_RULE_IDS = frozenset([
    "DEFICIT_WITH_DEBT",
    "DEFICIT_NO_DEBT",
    "INCOME_ZERO_UNEMPLOYED",
    "BREAK_EVEN_ZERO_MARGIN",
    "TIGHT_MARGIN_HIGH_EXPENSE",
    "SURPLUS_WITH_DEBT_SERVICING",
    "BALANCED_BUDGET_BUFFER_BUILDING",
    "FLEXIBLE_BUDGET_CAPITAL_GROWTH",
])


class ValidationError:
    """Structured validation error."""
    def __init__(self, file: str, template_id: str, field: str, message: str):
        self.file = file
        self.template_id = template_id
        self.field = field
        self.message = message

    def __str__(self):
        return f"[{self.file}] {self.template_id} -> {self.field}: {self.message}"


def validate_template(tmpl: Dict[str, Any], filename: str) -> List[ValidationError]:
    """Validate a single template dictionary against the canonical contract."""
    errors = []
    tid = tmpl.get("template_id", "<MISSING_ID>")

    # template_id
    if "template_id" not in tmpl or not isinstance(tmpl["template_id"], str):
        errors.append(ValidationError(filename, tid, "template_id", "Missing or non-string."))
    elif not tmpl["template_id"].startswith("T_"):
        errors.append(ValidationError(filename, tid, "template_id", "Must start with 'T_'."))

    # template_family
    tf = tmpl.get("template_family")
    if tf not in VALID_TEMPLATE_FAMILIES:
        errors.append(ValidationError(filename, tid, "template_family",
                                      f"Invalid family '{tf}'. Must be one of {sorted(VALID_TEMPLATE_FAMILIES)}."))

    # intent
    intent = tmpl.get("intent")
    if intent not in VALID_INTENTS:
        errors.append(ValidationError(filename, tid, "intent",
                                      f"Invalid intent '{intent}'. Must be one of {sorted(VALID_INTENTS)}."))

    # text_pattern
    tp = tmpl.get("text_pattern")
    if not isinstance(tp, str) or len(tp.strip()) == 0:
        errors.append(ValidationError(filename, tid, "text_pattern", "Missing or empty."))

    # language
    lang = tmpl.get("language")
    if lang != "en":
        errors.append(ValidationError(filename, tid, "language",
                                      f"Must be 'en' for Phase 1. Got '{lang}'."))

    # source_type
    st = tmpl.get("source_type")
    if st not in VALID_SOURCE_TYPES:
        errors.append(ValidationError(filename, tid, "source_type",
                                      f"Invalid source_type '{st}'."))

    # concept_source
    cs = tmpl.get("concept_source")
    if isinstance(cs, str):
        if not any(cs.startswith(p) for p in VALID_CONCEPT_SOURCES_PREFIXES):
            errors.append(ValidationError(filename, tid, "concept_source",
                                          f"Invalid prefix in '{cs}'. Must start with one of {VALID_CONCEPT_SOURCES_PREFIXES}."))
    else:
        errors.append(ValidationError(filename, tid, "concept_source", "Missing or non-string."))

    # required_slots — each must be a canonical slot key
    req_slots = tmpl.get("required_slots", [])
    if isinstance(req_slots, list):
        for s in req_slots:
            if s not in CANONICAL_SLOT_KEYS:
                errors.append(ValidationError(filename, tid, "required_slots",
                                              f"Unknown slot '{s}'. Valid: {sorted(CANONICAL_SLOT_KEYS)}."))

    # expected_slot_behavior — check enum validity
    esb = tmpl.get("expected_slot_behavior", {})
    if isinstance(esb, dict):
        for slot_key, slot_val in esb.items():
            if slot_key not in CANONICAL_SLOT_KEYS:
                errors.append(ValidationError(filename, tid, "expected_slot_behavior",
                                              f"Unknown slot key '{slot_key}'."))
                continue
            if slot_val is None:
                continue  # null is always valid
            if slot_key in ENUM_SLOTS:
                if slot_val not in ENUM_SLOTS[slot_key]:
                    errors.append(ValidationError(filename, tid, "expected_slot_behavior",
                                                  f"Slot '{slot_key}' has invalid enum value '{slot_val}'. "
                                                  f"Valid: {sorted(ENUM_SLOTS[slot_key])}."))
            elif slot_key in NUMERIC_SLOTS:
                if not isinstance(slot_val, (int, float)):
                    errors.append(ValidationError(filename, tid, "expected_slot_behavior",
                                                  f"Numeric slot '{slot_key}' has non-numeric value '{slot_val}'."))
                elif slot_val < 0:
                    errors.append(ValidationError(filename, tid, "expected_slot_behavior",
                                                  f"Numeric slot '{slot_key}' must be >= 0. Got {slot_val}."))

    # Ensure no protected decision-control fields
    PROTECTED = {"rule_id", "priority", "certainty", "conditions", "kb_version", "is_active"}
    for pf in PROTECTED:
        if pf in tmpl:
            errors.append(ValidationError(filename, tid, pf,
                                          f"Protected control field '{pf}' must NOT appear in templates."))

    return errors


def validate_template_file(filepath: str) -> Tuple[List[Dict[str, Any]], List[ValidationError]]:
    """Load and validate a single template JSON file."""
    filename = os.path.basename(filepath)
    errors = []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        errors.append(ValidationError(filename, "<FILE>", "json", f"Invalid JSON: {e}"))
        return [], errors
    except Exception as e:
        errors.append(ValidationError(filename, "<FILE>", "io", f"Cannot read file: {e}"))
        return [], errors

    if not isinstance(data, list):
        errors.append(ValidationError(filename, "<FILE>", "root", "Root must be a JSON array."))
        return [], errors

    for tmpl in data:
        errors.extend(validate_template(tmpl, filename))

    return data, errors


def validate_all_templates(templates_dir: str) -> Tuple[int, int, List[ValidationError]]:
    """
    Validate all template JSON files in the given directory.
    Returns (total_templates, total_files, errors).
    """
    all_errors = []
    all_template_ids: Set[str] = set()
    total_templates = 0
    total_files = 0

    if not os.path.isdir(templates_dir):
        all_errors.append(ValidationError("<DIR>", "<DIR>", "directory",
                                          f"Templates directory not found: {templates_dir}"))
        return 0, 0, all_errors

    for fname in sorted(os.listdir(templates_dir)):
        if not fname.endswith(".json"):
            continue
        total_files += 1
        fpath = os.path.join(templates_dir, fname)
        templates, file_errors = validate_template_file(fpath)
        all_errors.extend(file_errors)

        for tmpl in templates:
            total_templates += 1
            tid = tmpl.get("template_id", "")
            if tid in all_template_ids:
                all_errors.append(ValidationError(fname, tid, "template_id",
                                                  f"DUPLICATE template_id '{tid}' found across files."))
            all_template_ids.add(tid)

    return total_templates, total_files, all_errors


def validate_schema_file(schema_path: str) -> List[ValidationError]:
    """Basic structural validation of the JSON Schema file itself."""
    errors = []
    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
    except json.JSONDecodeError as e:
        errors.append(ValidationError("nlu_schema_v1.json", "<SCHEMA>", "json", f"Invalid JSON: {e}"))
        return errors
    except FileNotFoundError:
        errors.append(ValidationError("nlu_schema_v1.json", "<SCHEMA>", "file", "Schema file not found."))
        return errors

    # Verify key structural elements
    if schema.get("type") != "object":
        errors.append(ValidationError("nlu_schema_v1.json", "<SCHEMA>", "type", "Root type must be 'object'."))

    required_top = schema.get("required", [])
    expected_top_fields = [
        "example_id", "template_id", "template_family", "language", "split",
        "input_text", "intent", "slots", "expected_rule_id",
        "validation_status", "source_type", "concept_source", "metadata"
    ]
    for field in expected_top_fields:
        if field not in required_top:
            errors.append(ValidationError("nlu_schema_v1.json", "<SCHEMA>", "required",
                                          f"Missing required top-level field: '{field}'."))

    # Verify slots subschema
    slots_props = schema.get("properties", {}).get("slots", {}).get("properties", {})
    for slot_key in CANONICAL_SLOT_KEYS:
        if slot_key not in slots_props:
            errors.append(ValidationError("nlu_schema_v1.json", "<SCHEMA>", "slots",
                                          f"Missing canonical slot definition: '{slot_key}'."))

    return errors


def main():
    """Run full validation suite and print results."""
    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "datasets", "financial_nlu")

    # Fallback: try relative to CWD if the above doesn't work
    if not os.path.isdir(base_dir):
        base_dir = os.path.join("datasets", "financial_nlu")

    schema_path = os.path.join(base_dir, "schemas", "nlu_schema_v1.json")
    templates_dir = os.path.join(base_dir, "templates")

    print("=" * 70)
    print("FINANCIAL NLU DATASET TEMPLATE VALIDATION")
    print("=" * 70)

    # 1. Validate schema
    print("\n[1/2] Validating JSON Schema...")
    schema_errors = validate_schema_file(schema_path)
    if schema_errors:
        for e in schema_errors:
            print(f"  ERROR: {e}")
    else:
        print("  PASS: Schema file is structurally valid.")

    # 2. Validate templates
    print("\n[2/2] Validating template files...")
    total_templates, total_files, tmpl_errors = validate_all_templates(templates_dir)

    if tmpl_errors:
        for e in tmpl_errors:
            print(f"  ERROR: {e}")
    else:
        print("  PASS: All template files are valid.")

    # Summary
    all_errors = schema_errors + tmpl_errors
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print(f"  Schema file:     {'PASS' if not schema_errors else 'FAIL'}")
    print(f"  Template files:  {total_files}")
    print(f"  Total templates: {total_templates}")
    print(f"  Total errors:    {len(all_errors)}")
    print(f"  Overall:         {'PASS' if not all_errors else 'FAIL'}")
    print("=" * 70)

    return 0 if not all_errors else 1


if __name__ == "__main__":
    sys.exit(main())
