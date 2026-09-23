"""
Step 8K: Deterministic NLU Baseline & Evaluation Utility.

Performs authoritative evaluation of NLU predictions against the ground-truth
controlled English NLU dataset (100 total records: annotation_dry_run.jsonl + phase1_batch02.jsonl).

Evaluation Metrics:
- Intent Accuracy & Macro-F1 (across all 9 canonical intents)
- Per-Slot Accuracy & Slot Micro-F1 (across all 7 canonical slots)
- Full Structured-Output Exact Match (intent + all 7 slots match exactly)
- Null Preservation Accuracy (unknown fields remain null)
- Zero Preservation Accuracy (explicit 0.0 remains 0.0)
- Third-Party Isolation Accuracy (user income remains null)
- Non-Monthly Cadence Safety (annual/weekly/hourly income remains null)
- Out-of-Scope Isolation (investment & loan queries)
- Slice-Level Metrics (across 14 defined evaluation slices)

Guarantees:
- Pure evaluation and metric calculation only.
- No ML frameworks, no model creation, no external APIs.
- Production expert engine logic and database schema remain untouched.
"""

import json
import os
import sys
from typing import Dict, Any, List, Optional, Set, Tuple

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

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

RAW_DIR = os.path.join(WORKSPACE_ROOT, "datasets", "financial_nlu", "raw")
REPORTS_DIR = os.path.join(WORKSPACE_ROOT, "datasets", "financial_nlu", "reports")
DRY_RUN_FILE = os.path.join(RAW_DIR, "annotation_dry_run.jsonl")
BATCH02_FILE = os.path.join(RAW_DIR, "phase1_batch02.jsonl")
BASELINE_REPORT_JSON = os.path.join(REPORTS_DIR, "step8k_baseline_evaluation.json")


def load_jsonl(filepath: str) -> List[Dict[str, Any]]:
    records = []
    if not os.path.isfile(filepath):
        return records
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if line_str:
                records.append(json.loads(line_str))
    return records


def load_ground_truth_corpus() -> List[Dict[str, Any]]:
    """Loads combined 100-record ground truth corpus."""
    dry_run = load_jsonl(DRY_RUN_FILE)
    batch02 = load_jsonl(BATCH02_FILE)
    return dry_run + batch02


# ──────────────────────────────────────────────────────────────
# Metric Calculations
# ──────────────────────────────────────────────────────────────

def compute_intent_metrics(
    expected_intents: List[str],
    predicted_intents: List[str]
) -> Dict[str, Any]:
    """Computes intent accuracy and per-intent precision, recall, F1, and macro-F1."""
    assert len(expected_intents) == len(predicted_intents)
    total = len(expected_intents)
    if total == 0:
        return {"accuracy": 0.0, "macro_f1": 0.0, "per_intent": {}}

    correct = sum(1 for e, p in zip(expected_intents, predicted_intents) if e == p)
    accuracy = correct / total

    per_intent = {}
    f1_list = []

    for intent in VALID_INTENTS:
        tp = sum(1 for e, p in zip(expected_intents, predicted_intents) if e == intent and p == intent)
        fp = sum(1 for e, p in zip(expected_intents, predicted_intents) if e != intent and p == intent)
        fn = sum(1 for e, p in zip(expected_intents, predicted_intents) if e == intent and p != intent)
        support = sum(1 for e in expected_intents if e == intent)

        prec = tp / (tp + fp) if (tp + fp) > 0 else (1.0 if support == 0 and fp == 0 else 0.0)
        rec = tp / (tp + fn) if (tp + fn) > 0 else (1.0 if support == 0 else 0.0)
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

        per_intent[intent] = {
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "support": support,
        }
        if support > 0:
            f1_list.append(f1)

    macro_f1 = sum(f1_list) / len(f1_list) if f1_list else 0.0

    return {
        "accuracy": round(accuracy, 4),
        "macro_f1": round(macro_f1, 4),
        "correct_count": correct,
        "total_count": total,
        "per_intent": per_intent,
    }


def compute_slot_metrics(
    expected_slots_list: List[Dict[str, Any]],
    predicted_slots_list: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Computes per-slot exact accuracy and global slot micro-precision, recall, and F1."""
    assert len(expected_slots_list) == len(predicted_slots_list)
    total_examples = len(expected_slots_list)

    per_slot_accuracy = {}
    micro_tp = 0
    micro_fp = 0
    micro_fn = 0

    for slot in CANONICAL_SLOT_KEYS:
        slot_correct = 0
        for exp_dict, pred_dict in zip(expected_slots_list, predicted_slots_list):
            e_val = exp_dict.get(slot)
            p_val = pred_dict.get(slot) if pred_dict else None

            # Equality check
            if e_val == p_val:
                slot_correct += 1

            # Micro-F1 tracking (non-null slot extractions)
            if e_val is not None and p_val is not None and e_val == p_val:
                micro_tp += 1
            elif e_val is not None and (p_val is None or e_val != p_val):
                micro_fn += 1
                if p_val is not None:
                    micro_fp += 1
            elif e_val is None and p_val is not None:
                micro_fp += 1

        per_slot_accuracy[slot] = round(slot_correct / total_examples, 4) if total_examples > 0 else 0.0

    micro_prec = micro_tp / (micro_tp + micro_fp) if (micro_tp + micro_fp) > 0 else (1.0 if micro_fn == 0 else 0.0)
    micro_rec = micro_tp / (micro_tp + micro_fn) if (micro_tp + micro_fn) > 0 else (1.0 if micro_tp == 0 else 0.0)
    micro_f1 = (2 * micro_prec * micro_rec) / (micro_prec + micro_rec) if (micro_prec + micro_rec) > 0 else 0.0

    return {
        "per_slot_accuracy": per_slot_accuracy,
        "micro_precision": round(micro_prec, 4),
        "micro_recall": round(micro_rec, 4),
        "micro_f1": round(micro_f1, 4),
        "micro_tp": micro_tp,
        "micro_fp": micro_fp,
        "micro_fn": micro_fn,
    }


def compute_structured_exact_match(
    expected_records: List[Dict[str, Any]],
    predicted_records: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Full structured output exact match: intent correct AND all 7 slots match exactly."""
    assert len(expected_records) == len(predicted_records)
    total = len(expected_records)
    if total == 0:
        return {"exact_match_count": 0, "total": 0, "exact_match_rate": 0.0}

    exact_matches = 0
    for exp, pred in zip(expected_records, predicted_records):
        intent_match = (exp.get("intent") == pred.get("intent"))
        e_slots = exp.get("slots", {})
        p_slots = pred.get("slots", {}) if pred else {}

        slots_match = all(e_slots.get(s) == p_slots.get(s) for s in CANONICAL_SLOT_KEYS)

        if intent_match and slots_match:
            exact_matches += 1

    return {
        "exact_match_count": exact_matches,
        "total": total,
        "exact_match_rate": round(exact_matches / total, 4),
    }


def compute_semantic_invariants_metrics(
    expected_records: List[Dict[str, Any]],
    predicted_records: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Computes null preservation, zero preservation, third-party isolation, and cadence safety."""
    assert len(expected_records) == len(predicted_records)

    # 1. Null Preservation Accuracy
    total_expected_nulls = 0
    preserved_nulls = 0
    for exp, pred in zip(expected_records, predicted_records):
        e_slots = exp.get("slots", {})
        p_slots = pred.get("slots", {}) if pred else {}
        for s in CANONICAL_SLOT_KEYS:
            if e_slots.get(s) is None:
                total_expected_nulls += 1
                if p_slots.get(s) is None:
                    preserved_nulls += 1

    null_preservation_acc = preserved_nulls / total_expected_nulls if total_expected_nulls > 0 else 1.0

    # 2. Zero Preservation Accuracy (Explicit 0.0)
    total_expected_zeros = 0
    preserved_zeros = 0
    for exp, pred in zip(expected_records, predicted_records):
        e_slots = exp.get("slots", {})
        p_slots = pred.get("slots", {}) if pred else {}
        for s in CANONICAL_SLOT_KEYS:
            if e_slots.get(s) == 0.0:
                total_expected_zeros += 1
                if p_slots.get(s) == 0.0:
                    preserved_zeros += 1

    zero_preservation_acc = preserved_zeros / total_expected_zeros if total_expected_zeros > 0 else 1.0

    # 3. Third-party Isolation Accuracy
    third_party_recs = [
        (e, p) for e, p in zip(expected_records, predicted_records)
        if e.get("metadata", {}).get("ambiguity_type") == "third_party_income"
    ]
    tp_safe = 0
    for e, p in third_party_recs:
        p_slots = p.get("slots", {}) if p else {}
        # User income must NOT be populated with third-party income
        if p_slots.get("monthly_income") is None:
            tp_safe += 1

    tp_isolation_acc = tp_safe / len(third_party_recs) if third_party_recs else 1.0

    # 4. Non-monthly Cadence Safety
    cadence_recs = [
        (e, p) for e, p in zip(expected_records, predicted_records)
        if e.get("metadata", {}).get("ambiguity_type") == "non_monthly_cadence"
    ]
    cadence_safe = 0
    for e, p in cadence_recs:
        p_slots = p.get("slots", {}) if p else {}
        if p_slots.get("monthly_income") is None:
            cadence_safe += 1

    cadence_safety_acc = cadence_safe / len(cadence_recs) if cadence_recs else 1.0

    # 5. Out-of-Scope Isolation
    oos_invest_recs = [
        (e, p) for e, p in zip(expected_records, predicted_records)
        if e.get("intent") == "out_of_scope_investment"
    ]
    invest_detected = sum(1 for e, p in oos_invest_recs if p.get("intent") == "out_of_scope_investment")
    invest_acc = invest_detected / len(oos_invest_recs) if oos_invest_recs else 1.0

    oos_loan_recs = [
        (e, p) for e, p in zip(expected_records, predicted_records)
        if e.get("intent") == "out_of_scope_loan"
    ]
    loan_detected = sum(1 for e, p in oos_loan_recs if p.get("intent") == "out_of_scope_loan")
    loan_acc = loan_detected / len(oos_loan_recs) if oos_loan_recs else 1.0

    return {
        "null_preservation_accuracy": round(null_preservation_acc, 4),
        "null_preservation_count": f"{preserved_nulls}/{total_expected_nulls}",
        "zero_preservation_accuracy": round(zero_preservation_acc, 4),
        "zero_preservation_count": f"{preserved_zeros}/{total_expected_zeros}",
        "third_party_isolation_accuracy": round(tp_isolation_acc, 4),
        "third_party_isolation_count": f"{tp_safe}/{len(third_party_recs)}",
        "non_monthly_cadence_safety": round(cadence_safety_acc, 4),
        "non_monthly_cadence_count": f"{cadence_safe}/{len(cadence_recs)}",
        "oos_investment_accuracy": round(invest_acc, 4),
        "oos_loan_accuracy": round(loan_acc, 4),
    }


def compute_slice_metrics(
    expected_records: List[Dict[str, Any]],
    predicted_records: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Computes exact-match and intent accuracy across 14 fine-grained evaluation slices."""
    assert len(expected_records) == len(predicted_records)

    slices_def = {
        "1_simple_direct_requests": lambda e: (
            e.get("intent") in ["financial_consultation", "budget_analysis", "cashflow_question"]
            and not e.get("metadata", {}).get("has_missing_critical")
            and e.get("metadata", {}).get("numerical_format") == "standard"
            and not e.get("metadata", {}).get("ambiguity_type")
        ),
        "2_missing_information": lambda e: (
            e.get("metadata", {}).get("has_missing_critical") is True
            or any(e.get("slots", {}).get(s) is None for s in ["monthly_income", "monthly_expense"])
        ),
        "3_explicit_zero": lambda e: e.get("metadata", {}).get("numerical_format") == "explicit_zero",
        "4_ambiguous_numbers": lambda e: e.get("metadata", {}).get("ambiguity_type") in [
            "range_ambiguity", "non_monthly_cadence", "expense_unknown"
        ],
        "5_non_monthly_cadence": lambda e: e.get("metadata", {}).get("ambiguity_type") == "non_monthly_cadence",
        "6_debt_explicit": lambda e: e.get("slots", {}).get("debt_status") is not None,
        "7_employment_explicit": lambda e: e.get("slots", {}).get("employment_status") is not None,
        "8_spending_habit_explicit": lambda e: e.get("slots", {}).get("spending_habit") is not None,
        "9_marital_status_explicit": lambda e: e.get("slots", {}).get("marital_status") is not None,
        "10_third_party_finances": lambda e: e.get("metadata", {}).get("ambiguity_type") == "third_party_income",
        "11_conflicting_information": lambda e: e.get("metadata", {}).get("ambiguity_type") in [
            "range_ambiguity", "conflict"
        ],
        "12_investment_out_of_scope": lambda e: e.get("intent") == "out_of_scope_investment",
        "13_loan_out_of_scope": lambda e: e.get("intent") == "out_of_scope_loan",
        "14_financial_education": lambda e: e.get("intent") == "financial_education",
    }

    results = {}
    for slice_name, predicate in slices_def.items():
        slice_indices = [idx for idx, e in enumerate(expected_records) if predicate(e)]
        if not slice_indices:
            results[slice_name] = {"count": 0, "intent_accuracy": None, "full_exact_match": None}
            continue

        s_exp = [expected_records[i] for i in slice_indices]
        s_pred = [predicted_records[i] for i in slice_indices]

        # Intent acc
        intent_corr = sum(1 for e, p in zip(s_exp, s_pred) if e.get("intent") == p.get("intent"))
        intent_acc = intent_corr / len(s_exp)

        # Full exact match
        em_res = compute_structured_exact_match(s_exp, s_pred)

        results[slice_name] = {
            "count": len(slice_indices),
            "intent_accuracy": round(intent_acc, 4),
            "full_exact_match": em_res["exact_match_rate"],
        }

    return results


def evaluate_predictions(
    expected_records: List[Dict[str, Any]],
    predicted_records: List[Dict[str, Any]],
    evaluation_name: str = "NLU Evaluation"
) -> Dict[str, Any]:
    """Full comprehensive evaluation suite."""
    assert len(expected_records) == len(predicted_records)

    exp_intents = [r.get("intent") for r in expected_records]
    pred_intents = [r.get("intent") for r in predicted_records]
    exp_slots = [r.get("slots", {}) for r in expected_records]
    pred_slots = [r.get("slots", {}) for r in predicted_records]

    intent_res = compute_intent_metrics(exp_intents, pred_intents)
    slot_res = compute_slot_metrics(exp_slots, pred_slots)
    sem_res = compute_structured_exact_match(expected_records, predicted_records)
    inv_res = compute_semantic_invariants_metrics(expected_records, predicted_records)
    slice_res = compute_slice_metrics(expected_records, predicted_records)

    return {
        "evaluation_name": evaluation_name,
        "total_records": len(expected_records),
        "summary": {
            "intent_accuracy": intent_res["accuracy"],
            "intent_macro_f1": intent_res["macro_f1"],
            "slot_micro_f1": slot_res["micro_f1"],
            "full_structured_exact_match_rate": sem_res["exact_match_rate"],
            "null_preservation_accuracy": inv_res["null_preservation_accuracy"],
            "zero_preservation_accuracy": inv_res["zero_preservation_accuracy"],
            "third_party_isolation_accuracy": inv_res["third_party_isolation_accuracy"],
            "non_monthly_cadence_safety": inv_res["non_monthly_cadence_safety"],
        },
        "intent_metrics": intent_res,
        "slot_metrics": slot_res,
        "exact_match": sem_res,
        "invariants": inv_res,
        "slices": slice_res,
    }


# ──────────────────────────────────────────────────────────────
# Baseline Generators (Non-ML Reference Baselines)
# ──────────────────────────────────────────────────────────────

def generate_majority_null_baseline(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deterministic Non-ML Baseline:
    Predicts the majority intent ('financial_consultation', 20%) and all slots = null.
    Establishes the minimal benchmark floor.
    """
    baseline_predictions = []
    for r in records:
        pred = {
            "example_id": r.get("example_id"),
            "intent": "financial_consultation",
            "slots": {s: None for s in CANONICAL_SLOT_KEYS}
        }
        baseline_predictions.append(pred)
    return baseline_predictions


# ──────────────────────────────────────────────────────────────
# Main CLI Runner
# ──────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("STEP 8K: NLU EVALUATION & DETERMINISTIC BASELINE RUNNER")
    print("=" * 70)

    ground_truth = load_ground_truth_corpus()
    print(f"\n[1/3] Loaded Ground Truth Corpus: {len(ground_truth)} records")
    assert len(ground_truth) == 100, f"Expected 100 records, got {len(ground_truth)}"

    # 1. Sanity Check: Self-evaluation (Ground Truth vs Ground Truth)
    print("\n[2/3] Computing Self-Evaluation (Perfect Sanity Check)...")
    perfect_report = evaluate_predictions(ground_truth, ground_truth, "Ground Truth Sanity Evaluation")
    assert perfect_report["summary"]["full_structured_exact_match_rate"] == 1.0
    assert perfect_report["summary"]["intent_accuracy"] == 1.0
    assert perfect_report["summary"]["slot_micro_f1"] == 1.0
    print("  PASS: Ground truth sanity check passed with 100% metrics.")

    # 2. Benchmark Reference: Majority-Class / All-Null Baseline
    print("\n[3/3] Computing Non-ML Majority-Class / All-Null Baseline...")
    baseline_preds = generate_majority_null_baseline(ground_truth)
    baseline_report = evaluate_predictions(ground_truth, baseline_preds, "Majority-Null Deterministic Baseline")

    full_output = {
        "step": "STEP 8K",
        "dataset_size": len(ground_truth),
        "sanity_check": perfect_report["summary"],
        "baseline_evaluation": baseline_report,
    }

    os.makedirs(REPORTS_DIR, exist_ok=True)
    with open(BASELINE_REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(full_output, f, indent=2, ensure_ascii=False)

    print(f"\n--- Baseline Evaluation Results (Floor Benchmark) ---")
    print(f"  Intent Accuracy:               {baseline_report['summary']['intent_accuracy'] * 100:.1f}%")
    print(f"  Intent Macro-F1:               {baseline_report['summary']['intent_macro_f1'] * 100:.1f}%")
    print(f"  Slot Micro-F1:                 {baseline_report['summary']['slot_micro_f1'] * 100:.1f}%")
    print(f"  Full Structured Exact Match:   {baseline_report['summary']['full_structured_exact_match_rate'] * 100:.1f}%")
    print(f"  Null Preservation Accuracy:    {baseline_report['summary']['null_preservation_accuracy'] * 100:.1f}%")
    print(f"  Zero Preservation Accuracy:    {baseline_report['summary']['zero_preservation_accuracy'] * 100:.1f}%")
    print(f"  Third-Party Isolation:         {baseline_report['summary']['third_party_isolation_accuracy'] * 100:.1f}%")
    print(f"  Non-Monthly Cadence Safety:    {baseline_report['summary']['non_monthly_cadence_safety'] * 100:.1f}%")

    print("\n--- Slice-Level Baseline Exact Match ---")
    for s_name, s_met in baseline_report["slices"].items():
        em_val = f"{s_met['full_exact_match'] * 100:.1f}%" if s_met['full_exact_match'] is not None else "N/A"
        print(f"  {s_name:30s} (n={s_met['count']:2d}): {em_val}")

    print(f"\nReport written to: {BASELINE_REPORT_JSON}")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
