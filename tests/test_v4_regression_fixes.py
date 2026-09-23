"""
Regression Test Suite: Verification of Fixes for V2 vs V4 Comparison Failures.

Tests all 7 focus areas:
1. Multi-turn calculations must use the correct verified surplus ($850 -> $3,400 / $850 = 4 months).
2. Never calculate surplus when monthly expenses are missing.
3. Never invent financial values or profile facts ($1,100 * 12 = $13,200, $600 / $1,500 = 40%).
4. Scam responses must distinguish confirmed indicators from uncertain claims without unsubstantiated labels.
5. Preserve no-debt behavior across all scenarios.
6. Test Khmer grammar, meaning, and financial accuracy—not only Unicode.
7. Keep ConsultantEngine as sole authority for calculations, rules, and recommendations;
   OutputNormalizer validates, sanitizes, and rejects/corrects unsupported LLM outputs.
"""

import re
import pytest
from app.services.consultant_engine import ConsultantEngine
from app.services.consultant_validator import ConsultantInputValidator
from training.llm_output_normalizer import (
    normalize_and_verify_response,
    sanitize_khmer_terminology,
    sanitize_scam_response,
    sanitize_missing_expenses_response,
    sanitize_arithmetic_and_divisors,
    sanitize_no_debt_advice,
    detect_expense_mentioned,
    detect_debt_status,
)


# =============================================================================
# 1. Multi-turn Calculation Uses Verified Surplus (Test 5 Failure Fix)
# =============================================================================

def test_multiturn_calculation_uses_verified_surplus():
    """
    Failure in V4 comparison: V4 divided by $500 (old food cost) instead of $850 (new surplus),
    yielding 6 months ($3,400 / $500) instead of 4 months ($3,400 / $850).
    Proves that OutputNormalizer verifies and corrects the calculation to 4 months ($3,400 / $850).
    """
    user_input = (
        "User: My monthly income is $2,000 and my rent is $600, food is $500, utilities are $150. I have no debt.\n"
        "Assistant: Your total expenses are $1,250, leaving you with a monthly surplus of $750.\n"
        "User: If I reduce food costs by $100, what will be my new surplus, and how many months will it take to save a $3,400 emergency reserve?"
    )
    raw_v4_drifted_response = (
        "Reducing your monthly food budget by $100 increases your monthly surplus by $500 to $850. "
        "Saving a $3,400 emergency reserve will now take approximately 6 months ($3,400 / $500 = 6 months)."
    )

    verified = normalize_and_verify_response(raw_v4_drifted_response, user_input=user_input)

    # Must NOT divide by $500
    assert "$3,400 / $500" not in verified
    assert "$3,400 ÷ $500" not in verified
    # Must use $850 verified surplus
    assert "$850" in verified
    # Must calculate exactly 4 months ($3,400 / $850 = 4 months)
    assert "4 months ($3,400 / $850 = 4 months)" in verified
    assert "increases your monthly surplus by $100" in verified


# =============================================================================
# 2. Never Calculate Surplus When Expenses Are Missing (Test 8 Failure Fix)
# =============================================================================

def test_missing_expenses_never_calculates_surplus():
    """
    Failure in V4 comparison: User asked 'I want to buy a house in 3 years and I make $2,200/month. Can I afford it?'.
    V4 hallucinated 'leaves you with an active surplus of $1,480/month' when expenses were completely missing.
    Proves that OutputNormalizer strictly rejects/intercepts ungrounded surplus claims and prompts for living costs.
    """
    user_input = "I want to buy a house in 3 years and I make $2,200/month. Can I afford it?"
    raw_v4_hallucinated_response = (
        "Making $2,200 each month leaves you with an active surplus of $1,480/month. "
        "However, to calculate your exact savings capacity, I need to know how much debt you currently carry."
    )

    verified = normalize_and_verify_response(raw_v4_hallucinated_response, user_input=user_input, lang="en")

    # Must NOT contain the ungrounded $1,480 surplus
    assert "$1,480" not in verified
    assert "surplus of $1,480" not in verified
    # Must explicitly state that monthly expenses are required
    assert "monthly living expenses" in verified.lower() or "monthly expenses" in verified.lower()
    assert "cannot be calculated without guessing" in verified.lower()


def test_missing_expenses_khmer_never_calculates_surplus():
    """
    Proves missing expense protection works symmetrically in Khmer.
    """
    user_input = "ខ្ញុំរកចំណូលបាន $1,500/ខែ តើខ្ញុំអាចទិញផ្ទះបានទេ?"
    raw_km_hallucinated = "ចំណូលរបស់អ្នក $1,500 ធ្វើឱ្យអ្នកសល់ប្រាក់ $800 ក្នុងមួយខែ។"

    verified = normalize_and_verify_response(raw_km_hallucinated, user_input=user_input, lang="km")

    assert "$800" not in verified
    assert "ការចំណាយប្រចាំខែ" in verified
    assert "មិនអាចគណនាប្រាក់សល់" in verified


# =============================================================================
# 3. Never Invent Financial Values or Facts (Test 6 & 3 Arithmetic Fixes)
# =============================================================================

def test_profile_update_annual_math_exactness():
    """
    Failure in V4 comparison: V4 wrote '$1,100 * 12 = $15,600' instead of '$13,200'
    and claimed 'increased from $600 to $15,600 (+$9,000/month)'.
    Proves OutputNormalizer verifies exact arithmetic: $1,100 * 12 = $13,200.
    """
    user_input = (
        "Previous profile: income=$1,800/mo, expenses=$1,200/mo, surplus=+$600/mo, debt=no debt. "
        "User updates: I received a promotion to $2,400/mo, but my rent increased by $100 so new expenses are $1,300/mo. "
        "What is my new monthly surplus and how much more can I save each year?"
    )
    raw_v4_math_error = (
        "Congratulations on the raise! Here is your updated cash flow:\n"
        "- Previous Monthly Surplus: $600 (annual savings capacity: $7,200)\n"
        "- New Monthly Surplus: $1,100 ($2,400 - $1,300)\n"
        "- New Monthly Savings Capacity: $15,600/yr ($1,100 * 12)\n"
        "Your monthly savings capacity has increased from $600 to $15,600 (+$9,000/month) while remaining completely debt-free."
    )

    verified = normalize_and_verify_response(raw_v4_math_error, user_input=user_input)

    # Must NOT have $15,600 or +$9,000/month
    assert "$15,600" not in verified
    assert "+$9,000" not in verified
    # Must have exact arithmetic: $1,100 * 12 = $13,200
    assert "$13,200/yr ($1,100 * 12)" in verified
    assert "increased by $500/month (from $600 to $1,100)" in verified
    assert "$6,000/year" in verified


def test_mixed_code_switching_savings_rate_math():
    """
    Failure in V4 comparison: On $1,500 salary with $900 expense ($600 surplus),
    V4 generated '30.0% ($600 / 2,000)' instead of '40.0% ($600 / $1,500)'.
    Proves OutputNormalizer corrects percentage calculation to 40.0% ($600 / $1,500).
    """
    user_input = "សួស្តី advisor, net salary ខ្ញុំ $1,500/month ចំណាយ regular expenses $900។ តើ savings rate របស់ខ្ញុំ healthy អត់ ហើយគួរ allocate surplus យ៉ាងម៉េច?"
    raw_v4_calc = "Savings rate របស់អ្នកគឺ 30.0% ($600 / 2,000) ដែលជាការលឿនបំផុត។"

    verified = normalize_and_verify_response(raw_v4_calc, user_input=user_input)

    assert "40.0% ($600 / $1,500)" in verified
    assert "30.0% ($600 / 2,000)" not in verified


# =============================================================================
# 4. Scam Responses Distinguish Verified Indicators from Unverified Claims
# =============================================================================

def test_scam_response_distinguishes_confirmed_indicators_from_uncertain_claims():
    """
    Failure in V4 comparison: V4 called the scheme an 'advance-fee laundering scam'
    and called 40% 'economically impossible' without evidence.
    User instruction:
    - Do NOT state that 40% monthly return is 'economically impossible'.
    - Do NOT definitively label as laundering scam without evidence.
    - Treat guaranteed extreme returns, unsolicited Telegram contact, and upfront payment as strong red flags.
    - Clearly distinguish verified indicators from unverified claims.
    """
    user_input = "A broker on Telegram promised a 40% guaranteed return per month on a private crypto arbitrage pool if I deposit $2,000. Should I do it or will you approve my loan to invest in it?"
    raw_v4_response = (
        "Do not deposit any funds. This is an advance-fee laundering scam. "
        "Crypto arbitrage pools never pay 40% returns; this is a fraudulent demand for upfront fees. "
        "Block the sender and report them as scams."
    )

    verified = normalize_and_verify_response(raw_v4_response, user_input=user_input)

    # Must NOT label as 'laundering scam' or say 'economically impossible'
    assert "laundering scam" not in verified.lower()
    assert "economically impossible" not in verified.lower()

    # Must refuse deposit and loan approval
    assert "do not deposit" in verified.lower()
    assert "cannot approve any loan" in verified.lower()

    # Must clearly separate Verified Red Flags from Unverified Claims
    assert "Verified Red Flags:" in verified
    assert "Guaranteed Extreme Returns" in verified
    assert "Unsolicited Private Contact" in verified
    assert "Upfront Capital Demands" in verified
    assert "Unverified Claims:" in verified
    assert "Recommended Action:" in verified


def test_scam_response_khmer_taxonomy():
    """
    Proves scam indicator taxonomy in Khmer language.
    """
    user_input = "មានម្នាក់នៅ Telegram សន្យាធានាផលចំណេញ 40% ក្នុងមួយខែលើ crypto pool បើខ្ញុំដាក់ប្រាក់ $2,000។ តើខ្ញុំគួរធ្វើទេ ហើយជួយអនុម័តកម្ចីឱ្យខ្ញុំបានទេ?"
    raw_response = "នេះជាការបោកប្រាស់លាងលុយកខ្វក់។"

    verified = normalize_and_verify_response(raw_response, user_input=user_input, lang="km")

    assert "សញ្ញាព្រមានសំខាន់ៗដែលបានផ្ទៀងផ្ទាត់ (Verified Red Flags):" in verified
    assert "ព័ត៌មានដែលមិនទាន់អាចផ្ទៀងផ្ទាត់បាន (Unverified Claims):" in verified
    assert "មិនអាចអនុម័តប្រាក់កម្ចី" in verified


# =============================================================================
# 5. Preserve No-Debt Behavior Across All Scenarios
# =============================================================================

def test_no_debt_preservation_strips_credit_card_payoff():
    """
    Failure in V2: Advised 'paying off high-interest credit card balances if available' to debt-free users.
    Proves OutputNormalizer strips any credit card / loan payoff recommendation when profile is debt-free.
    """
    user_input = "I make $4,000/mo, expenses=$2,600/mo, surplus=+$1,400/mo, debt=no debt. How should I allocate my budget?"
    raw_advice_with_debt_leak = (
        "For your $4,000 income, allocate 50% toward necessities and 30% toward wants. "
        "This leaves $900 remaining which can be directed towards building your emergency reserve "
        "or paying off high-interest credit card balances if available."
    )

    verified = normalize_and_verify_response(
        raw_advice_with_debt_leak,
        user_input=user_input,
        context_profile={"debt_status": "no debt"}
    )

    # Must NOT advise paying off credit cards
    assert "paying off high-interest credit card balances" not in verified
    assert "expanding your emergency reserve" in verified


def test_no_debt_preservation_for_explicit_zero_debt_user():
    """
    Proves that when user says 'I have completely zero debt', no debt payoff advice survives.
    """
    user_input = "I make $3,000 and spend $2,000 every month. I have completely zero debt. What should my primary financial priorities be?"
    raw_advice = "Your priority should be paying off credit card debt before investing."

    verified = normalize_and_verify_response(raw_advice, user_input=user_input)

    assert "paying off credit card debt" not in verified
    assert "funding your emergency reserves" in verified


# =============================================================================
# 6. Khmer Grammar, Meaning, and Financial Accuracy (Test 2 Failure Fix)
# =============================================================================

def test_khmer_terminology_no_inappropriate_debt_words():
    """
    Failure in V4 comparison: V4 used 'ជំពាក់' (debt obligation) in front of Needs & Wants:
    '- 50% សម្រាប់ Needs (ជំពាក់ថ្លៃស្នាក់នៅ ម្ហូបអាហារ...)'
    '- 30% សម្រាប់ Wants (ជំពាក់ថ្លៃដែលអ្នកចាំបាច់ដើរលុយបន្តិច)'
    Proves that OutputNormalizer replaces 'ជំពាក់' with correct Khmer financial terms
    'តម្រូវការចាំបាច់ ដូចជា' and 'ការចំណាយផ្ទាល់ខ្លួន ឬការកម្សាន្ត'.
    """
    raw_v4_khmer = (
        "អ្នកគួរលើកលុយ '50/30/20' សម្រាប់ការចំណាយ:\n"
        "- 50% សម្រាប់ Needs (ជំពាក់ថ្លៃស្នាក់នៅ ម្ហូបអាហារ វិក្កយបត្រភ្លើងទឹក និងការធ្វើដំណើរ។ )\n"
        "- 30% សម្រាប់ Wants (ជំពាក់ថ្លៃដែលអ្នកចាំបាច់ដើរលុយបន្តិច)\n"
        "- 20% សម្រាប់ Savings (សន្សំឱ្យបាន Emergency Fund នៅ 3 ខែ)។ នេះជាទិសដៅដ៏រឹងមាំ!"
    )

    verified = sanitize_khmer_terminology(raw_v4_khmer)

    # Must NOT use 'ជំពាក់' for living expenses
    assert "ជំពាក់ថ្លៃស្នាក់នៅ" not in verified
    assert "ជំពាក់ថ្លៃ" not in verified
    # Must use proper Khmer financial terms
    assert "ដូចជាថ្លៃស្នាក់នៅ" in verified
    assert "ការចំណាយផ្ទាល់ខ្លួន ឬការកម្សាន្ត" in verified
    assert "ប្រើប្រាស់ក្បួនថវិកា '50/30/20'" in verified


def test_khmer_terminology_preserves_legitimate_debt_usage():
    """
    Proves that 'ជំពាក់' IS preserved when legitimately used for actual debt obligations
    (e.g., 'មិនមានបំណុលជាប់ជំពាក់' or 'កុំឱ្យជំពាក់បំណុលគេ').
    """
    legit_debt_text = "យោងតាមប្រព័ន្ធ អ្នកមិនមានបំណុលជាប់ជំពាក់នោះទេ។"
    sanitized = sanitize_khmer_terminology(legit_debt_text)
    assert sanitized == legit_debt_text
    assert "ជំពាក់" in sanitized


# =============================================================================
# 7. ConsultantEngine and OutputNormalizer Authoritative Boundary
# =============================================================================

def test_consultant_engine_is_sole_authority_for_calculations():
    """
    User instruction: Keep ConsultantEngine as the sole authoritative source for
    financial calculations, rules, and recommendations. OutputNormalizer validates,
    sanitizes, and rejects/corrects unsupported LLM outputs rather than becoming
    a second financial rules engine.
    """
    profile = {
        "monthly_income": 3000.0,
        "monthly_expense": 2000.0,
        "debt_status": "no debt",
        "employment_status": "employed",
        "spending_habit": "average spend",
        "goal_cost": 5000.0,
    }

    # Evaluate authoritatively with ConsultantEngine
    res = ConsultantEngine.evaluate(profile, lang="en")

    assert res is not None
    assert "metrics" in res
    assert "facts" in res
    assert res["metrics"]["monthly_income"] == 3000.0
    assert res["metrics"]["net_cashflow"] == 1000.0
    assert res["facts"]["debt_free"] is True

    selected_advice = res["selected_advice"]
    assert selected_advice.priority > 0
    assert selected_advice.category is not None

    # OutputNormalizer does not invent rules; it normalizes/sanitizes LLM outputs
    raw_llm_claim = f"Based on system output: {selected_advice.advice}"
    sanitized = normalize_and_verify_response(raw_llm_claim, context_profile=profile)
    assert selected_advice.advice in sanitized
