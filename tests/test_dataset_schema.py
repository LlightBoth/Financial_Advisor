"""
Tests for the NLU Dataset Schema and Controlled Template System (Step 8C).

Verifies:
1. Schema files exist and parse as valid JSON.
2. All template files exist and parse as valid JSON arrays.
3. Template IDs are globally unique across all template files.
4. All intents are from the canonical 9-intent taxonomy.
5. All slot names match the canonical 7-slot taxonomy.
6. All enum slot values match ConsultantValidator canonical values.
7. Language is 'en' for Phase 1.
8. Null policies are represented correctly in missing_info templates.
9. Out-of-scope templates use the correct intent.
10. No template claims to be a trained model artifact.

Does NOT modify existing tests or production code.
"""

import json
import os
import pytest


# ──────────────────────────────────────────────────────────────
# Constants from production code (verified, not assumed)
# ──────────────────────────────────────────────────────────────

CANONICAL_SLOT_KEYS = frozenset([
    "monthly_income", "monthly_expense", "employment_status",
    "debt_status", "spending_habit", "goal_cost", "marital_status",
])

VALID_INTENTS = frozenset([
    "financial_consultation", "budget_analysis", "cashflow_question",
    "savings_question", "debt_management", "financial_goal",
    "financial_education", "out_of_scope_investment", "out_of_scope_loan",
])

VALID_TEMPLATE_FAMILIES = frozenset([
    "TF_BUDGET", "TF_CASHFLOW", "TF_DEBT", "TF_SAVINGS",
    "TF_EMPLOYMENT", "TF_HOUSEHOLD", "TF_MISSING_INFO", "TF_OUT_OF_SCOPE",
])

ENUM_SLOTS = {
    "employment_status": {"employed", "not employed"},
    "debt_status": {"debt", "no debt"},
    "spending_habit": {"average spend", "big spend"},
    "marital_status": {"Single", "Married"},
}

NUMERIC_SLOTS = {"monthly_income", "monthly_expense", "goal_cost"}

BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                        "datasets", "financial_nlu")

SCHEMA_PATH = os.path.join(BASE_DIR, "schemas", "nlu_schema_v1.json")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

TEMPLATE_FILES = [
    "budget_templates.json",
    "cashflow_templates.json",
    "debt_templates.json",
    "savings_templates.json",
    "employment_templates.json",
    "household_templates.json",
    "missing_info_templates.json",
    "out_of_scope_templates.json",
]


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────

def load_all_templates():
    """Load all templates from all template files."""
    all_templates = []
    for fname in TEMPLATE_FILES:
        fpath = os.path.join(TEMPLATES_DIR, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            templates = json.load(f)
        for t in templates:
            t["_source_file"] = fname
        all_templates.extend(templates)
    return all_templates


# ──────────────────────────────────────────────────────────────
# 1. Schema file existence and validity
# ──────────────────────────────────────────────────────────────

class TestSchemaFile:
    """Tests for the JSON Schema definition file."""

    def test_schema_file_exists(self):
        assert os.path.isfile(SCHEMA_PATH), \
            f"Schema file not found: {SCHEMA_PATH}"

    def test_schema_is_valid_json(self):
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema = json.load(f)
        assert isinstance(schema, dict), "Schema root must be a JSON object"

    def test_schema_has_required_top_fields(self):
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema = json.load(f)
        required = schema.get("required", [])
        expected = [
            "example_id", "template_id", "template_family", "language",
            "split", "input_text", "intent", "slots", "expected_rule_id",
            "validation_status", "source_type", "concept_source", "metadata"
        ]
        for field in expected:
            assert field in required, f"Missing required field: {field}"

    def test_schema_has_all_canonical_slots(self):
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema = json.load(f)
        slot_props = schema["properties"]["slots"]["properties"]
        for slot_key in CANONICAL_SLOT_KEYS:
            assert slot_key in slot_props, f"Missing canonical slot: {slot_key}"

    def test_schema_enforces_english_only(self):
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema = json.load(f)
        lang_enum = schema["properties"]["language"]["enum"]
        assert lang_enum == ["en"], \
            f"Phase 1 must be English only. Got: {lang_enum}"

    def test_schema_enforces_canonical_intents(self):
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema = json.load(f)
        intent_enum = set(schema["properties"]["intent"]["enum"])
        assert intent_enum == VALID_INTENTS, \
            f"Intent enum mismatch. Schema: {intent_enum}, Expected: {VALID_INTENTS}"


# ──────────────────────────────────────────────────────────────
# 2. Template file existence and parsing
# ──────────────────────────────────────────────────────────────

class TestTemplateFiles:
    """Tests for template file existence and JSON validity."""

    @pytest.mark.parametrize("filename", TEMPLATE_FILES)
    def test_template_file_exists(self, filename):
        fpath = os.path.join(TEMPLATES_DIR, filename)
        assert os.path.isfile(fpath), f"Template file not found: {fpath}"

    @pytest.mark.parametrize("filename", TEMPLATE_FILES)
    def test_template_file_is_valid_json_array(self, filename):
        fpath = os.path.join(TEMPLATES_DIR, filename)
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, list), f"{filename} root must be a JSON array"
        assert len(data) > 0, f"{filename} must contain at least one template"

    @pytest.mark.parametrize("filename", TEMPLATE_FILES)
    def test_template_file_has_at_least_five_templates(self, filename):
        fpath = os.path.join(TEMPLATES_DIR, filename)
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert len(data) >= 5, \
            f"{filename} has only {len(data)} templates. Minimum 5 required."


# ──────────────────────────────────────────────────────────────
# 3. Template ID uniqueness
# ──────────────────────────────────────────────────────────────

class TestTemplateIDUniqueness:
    """Verify template_id is globally unique across all files."""

    def test_no_duplicate_template_ids(self):
        all_templates = load_all_templates()
        seen_ids = {}
        duplicates = []
        for t in all_templates:
            tid = t.get("template_id")
            src = t.get("_source_file")
            if tid in seen_ids:
                duplicates.append(f"{tid} in {src} (first seen in {seen_ids[tid]})")
            else:
                seen_ids[tid] = src
        assert len(duplicates) == 0, \
            f"Duplicate template_ids found: {duplicates}"


# ──────────────────────────────────────────────────────────────
# 4-8. Template content validation
# ──────────────────────────────────────────────────────────────

class TestTemplateContent:
    """Validate content of every template against canonical contract."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.all_templates = load_all_templates()

    def test_all_intents_are_valid(self):
        invalid = []
        for t in self.all_templates:
            if t.get("intent") not in VALID_INTENTS:
                invalid.append(f"{t['template_id']}: {t.get('intent')}")
        assert len(invalid) == 0, f"Invalid intents: {invalid}"

    def test_all_template_families_are_valid(self):
        invalid = []
        for t in self.all_templates:
            if t.get("template_family") not in VALID_TEMPLATE_FAMILIES:
                invalid.append(f"{t['template_id']}: {t.get('template_family')}")
        assert len(invalid) == 0, f"Invalid families: {invalid}"

    def test_all_required_slots_are_canonical(self):
        invalid = []
        for t in self.all_templates:
            for s in t.get("required_slots", []):
                if s not in CANONICAL_SLOT_KEYS:
                    invalid.append(f"{t['template_id']}: {s}")
        assert len(invalid) == 0, f"Non-canonical required_slots: {invalid}"

    def test_all_languages_are_english(self):
        non_english = []
        for t in self.all_templates:
            if t.get("language") != "en":
                non_english.append(f"{t['template_id']}: {t.get('language')}")
        assert len(non_english) == 0, \
            f"Phase 1 requires language='en'. Non-English: {non_english}"

    def test_enum_slot_values_are_valid(self):
        invalid = []
        for t in self.all_templates:
            esb = t.get("expected_slot_behavior", {})
            for slot_key, valid_vals in ENUM_SLOTS.items():
                val = esb.get(slot_key)
                if val is not None and val not in valid_vals:
                    invalid.append(f"{t['template_id']}: {slot_key}={val}")
        assert len(invalid) == 0, f"Invalid enum values: {invalid}"

    def test_numeric_slot_values_are_non_negative(self):
        invalid = []
        for t in self.all_templates:
            esb = t.get("expected_slot_behavior", {})
            for slot_key in NUMERIC_SLOTS:
                val = esb.get(slot_key)
                if val is not None and isinstance(val, (int, float)) and val < 0:
                    invalid.append(f"{t['template_id']}: {slot_key}={val}")
        assert len(invalid) == 0, f"Negative numeric values: {invalid}"

    def test_text_patterns_are_non_empty(self):
        empty = []
        for t in self.all_templates:
            tp = t.get("text_pattern", "")
            if not isinstance(tp, str) or len(tp.strip()) == 0:
                empty.append(t.get("template_id"))
        assert len(empty) == 0, f"Empty text patterns: {empty}"

    def test_no_protected_control_fields(self):
        """Templates must NOT contain expert-system control fields."""
        PROTECTED = {"rule_id", "priority", "certainty", "conditions",
                     "kb_version", "is_active"}
        violations = []
        for t in self.all_templates:
            for pf in PROTECTED:
                if pf in t:
                    violations.append(f"{t['template_id']}: {pf}")
        assert len(violations) == 0, \
            f"Templates contain protected control fields: {violations}"


# ──────────────────────────────────────────────────────────────
# 9. Out-of-scope intent validation
# ──────────────────────────────────────────────────────────────

class TestOutOfScopeTemplates:
    """Verify out-of-scope templates use the correct intents."""

    def test_oos_templates_have_correct_intents(self):
        fpath = os.path.join(TEMPLATES_DIR, "out_of_scope_templates.json")
        with open(fpath, "r", encoding="utf-8") as f:
            templates = json.load(f)
        oos_intents = {"out_of_scope_investment", "out_of_scope_loan"}
        invalid = []
        for t in templates:
            if t.get("intent") not in oos_intents:
                invalid.append(f"{t['template_id']}: {t.get('intent')}")
        assert len(invalid) == 0, \
            f"OOS templates with non-OOS intents: {invalid}"

    def test_oos_templates_have_all_null_slots(self):
        fpath = os.path.join(TEMPLATES_DIR, "out_of_scope_templates.json")
        with open(fpath, "r", encoding="utf-8") as f:
            templates = json.load(f)
        violations = []
        for t in templates:
            esb = t.get("expected_slot_behavior", {})
            for slot_key in CANONICAL_SLOT_KEYS:
                if esb.get(slot_key) is not None:
                    violations.append(f"{t['template_id']}: {slot_key}={esb[slot_key]}")
        assert len(violations) == 0, \
            f"OOS templates must have all-null slots: {violations}"


# ──────────────────────────────────────────────────────────────
# 10. Null policy in missing_info templates
# ──────────────────────────────────────────────────────────────

class TestMissingInfoNullPolicy:
    """Verify missing_info templates correctly represent the null invariant."""

    def test_missing_info_has_ambiguity_or_null_policy(self):
        fpath = os.path.join(TEMPLATES_DIR, "missing_info_templates.json")
        with open(fpath, "r", encoding="utf-8") as f:
            templates = json.load(f)
        missing_policy = []
        for t in templates:
            if "ambiguity_policy" not in t:
                missing_policy.append(t.get("template_id"))
        assert len(missing_policy) == 0, \
            f"Missing ambiguity_policy in templates: {missing_policy}"

    def test_no_template_claims_model_artifact(self):
        """No template should indicate it is a trained model artifact."""
        all_templates = load_all_templates()
        violations = []
        for t in all_templates:
            st = t.get("source_type", "")
            if "model" in st.lower() or "checkpoint" in st.lower():
                violations.append(f"{t['template_id']}: source_type={st}")
        assert len(violations) == 0, \
            f"Templates claiming to be model artifacts: {violations}"
