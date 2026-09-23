"""
Step 8J Quality Gate: NLU Dataset Expansion Quality & Invariant Tests.

Tests the combined controlled English NLU dataset (100 total records:
22 dry-run records + 78 Batch 02 expansion records).

Verifies:
1. Schema conformance of all records
2. Zero exact or normalized duplicate utterances
3. Zero template leakage across train/val/test partitions
4. Coverage of all 9 canonical intents (with savings_question >= 10)
5. Non-null representation across all 7 canonical slots
6. Enum coverage:
   - employed vs not employed
   - debt vs no debt
   - average spend vs big spend
   - Single vs Married
7. Unknown semantics: missing fields strictly null
8. Zero semantics: explicit 0.0 income preserved and distinct from null
9. Third-party isolation: spouse/partner/parent amounts not assigned to user income
10. Out-of-scope negative isolation: all 7 slots null, expected_rule_id null
11. Language scope: English only (language == 'en')
12. Deterministic engine alignment: ConsultantEngine agrees 100% with expected_rule_id
"""

import json
import os
import re
import string
import pytest

from app.services.consultant_engine import ConsultantEngine, CANONICAL_KB_VERSION, CANONICAL_RULE_IDS
from app.services.consultant_validator import ConsultantInputValidator
from app.security.seed_rule_facts import CONSULTANT_RULES

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW_DIR = os.path.join(WORKSPACE_ROOT, "datasets", "financial_nlu", "raw")
DRY_RUN_FILE = os.path.join(RAW_DIR, "annotation_dry_run.jsonl")
BATCH02_FILE = os.path.join(RAW_DIR, "phase1_batch02.jsonl")

STANDALONE_RULES = [
    dict(r, kb_version=CANONICAL_KB_VERSION) for r in CONSULTANT_RULES
]

CANONICAL_SLOT_KEYS = [
    "monthly_income",
    "monthly_expense",
    "employment_status",
    "debt_status",
    "spending_habit",
    "goal_cost",
    "marital_status",
]

VALID_INTENTS = {
    "financial_consultation",
    "budget_analysis",
    "cashflow_question",
    "savings_question",
    "debt_management",
    "financial_goal",
    "financial_education",
    "out_of_scope_investment",
    "out_of_scope_loan",
}

ENGINE_ROUTABLE_INTENTS = {
    "financial_consultation",
    "budget_analysis",
    "cashflow_question",
    "savings_question",
    "debt_management",
    "financial_goal",
}


def normalize_text(text: str) -> str:
    t = text.lower()
    t = t.translate(str.maketrans("", "", string.punctuation))
    return re.sub(r"\s+", " ", t).strip()


@pytest.fixture(scope="module")
def dry_run_records():
    assert os.path.isfile(DRY_RUN_FILE), f"Missing {DRY_RUN_FILE}"
    with open(DRY_RUN_FILE, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


@pytest.fixture(scope="module")
def batch02_records():
    assert os.path.isfile(BATCH02_FILE), f"Missing {BATCH02_FILE}"
    with open(BATCH02_FILE, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


@pytest.fixture(scope="module")
def combined_records(dry_run_records, batch02_records):
    return dry_run_records + batch02_records


# ==============================================================================
# 1. Corpus Sizing and Schema Integrity
# ==============================================================================

def test_corpus_record_counts(dry_run_records, batch02_records, combined_records):
    assert len(dry_run_records) == 22, f"Dry-run must have 22 records, got {len(dry_run_records)}"
    assert len(batch02_records) == 78, f"Batch 02 must have 78 records, got {len(batch02_records)}"
    assert len(combined_records) == 100, f"Combined corpus must have 100 records, got {len(combined_records)}"


def test_records_schema_structure(combined_records):
    required_top = [
        "example_id", "template_id", "template_family", "language",
        "split", "input_text", "intent", "slots", "expected_rule_id",
        "validation_status", "source_type", "concept_source", "metadata"
    ]
    for rec in combined_records:
        eid = rec.get("example_id")
        for k in required_top:
            assert k in rec, f"Record {eid} missing required key '{k}'"

        assert rec["language"] == "en", f"Record {eid} must be English ('en')"
        assert rec["split"] in ("train", "val", "test", "unassigned")
        assert rec["intent"] in VALID_INTENTS, f"Record {eid} invalid intent: {rec['intent']}"

        slots = rec["slots"]
        assert isinstance(slots, dict), f"Record {eid} slots must be dict"
        for sk in CANONICAL_SLOT_KEYS:
            assert sk in slots, f"Record {eid} missing slot {sk}"


# ==============================================================================
# 2. Duplicate Detection
# ==============================================================================

def test_no_exact_or_normalized_duplicates(combined_records):
    exact = set()
    normalized = set()
    example_ids = set()

    for rec in combined_records:
        eid = rec["example_id"]
        assert eid not in example_ids, f"Duplicate example_id: {eid}"
        example_ids.add(eid)

        txt = rec["input_text"]
        assert txt not in exact, f"Exact duplicate utterance found: '{txt}'"
        exact.add(txt)

        norm = normalize_text(txt)
        assert norm not in normalized, f"Normalized duplicate found: '{norm}'"
        normalized.add(norm)


# ==============================================================================
# 3. Template-Grouped Split Integrity (Zero Leakage Invariant)
# ==============================================================================

def test_template_split_zero_leakage(combined_records):
    template_splits = {}
    for rec in combined_records:
        tid = rec["template_id"]
        sp = rec["split"]
        if tid not in template_splits:
            template_splits[tid] = set()
        template_splits[tid].add(sp)

    leakage = {tid: splits for tid, splits in template_splits.items() if len(splits) > 1}
    assert not leakage, f"Template leakage detected! Templates spanning multiple splits: {leakage}"


# ==============================================================================
# 4. Intent Balance (All 9 Intents Represented)
# ==============================================================================

def test_all_nine_intents_represented(combined_records):
    counts = {i: 0 for i in VALID_INTENTS}
    for rec in combined_records:
        counts[rec["intent"]] += 1

    # Every intent must have at least 5 examples
    for intent, count in counts.items():
        assert count >= 5, f"Intent {intent} has only {count} records; expected >= 5"

    # Specific check: savings_question was 0 in dry run, now must be >= 10
    assert counts["savings_question"] >= 10, f"savings_question must have >= 10, got {counts['savings_question']}"


# ==============================================================================
# 5. Slot Coverage and Enum Values
# ==============================================================================

def test_slot_non_null_coverage(combined_records):
    for sk in CANONICAL_SLOT_KEYS:
        non_null_count = sum(1 for r in combined_records if r["slots"].get(sk) is not None)
        assert non_null_count >= 10, f"Slot {sk} has only {non_null_count} non-null values; expected >= 10"


def test_enum_coverage_balance(combined_records):
    emp_employed = sum(1 for r in combined_records if r["slots"].get("employment_status") == "employed")
    emp_unemployed = sum(1 for r in combined_records if r["slots"].get("employment_status") == "not employed")
    assert emp_employed >= 50, f"Expected >= 50 employed, got {emp_employed}"
    assert emp_unemployed >= 6, f"Expected >= 6 not employed, got {emp_unemployed}"

    debt_yes = sum(1 for r in combined_records if r["slots"].get("debt_status") == "debt")
    debt_no = sum(1 for r in combined_records if r["slots"].get("debt_status") == "no debt")
    debt_null = sum(1 for r in combined_records if r["slots"].get("debt_status") is None)
    assert debt_yes >= 15, f"Expected >= 15 debt, got {debt_yes}"
    assert debt_no >= 6, f"Expected >= 6 no debt, got {debt_no}"
    assert debt_null >= 50, f"Expected >= 50 null debt, got {debt_null}"

    spend_avg = sum(1 for r in combined_records if r["slots"].get("spending_habit") == "average spend")
    spend_big = sum(1 for r in combined_records if r["slots"].get("spending_habit") == "big spend")
    spend_null = sum(1 for r in combined_records if r["slots"].get("spending_habit") is None)
    assert spend_avg >= 6, f"Expected >= 6 average spend, got {spend_avg}"
    assert spend_big >= 6, f"Expected >= 6 big spend, got {spend_big}"
    assert spend_null >= 70, f"Expected >= 70 null spending habit, got {spend_null}"

    mar_single = sum(1 for r in combined_records if r["slots"].get("marital_status") == "Single")
    mar_married = sum(1 for r in combined_records if r["slots"].get("marital_status") == "Married")
    mar_null = sum(1 for r in combined_records if r["slots"].get("marital_status") is None)
    assert mar_single >= 6, f"Expected >= 6 Single, got {mar_single}"
    assert mar_married >= 6, f"Expected >= 6 Married, got {mar_married}"
    assert mar_null >= 70, f"Expected >= 70 null marital status, got {mar_null}"


# ==============================================================================
# 6. Null vs Zero Semantics & Character Spans
# ==============================================================================

def test_zero_vs_missing_income_semantics(combined_records):
    zero_income_recs = [r for r in combined_records if r["slots"].get("monthly_income") == 0.0]
    null_income_recs = [r for r in combined_records if r["slots"].get("monthly_income") is None]

    assert len(zero_income_recs) >= 5, f"Expected >= 5 explicit zero income records, got {len(zero_income_recs)}"
    assert len(null_income_recs) >= 15, f"Expected >= 15 missing income records, got {len(null_income_recs)}"

    for r in zero_income_recs:
        assert r["metadata"].get("numerical_format") == "explicit_zero"
        # Spans must capture '0' or 'zero'
        income_spans = [sp for sp in r.get("slot_spans", []) if sp["slot"] == "monthly_income"]
        assert len(income_spans) >= 1
        assert income_spans[0]["value"] == 0.0


def test_character_span_integrity(combined_records):
    for rec in combined_records:
        txt = rec["input_text"]
        spans = rec.get("slot_spans", [])
        for sp in spans:
            st = sp["start"]
            en = sp["end"]
            raw = sp["raw_text"]
            assert txt[st:en] == raw, f"Span mismatch in {rec['example_id']}: '{txt[st:en]}' != '{raw}'"


# ==============================================================================
# 7. Third-Party and Out-of-Scope Isolation
# ==============================================================================

def test_third_party_income_not_attributed_to_user(combined_records):
    third_party_recs = [r for r in combined_records if r["metadata"].get("ambiguity_type") == "third_party_income"]
    assert len(third_party_recs) >= 1
    for r in third_party_recs:
        # User income must remain null
        assert r["slots"]["monthly_income"] is None
        # No span pointing to third-party amount as user income
        user_income_spans = [sp for sp in r.get("slot_spans", []) if sp["slot"] == "monthly_income"]
        assert len(user_income_spans) == 0


def test_out_of_scope_isolation(combined_records):
    oos_recs = [r for r in combined_records if r["intent"] in ("out_of_scope_investment", "out_of_scope_loan")]
    assert len(oos_recs) == 16, f"Expected 16 out of scope records, got {len(oos_recs)}"
    for r in oos_recs:
        assert r["expected_rule_id"] is None
        for sk in CANONICAL_SLOT_KEYS:
            assert r["slots"][sk] is None, f"OOS record {r['example_id']} has non-null slot {sk}"


# ==============================================================================
# 8. Deterministic ConsultantEngine Alignment
# ==============================================================================

def test_deterministic_consultant_engine_alignment(combined_records):
    for rec in combined_records:
        eid = rec["example_id"]
        slots = rec["slots"]
        expected_rule = rec.get("expected_rule_id")
        intent = rec["intent"]

        if slots.get("monthly_income") is not None and slots.get("monthly_expense") is not None and intent in ENGINE_ROUTABLE_INTENTS:
            norm, err = ConsultantInputValidator.validate(slots, default_lang="en")
            assert not err, f"Record {eid} failed validator: {err}"
            eng_res = ConsultantEngine.evaluate(norm, rules=STANDALONE_RULES)
            calc_rule = eng_res["selected_advice"].rule_id
            assert expected_rule == calc_rule, f"Record {eid} rule mismatch: {expected_rule} != {calc_rule}"
        else:
            assert expected_rule is None, f"Record {eid} should have expected_rule_id=null"
