import pytest
from training.llm_output_normalizer import normalize_llm_output, clean_numeric

def test_clean_numeric():
    assert clean_numeric("$5,000") == 5000.0
    assert clean_numeric("5,000") == 5000.0
    assert clean_numeric("$5000") == 5000.0
    assert clean_numeric(5000) == 5000.0
    assert clean_numeric(5000.0) == 5000.0
    assert clean_numeric("5000.50") == 5000.50
    assert clean_numeric(None) is None
    assert clean_numeric("null") is None
    assert clean_numeric("unknown") is None
    assert clean_numeric("invalid") is None

def test_case_1_prevent_copy_expense_to_income():
    user = "I spend about $2,300 every month and I am employed."
    llm = {
        "monthly_income": 2300.0,
        "monthly_expense": 2300.0,
        "employment_status": "employed"
    }
    res = normalize_llm_output(llm, user)
    assert res["monthly_income"] is None
    assert res["monthly_expense"] == 2300.0
    assert res["employment_status"] == "employed"

def test_case_2_no_employment_inference_from_income():
    user = "I earn $4,000 and spend $2,500. I'm married."
    llm = {
        "monthly_income": 4000.0,
        "monthly_expense": 2500.0,
        "employment_status": "employed",
        "marital_status": "Married"
    }
    res = normalize_llm_output(llm, user)
    assert res["monthly_income"] == 4000.0
    assert res["monthly_expense"] == 2500.0
    assert res["employment_status"] is None
    assert res["marital_status"] == "Married"

def test_case_3_explicit_zero_income():
    user = "I have no income and my expenses are $500."
    llm = {
        "monthly_income": 0.0,
        "monthly_expense": 500.0
    }
    res = normalize_llm_output(llm, user)
    assert res["monthly_income"] == 0.0
    assert res["monthly_expense"] == 500.0

def test_case_4_currency_string_normalization_and_null_preservation():
    user = "I have no debt and want to save $5,000."
    llm = {
        "monthly_income": None,
        "monthly_expense": None,
        "goal_cost": "$5,000",
        "debt_status": "no debt"
    }
    res = normalize_llm_output(llm, user)
    assert res["monthly_income"] is None
    assert res["monthly_expense"] is None
    assert res["goal_cost"] == 5000.0
    assert res["debt_status"] == "no debt"

def test_case_5_debt_omission_preservation():
    user = "I earn $3,000 and spend $2,000. I didn't say whether I have debt."
    llm = {
        "monthly_income": 3000,
        "monthly_expense": 2000,
        "debt_status": None
    }
    res = normalize_llm_output(llm, user)
    assert res["monthly_income"] == 3000.0
    assert res["monthly_expense"] == 2000.0
    assert res["debt_status"] is None

def test_case_6_explicit_full_time_work():
    user = "I work full-time and earn $4,000 per month."
    llm = {
        "monthly_income": 4000,
        "employment_status": "employed"
    }
    res = normalize_llm_output(llm, user)
    assert res["monthly_income"] == 4000.0
    assert res["employment_status"] == "employed"

def test_case_7_explicit_not_employed_and_zero_income():
    user = "I have no job and currently have no income."
    llm = {
        "monthly_income": 0,
        "employment_status": "not employed"
    }
    res = normalize_llm_output(llm, user)
    assert res["monthly_income"] == 0.0
    assert res["employment_status"] == "not employed"

def test_case_8_reject_unsupported_guesses():
    user = "I earn $3,000."
    llm = {
        "monthly_income": 3000,
        "monthly_expense": 3000,
        "employment_status": "employed"
    }
    res = normalize_llm_output(llm, user)
    assert res["monthly_income"] == 3000.0
    assert res["monthly_expense"] is None
    assert res["employment_status"] is None

def test_string_llm_input_with_markdown():
    user = "I earn $3,000 per month and have no debt."
    raw_llm_str = '```json\n{"monthly_income": "3,000", "monthly_expense": null, "debt_status": "no debt"}\n```'
    res = normalize_llm_output(raw_llm_str, user)
    assert res["monthly_income"] == 3000.0
    assert res["monthly_expense"] is None
    assert res["debt_status"] == "no debt"
    assert res["employment_status"] is None

def test_no_debt_inference_when_debt_unmentioned():
    user = "I earn $2,500 and spend $1,800 every month."
    # LLM incorrectly guesses "no debt"
    llm = {
        "monthly_income": 2500.0,
        "monthly_expense": 1800.0,
        "debt_status": "no debt"
    }
    res = normalize_llm_output(llm, user)
    # Since user never mentioned debt, debt_status must be None
    assert res["debt_status"] is None

def test_no_expense_inference_when_expenses_unmentioned():
    user = "I earn $3,500 monthly."
    # LLM incorrectly guesses an expense of 1000 or copies income
    llm = {
        "monthly_income": 3500.0,
        "monthly_expense": 1000.0
    }
    res = normalize_llm_output(llm, user)
    assert res["monthly_income"] == 3500.0
    assert res["monthly_expense"] is None
