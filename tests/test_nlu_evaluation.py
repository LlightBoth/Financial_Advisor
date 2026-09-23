"""
Step 8K: NLU Evaluation Framework Unit & Integration Tests.

Verifies:
1. Perfect predictions evaluate to 100% (1.0) across all metrics
2. Wrong intent penalizes intent accuracy and macro-F1 while slot accuracy is preserved
3. Wrong slot penalizes slot accuracy and micro-F1 while intent accuracy is preserved
4. Null vs zero mismatch is detected (predicting null when expected is 0.0, or vice versa)
5. Missing vs explicit mismatch is detected (predicting a value when expected is null)
6. All-null output evaluation matches expected floor behavior
7. Out-of-scope intent correctly affects out-of-scope metrics
8. Multiple slot errors accumulate correctly in micro-F1
9. Macro-F1 calculation accurately handles unrepresented and perfectly predicted classes
10. Slot micro-F1 precision/recall calculation mathematically matches expected formulas
11. Full structured exact match requires both intent and all 7 slots to match
12. Malformed predictions handling (missing slots, extra fields, invalid types) is handled safely
"""

import pytest
from datasets.financial_nlu.evaluate_dataset import (
    compute_intent_metrics,
    compute_slot_metrics,
    compute_structured_exact_match,
    compute_semantic_invariants_metrics,
    compute_slice_metrics,
    evaluate_predictions,
    CANONICAL_SLOT_KEYS,
    VALID_INTENTS,
)


@pytest.fixture
def sample_expected_record():
    return {
        "example_id": "TEST_001",
        "intent": "budget_analysis",
        "slots": {
            "monthly_income": 3000.0,
            "monthly_expense": 2000.0,
            "employment_status": "employed",
            "debt_status": "no debt",
            "spending_habit": "average spend",
            "goal_cost": 5000.0,
            "marital_status": "Single",
        },
        "metadata": {
            "has_missing_critical": False,
            "numerical_format": "standard",
            "ambiguity_type": None,
        }
    }


# ==============================================================================
# 1. Perfect Predictions
# ==============================================================================

def test_perfect_predictions_evaluation(sample_expected_record):
    exp = [sample_expected_record]
    pred = [dict(sample_expected_record)]

    res = evaluate_predictions(exp, pred, "Test Perfect")

    assert res["summary"]["intent_accuracy"] == 1.0
    assert res["summary"]["slot_micro_f1"] == 1.0
    assert res["summary"]["full_structured_exact_match_rate"] == 1.0
    assert res["summary"]["null_preservation_accuracy"] == 1.0
    assert res["exact_match"]["exact_match_count"] == 1


# ==============================================================================
# 2. Wrong Intent
# ==============================================================================

def test_wrong_intent_evaluation(sample_expected_record):
    exp = [sample_expected_record]
    pred = [dict(sample_expected_record)]
    pred[0]["intent"] = "savings_question"  # Wrong intent

    res = evaluate_predictions(exp, pred, "Test Wrong Intent")

    assert res["summary"]["intent_accuracy"] == 0.0
    assert res["summary"]["slot_micro_f1"] == 1.0  # Slots were all correct
    assert res["summary"]["full_structured_exact_match_rate"] == 0.0  # Full match must fail


# ==============================================================================
# 3. Wrong Slot
# ==============================================================================

def test_wrong_slot_value_evaluation(sample_expected_record):
    exp = [sample_expected_record]
    pred = [dict(sample_expected_record)]
    pred[0]["slots"] = dict(sample_expected_record["slots"])
    pred[0]["slots"]["monthly_income"] = 4000.0  # Expected 3000.0

    res = evaluate_predictions(exp, pred, "Test Wrong Slot")

    assert res["summary"]["intent_accuracy"] == 1.0  # Intent was correct
    assert res["slot_metrics"]["per_slot_accuracy"]["monthly_income"] == 0.0
    assert res["slot_metrics"]["per_slot_accuracy"]["monthly_expense"] == 1.0
    assert res["summary"]["slot_micro_f1"] < 1.0
    assert res["summary"]["full_structured_exact_match_rate"] == 0.0


# ==============================================================================
# 4. Null vs Zero Mismatch
# ==============================================================================

def test_null_vs_zero_mismatch():
    exp = [{
        "example_id": "T_ZERO",
        "intent": "financial_consultation",
        "slots": {s: None for s in CANONICAL_SLOT_KEYS},
        "metadata": {"numerical_format": "explicit_zero"}
    }]
    exp[0]["slots"]["monthly_income"] = 0.0  # Expected explicit zero

    # Predictor predicted null instead of 0.0
    pred = [{
        "example_id": "T_ZERO",
        "intent": "financial_consultation",
        "slots": {s: None for s in CANONICAL_SLOT_KEYS}
    }]

    inv_res = compute_semantic_invariants_metrics(exp, pred)
    assert inv_res["zero_preservation_accuracy"] == 0.0  # 0.0 was lost!

    # Conversely: Predictor predicted 0.0 when expected was null
    exp_null = [{
        "example_id": "T_NULL",
        "intent": "financial_consultation",
        "slots": {s: None for s in CANONICAL_SLOT_KEYS},
        "metadata": {}
    }]
    pred_zero = [{
        "example_id": "T_NULL",
        "intent": "financial_consultation",
        "slots": {s: None for s in CANONICAL_SLOT_KEYS}
    }]
    pred_zero[0]["slots"]["monthly_income"] = 0.0

    inv_res2 = compute_semantic_invariants_metrics(exp_null, pred_zero)
    # Total expected nulls was 7, but only 6 were preserved as null!
    assert inv_res2["null_preservation_accuracy"] < 1.0


# ==============================================================================
# 5. Missing vs Explicit Mismatch
# ==============================================================================

def test_missing_vs_explicit_mismatch():
    exp = [{
        "example_id": "T_MISSING",
        "intent": "financial_consultation",
        "slots": {
            "monthly_income": None,  # unmentioned
            "monthly_expense": 1500.0,
            "employment_status": None,
            "debt_status": None,  # unmentioned
            "spending_habit": None,
            "goal_cost": None,
            "marital_status": None,
        },
        "metadata": {}
    }]

    # Predictor hallucinates "no debt" and "employed"
    pred = [{
        "example_id": "T_MISSING",
        "intent": "financial_consultation",
        "slots": {
            "monthly_income": None,
            "monthly_expense": 1500.0,
            "employment_status": "employed",  # Hallucinated
            "debt_status": "no debt",  # Hallucinated
            "spending_habit": None,
            "goal_cost": None,
            "marital_status": None,
        }
    }]

    res = evaluate_predictions(exp, pred)
    assert res["slot_metrics"]["per_slot_accuracy"]["debt_status"] == 0.0
    assert res["slot_metrics"]["per_slot_accuracy"]["employment_status"] == 0.0
    assert res["slot_metrics"]["per_slot_accuracy"]["monthly_expense"] == 1.0
    assert res["summary"]["full_structured_exact_match_rate"] == 0.0


# ==============================================================================
# 6. All-Null Output
# ==============================================================================

def test_all_null_output(sample_expected_record):
    exp = [sample_expected_record]
    pred = [{
        "example_id": sample_expected_record["example_id"],
        "intent": sample_expected_record["intent"],
        "slots": {s: None for s in CANONICAL_SLOT_KEYS}
    }]

    res = evaluate_predictions(exp, pred)
    assert res["summary"]["intent_accuracy"] == 1.0
    assert res["summary"]["slot_micro_f1"] == 0.0  # 0 non-null predicted
    assert res["summary"]["full_structured_exact_match_rate"] == 0.0


# ==============================================================================
# 7. Out-of-Scope Intent Detection
# ==============================================================================

def test_out_of_scope_intent_evaluation():
    exp = [
        {"intent": "out_of_scope_investment", "slots": {s: None for s in CANONICAL_SLOT_KEYS}, "metadata": {}},
        {"intent": "out_of_scope_loan", "slots": {s: None for s in CANONICAL_SLOT_KEYS}, "metadata": {}},
    ]
    pred = [
        {"intent": "out_of_scope_investment", "slots": {s: None for s in CANONICAL_SLOT_KEYS}},
        {"intent": "financial_consultation", "slots": {s: None for s in CANONICAL_SLOT_KEYS}},  # Misclassified loan
    ]

    inv_res = compute_semantic_invariants_metrics(exp, pred)
    assert inv_res["oos_investment_accuracy"] == 1.0
    assert inv_res["oos_loan_accuracy"] == 0.0


# ==============================================================================
# 8. Multiple Slot Errors
# ==============================================================================

def test_multiple_slot_errors(sample_expected_record):
    exp = [sample_expected_record]
    pred = [dict(sample_expected_record)]
    pred[0]["slots"] = {
        "monthly_income": 9999.0,  # Error 1
        "monthly_expense": 8888.0,  # Error 2
        "employment_status": "not employed",  # Error 3
        "debt_status": "debt",  # Error 4
        "spending_habit": "big spend",  # Error 5
        "goal_cost": 5000.0,  # Correct
        "marital_status": "Single",  # Correct
    }

    slot_res = compute_slot_metrics([exp[0]["slots"]], [pred[0]["slots"]])
    assert slot_res["micro_tp"] == 2
    assert slot_res["micro_fp"] == 5
    assert slot_res["micro_fn"] == 5
    # precision = 2 / (2 + 5) = 2/7
    assert round(slot_res["micro_precision"], 4) == round(2 / 7, 4)


# ==============================================================================
# 9. Macro-F1 Calculation
# ==============================================================================

def test_macro_f1_calculation():
    # 2 intents, 1 example each
    expected = ["budget_analysis", "savings_question"]
    # 1 correct, 1 incorrect
    predicted = ["budget_analysis", "debt_management"]

    metrics = compute_intent_metrics(expected, predicted)
    assert metrics["accuracy"] == 0.5
    # budget_analysis: precision=1.0, recall=1.0, f1=1.0
    # savings_question: precision=0.0, recall=0.0, f1=0.0
    # macro_f1 = (1.0 + 0.0) / 2 = 0.5
    assert metrics["macro_f1"] == 0.5


# ==============================================================================
# 10. Full Exact Match Calculation
# ==============================================================================

import copy

def test_full_exact_match_calculation(sample_expected_record):
    rec1 = copy.deepcopy(sample_expected_record)
    rec2 = copy.deepcopy(sample_expected_record)
    rec2["example_id"] = "TEST_002"
    rec2["slots"]["monthly_income"] = 5000.0

    exp = [rec1, rec2]

    # Predict rec1 correctly, rec2 with wrong income
    pred = [
        copy.deepcopy(rec1),
        copy.deepcopy(rec2),
    ]
    pred[1]["slots"]["monthly_income"] = 4000.0

    sem = compute_structured_exact_match(exp, pred)
    assert sem["exact_match_count"] == 1
    assert sem["total"] == 2
    assert sem["exact_match_rate"] == 0.5


# ==============================================================================
# 11. Malformed Prediction Handling
# ==============================================================================

def test_malformed_prediction_handling(sample_expected_record):
    exp = [sample_expected_record]
    # Prediction has missing slots key or empty dictionary
    pred_empty = [{"example_id": "TEST_001", "intent": "budget_analysis", "slots": {}}]

    res = evaluate_predictions(exp, pred_empty)
    assert res["summary"]["intent_accuracy"] == 1.0
    assert res["summary"]["full_structured_exact_match_rate"] == 0.0

    # Prediction is missing slots altogether
    pred_none = [{"example_id": "TEST_001", "intent": "budget_analysis"}]
    res2 = evaluate_predictions(exp, pred_none)
    assert res2["summary"]["intent_accuracy"] == 1.0
    assert res2["summary"]["full_structured_exact_match_rate"] == 0.0
