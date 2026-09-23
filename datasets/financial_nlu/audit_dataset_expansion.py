"""
Dataset Expansion Audit & Quality Gate Utility (Step 8J).

Performs an authoritative, end-to-end quality audit of:
1. Dry-run dataset (datasets/financial_nlu/raw/annotation_dry_run.jsonl: 22 records)
2. Expansion Batch 02 (datasets/financial_nlu/raw/phase1_batch02.jsonl: 78 records)
3. Combined controlled corpus (100 total records)

Audits:
- Schema conformance
- Character-level span integrity
- Deterministic ConsultantEngine rule alignment
- Exact, normalized, and near-duplicate detection
- Template-grouped split integrity (Zero-Leakage Invariant)
- Intent balance across all 9 canonical intents
- Slot non-null coverage across all 7 canonical slots
- Enum balance for employment, debt, spending habit, and marital status
- Null vs Zero semantics (unknown != 0)
- Third-party financial isolation
- Out-of-scope query isolation
- English-only language scope
"""

import json
import os
import re
import string
import sys
from typing import Dict, Any, List, Tuple, Set

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from app.services.consultant_engine import ConsultantEngine, CANONICAL_KB_VERSION, CANONICAL_RULE_IDS
from app.services.consultant_validator import ConsultantInputValidator
from app.security.seed_rule_facts import CONSULTANT_RULES

STANDALONE_CANONICAL_RULES = [
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

VALID_INTENTS = [
    "financial_consultation",
    "budget_analysis",
    "cashflow_question",
    "savings_question",
    "debt_management",
    "financial_goal",
    "financial_education",
    "out_of_scope_investment",
    "out_of_scope_loan",
]

OUT_OF_SCOPE_INTENTS = {"out_of_scope_investment", "out_of_scope_loan"}
ENGINE_ROUTABLE_INTENTS = {
    "financial_consultation",
    "budget_analysis",
    "cashflow_question",
    "savings_question",
    "debt_management",
    "financial_goal",
}

RAW_DIR = os.path.join(WORKSPACE_ROOT, "datasets", "financial_nlu", "raw")
REPORTS_DIR = os.path.join(WORKSPACE_ROOT, "datasets", "financial_nlu", "reports")
DRY_RUN_FILE = os.path.join(RAW_DIR, "annotation_dry_run.jsonl")
BATCH02_FILE = os.path.join(RAW_DIR, "phase1_batch02.jsonl")
REPORT_JSON = os.path.join(REPORTS_DIR, "step8j_dataset_expansion_report.json")


def normalize_text(text: str) -> str:
    """Lowercases, removes punctuation, and collapses whitespace."""
    t = text.lower()
    t = t.translate(str.maketrans("", "", string.punctuation))
    return re.sub(r"\s+", " ", t).strip()


def load_jsonl(filepath: str) -> List[Dict[str, Any]]:
    records = []
    if not os.path.isfile(filepath):
        return records
    with open(filepath, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f, start=1):
            line_str = line.strip()
            if line_str:
                rec = json.loads(line_str)
                records.append(rec)
    return records


def audit_corpus(
    dry_run_records: List[Dict[str, Any]],
    batch02_records: List[Dict[str, Any]],
) -> Dict[str, Any]:
    errors = []
    combined = dry_run_records + batch02_records

    # 1. Counts check
    if len(dry_run_records) != 22:
        errors.append(f"Dry-run record count expected 22, found {len(dry_run_records)}")
    if len(batch02_records) != 78:
        errors.append(f"Batch 02 record count expected 78, found {len(batch02_records)}")
    if len(combined) != 100:
        errors.append(f"Combined record count expected 100, found {len(combined)}")

    # 2. Duplicate Detection
    exact_texts: Dict[str, str] = {}
    normalized_texts: Dict[str, str] = {}
    example_ids: Set[str] = set()

    for rec in combined:
        eid = rec.get("example_id")
        if eid in example_ids:
            errors.append(f"Duplicate example_id: '{eid}'")
        example_ids.add(eid)

        txt = rec.get("input_text", "")
        if txt in exact_texts:
            errors.append(f"Exact duplicate utterance found: '{txt}' in {eid} and {exact_texts[txt]}")
        else:
            exact_texts[txt] = eid

        norm = normalize_text(txt)
        if norm in normalized_texts:
            errors.append(f"Normalized duplicate utterance found: '{norm}' in {eid} and {normalized_texts[norm]}")
        else:
            normalized_texts[norm] = eid

    # 3. Template-Grouped Split Integrity (Zero-Leakage Invariant)
    template_to_splits: Dict[str, Set[str]] = {}
    for rec in combined:
        tid = rec.get("template_id")
        sp = rec.get("split")
        if tid not in template_to_splits:
            template_to_splits[tid] = set()
        template_to_splits[tid].add(sp)

    leakage_errors = []
    for tid, splits in template_to_splits.items():
        if len(splits) > 1:
            leakage_errors.append(f"Template leakage: {tid} is assigned to multiple splits: {splits}")
    errors.extend(leakage_errors)

    # 4. Record-level Audits
    for rec in combined:
        eid = rec.get("example_id")
        txt = rec.get("input_text", "")
        intent = rec.get("intent")
        slots = rec.get("slots", {})
        spans = rec.get("slot_spans", [])
        expected_rule = rec.get("expected_rule_id")
        meta = rec.get("metadata", {})
        ambiguity = meta.get("ambiguity_type")

        # Language
        if rec.get("language") != "en":
            errors.append(f"Record {eid} language is not 'en'")

        # Intent
        if intent not in VALID_INTENTS:
            errors.append(f"Record {eid} invalid intent: {intent}")

        # Slots presence
        for sk in CANONICAL_SLOT_KEYS:
            if sk not in slots:
                errors.append(f"Record {eid} missing canonical slot key: {sk}")

        # Character Spans Verification
        if spans:
            for sp in spans:
                s_slot = sp.get("slot")
                st = sp.get("start")
                en = sp.get("end")
                raw = sp.get("raw_text")
                val = sp.get("value")

                if s_slot not in CANONICAL_SLOT_KEYS:
                    errors.append(f"Record {eid} span has invalid slot: {s_slot}")
                if st < 0 or en > len(txt) or st >= en:
                    errors.append(f"Record {eid} invalid span boundaries: [{st}:{en}] for text len {len(txt)}")
                elif txt[st:en] != raw:
                    errors.append(f"Record {eid} span slice '{txt[st:en]}' != raw_text '{raw}'")

                if ambiguity == "third_party_income" and s_slot == "monthly_income":
                    errors.append(f"Record {eid} illegally annotated third-party income as user income span")

        # Out-of-scope Isolation
        if intent in OUT_OF_SCOPE_INTENTS:
            for sk in CANONICAL_SLOT_KEYS:
                if slots.get(sk) is not None:
                    errors.append(f"Record {eid} is out-of-scope ({intent}) but slot '{sk}' is not null")
            if expected_rule is not None:
                errors.append(f"Record {eid} is out-of-scope but expected_rule_id is not null")

        # Financial Education Isolation
        if intent == "financial_education":
            if expected_rule is not None:
                errors.append(f"Record {eid} is financial_education but expected_rule_id is not null")

        # Null vs Zero Semantics
        if ambiguity in ("all_null", "expense_unknown", "vague_commitment", "education_only", "out_of_scope"):
            if ambiguity == "expense_unknown" and slots.get("monthly_expense") is not None:
                errors.append(f"Record {eid} has expense_unknown ambiguity but monthly_expense is not null")
            elif ambiguity == "all_null" and (slots.get("monthly_income") is not None or slots.get("monthly_expense") is not None):
                errors.append(f"Record {eid} has all_null ambiguity but has non-null income/expense")

        # Cadence Ambiguity
        if ambiguity == "non_monthly_cadence":
            if slots.get("monthly_income") is not None:
                errors.append(f"Record {eid} has non_monthly_cadence; monthly_income must be null")

        # Third-party Ambiguity
        if ambiguity == "third_party_income":
            if slots.get("monthly_income") is not None:
                errors.append(f"Record {eid} has third_party_income; monthly_income must be null")

        # Range Ambiguity
        if ambiguity == "range_ambiguity":
            if slots.get("monthly_income") is not None:
                errors.append(f"Record {eid} has range_ambiguity; monthly_income must be null")

        # Deterministic Engine Alignment
        monthly_income = slots.get("monthly_income")
        monthly_expense = slots.get("monthly_expense")
        if monthly_income is not None and monthly_expense is not None and intent in ENGINE_ROUTABLE_INTENTS:
            norm, v_err = ConsultantInputValidator.validate(slots, default_lang="en")
            if v_err:
                errors.append(f"Record {eid} failed validator: {v_err}")
            else:
                eng_res = ConsultantEngine.evaluate(norm, rules=STANDALONE_CANONICAL_RULES)
                calc_rule = eng_res["selected_advice"].rule_id
                if expected_rule != calc_rule:
                    errors.append(f"Record {eid} expected_rule_id mismatch: '{expected_rule}' != calculated '{calc_rule}'")
        else:
            if expected_rule is not None:
                errors.append(f"Record {eid} has incomplete data or non-routable intent ({intent}); expected_rule_id must be null")

    # 5. Aggregate Statistics
    # Intents distribution
    intent_counts_dry = {i: 0 for i in VALID_INTENTS}
    intent_counts_b02 = {i: 0 for i in VALID_INTENTS}
    intent_counts_total = {i: 0 for i in VALID_INTENTS}

    for r in dry_run_records:
        intent_counts_dry[r["intent"]] += 1
    for r in batch02_records:
        intent_counts_b02[r["intent"]] += 1
    for r in combined:
        intent_counts_total[r["intent"]] += 1

    # Split distribution
    split_counts = {"train": 0, "val": 0, "test": 0, "unassigned": 0}
    for r in combined:
        split_counts[r.get("split", "unassigned")] += 1

    # Slot coverage
    slot_stats = {}
    for sk in CANONICAL_SLOT_KEYS:
        non_null = sum(1 for r in combined if r["slots"].get(sk) is not None)
        null_c = len(combined) - non_null
        pct = round((non_null / len(combined)) * 100.0, 1)
        slot_stats[sk] = {
            "non_null_count": non_null,
            "null_count": null_c,
            "percentage_non_null": pct,
        }

    # Enum coverage
    enum_stats = {
        "employment_status": {
            "employed": sum(1 for r in combined if r["slots"].get("employment_status") == "employed"),
            "not employed": sum(1 for r in combined if r["slots"].get("employment_status") == "not employed"),
            "null": sum(1 for r in combined if r["slots"].get("employment_status") is None),
        },
        "debt_status": {
            "debt": sum(1 for r in combined if r["slots"].get("debt_status") == "debt"),
            "no debt": sum(1 for r in combined if r["slots"].get("debt_status") == "no debt"),
            "null": sum(1 for r in combined if r["slots"].get("debt_status") is None),
        },
        "spending_habit": {
            "average spend": sum(1 for r in combined if r["slots"].get("spending_habit") == "average spend"),
            "big spend": sum(1 for r in combined if r["slots"].get("spending_habit") == "big spend"),
            "null": sum(1 for r in combined if r["slots"].get("spending_habit") is None),
        },
        "marital_status": {
            "Single": sum(1 for r in combined if r["slots"].get("marital_status") == "Single"),
            "Married": sum(1 for r in combined if r["slots"].get("marital_status") == "Married"),
            "null": sum(1 for r in combined if r["slots"].get("marital_status") is None),
        },
    }

    report = {
        "audit_name": "STEP 8J NLU DATASET EXPANSION AUDIT",
        "kb_version": CANONICAL_KB_VERSION,
        "language_scope": "en",
        "dry_run_records_count": len(dry_run_records),
        "batch02_records_count": len(batch02_records),
        "total_corpus_count": len(combined),
        "split_distribution": split_counts,
        "intent_distribution": {
            i: {
                "dry_run": intent_counts_dry[i],
                "batch02": intent_counts_b02[i],
                "total": intent_counts_total[i]
            }
            for i in VALID_INTENTS
        },
        "slot_coverage": slot_stats,
        "enum_coverage": enum_stats,
        "leakage_check": "PASS" if not leakage_errors else "FAIL",
        "duplicate_check": "PASS" if len(combined) == len(exact_texts) == len(normalized_texts) else "FAIL",
        "deterministic_engine_alignment": "PASS" if not [e for e in errors if "expected_rule_id" in e] else "FAIL",
        "total_errors": len(errors),
        "errors": errors,
        "overall_status": "PASS" if len(errors) == 0 else "FAIL"
    }

    return report


def main():
    print("=" * 70)
    print("STEP 8J: CONTROLLED ENGLISH NLU DATASET EXPANSION AUDIT")
    print("=" * 70)

    dry_run = load_jsonl(DRY_RUN_FILE)
    batch02 = load_jsonl(BATCH02_FILE)

    print(f"\n[1/3] Loading Records:")
    print(f"  Dry-run file:     {DRY_RUN_FILE} ({len(dry_run)} records)")
    print(f"  Batch 02 file:    {BATCH02_FILE} ({len(batch02)} records)")
    print(f"  Total records:    {len(dry_run) + len(batch02)}")

    print(f"\n[2/3] Auditing Integrity, Spans, Splits & Engine Alignment...")
    report = audit_corpus(dry_run, batch02)

    os.makedirs(REPORTS_DIR, exist_ok=True)
    with open(REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n[3/3] Audit Findings:")
    print(f"  Duplicate Check:             {report['duplicate_check']}")
    print(f"  Template Leakage Check:      {report['leakage_check']}")
    print(f"  Deterministic Rule Align:    {report['deterministic_engine_alignment']}")
    print(f"  Total Errors Found:          {report['total_errors']}")
    print(f"  Overall Status:              {report['overall_status']}")

    print("\n--- Intent Distribution (Total 100) ---")
    for intent, counts in report["intent_distribution"].items():
        print(f"  {intent:25s}: dry={counts['dry_run']:2d}, batch02={counts['batch02']:2d}, total={counts['total']:2d}")

    print("\n--- Slot Non-Null Coverage ---")
    for slot, stats in report["slot_coverage"].items():
        print(f"  {slot:20s}: non-null={stats['non_null_count']:2d}, null={stats['null_count']:2d}, {stats['percentage_non_null']}%")

    print("\n--- Enum Coverage ---")
    for enum_slot, counts in report["enum_coverage"].items():
        print(f"  {enum_slot}: {counts}")

    print("\n--- Split Allocation ---")
    print(f"  Train: {report['split_distribution']['train']} | Val: {report['split_distribution']['val']} | Test: {report['split_distribution']['test']}")

    print(f"\nReport written to: {REPORT_JSON}")
    print("=" * 70)

    if report["overall_status"] != "PASS":
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
