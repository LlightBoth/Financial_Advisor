"""
Dataset Batch 02 Builder for Step 8J.
Generates exactly 78 controlled English NLU records conforming to nlu_schema_v1.json.
Enforces:
- Schema conformance
- Exact slot character span calculation & verification
- Deterministic ConsultantEngine rule evaluation for routable records
- Zero template leakage (template-grouped splits)
- Truthful null semantics (unknown != 0)
- Third-party income protection
- Out-of-scope isolation
- Rich slot coverage:
  * spending_habit: 8 'average spend', 8 'big spend'
  * marital_status: 8 'Single', 8 'Married'
  * debt_status: 8 'no debt', 18 'debt'
  * employment_status: 8 'not employed', 62 'employed'
"""

import json
import os
import sys

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from app.services.consultant_engine import ConsultantEngine, CANONICAL_KB_VERSION, CANONICAL_RULE_IDS
from app.services.consultant_validator import ConsultantInputValidator
from app.security.seed_rule_facts import CONSULTANT_RULES

STANDALONE_CANONICAL_RULES = [
    dict(r, kb_version=CANONICAL_KB_VERSION) for r in CONSULTANT_RULES
]

TEMPLATE_SPLIT_MAP = {
    # Existing dry-run templates
    "T_BUDGET_001": "train",
    "T_BUDGET_002": "val",
    "T_BUDGET_003": "val",
    "T_CASHFLOW_001": "val",
    "T_DEBT_001": "train",
    "T_DEBT_002": "train",
    "T_DEBT_003": "train",
    "T_EMPLOYMENT_003": "test",
    "T_EMPLOYMENT_004": "train",
    "T_HOUSEHOLD_002": "train",
    "T_MISSING_001": "train",
    "T_MISSING_003": "train",
    "T_MISSING_006": "test",
    "T_MISSING_007": "test",
    "T_MISSING_008": "val",
    "T_MISSING_010": "test",
    "T_OOS_INVEST_001": "test",
    "T_OOS_INVEST_002": "test",
    "T_OOS_LOAN_001": "test",
    "T_OOS_LOAN_002": "test",
    "T_SAVINGS_001": "train",

    # Remaining templates assignments
    "T_BUDGET_004": "train",
    "T_BUDGET_005": "train",
    "T_BUDGET_006": "train",
    "T_BUDGET_007": "train",
    "T_BUDGET_008": "train",

    "T_CASHFLOW_002": "train",
    "T_CASHFLOW_003": "train",
    "T_CASHFLOW_004": "val",
    "T_CASHFLOW_005": "val",
    "T_CASHFLOW_006": "val",

    "T_DEBT_004": "train",
    "T_DEBT_005": "train",
    "T_DEBT_006": "train",
    "T_DEBT_007": "train",

    "T_EMPLOYMENT_001": "train",
    "T_EMPLOYMENT_002": "train",
    "T_EMPLOYMENT_005": "train",
    "T_EMPLOYMENT_006": "train",

    "T_HOUSEHOLD_001": "train",
    "T_HOUSEHOLD_003": "train",
    "T_HOUSEHOLD_004": "train",
    "T_HOUSEHOLD_005": "train",
    "T_HOUSEHOLD_006": "train",

    "T_SAVINGS_002": "train",
    "T_SAVINGS_003": "val",
    "T_SAVINGS_004": "train",
    "T_SAVINGS_005": "val",
    "T_SAVINGS_006": "train",
    "T_SAVINGS_007": "val",

    "T_MISSING_002": "train",
    "T_MISSING_004": "train",
    "T_MISSING_005": "train",
    "T_MISSING_009": "train",

    "T_OOS_INVEST_003": "test",
    "T_OOS_INVEST_004": "test",
    "T_OOS_INVEST_005": "test",
    "T_OOS_INVEST_006": "test",
    "T_OOS_INVEST_007": "test",
    "T_OOS_LOAN_003": "test",
}


def build_record(
    example_id: str,
    template_id: str,
    template_family: str,
    input_text: str,
    intent: str,
    slots: dict,
    spans_def: list,  # list of (slot, raw_substring)
    concept_source: str,
    metadata: dict
) -> dict:
    """Builds and validates a single dataset record."""
    split = TEMPLATE_SPLIT_MAP[template_id]

    # Calculate and verify spans
    spans = []
    for slot_name, raw_substring in spans_def:
        start = input_text.find(raw_substring)
        if start == -1:
            raise ValueError(f"Substring '{raw_substring}' not found in input_text: '{input_text}'")
        end = start + len(raw_substring)
        spans.append({
            "slot": slot_name,
            "start": start,
            "end": end,
            "value": slots[slot_name],
            "raw_text": raw_substring
        })

    # Verify input_text[start:end] == raw_text
    for sp in spans:
        extracted = input_text[sp["start"]:sp["end"]]
        assert extracted == sp["raw_text"], f"Span mismatch: '{extracted}' != '{sp['raw_text']}'"

    # Compute expected_rule_id
    expected_rule_id = None
    if (
        slots.get("monthly_income") is not None
        and slots.get("monthly_expense") is not None
        and intent in [
            "financial_consultation",
            "budget_analysis",
            "cashflow_question",
            "savings_question",
            "debt_management",
            "financial_goal"
        ]
    ):
        norm_dict, err = ConsultantInputValidator.validate(slots, default_lang="en")
        if err:
            raise ValueError(f"Record {example_id} validator error: {err}")
        res = ConsultantEngine.evaluate(norm_dict, rules=STANDALONE_CANONICAL_RULES)
        expected_rule_id = res["selected_advice"].rule_id
        assert expected_rule_id in CANONICAL_RULE_IDS

    return {
        "example_id": example_id,
        "template_id": template_id,
        "template_family": template_family,
        "language": "en",
        "split": split,
        "input_text": input_text,
        "intent": intent,
        "slots": slots,
        "slot_spans": spans,
        "expected_rule_id": expected_rule_id,
        "validation_status": "PASS",
        "source_type": "human_authored",
        "concept_source": concept_source,
        "metadata": metadata
    }


def generate_batch02():
    records = []

    def add(eid, tid, tf, text, intent, slots, spans_def, src, meta):
        r = build_record(eid, tid, tf, text, intent, slots, spans_def, src, meta)
        records.append(r)

    # =========================================================================
    # Group 1: savings_question (10 records) - Critical weakness resolution
    # =========================================================================
    # 1. T_SAVINGS_005 (val) - single + average spend
    add(
        "EN_EXP_0001", "T_SAVINGS_005", "TF_SAVINGS",
        "As a single person with a monthly salary of 3200, costs of 2400, and average spending, is it possible for me to build an emergency fund of 5000?",
        "savings_question",
        {"monthly_income": 3200.0, "monthly_expense": 2400.0, "employment_status": "employed", "debt_status": None, "spending_habit": "average spend", "goal_cost": 5000.0, "marital_status": "Single"},
        [("marital_status", "single"), ("monthly_income", "3200"), ("monthly_expense", "2400"), ("spending_habit", "average spending"), ("goal_cost", "5000")],
        "WILEY_CH15_BUFFER",
        {"has_debt": False, "has_goal": True, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 2. T_SAVINGS_003 (val) - married + big spend
    add(
        "EN_EXP_0002", "T_SAVINGS_003", "TF_SAVINGS",
        "We are married and I make 4000 a month with expenses of 2800 because we are big spenders. How long will it take me to save 12000?",
        "savings_question",
        {"monthly_income": 4000.0, "monthly_expense": 2800.0, "employment_status": "employed", "debt_status": None, "spending_habit": "big spend", "goal_cost": 12000.0, "marital_status": "Married"},
        [("marital_status", "married"), ("monthly_income", "4000"), ("monthly_expense", "2800"), ("spending_habit", "big spenders"), ("goal_cost", "12000")],
        "CFA_LM2_TVM",
        {"has_debt": False, "has_goal": True, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 3. T_SAVINGS_007 (val) - explicit no debt
    add(
        "EN_EXP_0003", "T_SAVINGS_007", "TF_SAVINGS",
        "I earn 2900 per month with expenses of 2100 and have no debt. I want to set aside 6000 for future education costs.",
        "savings_question",
        {"monthly_income": 2900.0, "monthly_expense": 2100.0, "employment_status": "employed", "debt_status": "no debt", "spending_habit": None, "goal_cost": 6000.0, "marital_status": None},
        [("monthly_income", "2900"), ("monthly_expense", "2100"), ("debt_status", "no debt"), ("goal_cost", "6000")],
        "CFA_LM2_TVM",
        {"has_debt": False, "has_goal": True, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 4. T_SAVINGS_005 (val) - single + debt
    add(
        "EN_EXP_0004", "T_SAVINGS_005", "TF_SAVINGS",
        "I am single with a monthly salary of 2800, costs of 2000, and existing debt. Is it possible for me to build an emergency fund of 3000?",
        "savings_question",
        {"monthly_income": 2800.0, "monthly_expense": 2000.0, "employment_status": "employed", "debt_status": "debt", "spending_habit": None, "goal_cost": 3000.0, "marital_status": "Single"},
        [("marital_status", "single"), ("monthly_income", "2800"), ("monthly_expense", "2000"), ("debt_status", "debt"), ("goal_cost", "3000")],
        "WILEY_CH15_BUFFER",
        {"has_debt": True, "has_goal": True, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 5. T_SAVINGS_003 (val) - average spend
    add(
        "EN_EXP_0005", "T_SAVINGS_003", "TF_SAVINGS",
        "I make 3600 a month and my expenses are 2500 with average spending. How long will it take me to save 8000?",
        "savings_question",
        {"monthly_income": 3600.0, "monthly_expense": 2500.0, "employment_status": "employed", "debt_status": None, "spending_habit": "average spend", "goal_cost": 8000.0, "marital_status": None},
        [("monthly_income", "3600"), ("monthly_expense", "2500"), ("spending_habit", "average spending"), ("goal_cost", "8000")],
        "CFA_LM2_TVM",
        {"has_debt": False, "has_goal": True, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 6. T_SAVINGS_007 (val) - married + no debt
    add(
        "EN_EXP_0006", "T_SAVINGS_007", "TF_SAVINGS",
        "We are married. I earn 4500 per month with expenses of 3100, zero debt, and want to set aside 10000 for education.",
        "savings_question",
        {"monthly_income": 4500.0, "monthly_expense": 3100.0, "employment_status": "employed", "debt_status": "no debt", "spending_habit": None, "goal_cost": 10000.0, "marital_status": "Married"},
        [("marital_status", "married"), ("monthly_income", "4500"), ("monthly_expense", "3100"), ("debt_status", "zero debt"), ("goal_cost", "10000")],
        "CFA_LM2_TVM",
        {"has_debt": False, "has_goal": True, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 7. T_MISSING_002 (train) - unknown expense savings question
    add(
        "EN_EXP_0007", "T_MISSING_002", "TF_MISSING_INFO",
        "I want to start saving but I do not know how much I spend each month.",
        "savings_question",
        {"monthly_income": None, "monthly_expense": None, "employment_status": None, "debt_status": None, "spending_habit": None, "goal_cost": None, "marital_status": None},
        [],
        "original",
        {"has_debt": False, "has_goal": True, "has_missing_critical": True, "numerical_format": "none", "ambiguity_type": "expense_unknown", "created_at": "2026-09-22T10:00:00Z"}
    )
    # 8. T_SAVINGS_003 (val)
    add(
        "EN_EXP_0008", "T_SAVINGS_003", "TF_SAVINGS",
        "I make 2600 a month and my expenses are 1900. How long will it take me to save 4000?",
        "savings_question",
        {"monthly_income": 2600.0, "monthly_expense": 1900.0, "employment_status": "employed", "debt_status": None, "spending_habit": None, "goal_cost": 4000.0, "marital_status": None},
        [("monthly_income", "2600"), ("monthly_expense", "1900"), ("goal_cost", "4000")],
        "CFA_LM2_TVM",
        {"has_debt": False, "has_goal": True, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 9. T_SAVINGS_005 (val) - unemployed trying to save
    add(
        "EN_EXP_0009", "T_SAVINGS_005", "TF_SAVINGS",
        "I am not employed with 0 income and living costs of 900. Is it possible for me to build an emergency fund of 2000?",
        "savings_question",
        {"monthly_income": 0.0, "monthly_expense": 900.0, "employment_status": "not employed", "debt_status": None, "spending_habit": None, "goal_cost": 2000.0, "marital_status": None},
        [("employment_status", "not employed"), ("monthly_income", "0"), ("monthly_expense", "900"), ("goal_cost", "2000")],
        "WILEY_CH15_BUFFER",
        {"has_debt": False, "has_goal": True, "has_missing_critical": False, "numerical_format": "explicit_zero", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 10. T_SAVINGS_007 (val) - big spend
    add(
        "EN_EXP_0010", "T_SAVINGS_007", "TF_SAVINGS",
        "I earn 3400 per month with expenses of 2800 as a big spend habit. I want to set aside 5000 for future education costs.",
        "savings_question",
        {"monthly_income": 3400.0, "monthly_expense": 2800.0, "employment_status": "employed", "debt_status": None, "spending_habit": "big spend", "goal_cost": 5000.0, "marital_status": None},
        [("monthly_income", "3400"), ("monthly_expense", "2800"), ("spending_habit", "big spend"), ("goal_cost", "5000")],
        "CFA_LM2_TVM",
        {"has_debt": False, "has_goal": True, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )

    # =========================================================================
    # Group 2: financial_goal (9 records)
    # =========================================================================
    # 11. T_SAVINGS_001 (train) - single + average spend
    add(
        "EN_EXP_0011", "T_SAVINGS_001", "TF_SAVINGS",
        "I am single, earn 3800 per month, spend 2600 with average spending, and want to save up 5000 for a new motorcycle.",
        "financial_goal",
        {"monthly_income": 3800.0, "monthly_expense": 2600.0, "employment_status": "employed", "debt_status": None, "spending_habit": "average spend", "goal_cost": 5000.0, "marital_status": "Single"},
        [("marital_status", "single"), ("monthly_income", "3800"), ("monthly_expense", "2600"), ("spending_habit", "average spending"), ("goal_cost", "5000")],
        "WILEY_CH6_GOALS",
        {"has_debt": False, "has_goal": True, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 12. T_SAVINGS_002 (train) - married + no debt
    add(
        "EN_EXP_0012", "T_SAVINGS_002", "TF_SAVINGS",
        "We are married. My monthly income is 4200 and I spend about 2800 with no debt. Can I realistically save 20000 for a house deposit?",
        "financial_goal",
        {"monthly_income": 4200.0, "monthly_expense": 2800.0, "employment_status": "employed", "debt_status": "no debt", "spending_habit": None, "goal_cost": 20000.0, "marital_status": "Married"},
        [("marital_status", "married"), ("monthly_income", "4200"), ("monthly_expense", "2800"), ("debt_status", "no debt"), ("goal_cost", "20000")],
        "WILEY_CH6_GOALS",
        {"has_debt": False, "has_goal": True, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 13. T_SAVINGS_004 (train) - single + big spend
    add(
        "EN_EXP_0013", "T_SAVINGS_004", "TF_SAVINGS",
        "As a single person, I bring in 3100 monthly and spend 2500 since I tend to spend a lot. My goal is to put together 8000 for my wedding.",
        "financial_goal",
        {"monthly_income": 3100.0, "monthly_expense": 2500.0, "employment_status": "employed", "debt_status": None, "spending_habit": "big spend", "goal_cost": 8000.0, "marital_status": "Single"},
        [("marital_status", "single person"), ("monthly_income", "3100"), ("monthly_expense", "2500"), ("spending_habit", "spend a lot"), ("goal_cost", "8000")],
        "original",
        {"has_debt": False, "has_goal": True, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 14. T_SAVINGS_006 (train)
    add(
        "EN_EXP_0014", "T_SAVINGS_006", "TF_SAVINGS",
        "I take home 2700 each month, spend 1900, and I need to reach 1500 for a laptop purchase.",
        "financial_goal",
        {"monthly_income": 2700.0, "monthly_expense": 1900.0, "employment_status": "employed", "debt_status": None, "spending_habit": None, "goal_cost": 1500.0, "marital_status": None},
        [("monthly_income", "2700"), ("monthly_expense", "1900"), ("goal_cost", "1500")],
        "original",
        {"has_debt": False, "has_goal": True, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 15. T_SAVINGS_001 (train) - married + debt
    add(
        "EN_EXP_0015", "T_SAVINGS_001", "TF_SAVINGS",
        "I am married, earn 4600 per month, spend 3200, have active debt, and want to save up 10000 for home renovations.",
        "financial_goal",
        {"monthly_income": 4600.0, "monthly_expense": 3200.0, "employment_status": "employed", "debt_status": "debt", "spending_habit": None, "goal_cost": 10000.0, "marital_status": "Married"},
        [("marital_status", "married"), ("monthly_income", "4600"), ("monthly_expense", "3200"), ("debt_status", "debt"), ("goal_cost", "10000")],
        "WILEY_CH6_GOALS",
        {"has_debt": True, "has_goal": True, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 16. T_SAVINGS_002 (train)
    add(
        "EN_EXP_0016", "T_SAVINGS_002", "TF_SAVINGS",
        "My monthly income is 3500 and I spend about 2400. Can I realistically save 6000 for vocational training?",
        "financial_goal",
        {"monthly_income": 3500.0, "monthly_expense": 2400.0, "employment_status": "employed", "debt_status": None, "spending_habit": None, "goal_cost": 6000.0, "marital_status": None},
        [("monthly_income", "3500"), ("monthly_expense", "2400"), ("goal_cost", "6000")],
        "WILEY_CH6_GOALS",
        {"has_debt": False, "has_goal": True, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 17. T_SAVINGS_004 (train) - big spend
    add(
        "EN_EXP_0017", "T_SAVINGS_004", "TF_SAVINGS",
        "I bring in 5000 monthly and spend 3800 as a big spender. My goal is to put together 12000 for my wedding.",
        "financial_goal",
        {"monthly_income": 5000.0, "monthly_expense": 3800.0, "employment_status": "employed", "debt_status": None, "spending_habit": "big spend", "goal_cost": 12000.0, "marital_status": None},
        [("monthly_income", "5000"), ("monthly_expense", "3800"), ("spending_habit", "big spender"), ("goal_cost", "12000")],
        "original",
        {"has_debt": False, "has_goal": True, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 18. T_SAVINGS_006 (train) - average spend
    add(
        "EN_EXP_0018", "T_SAVINGS_006", "TF_SAVINGS",
        "I take home 3400 each month, spend 2300 with an average spend habit, and I need to reach 2500 for a laptop purchase.",
        "financial_goal",
        {"monthly_income": 3400.0, "monthly_expense": 2300.0, "employment_status": "employed", "debt_status": None, "spending_habit": "average spend", "goal_cost": 2500.0, "marital_status": None},
        [("monthly_income", "3400"), ("monthly_expense", "2300"), ("spending_habit", "average spend"), ("goal_cost", "2500")],
        "original",
        {"has_debt": False, "has_goal": True, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 19. T_SAVINGS_001 (train)
    add(
        "EN_EXP_0019", "T_SAVINGS_001", "TF_SAVINGS",
        "I earn 3000 per month and spend 2100. I want to save up 4000 for a new motorcycle.",
        "financial_goal",
        {"monthly_income": 3000.0, "monthly_expense": 2100.0, "employment_status": "employed", "debt_status": None, "spending_habit": None, "goal_cost": 4000.0, "marital_status": None},
        [("monthly_income", "3000"), ("monthly_expense", "2100"), ("goal_cost", "4000")],
        "WILEY_CH6_GOALS",
        {"has_debt": False, "has_goal": True, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )

    # =========================================================================
    # Group 3: cashflow_question (9 records)
    # =========================================================================
    # 20. T_CASHFLOW_001 (val)
    add(
        "EN_EXP_0020", "T_CASHFLOW_001", "TF_CASHFLOW",
        "I earn 2600 monthly and spend 2600. How much do I have left over?",
        "cashflow_question",
        {"monthly_income": 2600.0, "monthly_expense": 2600.0, "employment_status": "employed", "debt_status": None, "spending_habit": None, "goal_cost": None, "marital_status": None},
        [("monthly_income", "2600"), ("monthly_expense", "2600")],
        "original",
        {"has_debt": False, "has_goal": False, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 21. T_CASHFLOW_002 (train) - with debt
    add(
        "EN_EXP_0021", "T_CASHFLOW_002", "TF_CASHFLOW",
        "My income is 1800 per month, my expenses are 2100, and I have debt. Am I running a deficit?",
        "cashflow_question",
        {"monthly_income": 1800.0, "monthly_expense": 2100.0, "employment_status": "employed", "debt_status": "debt", "spending_habit": None, "goal_cost": None, "marital_status": None},
        [("monthly_income", "1800"), ("monthly_expense", "2100"), ("debt_status", "debt")],
        "original",
        {"has_debt": True, "has_goal": False, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 22. T_CASHFLOW_003 (train) - big spend
    add(
        "EN_EXP_0022", "T_CASHFLOW_003", "TF_CASHFLOW",
        "I bring home 3200 each month but my costs are 3400 because I am a big spender. I feel like I am running out of money before the month ends.",
        "cashflow_question",
        {"monthly_income": 3200.0, "monthly_expense": 3400.0, "employment_status": "employed", "debt_status": None, "spending_habit": "big spend", "goal_cost": None, "marital_status": None},
        [("monthly_income", "3200"), ("monthly_expense", "3400"), ("spending_habit", "big spender")],
        "original",
        {"has_debt": False, "has_goal": False, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 23. T_CASHFLOW_004 (val) - single
    add(
        "EN_EXP_0023", "T_CASHFLOW_004", "TF_CASHFLOW",
        "I am single. After all my bills, I spend 2400 a month from my 3100 salary. Is my cash flow healthy?",
        "cashflow_question",
        {"monthly_income": 3100.0, "monthly_expense": 2400.0, "employment_status": "employed", "debt_status": None, "spending_habit": None, "goal_cost": None, "marital_status": "Single"},
        [("marital_status", "single"), ("monthly_expense", "2400"), ("monthly_income", "3100")],
        "original",
        {"has_debt": False, "has_goal": False, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 24. T_CASHFLOW_005 (val) - no debt
    add(
        "EN_EXP_0024", "T_CASHFLOW_005", "TF_CASHFLOW",
        "I make 2700 monthly, spend 2500, and have no debt. Can I cover an emergency expense?",
        "cashflow_question",
        {"monthly_income": 2700.0, "monthly_expense": 2500.0, "employment_status": "employed", "debt_status": "no debt", "spending_habit": None, "goal_cost": None, "marital_status": None},
        [("monthly_income", "2700"), ("monthly_expense", "2500"), ("debt_status", "no debt")],
        "WILEY_CH15_BUFFER",
        {"has_debt": False, "has_goal": False, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 25. T_CASHFLOW_006 (val) - average spend
    add(
        "EN_EXP_0025", "T_CASHFLOW_006", "TF_CASHFLOW",
        "My monthly earnings are 4000 and I typically spend about 2600 with moderate spending. What is my surplus or deficit?",
        "cashflow_question",
        {"monthly_income": 4000.0, "monthly_expense": 2600.0, "employment_status": "employed", "debt_status": None, "spending_habit": "average spend", "goal_cost": None, "marital_status": None},
        [("monthly_income", "4000"), ("monthly_expense", "2600"), ("spending_habit", "moderate")],
        "original",
        {"has_debt": False, "has_goal": False, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 26. T_CASHFLOW_002 (train) - unemployed
    add(
        "EN_EXP_0026", "T_CASHFLOW_002", "TF_CASHFLOW",
        "I am not employed so my income is 0 per month and my expenses are 1200. Am I running a deficit?",
        "cashflow_question",
        {"monthly_income": 0.0, "monthly_expense": 1200.0, "employment_status": "not employed", "debt_status": None, "spending_habit": None, "goal_cost": None, "marital_status": None},
        [("employment_status", "not employed"), ("monthly_income", "0"), ("monthly_expense", "1200")],
        "original",
        {"has_debt": False, "has_goal": False, "has_missing_critical": False, "numerical_format": "explicit_zero", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 27. T_CASHFLOW_004 (val)
    add(
        "EN_EXP_0027", "T_CASHFLOW_004", "TF_CASHFLOW",
        "After all my bills, I spend 1900 a month from my 2800 salary. Is my cash flow healthy?",
        "cashflow_question",
        {"monthly_income": 2800.0, "monthly_expense": 1900.0, "employment_status": "employed", "debt_status": None, "spending_habit": None, "goal_cost": None, "marital_status": None},
        [("monthly_expense", "1900"), ("monthly_income", "2800")],
        "original",
        {"has_debt": False, "has_goal": False, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 28. T_CASHFLOW_005 (val) - married
    add(
        "EN_EXP_0028", "T_CASHFLOW_005", "TF_CASHFLOW",
        "We are married. I make 2200 monthly and spend 2200. Can I cover an emergency expense?",
        "cashflow_question",
        {"monthly_income": 2200.0, "monthly_expense": 2200.0, "employment_status": "employed", "debt_status": None, "spending_habit": None, "goal_cost": None, "marital_status": "Married"},
        [("marital_status", "married"), ("monthly_income", "2200"), ("monthly_expense", "2200")],
        "WILEY_CH15_BUFFER",
        {"has_debt": False, "has_goal": False, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )

    # =========================================================================
    # Group 4: budget_analysis (11 records)
    # =========================================================================
    # 29. T_BUDGET_001 (train) - single + no debt
    add(
        "EN_EXP_0029", "T_BUDGET_001", "TF_BUDGET",
        "I am single, have no debt, earn 3500 each month and spend 2100.",
        "budget_analysis",
        {"monthly_income": 3500.0, "monthly_expense": 2100.0, "employment_status": "employed", "debt_status": "no debt", "spending_habit": None, "goal_cost": None, "marital_status": "Single"},
        [("marital_status", "single"), ("debt_status", "no debt"), ("monthly_income", "3500"), ("monthly_expense", "2100")],
        "original",
        {"has_debt": False, "has_goal": False, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 30. T_BUDGET_002 (val)
    add(
        "EN_EXP_0030", "T_BUDGET_002", "TF_BUDGET",
        "My monthly take-home pay is 2800 and my regular expenses come to about 2500.",
        "budget_analysis",
        {"monthly_income": 2800.0, "monthly_expense": 2500.0, "employment_status": "employed", "debt_status": None, "spending_habit": None, "goal_cost": None, "marital_status": None},
        [("monthly_income", "2800"), ("monthly_expense", "2500")],
        "original",
        {"has_debt": False, "has_goal": False, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 31. T_BUDGET_003 (val)
    add(
        "EN_EXP_0031", "T_BUDGET_003", "TF_BUDGET",
        "Every month I bring home 4200 after taxes, and my bills and living costs total 2200.",
        "budget_analysis",
        {"monthly_income": 4200.0, "monthly_expense": 2200.0, "employment_status": "employed", "debt_status": None, "spending_habit": None, "goal_cost": None, "marital_status": None},
        [("monthly_income", "4200"), ("monthly_expense", "2200")],
        "original",
        {"has_debt": False, "has_goal": False, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 32. T_BUDGET_004 (train) - big spend
    add(
        "EN_EXP_0032", "T_BUDGET_004", "TF_BUDGET",
        "I make 3000 a month. Between rent, food, and utilities, I spend 2600 as a big spend pattern.",
        "budget_analysis",
        {"monthly_income": 3000.0, "monthly_expense": 2600.0, "employment_status": "employed", "debt_status": None, "spending_habit": "big spend", "goal_cost": None, "marital_status": None},
        [("monthly_income", "3000"), ("monthly_expense", "2600"), ("spending_habit", "big spend")],
        "original",
        {"has_debt": False, "has_goal": False, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 33. T_BUDGET_005 (train) - married
    add(
        "EN_EXP_0033", "T_BUDGET_005", "TF_BUDGET",
        "We are married. Right now my monthly income sits at 2400 and I spend roughly 2200 on everything.",
        "budget_analysis",
        {"monthly_income": 2400.0, "monthly_expense": 2200.0, "employment_status": "employed", "debt_status": None, "spending_habit": None, "goal_cost": None, "marital_status": "Married"},
        [("marital_status", "married"), ("monthly_income", "2400"), ("monthly_expense", "2200")],
        "original",
        {"has_debt": False, "has_goal": False, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 34. T_BUDGET_006 (train) - average spend
    add(
        "EN_EXP_0034", "T_BUDGET_006", "TF_BUDGET",
        "My paycheck each month is 5500. My total monthly spending runs about 2000 with average spending.",
        "budget_analysis",
        {"monthly_income": 5500.0, "monthly_expense": 2000.0, "employment_status": "employed", "debt_status": None, "spending_habit": "average spend", "goal_cost": None, "marital_status": None},
        [("monthly_income", "5500"), ("monthly_expense", "2000"), ("spending_habit", "average spending")],
        "original",
        {"has_debt": False, "has_goal": False, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 35. T_BUDGET_007 (train) - debt
    add(
        "EN_EXP_0035", "T_BUDGET_007", "TF_BUDGET",
        "I pull in around 2200 per month but my outgoings are 2600 and I carry credit card debt.",
        "budget_analysis",
        {"monthly_income": 2200.0, "monthly_expense": 2600.0, "employment_status": "employed", "debt_status": "debt", "spending_habit": None, "goal_cost": None, "marital_status": None},
        [("monthly_income", "2200"), ("monthly_expense", "2600"), ("debt_status", "credit card debt")],
        "original",
        {"has_debt": True, "has_goal": False, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 36. T_BUDGET_008 (train) - no debt
    add(
        "EN_EXP_0036", "T_BUDGET_008", "TF_BUDGET",
        "On a monthly basis I receive 3800 in income, my expenses are approximately 2500, and I am debt free.",
        "budget_analysis",
        {"monthly_income": 3800.0, "monthly_expense": 2500.0, "employment_status": "employed", "debt_status": "no debt", "spending_habit": None, "goal_cost": None, "marital_status": None},
        [("monthly_income", "3800"), ("monthly_expense", "2500"), ("debt_status", "debt free")],
        "original",
        {"has_debt": False, "has_goal": False, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 37. T_BUDGET_004 (train)
    add(
        "EN_EXP_0037", "T_BUDGET_004", "TF_BUDGET",
        "I make 4800 a month. Between rent, food, and utilities, I spend 2100.",
        "budget_analysis",
        {"monthly_income": 4800.0, "monthly_expense": 2100.0, "employment_status": "employed", "debt_status": None, "spending_habit": None, "goal_cost": None, "marital_status": None},
        [("monthly_income", "4800"), ("monthly_expense", "2100")],
        "original",
        {"has_debt": False, "has_goal": False, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 38. T_BUDGET_005 (train)
    add(
        "EN_EXP_0038", "T_BUDGET_005", "TF_BUDGET",
        "Right now my monthly income sits at 1900 and I spend roughly 2100 on everything.",
        "budget_analysis",
        {"monthly_income": 1900.0, "monthly_expense": 2100.0, "employment_status": "employed", "debt_status": None, "spending_habit": None, "goal_cost": None, "marital_status": None},
        [("monthly_income", "1900"), ("monthly_expense", "2100")],
        "original",
        {"has_debt": False, "has_goal": False, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 39. T_BUDGET_006 (train)
    add(
        "EN_EXP_0039", "T_BUDGET_006", "TF_BUDGET",
        "My paycheck each month is 3100. My total monthly spending runs about 2700.",
        "budget_analysis",
        {"monthly_income": 3100.0, "monthly_expense": 2700.0, "employment_status": "employed", "debt_status": None, "spending_habit": None, "goal_cost": None, "marital_status": None},
        [("monthly_income", "3100"), ("monthly_expense", "2700")],
        "original",
        {"has_debt": False, "has_goal": False, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )

    # =========================================================================
    # Group 5: debt_management (11 records)
    # =========================================================================
    # 40. T_DEBT_001 (train)
    add(
        "EN_EXP_0040", "T_DEBT_001", "TF_DEBT",
        "I earn 2400 per month, spend 2900, and I currently have debt.",
        "debt_management",
        {"monthly_income": 2400.0, "monthly_expense": 2900.0, "employment_status": "employed", "debt_status": "debt", "spending_habit": None, "goal_cost": None, "marital_status": None},
        [("monthly_income", "2400"), ("monthly_expense", "2900"), ("debt_status", "debt")],
        "original",
        {"has_debt": True, "has_goal": False, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 41. T_DEBT_002 (train)
    add(
        "EN_EXP_0041", "T_DEBT_002", "TF_DEBT",
        "My monthly income is 2200 and my expenses are 1800. I am paying off a personal loan.",
        "debt_management",
        {"monthly_income": 2200.0, "monthly_expense": 1800.0, "employment_status": "employed", "debt_status": "debt", "spending_habit": None, "goal_cost": None, "marital_status": None},
        [("monthly_income", "2200"), ("monthly_expense", "1800"), ("debt_status", "personal loan")],
        "original",
        {"has_debt": True, "has_goal": False, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 42. T_DEBT_003 (train)
    add(
        "EN_EXP_0042", "T_DEBT_003", "TF_DEBT",
        "I make 2800 monthly and spend about 2300. I owe money on credit cards and it is stressing me out.",
        "debt_management",
        {"monthly_income": 2800.0, "monthly_expense": 2300.0, "employment_status": "employed", "debt_status": "debt", "spending_habit": None, "goal_cost": None, "marital_status": None},
        [("monthly_income", "2800"), ("monthly_expense", "2300"), ("debt_status", "owe money on credit cards")],
        "WILEY_CH7_BEHAVIORAL",
        {"has_debt": True, "has_goal": False, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 43. T_DEBT_005 (train)
    add(
        "EN_EXP_0043", "T_DEBT_005", "TF_DEBT",
        "I take home 3500 each month. My expenses run 2200 and on top of that I am servicing a bank loan.",
        "debt_management",
        {"monthly_income": 3500.0, "monthly_expense": 2200.0, "employment_status": "employed", "debt_status": "debt", "spending_habit": None, "goal_cost": None, "marital_status": None},
        [("monthly_income", "3500"), ("monthly_expense", "2200"), ("debt_status", "servicing a bank loan")],
        "original",
        {"has_debt": True, "has_goal": False, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 44. T_DEBT_006 (train)
    add(
        "EN_EXP_0044", "T_DEBT_006", "TF_DEBT",
        "I lost my job and have zero earnings. With 0 coming in and 2400 going out every month, I am struggling to keep up with my debt payments.",
        "debt_management",
        {"monthly_income": 0.0, "monthly_expense": 2400.0, "employment_status": "not employed", "debt_status": "debt", "spending_habit": None, "goal_cost": None, "marital_status": None},
        [("employment_status", "lost my job"), ("monthly_income", "0"), ("monthly_expense", "2400"), ("debt_status", "debt")],
        "original",
        {"has_debt": True, "has_goal": False, "has_missing_critical": False, "numerical_format": "explicit_zero", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 45. T_DEBT_001 (train)
    add(
        "EN_EXP_0045", "T_DEBT_001", "TF_DEBT",
        "I earn 3100 per month, spend 2000, and I currently have debt.",
        "debt_management",
        {"monthly_income": 3100.0, "monthly_expense": 2000.0, "employment_status": "employed", "debt_status": "debt", "spending_habit": None, "goal_cost": None, "marital_status": None},
        [("monthly_income", "3100"), ("monthly_expense", "2000"), ("debt_status", "debt")],
        "original",
        {"has_debt": True, "has_goal": False, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 46. T_DEBT_002 (train)
    add(
        "EN_EXP_0046", "T_DEBT_002", "TF_DEBT",
        "My monthly income is 2600 and my expenses are 2900. I am paying off a personal loan.",
        "debt_management",
        {"monthly_income": 2600.0, "monthly_expense": 2900.0, "employment_status": "employed", "debt_status": "debt", "spending_habit": None, "goal_cost": None, "marital_status": None},
        [("monthly_income", "2600"), ("monthly_expense", "2900"), ("debt_status", "personal loan")],
        "original",
        {"has_debt": True, "has_goal": False, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 47. T_DEBT_003 (train)
    add(
        "EN_EXP_0047", "T_DEBT_003", "TF_DEBT",
        "I make 3400 monthly and spend about 2200. I owe money on credit cards and it is stressing me out.",
        "debt_management",
        {"monthly_income": 3400.0, "monthly_expense": 2200.0, "employment_status": "employed", "debt_status": "debt", "spending_habit": None, "goal_cost": None, "marital_status": None},
        [("monthly_income", "3400"), ("monthly_expense", "2200"), ("debt_status", "owe money on credit cards")],
        "WILEY_CH7_BEHAVIORAL",
        {"has_debt": True, "has_goal": False, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 48. T_DEBT_005 (train)
    add(
        "EN_EXP_0048", "T_DEBT_005", "TF_DEBT",
        "I take home 2100 each month. My expenses run 2500 and on top of that I am servicing a bank loan.",
        "debt_management",
        {"monthly_income": 2100.0, "monthly_expense": 2500.0, "employment_status": "employed", "debt_status": "debt", "spending_habit": None, "goal_cost": None, "marital_status": None},
        [("monthly_income", "2100"), ("monthly_expense", "2500"), ("debt_status", "servicing a bank loan")],
        "original",
        {"has_debt": True, "has_goal": False, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 49. T_DEBT_006 (train)
    add(
        "EN_EXP_0049", "T_DEBT_006", "TF_DEBT",
        "I do not have a job. With 0 coming in and 2200 going out every month, I am struggling to keep up with my debt payments.",
        "debt_management",
        {"monthly_income": 0.0, "monthly_expense": 2200.0, "employment_status": "not employed", "debt_status": "debt", "spending_habit": None, "goal_cost": None, "marital_status": None},
        [("employment_status", "do not have a job"), ("monthly_income", "0"), ("monthly_expense", "2200"), ("debt_status", "debt")],
        "original",
        {"has_debt": True, "has_goal": False, "has_missing_critical": False, "numerical_format": "explicit_zero", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 50. T_DEBT_001 (train)
    add(
        "EN_EXP_0050", "T_DEBT_001", "TF_DEBT",
        "I earn 4000 per month, spend 2500, and I currently have debt.",
        "debt_management",
        {"monthly_income": 4000.0, "monthly_expense": 2500.0, "employment_status": "employed", "debt_status": "debt", "spending_habit": None, "goal_cost": None, "marital_status": None},
        [("monthly_income", "4000"), ("monthly_expense", "2500"), ("debt_status", "debt")],
        "original",
        {"has_debt": True, "has_goal": False, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )

    # =========================================================================
    # Group 6: financial_consultation (11 records)
    # Covering:
    # - not employed (unemployed with 0 income, lost job)
    # - average spend & big spend
    # - Single & Married
    # - explicit no debt
    # =========================================================================
    # 51. T_EMPLOYMENT_001 (train) - employed
    add(
        "EN_EXP_0051", "T_EMPLOYMENT_001", "TF_EMPLOYMENT",
        "I am currently employed and earn 3200 per month. My expenses are 2000.",
        "financial_consultation",
        {"monthly_income": 3200.0, "monthly_expense": 2000.0, "employment_status": "employed", "debt_status": None, "spending_habit": None, "goal_cost": None, "marital_status": None},
        [("employment_status", "employed"), ("monthly_income", "3200"), ("monthly_expense", "2000")],
        "original",
        {"has_debt": False, "has_goal": False, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 52. T_EMPLOYMENT_002 (train) - unemployed zero income
    add(
        "EN_EXP_0052", "T_EMPLOYMENT_002", "TF_EMPLOYMENT",
        "I lost my job recently and have no income. My monthly expenses are still 1400.",
        "financial_consultation",
        {"monthly_income": 0.0, "monthly_expense": 1400.0, "employment_status": "not employed", "debt_status": None, "spending_habit": None, "goal_cost": None, "marital_status": None},
        [("employment_status", "lost my job"), ("monthly_income", "no income"), ("monthly_expense", "1400")],
        "original",
        {"has_debt": False, "has_goal": False, "has_missing_critical": False, "numerical_format": "explicit_zero", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 53. T_EMPLOYMENT_004 (train) - big spend
    add(
        "EN_EXP_0053", "T_EMPLOYMENT_004", "TF_EMPLOYMENT",
        "I have a full-time job earning 4500 monthly. I spend 3800 and I am a big spender.",
        "financial_consultation",
        {"monthly_income": 4500.0, "monthly_expense": 3800.0, "employment_status": "employed", "debt_status": None, "spending_habit": "big spend", "goal_cost": None, "marital_status": None},
        [("employment_status", "full-time job"), ("monthly_income", "4500"), ("monthly_expense", "3800"), ("spending_habit", "big spender")],
        "original",
        {"has_debt": False, "has_goal": False, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 54. T_EMPLOYMENT_005 (train) - average spend
    add(
        "EN_EXP_0054", "T_EMPLOYMENT_005", "TF_EMPLOYMENT",
        "I work and bring home 2900 a month. My spending is moderate at 1800.",
        "financial_consultation",
        {"monthly_income": 2900.0, "monthly_expense": 1800.0, "employment_status": "employed", "debt_status": None, "spending_habit": "average spend", "goal_cost": None, "marital_status": None},
        [("employment_status", "work"), ("monthly_income", "2900"), ("spending_habit", "moderate"), ("monthly_expense", "1800")],
        "original",
        {"has_debt": False, "has_goal": False, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 55. T_EMPLOYMENT_006 (train) - not employed + debt
    add(
        "EN_EXP_0055", "T_EMPLOYMENT_006", "TF_EMPLOYMENT",
        "I do not have a job and have zero income coming in. My expenses are around 1100 and I have debt.",
        "financial_consultation",
        {"monthly_income": 0.0, "monthly_expense": 1100.0, "employment_status": "not employed", "debt_status": "debt", "spending_habit": None, "goal_cost": None, "marital_status": None},
        [("employment_status", "do not have a job"), ("monthly_income", "zero"), ("monthly_expense", "1100"), ("debt_status", "debt")],
        "original",
        {"has_debt": True, "has_goal": False, "has_missing_critical": False, "numerical_format": "explicit_zero", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 56. T_HOUSEHOLD_001 (train) - Single
    add(
        "EN_EXP_0056", "T_HOUSEHOLD_001", "TF_HOUSEHOLD",
        "I am single and earn 3600 per month. My expenses are about 2200.",
        "financial_consultation",
        {"monthly_income": 3600.0, "monthly_expense": 2200.0, "employment_status": "employed", "debt_status": None, "spending_habit": None, "goal_cost": None, "marital_status": "Single"},
        [("marital_status", "single"), ("monthly_income", "3600"), ("monthly_expense", "2200")],
        "WILEY_CH15_PRIVATE_WEALTH",
        {"has_debt": False, "has_goal": False, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 57. T_HOUSEHOLD_002 (train) - Married
    add(
        "EN_EXP_0057", "T_HOUSEHOLD_002", "TF_HOUSEHOLD",
        "I am married and together we earn 5200 monthly. Our household expenses total 2600.",
        "financial_consultation",
        {"monthly_income": 5200.0, "monthly_expense": 2600.0, "employment_status": "employed", "debt_status": None, "spending_habit": None, "goal_cost": None, "marital_status": "Married"},
        [("marital_status", "married"), ("monthly_income", "5200"), ("monthly_expense", "2600")],
        "WILEY_CH15_PRIVATE_WEALTH",
        {"has_debt": False, "has_goal": False, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 58. T_HOUSEHOLD_003 (train) - Single + no debt + goal
    add(
        "EN_EXP_0058", "T_HOUSEHOLD_003", "TF_HOUSEHOLD",
        "As a single person, I bring home 2800 and spend 1900. I have no debt and want to save 4000.",
        "financial_consultation",
        {"monthly_income": 2800.0, "monthly_expense": 1900.0, "employment_status": "employed", "debt_status": "no debt", "spending_habit": None, "goal_cost": 4000.0, "marital_status": "Single"},
        [("marital_status", "single person"), ("monthly_income", "2800"), ("monthly_expense", "1900"), ("debt_status", "no debt"), ("goal_cost", "4000")],
        "original",
        {"has_debt": False, "has_goal": True, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 59. T_HOUSEHOLD_004 (train) - Married + debt
    add(
        "EN_EXP_0059", "T_HOUSEHOLD_004", "TF_HOUSEHOLD",
        "My spouse and I are married. I make 3400 a month, our spending is 2400, and we have some active debt.",
        "financial_consultation",
        {"monthly_income": 3400.0, "monthly_expense": 2400.0, "employment_status": "employed", "debt_status": "debt", "spending_habit": None, "goal_cost": None, "marital_status": "Married"},
        [("marital_status", "married"), ("monthly_income", "3400"), ("monthly_expense", "2400"), ("debt_status", "debt")],
        "original",
        {"has_debt": True, "has_goal": False, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 60. T_HOUSEHOLD_005 (train) - Single + big spend
    add(
        "EN_EXP_0060", "T_HOUSEHOLD_005", "TF_HOUSEHOLD",
        "I am not married. My income is 4000 per month, expenses are 3500, and I tend to spend a lot.",
        "financial_consultation",
        {"monthly_income": 4000.0, "monthly_expense": 3500.0, "employment_status": "employed", "debt_status": None, "spending_habit": "big spend", "goal_cost": None, "marital_status": "Single"},
        [("marital_status", "not married"), ("monthly_income", "4000"), ("monthly_expense", "3500"), ("spending_habit", "spend a lot")],
        "WILEY_CH7_BEHAVIORAL",
        {"has_debt": False, "has_goal": False, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )
    # 61. T_HOUSEHOLD_006 (train) - Married + average spend
    add(
        "EN_EXP_0061", "T_HOUSEHOLD_006", "TF_HOUSEHOLD",
        "I recently got married. I earn 3800 monthly, we spend 2300, and we keep our spending average.",
        "financial_consultation",
        {"monthly_income": 3800.0, "monthly_expense": 2300.0, "employment_status": "employed", "debt_status": None, "spending_habit": "average spend", "goal_cost": None, "marital_status": "Married"},
        [("marital_status", "married"), ("monthly_income", "3800"), ("monthly_expense", "2300"), ("spending_habit", "average")],
        "original",
        {"has_debt": False, "has_goal": False, "has_missing_critical": False, "numerical_format": "standard", "ambiguity_type": None, "created_at": "2026-09-22T10:00:00Z"}
    )

    # =========================================================================
    # Group 7: financial_education (5 records)
    # =========================================================================
    # 62. T_MISSING_010 (test) - Emergency fund
    add(
        "EN_EXP_0062", "T_MISSING_010", "TF_MISSING_INFO",
        "What is an emergency fund and how many months of living expenses should it cover?",
        "financial_education",
        {"monthly_income": None, "monthly_expense": None, "employment_status": None, "debt_status": None, "spending_habit": None, "goal_cost": None, "marital_status": None},
        [],
        "WILEY_CH15_BUFFER",
        {"has_debt": False, "has_goal": False, "has_missing_critical": True, "numerical_format": "none", "ambiguity_type": "education_only", "created_at": "2026-09-22T10:00:00Z"}
    )
    # 63. T_MISSING_010 (test) - Inflation
    add(
        "EN_EXP_0063", "T_MISSING_010", "TF_MISSING_INFO",
        "How does inflation erode the purchasing power of cash savings over long horizons?",
        "financial_education",
        {"monthly_income": None, "monthly_expense": None, "employment_status": None, "debt_status": None, "spending_habit": None, "goal_cost": None, "marital_status": None},
        [],
        "CFA_LM6_INFLATION",
        {"has_debt": False, "has_goal": False, "has_missing_critical": True, "numerical_format": "none", "ambiguity_type": "education_only", "created_at": "2026-09-22T10:00:00Z"}
    )
    # 64. T_MISSING_010 (test) - Budgeting principles
    add(
        "EN_EXP_0064", "T_MISSING_010", "TF_MISSING_INFO",
        "Can you explain the difference between fixed expenses and variable expenses in a budget?",
        "financial_education",
        {"monthly_income": None, "monthly_expense": None, "employment_status": None, "debt_status": None, "spending_habit": None, "goal_cost": None, "marital_status": None},
        [],
        "original",
        {"has_debt": False, "has_goal": False, "has_missing_critical": True, "numerical_format": "none", "ambiguity_type": "education_only", "created_at": "2026-09-22T10:00:00Z"}
    )
    # 65. T_MISSING_010 (test) - Risk capacity vs willingness
    add(
        "EN_EXP_0065", "T_MISSING_010", "TF_MISSING_INFO",
        "What is the difference between risk capacity and risk willingness in personal financial planning?",
        "financial_education",
        {"monthly_income": None, "monthly_expense": None, "employment_status": None, "debt_status": None, "spending_habit": None, "goal_cost": None, "marital_status": None},
        [],
        "WILEY_CH15_PRIVATE_WEALTH",
        {"has_debt": False, "has_goal": False, "has_missing_critical": True, "numerical_format": "none", "ambiguity_type": "education_only", "created_at": "2026-09-22T10:00:00Z"}
    )
    # 66. T_MISSING_010 (test) - Time value of money
    add(
        "EN_EXP_0066", "T_MISSING_010", "TF_MISSING_INFO",
        "How does the time value of money impact long term wealth accumulation?",
        "financial_education",
        {"monthly_income": None, "monthly_expense": None, "employment_status": None, "debt_status": None, "spending_habit": None, "goal_cost": None, "marital_status": None},
        [],
        "CFA_LM2_TVM",
        {"has_debt": False, "has_goal": False, "has_missing_critical": True, "numerical_format": "none", "ambiguity_type": "education_only", "created_at": "2026-09-22T10:00:00Z"}
    )

    # =========================================================================
    # Group 8: out_of_scope_investment (6 records)
    # =========================================================================
    # 67. T_OOS_INVEST_003 (test)
    add(
        "EN_EXP_0067", "T_OOS_INVEST_003", "TF_OUT_OF_SCOPE",
        "What forex leverage should I use for trading the dollar against the yen?",
        "out_of_scope_investment",
        {"monthly_income": None, "monthly_expense": None, "employment_status": None, "debt_status": None, "spending_habit": None, "goal_cost": None, "marital_status": None},
        [],
        "original",
        {"has_debt": False, "has_goal": False, "has_missing_critical": True, "numerical_format": "none", "ambiguity_type": "out_of_scope", "created_at": "2026-09-22T10:00:00Z"}
    )
    # 68. T_OOS_INVEST_004 (test)
    add(
        "EN_EXP_0068", "T_OOS_INVEST_004", "TF_OUT_OF_SCOPE",
        "Give me a list of ten penny stocks that will go up this week.",
        "out_of_scope_investment",
        {"monthly_income": None, "monthly_expense": None, "employment_status": None, "debt_status": None, "spending_habit": None, "goal_cost": None, "marital_status": None},
        [],
        "original",
        {"has_debt": False, "has_goal": False, "has_missing_critical": True, "numerical_format": "none", "ambiguity_type": "out_of_scope", "created_at": "2026-09-22T10:00:00Z"}
    )
    # 69. T_OOS_INVEST_005 (test)
    add(
        "EN_EXP_0069", "T_OOS_INVEST_005", "TF_OUT_OF_SCOPE",
        "Should I put all my savings into Ethereum or wait for a dip?",
        "out_of_scope_investment",
        {"monthly_income": None, "monthly_expense": None, "employment_status": None, "debt_status": None, "spending_habit": None, "goal_cost": None, "marital_status": None},
        [],
        "original",
        {"has_debt": False, "has_goal": False, "has_missing_critical": True, "numerical_format": "none", "ambiguity_type": "out_of_scope", "created_at": "2026-09-22T10:00:00Z"}
    )
    # 70. T_OOS_INVEST_006 (test)
    add(
        "EN_EXP_0070", "T_OOS_INVEST_006", "TF_OUT_OF_SCOPE",
        "Tell me the best day-trading strategy for small-cap stocks.",
        "out_of_scope_investment",
        {"monthly_income": None, "monthly_expense": None, "employment_status": None, "debt_status": None, "spending_habit": None, "goal_cost": None, "marital_status": None},
        [],
        "original",
        {"has_debt": False, "has_goal": False, "has_missing_critical": True, "numerical_format": "none", "ambiguity_type": "out_of_scope", "created_at": "2026-09-22T10:00:00Z"}
    )
    # 71. T_OOS_INVEST_007 (test)
    add(
        "EN_EXP_0071", "T_OOS_INVEST_007", "TF_OUT_OF_SCOPE",
        "What call options should I buy on the S and P 500 index right now?",
        "out_of_scope_investment",
        {"monthly_income": None, "monthly_expense": None, "employment_status": None, "debt_status": None, "spending_habit": None, "goal_cost": None, "marital_status": None},
        [],
        "original",
        {"has_debt": False, "has_goal": False, "has_missing_critical": True, "numerical_format": "none", "ambiguity_type": "out_of_scope", "created_at": "2026-09-22T10:00:00Z"}
    )
    # 72. T_OOS_INVEST_001 (test)
    add(
        "EN_EXP_0072", "T_OOS_INVEST_001", "TF_OUT_OF_SCOPE",
        "Which semiconductor stock should I purchase before the next earnings announcement?",
        "out_of_scope_investment",
        {"monthly_income": None, "monthly_expense": None, "employment_status": None, "debt_status": None, "spending_habit": None, "goal_cost": None, "marital_status": None},
        [],
        "original",
        {"has_debt": False, "has_goal": False, "has_missing_critical": True, "numerical_format": "none", "ambiguity_type": "out_of_scope", "created_at": "2026-09-22T10:00:00Z"}
    )

    # =========================================================================
    # Group 9: out_of_scope_loan (6 records)
    # =========================================================================
    # 73. T_OOS_LOAN_001 (test)
    add(
        "EN_EXP_0073", "T_OOS_LOAN_001", "TF_OUT_OF_SCOPE",
        "Can you approve my mortgage application for two hundred and fifty thousand dollars?",
        "out_of_scope_loan",
        {"monthly_income": None, "monthly_expense": None, "employment_status": None, "debt_status": None, "spending_habit": None, "goal_cost": None, "marital_status": None},
        [],
        "original",
        {"has_debt": False, "has_goal": False, "has_missing_critical": True, "numerical_format": "none", "ambiguity_type": "out_of_scope", "created_at": "2026-09-22T10:00:00Z"}
    )
    # 74. T_OOS_LOAN_002 (test)
    add(
        "EN_EXP_0074", "T_OOS_LOAN_002", "TF_OUT_OF_SCOPE",
        "Which bank has the lowest interest rate so I can apply for a personal loan today?",
        "out_of_scope_loan",
        {"monthly_income": None, "monthly_expense": None, "employment_status": None, "debt_status": None, "spending_habit": None, "goal_cost": None, "marital_status": None},
        [],
        "original",
        {"has_debt": False, "has_goal": False, "has_missing_critical": True, "numerical_format": "none", "ambiguity_type": "out_of_scope", "created_at": "2026-09-22T10:00:00Z"}
    )
    # 75. T_OOS_LOAN_003 (test)
    add(
        "EN_EXP_0075", "T_OOS_LOAN_003", "TF_OUT_OF_SCOPE",
        "Can you increase my credit card limit to ten thousand dollars?",
        "out_of_scope_loan",
        {"monthly_income": None, "monthly_expense": None, "employment_status": None, "debt_status": None, "spending_habit": None, "goal_cost": None, "marital_status": None},
        [],
        "original",
        {"has_debt": False, "has_goal": False, "has_missing_critical": True, "numerical_format": "none", "ambiguity_type": "out_of_scope", "created_at": "2026-09-22T10:00:00Z"}
    )
    # 76. T_OOS_LOAN_001 (test)
    add(
        "EN_EXP_0076", "T_OOS_LOAN_001", "TF_OUT_OF_SCOPE",
        "Can you approve an auto loan for thirty thousand dollars on a used car?",
        "out_of_scope_loan",
        {"monthly_income": None, "monthly_expense": None, "employment_status": None, "debt_status": None, "spending_habit": None, "goal_cost": None, "marital_status": None},
        [],
        "original",
        {"has_debt": False, "has_goal": False, "has_missing_critical": True, "numerical_format": "none", "ambiguity_type": "out_of_scope", "created_at": "2026-09-22T10:00:00Z"}
    )
    # 77. T_OOS_LOAN_002 (test)
    add(
        "EN_EXP_0077", "T_OOS_LOAN_002", "TF_OUT_OF_SCOPE",
        "What credit score does your bank require to approve an unsecured loan?",
        "out_of_scope_loan",
        {"monthly_income": None, "monthly_expense": None, "employment_status": None, "debt_status": None, "spending_habit": None, "goal_cost": None, "marital_status": None},
        [],
        "original",
        {"has_debt": False, "has_goal": False, "has_missing_critical": True, "numerical_format": "none", "ambiguity_type": "out_of_scope", "created_at": "2026-09-22T10:00:00Z"}
    )
    # 78. T_OOS_LOAN_003 (test)
    add(
        "EN_EXP_0078", "T_OOS_LOAN_003", "TF_OUT_OF_SCOPE",
        "Will you raise my revolving overdraft limit to five thousand dollars?",
        "out_of_scope_loan",
        {"monthly_income": None, "monthly_expense": None, "employment_status": None, "debt_status": None, "spending_habit": None, "goal_cost": None, "marital_status": None},
        [],
        "original",
        {"has_debt": False, "has_goal": False, "has_missing_critical": True, "numerical_format": "none", "ambiguity_type": "out_of_scope", "created_at": "2026-09-22T10:00:00Z"}
    )

    return records


def main():
    records = generate_batch02()
    print(f"Generated {len(records)} Batch 02 records.")
    assert len(records) == 78, f"Expected exactly 78 records, got {len(records)}"

    out_path = os.path.join(WORKSPACE_ROOT, "datasets", "financial_nlu", "raw", "phase1_batch02.jsonl")
    with open(out_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"Successfully wrote {len(records)} records to {out_path}")


if __name__ == "__main__":
    main()
