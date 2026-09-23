"""
Build V4 Conversational SFT Dataset for Financial Advisor AI.

Preserves:
- 600 existing validated V3 records (340 V2 + 260 V3 conversational)

Generates:
- 1,900 new high-quality conversational records across 8 focus areas:
  1. Khmer-English Mixed (Code-Switching) Conversations (320 records)
  2. Multi-turn Financial Conversations & Context Tracking (380 records)
  3. Profile Updates, Dynamic Changes & Follow-up Scenarios (280 records)
  4. Profile-Aware Factual Answering & Deep Verification (320 records)
  5. Budgeting, Savings, Goals & Natural Financial Planning (300 records)
  6. Missing Information Without Guessing (Strict Null Semantics) (140 records)
  7. Greetings, Casual Conversations & Boundaries (100 records)
  8. Safety Boundaries & Guardrails (60 records)

Total Records: 600 + 1,900 = 2,500 records.
Output Files:
- training/sft_financial_advisor_v4_conversational.jsonl (1,900 records)
- training/sft_financial_advisor_v4_combined.jsonl (2,500 records)
"""

import json
import math
import os
import sys

# Ensure UTF-8 output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

V3_COMBINED_PATH = r"d:\Year3\Finance\Financial_Advisor\training\sft_financial_advisor_v3_combined.jsonl"
V4_CONVERSATIONAL_PATH = r"d:\Year3\Finance\Financial_Advisor\training\sft_financial_advisor_v4_conversational.jsonl"
V4_COMBINED_PATH = r"d:\Year3\Finance\Financial_Advisor\training\sft_financial_advisor_v4_combined.jsonl"

# Instructions Definitions
INSTR_GREET = "You are a helpful Financial AI Assistant. Respond warmly, politely, and conversationally. Do not generate unsolicited financial analyses, budget breakdowns, or deficit warnings for simple pleasantries."
INSTR_FACT = "You are a helpful Financial AI Assistant. The user has an authoritative financial profile loaded. Answer the user's factual questions accurately using only their verified profile facts. Do not hallucinate numbers or invent figures."
INSTR_PLAN = "You are a helpful Financial AI Assistant. Provide structured, personalized financial guidance based on verified profile figures. Calculate timelines accurately and explain recommendations clearly."
INSTR_NODEBT = "You are a helpful Financial AI Assistant. The user is debt-free. Provide financial advice strictly respecting that they have zero debt. Never advise debt consolidation, debt payoff, or servicing loans when the user has no debt."
INSTR_MISSING = "You are a helpful Financial AI Assistant. Identify known financial parameters, specify what critical information is missing or ambiguous, and explain what additional details are required for a complete financial plan without guessing values."
INSTR_CONV = "You are a helpful Financial AI Assistant. Provide practical, empathetic, and actionable guidance on budgeting, expense reduction, and savings habits. Ground your advice in sound financial principles without calculating complex synthetic rules."
INSTR_MULTITURN = "You are a helpful Financial AI Assistant engaged in an ongoing multi-turn financial conversation. Maintain context across conversation turns, track user-provided financial figures accurately, and provide relevant, grounded guidance."
INSTR_UPDATE = "You are a helpful Financial AI Assistant. The user is updating their financial profile or asking what-if scenario questions. Calculate the exact new financial surplus and timeline, compare with previous figures clearly, and explain the financial impact."
INSTR_SAFETY = "You are a helpful Financial AI Assistant. Respond to the user inquiry while maintaining strict professional boundaries. Refuse to provide speculative trading tips, cryptocurrency picks, loan underwriting approvals, or guaranteed return promises. Redirect towards sound personal budgeting and risk management."


# =============================================================================
# 1. Khmer-English Mixed (Code-Switching) Conversations (320 records)
# =============================================================================
def generate_group1_mixed():
    records = []
    
    # 64 unique profiles for 64 * 5 = 320 distinct records
    base_profiles = []
    for inc in range(500, 6900, 100):
        exp = int(inc * 0.65)
        sur = inc - exp
        goal = sur * 6
        base_profiles.append((inc, exp, sur, goal))
    
    profiles_64 = base_profiles[:64]
    
    for inc, exp, sur, goal in profiles_64:
        months = math.ceil(goal / sur)
        pct = (sur / inc) * 100

        # Template 1: Cash flow check
        q1 = f"Salary ខ្ញុំប្រហែល ${inc:,}/month ហើយ living expenses ផ្ទាល់ខ្លួនប្រហែល ${exp:,} ក្នុងមួយខែ។ តើខ្ញុំសល់ cash ប៉ុន្មានសម្រាប់ save?"
        a1 = f"ផ្អែកលើ salary ${inc:,} និង expenses ${exp:,} របស់អ្នក អ្នកមាន net cash surplus ចំនួន ${sur:,}/ខែ (${inc:,} - ${exp:,}) ដែលអាចយកទៅ save បានយ៉ាងល្អ។"
        records.append({"instruction": INSTR_CONV, "input": q1, "output": a1})

        # Template 2: Budget health check
        q2 = f"សួស្តី advisor ជួយ check budget ខ្ញុំបន្តិច: monthly income ${inc:,}, regular expenses ${exp:,}។ តើ cash flow ខ្ញុំ healthy អត់?"
        a2 = f"Cash flow របស់អ្នកមានសុខភាពល្អណាស់! ចំណូល ${inc:,} ធំជាងការចំណាយ ${exp:,} ផ្តល់ surplus ${sur:,}/ខែ ({pct:.1f}% នៃចំណូល)។ នេះជាគ្រឹះដ៏រឹងមាំសម្រាប់កសាងស្ថិរភាពហិរញ្ញវត្ថុ។"
        records.append({"instruction": INSTR_CONV, "input": q2, "output": a2})

        # Template 3: Emergency fund planning with zero debt
        q3 = f"ខ្ញុំអត់មាន debt អីទេ (zero debt) ចង់ create emergency fund ${goal:,} ពី salary ${inc:,} និង expenses ${exp:,}។ តើត្រូវចំណាយពេលប៉ុន្មាន months?"
        a3 = f"ដោយសារអ្នកគ្មានបំណុល (zero debt) និងមាន surplus ${sur:,}/ខែ (${inc:,} - ${exp:,}) ការសន្សំឱ្យបាន emergency fund ${goal:,} នឹងចំណាយពេលប្រហែល {months} ខែ (${goal:,} / ${sur:,} = {months} ខែ)។"
        records.append({"instruction": INSTR_NODEBT, "input": q3, "output": a3})

        # Template 4: 50/30/20 allocation
        needs = int(inc * 0.50)
        wants = int(inc * 0.30)
        savings = int(inc * 0.20)
        q4 = f"ខ្ញុំចង់ allocate budget តាម 50/30/20 rule លើ salary ${inc:,} របស់ខ្ញុំ។ តើត្រូវចែកយ៉ាងម៉េចខ្លះ?"
        a4 = f"ការបែងចែកថវិកា 50/30/20 លើ salary ${inc:,} របស់អ្នក:\n- 50% សម្រាប់ Needs (${needs:,}): ថ្លៃស្នាក់នៅ ម្ហូបអាហារ វិក្កយបត្រចាំបាច់\n- 30% សម្រាប់ Wants (${wants:,}): ការដើរលេង ញ៉ាំក្រៅ កម្សាន្ត\n- 20% សម្រាប់ Savings (${savings:,}): សន្សំទុកសម្រាប់មូលនិធិសង្គ្រោះបន្ទាន់ ឬគោលដៅអនាគត។"
        records.append({"instruction": INSTR_CONV, "input": q4, "output": a4})

        # Template 5: Goal timeline
        q5 = f"តើខ្ញុំអាច reach savings goal ${goal:,} បានដោយរបៀបណា បើមាន net surplus ${sur:,}/month ពី salary ${inc:,}?"
        a5 = f"ដើម្បីសម្រេច target ${goal:,} ជាមួយ surplus ${sur:,}/ខែ អ្នកគ្រាន់តែផ្ទេរប្រាក់សន្សំ ${sur:,} ចូលគណនីដាច់ដោយឡែកជារៀងរាល់ខែ។ អ្នកនឹងសម្រេចគោលដៅក្នុងរយៈពេលប្រហែល {months} ខែ (${goal:,} / ${sur:,} = {months} ខែ)។"
        records.append({"instruction": INSTR_PLAN, "input": q5, "output": a5})

    return records[:320]


# =============================================================================
# 2. Multi-Turn Financial Conversations & Context Tracking (380 records)
# =============================================================================
def generate_group2_multiturn():
    records = []

    # 2A: English Multi-turn (75 profiles * 2 arcs = 150 records)
    en_profiles = []
    for inc in range(1200, 8700, 100):
        exp = int(inc * 0.68)
        sur = inc - exp
        goal = sur * 6
        en_profiles.append((inc, exp, sur, goal))
    en_profiles = en_profiles[:75]

    for inc, exp, sur, goal in en_profiles:
        months = math.ceil(goal / sur)
        exp_ratio = (exp / inc) * 100

        # Arc 1: Emergency reserve timeline
        h1 = f"User: My monthly income is ${inc:,} and expenses are ${exp:,}.\nAssistant: You have an active monthly surplus of ${sur:,} (${inc:,} - ${exp:,}). Do you have any debt obligations, or are you saving toward a specific target?"
        u1 = f"I am completely debt-free, and I want to save ${goal:,} for an emergency fund."
        a1 = f"With zero debt obligations and a steady monthly surplus of ${sur:,}, you will achieve your ${goal:,} emergency fund in {months} months (${goal:,} / ${sur:,} = {months}). Being debt-free allows you to build this safety buffer without any interest drag."
        records.append({"instruction": INSTR_MULTITURN, "input": f"{h1}\nUser: {u1}", "output": a1})

        # Arc 2: Capacity and expense ratio
        h2 = f"User: I want to save ${goal:,}. My salary is ${inc:,}, expenses are ${exp:,}, and I have zero debt.\nAssistant: With your ${sur:,} monthly surplus (${inc:,} - ${exp:,}), you are on track to save ${goal:,} in {months} months."
        u2 = f"Can you confirm my monthly savings capacity and expense ratio for this ${goal:,} plan?"
        a2 = f"Your verified monthly savings capacity is ${sur:,}. Your expense-to-income ratio is {exp_ratio:.1f}% (${exp:,} / ${inc:,} * 100), leaving you with a healthy {100 - exp_ratio:.1f}% savings margin toward your ${goal:,} target."
        records.append({"instruction": INSTR_MULTITURN, "input": f"{h2}\nUser: {u2}", "output": a2})

    # 2B: Khmer Multi-turn (75 profiles * 2 arcs = 150 records)
    km_profiles = []
    for inc in range(1150, 8650, 100):
        exp = int(inc * 0.66)
        sur = inc - exp
        goal = sur * 5
        km_profiles.append((inc, exp, sur, goal))
    km_profiles = km_profiles[:75]

    for inc, exp, sur, goal in km_profiles:
        months = math.ceil(goal / sur)
        sav_pct = (sur / inc) * 100

        # Arc 1: Emergency reserve timeline in Khmer
        h1 = f"User: ចំណូលប្រចាំខែរបស់ខ្ញុំគឺ ${inc:,} ហើយការចំណាយគឺ ${exp:,}។\nAssistant: អ្នកមានប្រាក់សល់សុទ្ធ ${sur:,}/ខែ (${inc:,} - ${exp:,})។ តើអ្នកមានបំណុល ឬមានគោលដៅសន្សំជាក់លាក់ដែរឬទេ?"
        u1 = f"ខ្ញុំគ្មានបំណុលទេ ហើយខ្ញុំចង់សន្សំប្រាក់បម្រុងបន្ទាន់ចំនួន ${goal:,}។"
        a1 = f"ដោយសារអ្នកគ្មានបំណុល និងមានប្រាក់សល់ ${sur:,} ក្នុងមួយខែ អ្នកនឹងសម្រេចបានប្រាក់បម្រុងបន្ទាន់ ${goal:,} ក្នុងរយៈពេល {months} ខែ (${goal:,} / ${sur:,} = {months} ខែ)។ ការគ្មានបំណុលផ្ដល់ស្ថិរភាពខ្ពស់ក្នុងការសន្សំ។"
        records.append({"instruction": INSTR_MULTITURN, "input": f"{h1}\nUser: {u1}", "output": a1})

        # Arc 2: Savings ratio in Khmer
        h2 = f"User: ខ្ញុំចង់សន្សំប្រាក់ ${goal:,}។ ចំណូលខ្ញុំ ${inc:,} ចំណាយ ${exp:,} និងគ្មានបំណុល។\nAssistant: ជាមួយនឹងប្រាក់សល់ ${sur:,}/ខែ (${inc:,} - ${exp:,}) អ្នកនឹងសម្រេចគោលដៅ ${goal:,} ក្នុងរយៈពេល {months} ខែ។"
        u2 = f"តើខ្ញុំសន្សំបានប៉ុន្មានភាគរយនៃចំណូលសរុប ${inc:,} របស់ខ្ញុំ?"
        a2 = f"ផ្អែកលើប្រាក់សល់ ${sur:,} ពីចំណូល ${inc:,} អ្នកកំពុងសន្សំបាន {sav_pct:.1f}% នៃចំណូលប្រចាំខែរបស់អ្នក ដែលជាអត្រាសន្សំដ៏រឹងមាំ និងមានតុល្យភាពល្អ។"
        records.append({"instruction": INSTR_MULTITURN, "input": f"{h2}\nUser: {u2}", "output": a2})

    # 2C: Khmer-English Mixed Multi-turn (40 profiles * 2 arcs = 80 records)
    mix_profiles = []
    for inc in range(1250, 5250, 100):
        exp = int(inc * 0.64)
        sur = inc - exp
        goal = sur * 6
        mix_profiles.append((inc, exp, sur, goal))
    mix_profiles = mix_profiles[:40]

    for inc, exp, sur, goal in mix_profiles:
        months = math.ceil(goal / sur)

        # Arc 1: Mixed timeline
        h1 = f"User: Monthly salary ខ្ញុំ ${inc:,} ហើយ expenses ${exp:,}។\nAssistant: Cash flow របស់អ្នកល្អណាស់ អ្នកមាន surplus ${sur:,}/month (${inc:,} - ${exp:,})។ តើអ្នកមាន debt ឬចង់ save សម្រាប់ goal អ្វី?"
        u1 = f"ខ្ញុំ debt-free ហើយចង់ build emergency fund ${goal:,}។ How long will it take?"
        a1 = f"អបអរសាទរដែលអ្នក debt-free! ជាមួយនឹង monthly surplus ${sur:,} ការសន្សំឱ្យបាន emergency fund ${goal:,} នឹងចំណាយពេលត្រឹមតែ {months} ខែប៉ុណ្ណោះ (${goal:,} / ${sur:,} = {months} months)។"
        records.append({"instruction": INSTR_MULTITURN, "input": f"{h1}\nUser: {u1}", "output": a1})

        # Arc 2: Mixed allocation strategy
        h2 = f"User: ខ្ញុំចង់ reach savings goal ${goal:,} ពី income ${inc:,} និង expense ${exp:,} (zero debt)។\nAssistant: ជាមួយ surplus ${sur:,}/ខែ អ្នកនឹង reach goal ក្នុងរយៈពេល {months} ខែ។"
        u2 = f"តើខ្ញុំគួរ allocate surplus $${sur:,} នេះទៅក្នុង fixed deposit ឬ keep liquid cash?"
        a2 = f"ប្រសិនបើអ្នកទើបតែចាប់ផ្តើមសន្សំសម្រាប់ emergency fund សូមរក្សាទុកជា liquid cash ក្នុងគណនីសន្សំដែលអាចដកបានភ្លាមៗ។ បន្ទាប់ពីមានប្រាក់បម្រុងគ្រប់គ្រាន់ហើយ ទើបបែងចែកមួយចំណែកដាក់ Fixed Deposit ដើម្បីទទួលបានការប្រាក់ខ្ពស់។"
        records.append({"instruction": INSTR_MULTITURN, "input": f"{h2}\nUser: {u2}", "output": a2})

    return records[:380]


# =============================================================================
# 3. Profile Updates, Dynamic Changes & Follow-up Scenarios (280 records)
# =============================================================================
def generate_group3_updates():
    records = []

    # 3A: English Updates (28 unique profiles * 5 templates = 140 records)
    en_update_profiles = []
    for inc in range(1200, 6800, 200):
        exp = int(inc * 0.70)
        n_inc = inc + 500
        n_exp = exp
        goal = (n_inc - n_exp) * 6
        en_update_profiles.append((inc, exp, n_inc, n_exp, goal))
    en_update_profiles = en_update_profiles[:28]

    for o_inc, o_exp, n_inc, n_exp, goal in en_update_profiles:
        o_sur = o_inc - o_exp
        n_sur = n_inc - n_exp
        o_mo = math.ceil(goal / o_sur)
        n_mo = math.ceil(goal / n_sur)
        diff_mo = o_mo - n_mo

        # Template 1: Salary raise
        q1 = f"Previous profile: income=${o_inc:,}, expenses=${o_exp:,}, surplus=+${o_sur:,}, debt=no debt, goal=${goal:,}. User updates: I received a raise! My monthly income is now ${n_inc:,}, and expenses remain ${n_exp:,}. How does this impact my savings timeline?"
        a1 = f"Congratulations on the raise! Here is the updated breakdown:\n- Previous Monthly Surplus: ${o_sur:,} (timeline: ~{o_mo} months for ${goal:,})\n- New Monthly Surplus: ${n_sur:,} (${n_inc:,} - ${n_exp:,})\n- New Savings Timeline: ~{n_mo} months (${goal:,} / ${n_sur:,})\nYour raise accelerates your ${goal:,} goal by {diff_mo} month(s), while maintaining your strong debt-free foundation."
        records.append({"instruction": INSTR_UPDATE, "input": q1, "output": a1})

        # Template 2: Expense reduction
        reduced_exp = o_exp - 250
        red_sur = o_inc - reduced_exp
        q2 = f"Previous profile: income=${o_inc:,}, expenses=${o_exp:,}, surplus=+${o_sur:,}, debt=no debt. User updates: I cut my monthly living expenses down to ${reduced_exp:,} while earning ${o_inc:,}. What is my new monthly savings capacity?"
        a2 = f"Well done on reducing your expenses! With your living costs dropping from ${o_exp:,} to ${reduced_exp:,} on an income of ${o_inc:,}, your monthly savings capacity increases from ${o_sur:,} to ${red_sur:,} (+${red_sur - o_sur:,}/month). You remain completely debt-free with higher cash flow flexibility."
        records.append({"instruction": INSTR_UPDATE, "input": q2, "output": a2})

        # Template 3: Savings increase what-if
        q3 = f"Previous profile: income=${o_inc:,}, expenses=${o_exp:,}, surplus=+${o_sur:,}, debt=no debt, goal=${goal:,}. User asks: What if my monthly savings increase to ${n_sur:,} per month?"
        a3 = f"If you allocate ${n_sur:,} toward your ${goal:,} goal each month instead of ${o_sur:,}, your timeline shortens from {o_mo} months down to {n_mo} months. You reach your goal {diff_mo} month(s) faster."
        records.append({"instruction": INSTR_UPDATE, "input": q3, "output": a3})

        # Template 4: Cash flow recalculation
        q4 = f"Update: My income changed from ${o_inc:,} to ${n_inc:,} and expenses from ${o_exp:,} to ${n_exp:,}. Recalculate my net cash flow and confirm my debt status."
        a4 = f"Under your updated figures:\n- Monthly Income: ${n_inc:,}\n- Monthly Expenses: ${n_exp:,}\n- Net Monthly Surplus: +${n_sur:,} (${n_inc:,} - ${n_exp:,})\n- Debt Status: You remain confirmed debt-free with zero debt obligations."
        records.append({"instruction": INSTR_UPDATE, "input": q4, "output": a4})

        # Template 5: Debt payoff transition
        q5 = f"I just finished paying off all my debts! My income is ${n_inc:,} and expenses are ${n_exp:,}. How should I update my financial plan?"
        a5 = f"Congratulations on becoming 100% debt-free! That is a major financial milestone. With an income of ${n_inc:,} and expenses of ${n_exp:,}, your entire monthly surplus of ${n_sur:,} is now unencumbered. Prioritize building an emergency fund of 3-6 months living expenses (${n_exp * 3:,} - ${n_exp * 6:,}) before pursuing discretionary goals."
        records.append({"instruction": INSTR_UPDATE, "input": q5, "output": a5})

    # 3B: Khmer Updates (28 unique profiles * 5 templates = 140 records)
    km_update_profiles = []
    for inc in range(1100, 6700, 200):
        exp = int(inc * 0.68)
        n_inc = inc + 400
        n_exp = exp
        goal = (n_inc - n_exp) * 5
        km_update_profiles.append((inc, exp, n_inc, n_exp, goal))
    km_update_profiles = km_update_profiles[:28]

    for o_inc, o_exp, n_inc, n_exp, goal in km_update_profiles:
        o_sur = o_inc - o_exp
        n_sur = n_inc - n_exp
        o_mo = math.ceil(goal / o_sur)
        n_mo = math.ceil(goal / n_sur)
        diff_mo = o_mo - n_mo

        # Template 1: Salary raise in Khmer
        q1 = f"កម្រងព័ត៌មានពីមុន: ចំណូល=${o_inc:,}, ចំណាយ=${o_exp:,}, ប្រាក់សល់=+${o_sur:,}, គ្មានបំណុល, គោលដៅ=${goal:,}។ អ្នកប្រើប្រាស់ធ្វើបច្ចុប្បន្នភាព: ខ្ញុំបានឡើងប្រាក់ខែ! ឥឡូវចំណូលខ្ញុំគឺ ${n_inc:,} ហើយចំណាយនៅដដែល ${n_exp:,}។ តើវាជះឥទ្ធិពលដល់ផែនការសន្សំយ៉ាងដូចម្តេច?"
        a1 = f"សូមអបអរសាទរចំពោះការឡើងប្រាក់ខែ! នេះជាការវិភាគបច្ចុប្បន្នភាព:\n- ប្រាក់សល់ប្រចាំខែពីមុន: ${o_sur:,} (រយៈពេល: ~{o_mo} ខែសម្រាប់ ${goal:,})\n- ប្រាក់សល់ប្រចាំខែថ្មី: ${n_sur:,} (${n_inc:,} - ${n_exp:,})\n- រយៈពេលសន្សំថ្មី: ~{n_mo} ខែ (${goal:,} / ${n_sur:,})\nការកើនឡើងចំណូលនេះជួយឱ្យអ្នកសម្រេចគោលដៅ ${goal:,} លឿនជាងមុនចំនួន {diff_mo} ខែ ដោយរក្សាបាននូវស្ថានភាពគ្មានបំណុលដដែល។"
        records.append({"instruction": INSTR_UPDATE, "input": q1, "output": a1})

        # Template 2: Expense reduction in Khmer
        reduced_exp = o_exp - 200
        red_sur = o_inc - reduced_exp
        q2 = f"ព័ត៌មានពីមុន: ចំណូល=${o_inc:,}, ចំណាយ=${o_exp:,}។ ធ្វើបច្ចុប្បន្នភាព: ខ្ញុំបានកាត់បន្ថយការចំណាយមកត្រឹម ${reduced_exp:,} លើចំណូល ${o_inc:,}។ តើខ្ញុំសល់លុយប៉ុន្មានក្នុងមួយខែ?"
        a2 = f"ពិតជាល្អណាស់! ការកាត់បន្ថយការចំណាយពី ${o_exp:,} មក ${reduced_exp:,} ធ្វើឱ្យសមត្ថភាពសន្សំប្រចាំខែរបស់អ្នកកើនឡើងពី ${o_sur:,} ទៅ ${red_sur:,} (+${red_sur - o_sur:,}/ខែ)។ អ្នកនៅតែរក្សាបានស្ថានភាពគ្មានបំណុល និងមានលំហូរសាច់ប្រាក់កាន់តែប្រសើរ។"
        records.append({"instruction": INSTR_UPDATE, "input": q2, "output": a2})

        # Template 3: Savings increase what-if in Khmer
        q3 = f"កម្រងព័ត៌មាន: ចំណូល=${o_inc:,}, ចំណាយ=${o_exp:,}, គោលដៅ=${goal:,}។ តើមានអ្វីកើតឡើងចំពោះគោលដៅ ${goal:,} បើខ្ញុំបង្កើនការសន្សំពី ${o_sur:,} ទៅ ${n_sur:,} ក្នុងមួយខែ?"
        a3 = f"ប្រសិនបើអ្នកបង្កើនការសន្សំដល់ ${n_sur:,}/ខែ រយៈពេលសម្រេចគោលដៅ ${goal:,} នឹងកាត់បន្ថយពី {o_mo} ខែ មកត្រឹម {n_mo} ខែប៉ុណ្ណោះ។ អ្នកនឹងសម្រេចគោលដៅបានលឿនជាងមុន {diff_mo} ខែ។"
        records.append({"instruction": INSTR_UPDATE, "input": q3, "output": a3})

        # Template 4: Cash flow recalculation in Khmer
        q4 = f"ការធ្វើបច្ចុប្បន្នភាព: ចំណូលរបស់ខ្ញុំបានផ្លាស់ប្តូរពី ${o_inc:,} ទៅ ${n_inc:,} ហើយការចំណាយពី ${o_exp:,} ទៅ ${n_exp:,}។ សូមគណនាលំហូរសាច់ប្រាក់សុទ្ធឡើងវិញ និងបញ្ជាក់ពីស្ថានភាពបំណុល។"
        a4 = f"ផ្អែកលើទិន្នន័យថ្មីរបស់អ្នក:\n- ចំណូលប្រចាំខែ: ${n_inc:,}\n- ការចំណាយប្រចាំខែ: ${n_exp:,}\n- លំហូរសាច់ប្រាក់សល់សុទ្ធ: +${n_sur:,}/ខែ (${n_inc:,} - ${n_exp:,})\n- ស្ថានភាពបំណុល: បញ្ជាក់ច្បាស់ថាគ្មានកាតព្វកិច្ចបំណុលឡើយ (Zero Debt)។"
        records.append({"instruction": INSTR_UPDATE, "input": q4, "output": a4})

        # Template 5: Debt payoff transition in Khmer
        q5 = f"ខ្ញុំទើបតែសងបំណុលរួចរាល់ទាំងអស់! ឥឡូវគ្មានបំណុលទេ ចំណូល ${n_inc:,} ចំណាយ ${n_exp:,}។ តើគួររៀបចំផែនការយ៉ាងណា?"
        a5 = f"អបអរសាទរដែលអ្នកបានក្លាយជាបុគ្គលគ្មានបំណុល (Debt-free)! នេះជាជោគជ័យដ៏អស្ចារ្យ។ ជាមួយនឹងចំណូល ${n_inc:,} និងចំណាយ ${n_exp:,} អ្នកមានប្រាក់សល់សុទ្ធ ${n_sur:,}/ខែ។ ជំហានដំបូងគួរតែបង្កើតមូលនិធិសង្គ្រោះបន្ទាន់ 3-6 ខែនៃការចំណាយ (${n_exp * 3:,} - ${n_exp * 6:,}) មុននឹងបែងចែកទៅកាន់គោលដៅផ្សេងទៀត។"
        records.append({"instruction": INSTR_UPDATE, "input": q5, "output": a5})

    return records[:280]


# =============================================================================
# 4. Profile-Aware Factual Answering & Deep Verification (320 records)
# =============================================================================
def generate_group4_facts():
    records = []

    # 20 distinct profiles
    profiles_20 = [
        (550, 380, 170, "no debt", 1100),
        (750, 520, 230, "no debt", 1400),
        (950, 660, 290, "no debt", 1800),
        (1150, 800, 350, "no debt", 2200),
        (1350, 920, 430, "no debt", 2600),
        (1550, 1050, 500, "no debt", 3000),
        (1750, 1180, 570, "no debt", 3500),
        (1950, 1320, 630, "no debt", 3800),
        (2150, 1450, 700, "no debt", 4200),
        (2350, 1600, 750, "no debt", 4500),
        (2550, 1720, 830, "no debt", 5000),
        (2750, 1860, 890, "no debt", 5500),
        (2950, 2000, 950, "no debt", 6000),
        (3150, 2120, 1030, "no debt", 6500),
        (3450, 2300, 1150, "no debt", 7000),
        (3750, 2500, 1250, "no debt", 7500),
        (4150, 2750, 1400, "no debt", 8500),
        (4650, 3050, 1600, "no debt", 10000),
        (5250, 3450, 1800, "no debt", 11000),
        (5850, 3850, 2000, "no debt", 12000)
    ]

    # 4A: English Facts (20 profiles * 6 templates = 120 records)
    en_q_templates = [
        ("What is my verified monthly take-home income?",
         "Your verified monthly take-home income is ${inc:,}."),
        ("What are my recorded monthly living expenses?",
         "Your recorded monthly living expenses are ${exp:,}."),
        ("How much can I save each month based on my profile?",
         "Based on your verified monthly income of ${inc:,} and expenses of ${exp:,}, your monthly savings capacity is ${sur:,} (${inc:,} - ${exp:,})."),
        ("What is my recorded savings target?",
         "Your verified financial savings target is ${goal:,}."),
        ("Do I have any recorded debt obligations?",
         "According to your verified profile, you have no recorded debt obligations (debt-free status)."),
        ("What is my expense-to-income ratio?",
         "Your expense-to-income ratio is {exp_ratio:.1f}%, calculated as your ${exp:,} expenses divided by your ${inc:,} income.")
    ]

    for inc, exp, sur, debt, goal in profiles_20:
        exp_ratio = (exp / inc) * 100
        header = f"Verified user profile: income=${inc:,}/mo, expenses=${exp:,}/mo, surplus=+${sur:,}/mo, debt={debt}, savings goal=${goal:,}."
        for q_t, a_t in en_q_templates:
            q = f"{header} User asks: {q_t}"
            a = a_t.replace("${inc:,}", f"${inc:,}").replace("${exp:,}", f"${exp:,}").replace("${sur:,}", f"${sur:,}").replace("${goal:,}", f"${goal:,}").replace("{exp_ratio:.1f}", f"{exp_ratio:.1f}")
            records.append({"instruction": INSTR_FACT, "input": q, "output": a})

    # 4B: Khmer Facts (20 profiles * 6 templates = 120 records)
    km_q_templates = [
        ("តើចំណូលប្រចាំខែរបស់ខ្ញុំដែលបានកត់ត្រាមានចំនួនប៉ុន្មាន?",
         "ចំណូលប្រចាំខែដែលបានកត់ត្រារបស់អ្នកគឺ ${inc:,}។"),
        ("តើការចំណាយប្រចាំខែរបស់ខ្ញុំមានចំនួនប៉ុន្មាន?",
         "ការចំណាយប្រចាំខែដែលបានកត់ត្រារបស់អ្នកគឺ ${exp:,} ក្នុងមួយខែ។"),
        ("តើខ្ញុំអាចសន្សំប្រាក់បានចំនួនប៉ុន្មានក្នុងមួយខែ?",
         "ផ្អែកលើចំណូល ${inc:,} និងការចំណាយ ${exp:,} អ្នកមានសមត្ថភាពសន្សំប្រាក់បានចំនួន ${sur:,} ក្នុងមួយខែ (${inc:,} - ${exp:,})។"),
        ("តើគោលដៅហិរញ្ញវត្ថុរបស់ខ្ញុំមានចំនួនប៉ុន្មាន?",
         "គោលដៅសន្សំដែលបានកត់ត្រារបស់អ្នកគឺ ${goal:,}។"),
        ("តើខ្ញុំមានបំណុលដែលបានកត់ត្រាដែរឬទេ?",
         "យោងតាមកម្រងព័ត៌មានរបស់អ្នក អ្នកមិនមានបំណុលណាមួយត្រូវបានកត់ត្រាទុកនោះទេ (ស្ថានភាពគ្មានបំណុល)។"),
        ("តើសមាមាត្រចំណាយធៀបនឹងចំណូលរបស់ខ្ញុំប៉ុន្មាន?",
         "សមាមាត្រចំណាយធៀបនឹងចំណូលរបស់អ្នកគឺ {exp_ratio:.1f}% (${exp:,} ចែកនឹង ${inc:,})។")
    ]

    for inc, exp, sur, debt, goal in profiles_20:
        exp_ratio = (exp / inc) * 100
        header = f"Verified user profile: income=${inc:,}/mo, expenses=${exp:,}/mo, surplus=+${sur:,}/mo, debt={debt}, savings goal=${goal:,}."
        for q_t, a_t in km_q_templates:
            q = f"{header} User asks: {q_t}"
            a = a_t.replace("${inc:,}", f"${inc:,}").replace("${exp:,}", f"${exp:,}").replace("${sur:,}", f"${sur:,}").replace("${goal:,}", f"${goal:,}").replace("{exp_ratio:.1f}", f"{exp_ratio:.1f}")
            records.append({"instruction": INSTR_FACT, "input": q, "output": a})

    # 4C: Khmer-English Mixed Facts (20 profiles * 4 templates = 80 records)
    mix_q_templates = [
        ("Salary ខ្ញុំ recorded ប៉ុន្មានដែរ?",
         "Monthly take-home income របស់អ្នកដែលបានកត់ត្រាគឺ ${inc:,}។"),
        ("Monthly living expenses ខ្ញុំប៉ុន្មាន?",
         "Monthly living expenses របស់អ្នកគឺ ${exp:,} ក្នុងមួយខែ។"),
        ("Surplus ប្រចាំខែខ្ញុំសល់ប៉ុន្មានសម្រាប់ save?",
         "អ្នកមាន monthly surplus ចំនួន ${sur:,} (${inc:,} - ${exp:,}) សម្រាប់សន្សំ។"),
        ("Target savings goal ខ្ញុំប៉ុន្មាន?",
         "Target savings goal របស់អ្នកដែលបានកំណត់ទុកគឺ ${goal:,}។")
    ]

    for inc, exp, sur, debt, goal in profiles_20:
        header = f"Verified user profile: income=${inc:,}/mo, expenses=${exp:,}/mo, surplus=+${sur:,}/mo, debt={debt}, savings goal=${goal:,}."
        for q_t, a_t in mix_q_templates:
            q = f"{header} User asks: {q_t}"
            a = a_t.replace("${inc:,}", f"${inc:,}").replace("${exp:,}", f"${exp:,}").replace("${sur:,}", f"${sur:,}").replace("${goal:,}", f"${goal:,}")
            records.append({"instruction": INSTR_FACT, "input": q, "output": a})

    return records[:320]


# =============================================================================
# 5. Budgeting, Savings, Goals & Natural Financial Planning (300 records)
# =============================================================================
def generate_group5_budgeting():
    records = []

    # 5A: English Budgeting Guides (15 income levels * 8 questions = 120 records)
    incomes_5a = [800, 1100, 1400, 1700, 2000, 2300, 2600, 2900, 3200, 3600, 4000, 4500, 5000, 5500, 6000]
    for inc in incomes_5a:
        needs = int(inc * 0.50)
        wants = int(inc * 0.30)
        sav = int(inc * 0.20)
        exp = int(inc * 0.70)
        em_3m = exp * 3
        em_6m = exp * 6

        en_qa_list = [
            (f"How can I apply the 50/30/20 budgeting rule to my monthly income of ${inc:,}?",
             f"Under the 50/30/20 rule for a ${inc:,} monthly income:\n- 50% for Needs (${needs:,}): housing, groceries, utilities, basic transportation.\n- 30% for Wants (${wants:,}): dining out, entertainment, hobbies.\n- 20% for Savings (${sav:,}): emergency reserves or goal milestones.\nThis provides a balanced structure for sustainable spending."),

            (f"How large should my emergency fund be if my monthly living costs are ${exp:,} from a ${inc:,} salary?",
             f"For monthly living expenses of ${exp:,}:\n- 3-Month Minimum Reserve: ${em_3m:,} (${exp:,} * 3) — suitable for stable salaried workers.\n- 6-Month Full Reserve: ${em_6m:,} (${exp:,} * 6) — recommended for freelancers or single-income households.\nKeep these funds in a safe, liquid bank savings account."),

            (f"What practical steps can I take on a ${inc:,} income to trim discretionary spending?",
             f"To lower discretionary costs on a ${inc:,} budget:\n1. Meal plan weekly to prevent food waste and avoid last-minute takeout.\n2. Review bank statements and cancel recurring subscriptions you rarely use.\n3. Implement a 24-hour waiting rule before non-essential purchases.\n4. Save energy by managing air conditioning usage efficiently."),

            (f"How should I prioritize savings goals on a ${inc:,} income when I have zero debt?",
             f"With no debt obligations on a ${inc:,} income:\n1. First Priority: Build a liquid emergency fund of ${em_3m:,} (3 months of expenses).\n2. Second Priority: Fund upcoming planned milestones (like education or transport).\n3. Third Priority: Explore secure fixed-term deposits for long-term compound growth."),

            (f"Why should someone earning ${inc:,} avoid keeping all their savings in physical cash at home?",
             f"Keeping physical cash at home exposes you to risks of theft, fire, and accidental loss, while earning zero interest. Keeping your reserves in a licensed bank account ensures safety, instant liquidity, and protection under national banking regulations."),

            (f"How can I build consistent saving discipline every month with take-home pay of ${inc:,}?",
             f"The single most reliable method is to 'Pay Yourself First'. The moment your ${inc:,} salary is deposited, immediately transfer your planned savings (such as ${sav:,}) into a separate savings account before paying any discretionary expenses."),

            (f"What is a sinking fund and how does it help someone on a ${inc:,} salary?",
             f"A sinking fund is money set aside gradually for known, anticipated future expenses (such as annual vehicle insurance, laptop upgrades, or holiday gifts). On a ${inc:,} salary, saving $50-$100 a month prevents these predictable costs from disrupting your monthly budget."),

            (f"How does tracking daily expenses improve financial control for a ${inc:,} monthly earner?",
             f"Tracking expenses reveals subtle spending leaks—such as daily premium coffees or frequent convenience purchases. When you track every dollar of your ${inc:,} earnings, you gain total clarity on where your cash flow goes and can redirect leaks toward savings.")
        ]
        for q, a in en_qa_list:
            records.append({"instruction": INSTR_CONV, "input": q, "output": a})

    # 5B: Khmer Budgeting Guides (15 income levels * 8 questions = 120 records)
    incomes_5b = [750, 1050, 1350, 1650, 1950, 2250, 2550, 2850, 3150, 3550, 3950, 4450, 4950, 5450, 5950]
    for inc in incomes_5b:
        needs = int(inc * 0.50)
        wants = int(inc * 0.30)
        sav = int(inc * 0.20)
        exp = int(inc * 0.68)
        em_3m = exp * 3
        em_6m = exp * 6

        km_qa_list = [
            (f"តើខ្ញុំអាចអនុវត្តច្បាប់ថវិកា 50/30/20 លើចំណូល ${inc:,} របស់ខ្ញុំដោយរបៀបណា?",
             f"ការអនុវត្តច្បាប់ 50/30/20 លើចំណូល ${inc:,} រួមមាន:\n- 50% សម្រាប់ Needs (${needs:,}): ថ្លៃជួលបន្ទប់ ម្ហូបអាហារ វិក្កយបត្រភ្លើងទឹក និងការធ្វើដំណើរ។\n- 30% សម្រាប់ Wants (${wants:,}): ការដើរលេង ការញ៉ាំអាហារក្រៅ និងចំណង់ចំណូលចិត្ត។\n- 20% សម្រាប់ Savings (${sav:,}): សន្សំទុកសម្រាប់មូលនិធិសង្គ្រោះបន្ទាន់ ឬគោលដៅអនាគត។"),

            (f"តើប្រាក់បម្រុងបន្ទាន់គួរមានចំនួនប៉ុន្មាន បើការចំណាយប្រចាំខែគឺ ${exp:,} លើចំណូល ${inc:,}?",
             f"សម្រាប់ការចំណាយ ${exp:,} ក្នុងមួយខែ:\n- កម្រិតអប្បបរមា 3 ខែ: ${em_3m:,} (${exp:,} * 3) សមស្របសម្រាប់អ្នកដែលមានការងារថេរ។\n- កម្រិតរឹងមាំ 6 ខែ: ${em_6m:,} (${exp:,} * 6) សមស្របសម្រាប់អ្នកប្រកបរបរឯករាជ្យ។\nប្រាក់នេះត្រូវរក្សាទុកក្នុងគណនីសន្សំធនាគារដែលមានសុវត្ថិភាព និងអាចដកបានភ្លាមៗ។"),

            (f"តើទម្លាប់ណាខ្លះជួយកាត់បន្ថយការចំណាយប្រចាំថ្ងៃលើចំណូល ${inc:,}?",
             f"វិធីសាស្ត្រមានប្រសិទ្ធភាពរួមមាន:\n1. រៀបចំបញ្ជីទិញទំនិញមុនចេញទៅផ្សារ ដើម្បីជៀសវាងទិញតាមអារម្មណ៍។\n2. កាត់បន្ថយការញ៉ាំកាហ្វេប្រណិត ឬអាហារក្រៅផ្ទះ ដោយចម្អិនអាហារដោយខ្លួនឯង។\n3. ពិនិត្យមើល និងលុបចោល subscriptions ដែលមិនសូវបានប្រើប្រាស់។\n4. អនុវត្តច្បាប់រង់ចាំ 24 ម៉ោង មុននឹងសម្រេចចិត្តទិញរបស់របរដែលមិនចាំបាច់។"),

            (f"តើអ្វីជាភាពខុសគ្នារវាងប្រាក់សង្គ្រោះបន្ទាន់ និងប្រាក់សន្សំធម្មតា សម្រាប់អ្នករកបាន ${inc:,}?",
             f"ប្រាក់សង្គ្រោះបន្ទាន់ (Emergency Fund) គឺសម្រាប់តែហេតុការណ៍ចៃដន្យដែលមិនបានព្រាងទុកប៉ុណ្ណោះ ដូចជាការព្យាបាលជំងឺ ឬការបាត់បង់ការងារ។ ចំណែកប្រាក់សន្សំធម្មតា គឺសម្រាប់គោលដៅដែលបានគ្រោងទុកជាមុន ដូចជាការទិញម៉ូតូ ការរៀបការ ឬដំណើរកម្សាន្ត។"),

            (f"ហេតុអ្វីមិនគួរទុកប្រាក់សន្សំជាសាច់ប្រាក់សុទ្ធនៅផ្ទះច្រើនពេក បើមានប្រាក់ខែ ${inc:,}?",
             f"ការទុកសាច់ប្រាក់សុទ្ធនៅផ្ទះប្រឈមនឹងហានិភ័យចោរកម្ម អគ្គិភ័យ និងការខូចខាត ហើយមិនទទួលបានការប្រាក់អ្វីឡើយ។ ការដាក់ក្នុងធនាគារស្របច្បាប់ធានាសុវត្ថិភាពខ្ពស់ និងជួយឱ្យលុយរបស់អ្នកបង្កើតការប្រាក់បន្ថែម។"),

            (f"តើខ្ញុំគួរចាប់ផ្តើមទម្លាប់សន្សំប្រាក់ដោយរបៀបណា លើប្រាក់ខែ ${inc:,}?",
             f"ការចាប់ផ្តើមសន្សំដែលល្អបំផុតគឺអនុវត្តគោលការណ៍ 'សន្សំមុន ចាយក្រោយ'។ នៅពេលបើកប្រាក់ខែភ្លាម ផ្ទេរប្រាក់យ៉ាងតិច ${sav:,} ចូលគណនីសន្សំដាច់ដោយឡែកភ្លាមៗ មុនពេលចាប់ផ្តើមចំណាយ។"),

            (f"តើ Sinking Fund មានអត្ថប្រយោជន៍អ្វីខ្លះសម្រាប់អ្នកមានចំណូល ${inc:,}?",
             f"Sinking fund គឺជាការសន្សំសម្រាប់ចំណាយជាក់លាក់ដែលដឹងមុន (ដូចជា ថ្លៃបង់ពន្ធយានយន្ត, ទិញទូរស័ព្ទថ្មី, ឬបុណ្យទាន)។ ការសន្សំ $50-$100 ជារៀងរាល់ខែជួយកុំឱ្យចំណាយទាំងនេះប៉ះពាល់ដល់ថវិកាប្រចាំខែរបស់អ្នក។"),

            (f"តើការកត់ត្រាចំណាយប្រចាំថ្ងៃផ្តល់អត្ថប្រយោជន៍អ្វីខ្លះដល់អ្នកមានចំណូល ${inc:,}?",
             f"ការកត់ត្រាចំណាយជួយឱ្យអ្នកមើលឃើញលំហូរលុយច្បាស់លាស់ និងដឹងថាការចំណាយណាខ្លះមិនចាំបាច់។ នេះជាជំហានដំបូងបំផុតដើម្បីគ្រប់គ្រងលុយ ${inc:,} ឱ្យមានប្រសិទ្ធភាព និងសល់លុយសន្សំកាន់តែច្រើន។")
        ]
        for q, a in km_qa_list:
            records.append({"instruction": INSTR_CONV, "input": q, "output": a})

    # 5C: Khmer-English Mixed Budgeting (15 income levels * 4 questions = 60 records)
    incomes_5c = [900, 1200, 1500, 1800, 2100, 2400, 2700, 3000, 3300, 3700, 4100, 4600, 5100, 5600, 6200]
    for inc in incomes_5c:
        sur = int(inc * 0.32)
        mix_qa = [
            (f"Salary ${inc:,}/month ចង់ save លុយសម្រាប់ emergency fund តើគួររៀបចំយ៉ាងណា?",
             f"ជាមួយនឹង salary ${inc:,} អ្នកអាចសន្សំប្រមាណ ${sur:,}/ខែ ចូលទៅក្នុង emergency fund។ គោលដៅដំបូងគឺសន្សំឱ្យបាន 3 ខែនៃការចំណាយ ហើយដាក់ក្នុងគណនីសន្សំធនាគារដែលមានសុវត្ថិភាព។"),

            (f"តើធ្វើម៉េចទើបអាច balance រវាង saving money និង enjoying life លើចំណូល ${inc:,}?",
             f"ដើម្បីរក្សា balance អ្នកគួរប្រើ 50/30/20 rule: 50% សម្រាប់ needs, 20% សម្រាប់ savings, និង 30% ទុកសម្រាប់ wants (enjoyment)។ នៅពេលអ្នកកំណត់ budget ច្បាស់លាស់ អ្នកអាច enjoy life ដោយមិនមានអារម្មណ៍ស្តាយក្រោយឡើយ។"),

            (f"តើ sinking fund និង emergency fund ខុសគ្នាយ៉ាងម៉េច បើខ្ញុំមានប្រាក់ខែ ${inc:,}?",
             f"Sinking fund គឺជាការសន្សំសម្រាប់ចំណាយជាក់លាក់ដែលដឹងមុនលើចំណូល ${inc:,} (ដូចជា ទិញ laptop ថ្មី ឬបង់ពន្ធ)។ ចំណែក Emergency fund គឺសម្រាប់តែគ្រាអាសន្នដែលនឹកស្មានមិនដល់ប៉ុណ្ណោះ។"),

            (f"ជាមួយ salary ${inc:,} តើខ្ញុំគួរ direct surplus ទៅណាជាអាទិភាពដំបូង?",
             f"អាទិភាពដំបូងបំផុតលើ salary ${inc:,} គឺការកសាង emergency fund យ៉ាងតិច 3 ខែនៃការចំណាយ។ បន្ទាប់ពីមានខែលការពារនេះហើយ ទើបបែងចែកទៅកាន់គោលដៅអនាគតផ្សេងៗ។")
        ]
        for q, a in mix_qa:
            records.append({"instruction": INSTR_CONV, "input": q, "output": a})

    return records[:300]


# =============================================================================
# 6. Missing Information Without Guessing (140 records)
# =============================================================================
def generate_group6_missing():
    records = []

    # 6A: English Missing Info (14 amounts * 5 questions = 70 records)
    amounts_6a = [900, 1200, 1500, 1800, 2100, 2400, 2700, 3000, 3300, 3700, 4100, 4600, 5200, 5800]
    for amt in amounts_6a:
        en_missing_list = [
            (f"I earn ${amt:,} every month and want to buy a new car.",
             f"I acknowledge your monthly income of ${amt:,}. However, to create an accurate savings plan, your monthly living expenses and current debt status are missing. Please provide your regular expenses and whether you carry any debts."),

            (f"My monthly living expenses are ${amt:,}. Can you calculate how much I can save?",
             f"You provided monthly living expenses of ${amt:,}. However, your monthly income was not specified. Please share your take-home income so I can determine your net cash surplus without guessing."),

            (f"I want to save ${amt * 3:,} for an emergency fund. How many months will it take me?",
             f"A ${amt * 3:,} emergency fund is an excellent goal! To calculate your timeline, I need to know your monthly income and monthly expenses. How much do you earn and spend each month?"),

            (f"I have zero debt and want to save ${amt * 4:,} for a down payment.",
             f"Having zero debt is an outstanding financial foundation. However, to calculate your savings timeline for ${amt * 4:,}, I need your monthly take-home income and regular living costs. Please provide those details."),

            (f"I currently spend ${amt:,} on housing, utilities, and groceries each month.",
             f"Your specified living costs total ${amt:,}. However, your monthly income was not provided. Please state your monthly take-home income to calculate your savings capacity.")
        ]
        for q, a in en_missing_list:
            records.append({"instruction": INSTR_MISSING, "input": q, "output": a})

    # 6B: Khmer Missing Info (14 amounts * 5 questions = 70 records)
    amounts_6b = [850, 1150, 1450, 1750, 2050, 2350, 2650, 2950, 3250, 3650, 4050, 4550, 5150, 5750]
    for amt in amounts_6b:
        km_missing_list = [
            (f"ខ្ញុំរកចំណូលបាន ${amt:,} ក្នុងមួយខែ ហើយចង់សន្សំទិញដី។",
             f"ខ្ញុំបានកត់ត្រាចំណូល ${amt:,} របស់អ្នក។ ប៉ុន្តែដើម្បីគណនាផែនការសន្សំជាក់លាក់ ព័ត៌មានអំពីការចំណាយប្រចាំខែ និងស្ថានភាពបំណុលរបស់អ្នកមិនទាន់មាននៅឡើយទេ។ សូមប្រាប់ពីការចំណាយប្រចាំខែរបស់អ្នក។"),

            (f"ការចំណាយប្រចាំខែរបស់ខ្ញុំគឺ ${amt:,}។ តើខ្ញុំអាចសន្សំបានប៉ុន្មាន?",
             f"អ្នកបានបញ្ជាក់ការចំណាយ ${amt:,} ក្នុងមួយខែ។ ប៉ុន្តែដើម្បីគណនាប្រាក់សន្សំ ខ្ញុំត្រូវការដឹងពីប្រាក់ចំណូលប្រចាំខែរបស់អ្នក។ សូមចែករំលែកចំនួនចំណូលប្រចាំខែរបស់អ្នក។"),

            (f"ខ្ញុំចង់សន្សំលុយឱ្យបាន ${amt * 3:,}។ តើត្រូវចំណាយពេលប៉ុន្មាន?",
             f"គោលដៅសន្សំ ${amt * 3:,} គឺជាទិសដៅដ៏ល្អ! ដើម្បីគណនារយៈពេល ខ្ញុំត្រូវការដឹងពីចំណូល និងការចំណាយប្រចាំខែរបស់អ្នក។ តើអ្នករកបាន និងចំណាយប៉ុន្មានក្នុងមួយខែ?"),

            (f"ខ្ញុំគ្មានបំណុលទេ ហើយចង់រៀបចំផែនការសន្សំប្រាក់ ${amt * 4:,}។",
             f"ការគ្មានបំណុលជាគ្រឹះដ៏រឹងមាំ! ប៉ុន្តែដើម្បីរៀបចំផែនការលម្អិតសម្រាប់គោលដៅ ${amt * 4:,} ខ្ញុំត្រូវការដឹងពីប្រាក់ចំណូល និងការចំណាយប្រចាំខែរបស់អ្នក។ សូមផ្តល់ព័ត៌មានអំពីចំណូល និងការចំណាយ។"),

            (f"ខ្ញុំចំណាយថ្លៃផ្ទះ និងម្ហូបអាហារសរុបប្រហែល ${amt:,} រាល់ខែ។",
             f"ការចំណាយដែលបានរៀបរាប់សរុបគឺ ${amt:,}។ ប៉ុន្តែព័ត៌មានចំណូលប្រចាំខែមិនទាន់បានបញ្ជាក់នៅឡើយទេ។ សូមផ្តល់តួលេខចំណូលប្រចាំខែរបស់អ្នកដើម្បីគណនាសមត្ថភាពសន្សំ។")
        ]
        for q, a in km_missing_list:
            records.append({"instruction": INSTR_MISSING, "input": q, "output": a})

    return records[:140]


# =============================================================================
# 7. Greetings, Casual Conversations & Boundaries (100 records)
# =============================================================================
def generate_group7_greetings():
    records = []

    # 40 distinct English greetings
    en_greetings = [
        ("Hello, how are you doing today?", "Hello! I am doing well, thank you. How can I assist you with your budget, savings, or personal finances today?"),
        ("Good morning, financial advisor!", "Good morning! I am ready to help you review your finances, check your savings capacity, or plan your goals."),
        ("Good afternoon, assistant.", "Good afternoon! How can I help you manage your personal finances today?"),
        ("Good evening to you!", "Good evening! Feel free to ask any questions about budgeting, savings goals, or managing expenses."),
        ("Who created you and what is your purpose?", "I am a Financial Advisor AI designed to assist you with personal budgeting, savings calculations, and financial planning."),
        ("Are you a human advisor?", "No, I am an AI financial assistant. I help you analyze your budget, evaluate cash flow, and build healthy financial habits."),
        ("Thanks for your great assistance!", "You are very welcome! I am always here whenever you need help navigating your personal finances."),
        ("See you tomorrow, have a nice day!", "Have a wonderful day! Feel free to check in anytime you want to review your budget."),
        ("Hi there, I am ready to start my budget.", "Welcome! Taking control of your budget is a great step. Feel free to share your monthly income and expenses to begin."),
        ("Hello advisor, nice to meet you.", "Nice to meet you as well! I look forward to helping you reach your financial milestones."),
        ("Can you help me understand personal finance?", "Absolutely! I can guide you through cash flow management, budgeting rules like 50/30/20, and emergency fund strategies."),
        ("Greetings, hope you are having a productive day!", "Thank you! I am ready to assist you with any questions about your savings, expenses, or financial targets."),
        ("Thank you, that explanation was very clear.", "I'm glad to hear that! Clear understanding is the first step toward confident financial decisions."),
        ("Understood, thanks for the advice.", "You're welcome! Keep up the disciplined habits, and reach out whenever you want to review your numbers."),
        ("Hi, I just want to say thanks.", "Thank you for the kind words! Wishing you continuous progress on your financial journey."),
        ("Good night advisor!", "Good night! Rest well, and I will be here whenever you need your next financial check-in."),
        ("Hey, what topics can we discuss?", "We can discuss your monthly income, living expenses, emergency fund planning, debt-free strategies, and savings timelines."),
        ("I appreciate your quick responses.", "Happy to help! My goal is to provide clear, prompt, and grounded financial assistance."),
        ("That sounds reasonable, thank you.", "You're very welcome! Taking practical, steady steps is the key to lasting financial security."),
        ("Hello, is this the right place for budgeting help?", "Yes, indeed! I am here to help you calculate your cash surplus, plan savings goals, and track your budget."),
        ("Hi! How's your day going?", "Hello! Everything is going great, thank you. How can I assist with your personal finances today?"),
        ("Good day, assistant.", "Good day! How can I support your financial planning and budgeting today?"),
        ("Thanks for the detailed breakdown.", "My pleasure! Providing clear and transparent financial guidance is my priority."),
        ("Okay, I will review my expenses tonight.", "That's a wonderful proactive step! Reviewing your expenses is the best way to uncover savings opportunities."),
        ("Glad I reached out to you.", "I am glad to assist you! Feel free to ask anytime you have new financial questions."),
        ("Great talking with you!", "Likewise! Wishing you great success with your budget and savings."),
        ("Hello again, back for another check-in.", "Welcome back! What aspects of your budget or savings would you like to review today?"),
        ("Thanks, you made this easy to understand.", "I appreciate that! Simplifying financial concepts is what I am here for."),
        ("Sounds good, talk to you later.", "Take care! I'll be right here whenever you need your next financial update."),
        ("Hi assistant, thank you for being patient.", "Always my pleasure. Take all the time you need to explore and understand your finances."),
        ("Can we talk about general savings tips?", "Of course! We can explore automated savings, emergency fund sizing, and cutting unnecessary recurring costs."),
        ("Hello, ready when you are.", "I am fully ready! Please let me know what financial numbers or goals you would like to look at."),
        ("Thanks for staying objective and helpful.", "You are welcome. Objective, grounded advice is essential for sound financial planning."),
        ("Have a wonderful week ahead!", "Thank you so much! Wishing you a productive and financially successful week."),
        ("Hi, just checking in on my plan.", "Welcome! Feel free to review your current surplus, update any numbers, or check goal timelines."),
        ("Got it, this was very reassuring.", "I am glad it brought you peace of mind. Consistent financial planning brings clarity and confidence."),
        ("Thanks again for the guidance.", "Anytime! Remember that small, consistent monthly savings compound into major stability over time."),
        ("Hello, hope you are ready for a few questions.", "I am always ready! Ask away about your income, expenses, or financial targets."),
        ("I feel much more confident about my budget now.", "That is fantastic to hear! Confidence and consistency are the foundation of financial health."),
        ("Goodbye for now, assistant!", "Goodbye! Have a great day and stay focused on your financial goals.")
    ]

    # 40 distinct Khmer greetings
    km_greetings = [
        ("សួស្តី តើអ្នកសុខសប្បាយទេ?", "សួស្តី! ខ្ញុំសុខសប្បាយជាធម្មតាទេ អរគុណច្រើន។ តើខ្ញុំអាចជួយអ្នកក្នុងការរៀបចំផែនការហិរញ្ញវត្ថុ ឬការសន្សំយ៉ាងដូចម្តេចដែរ?"),
        ("អរុណសួស្តីអ្នកប្រឹក្សាហិរញ្ញវត្ថុ!", "អរុណសួស្តី! សូមឱ្យថ្ងៃនេះជាថ្ងៃដ៏ល្អសម្រាប់ការគ្រប់គ្រងលុយកាក់ និងការសន្សំរបស់អ្នក។"),
        ("ទិវាសួស្តីអ្នកប្រឹក្សា ខ្ញុំរីករាយណាស់ដែលបានជួបអ្នក!", "ទិវាសួស្តី! ខ្ញុំត្រៀមខ្លួនជានិច្ចដើម្បីជួយអ្នកពិនិត្យមើលថវិកា និងការចំណាយប្រចាំថ្ងៃ។"),
        ("សាយ័ណ្ហសួស្តី!", "សាយ័ណ្ហសួស្តី! តើអ្នកមានសំណួរអ្វីខ្លះទាក់ទងនឹងការគ្រប់គ្រងថវិកាថ្ងៃនេះ?"),
        ("តើអ្នកជាមនុស្សមែនទេ?", "ទេ ខ្ញុំជាជំនួយការបញ្ញាសិប្បនិម្មិត (AI) ដែលជួយប្រឹក្សាផ្នែកហិរញ្ញវត្ថុផ្ទាល់ខ្លួន ការរៀបចំថវិកា និងការសន្សំប្រាក់។"),
        ("អរគុណច្រើនសម្រាប់ជំនួយដ៏ល្អ", "ដោយក្តីរីករាយជានិច្ច! ប្រសិនបើអ្នកមានចម្ងល់បន្ថែម សូមសួរបានគ្រប់ពេល។"),
        ("លាហើយសម្រាប់ថ្ងៃនេះ ជួបគ្នាពេលក្រោយ។", "សូមជម្រាបលា! សូមឱ្យការសន្សំរបស់អ្នកដំណើរការទៅដោយរលូន និងជោគជ័យ។"),
        ("សួស្តីអ្នកជំនួយការ ខ្ញុំចង់រៀបចំថវិកា។", "សូមស្វាគមន៍! ការចាប់ផ្តើមរៀបចំថវិកាគឺជាការសម្រេចចិត្តដ៏ឆ្លាតវៃ។ សូមប្រាប់ពីចំណូល និងការចំណាយរបស់អ្នកដើម្បីចាប់ផ្តើម។"),
        ("ជម្រាបសួរ ខ្ញុំទើបតែចូលប្រើប្រាស់លើកដំបូង។", "សូមស្វាគមន៍មកកាន់ប្រព័ន្ធប្រឹក្សាហិរញ្ញវត្ថុ! ខ្ញុំរីករាយណាស់ក្នុងការជួយអ្នកគ្រប់គ្រងលុយកាក់ឱ្យកាន់តែមានប្រសិទ្ធភាព។"),
        ("តើខ្ញុំអាចពិភាក្សាអំពីអ្វីខ្លះជាមួយអ្នកប្រឹក្សា AI?", "អ្នកអាចសួរអំពីការរៀបចំថវិកា 50/30/20, ការគណនាប្រាក់បម្រុងបន្ទាន់, ការកាត់បន្ថយការចំណាយ និងការកំណត់ទិសដៅសន្សំ។"),
        ("អរគុណ ការពន្យល់របស់អ្នកងាយយល់ណាស់។", "ខ្ញុំពិតជារីករាយដែលបានជួយ! ការយល់ដឹងច្បាស់លាស់នឹងជួយឱ្យអ្នកធ្វើការសម្រេចចិត្តផ្នែកហិរញ្ញវត្ថុបានត្រឹមត្រូវ។"),
        ("យល់ព្រម ខ្ញុំនឹងចាប់ផ្តើមកត់ត្រាចំណាយ។", "ពិតជាអស្ចារ្យណាស់! ការកត់ត្រាចំណាយប្រចាំថ្ងៃគឺជាគ្រឹះដំបូងបំផុតដើម្បីគ្រប់គ្រងលុយឱ្យនៅសល់។"),
        ("សួស្តី ខ្ញុំសប្បាយចិត្តណាស់ដែលបានពិភាក្សាជាមួយអ្នក។", "ខ្ញុំក៏រីករាយណាស់ដែរដែលបានជួយអ្នក! សូមបន្តរក្សាទម្លាប់ហិរញ្ញវត្ថុល្អៗជានិច្ច។"),
        ("រាត្រីសួស្តីអ្នកប្រឹក្សា!", "រាត្រីសួស្តី! សូមសម្រាកឱ្យបានស្រួល ហើយខ្ញុំនឹងនៅទីនេះរង់ចាំជួយអ្នកនៅពេលក្រោយទៀត។"),
        ("តើអ្នកអាចជួយខ្ញុំសន្សំលុយបានដោយរបៀបណា?", "ខ្ញុំអាចជួយអ្នកវិភាគចំណូល ចំណាយ ស្វែងរកប្រាក់សល់សុទ្ធ និងកំណត់ផែនការសន្សំជាក់ស្តែងតាមគោលដៅរបស់អ្នក។"),
        ("ព័ត៌មាននេះមានតម្លៃណាស់សម្រាប់ខ្ញុំ។", "អរគុណច្រើនសម្រាប់ការលើកទឹកចិត្ត! គោលដៅរបស់ខ្ញុំគឺជួយអ្នកកសាងស្ថិរភាពហិរញ្ញវត្ថុពិតប្រាកដ។"),
        ("ខ្ញុំយល់ច្បាស់ហើយ អរគុណច្រើន!", "ដោយក្តីសោមនស្សរីករាយ! សូមឱ្យការអនុវត្តផែនការរបស់អ្នកទទួលបានជោគជ័យ។"),
        ("សួស្តីអ្នកជំនាញ! ថ្ងៃនេះសុខសប្បាយទេ?", "សួស្តី! ខ្ញុំសុខសប្បាយជាធម្មតាទេ អរគុណច្រើន។ តើស្ថានភាពហិរញ្ញវត្ថុរបស់អ្នកយ៉ាងណាដែរ?"),
        ("ខ្ញុំមានអារម្មណ៍ធូរស្រាលក្រោយបានពិភាក្សា។", "ពិតជារីករាយដែលបានជួយសម្រួលការព្រួយបារម្ភរបស់អ្នក។ ការមានផែនការច្បាស់លាស់នឹងកាត់បន្ថយភាពតានតឹងផ្នែកហិរញ្ញវត្ថុ។"),
        ("សូមអរគុណសម្រាប់ដំបូន្មានដ៏មានប្រយោជន៍។", "ដោយក្តីរីករាយជានិច្ច! ខ្ញុំនៅទីនេះរង់ចាំជួយអ្នកគ្រប់ពេលវេលា។"),
        ("សួស្តី ខ្ញុំត្រៀមខ្លួនរៀនពីការគ្រប់គ្រងលុយហើយ។", "អស្ចារ្យណាស់! ការរៀនគ្រប់គ្រងលុយកាក់គឺជាការវិនិយោគលើចំណេះដឹងដ៏មានតម្លៃបំផុត។"),
        ("អរគុណសម្រាប់ពេលវេលារបស់អ្នក។", "មិនអីទេ! ខ្ញុំរីករាយក្នុងការឆ្លើយរាល់សំណួរហិរញ្ញវត្ថុរបស់អ្នក។"),
        ("ខ្ញុំនឹងយកគំនិតនេះទៅអនុវត្តតាម។", "ពិតជាល្អណាស់! ភាពខ្ជាប់ខ្ជួនក្នុងការអនុវត្តជាក់ស្តែងនឹងនាំមកនូវលទ្ធផលជាទីគាប់ចិត្ត។"),
        ("ជម្រាបសួរ ជួបគ្នាម្តងទៀតហើយ។", "សូមស្វាគមន៍មកវិញ! តើអ្នកចង់ពិនិត្យមើលតួលេខអ្វីខ្លះថ្ងៃនេះ?"),
        ("ការពន្យល់នេះច្បាស់លាស់ និងត្រឹមត្រូវណាស់។", "អរគុណច្រើន! ខ្ញុំប្រកាន់ខ្ជាប់នូវគោលការណ៍ហិរញ្ញវត្ថុត្រឹមត្រូវ និងជាក់ស្តែងជានិច្ច។"),
        ("សួស្តីអ្នកជួយគិតលុយ!", "សួស្តី! ខ្ញុំត្រៀមខ្លួនជួយអ្នកគិតគូរចំណូល ចំណាយ និងការសន្សំឱ្យមានរបៀបរៀបរយ។"),
        ("តើថ្ងៃនេះយើងគួរពិភាក្សាអំពីអ្វី?", "យើងអាចពិភាក្សាអំពីការបែងចែកថវិកាប្រចាំខែ ឬការគណនារយៈពេលសម្រេចគោលដៅសន្សំរបស់អ្នក។"),
        ("ខ្ញុំពិតជាពេញចិត្តនឹងការណែនាំនេះ។", "អរគុណច្រើន! សូមបន្តថែរក្សាការសន្សំឱ្យបានល្អប្រសើរ។"),
        ("សួស្តី មានអារម្មណ៍ថាការសន្សំស្រួលជាងមុន។", "ពិតមែនហើយ! នៅពេលយើងបំបែកវាជាជំហានតូចៗ ការសន្សំនឹងក្លាយជារឿងងាយស្រួល និងរីករាយ។"),
        ("អរគុណច្រើន ជួបគ្នាសប្តាហ៍ក្រោយ។", "សូមជម្រាបលា! សូមឱ្យសប្តាហ៍ថ្មីរបស់អ្នកពោរពេញដោយភាពរីករាយ និងជោគជ័យ។"),
        ("ជម្រាបសួរអ្នកប្រឹក្សាដ៏ឆ្លាតវៃ!", "ជម្រាបសួរ! អរគុណច្រើនសម្រាប់ការសរសើរ។ តើខ្ញុំអាចជួយអ្វីបានខ្លះថ្ងៃនេះ?"),
        ("ខ្ញុំកាន់តែមានទំនុកចិត្តលើការគ្រប់គ្រងថវិកា។", "អបអរសាទរ! ទំនុកចិត្ត និងទម្លាប់ល្អជាកត្តាសំខាន់បំផុតឆ្ពោះទៅរកសេរីភាពហិរញ្ញវត្ថុ។"),
        ("អរគុណដែលតែងតែនៅទីនេះជួយខ្ញុំ។", "ដោយក្តីរីករាយ! ខ្ញុំនៅទីនេះជានិច្ចដើម្បីគាំទ្រដំណើរហិរញ្ញវត្ថុរបស់អ្នក។"),
        ("សួស្តី ខ្ញុំចង់សួរយោបល់បន្តិច។", "សូមសួរបានគ្រប់ពេល! ខ្ញុំរីករាយនឹងផ្តល់យោបល់ផ្អែកលើគោលការណ៍ហិរញ្ញវត្ថុត្រឹមត្រូវ។"),
        ("ពិតជាមានប្រយោជន៍ខ្លាំងណាស់។", "ខ្ញុំរីករាយណាស់ដែលព័ត៌មាននេះជួយអ្នកបាន។ សូមកុំស្ទាក់ស្ទើរក្នុងការសួរប្រសិនបើមានចម្ងល់។"),
        ("ថ្ងៃនេះប៉ុណ្ណឹងសិនហើយ អរគុណ។", "ចាស/បាទ! សូមឱ្យអ្នកមានថ្ងៃដ៏រីករាយ និងបន្តដំណើរការសន្សំដោយរលូន។"),
        ("សួស្តី សង្ឃឹមថាអ្នកអាចជួយខ្ញុំបាន។", "ពិតជាបាន! ខ្ញុំត្រៀមខ្លួនរួចរាល់ដើម្បីជួយអ្នកគ្រប់គ្រងថវិកា និងការសន្សំ។"),
        ("អរគុណសម្រាប់ការលើកទឹកចិត្ត។", "ដោយក្តីរីករាយ! ការខិតខំប្រឹងប្រែងរបស់អ្នកក្នុងថ្ងៃនេះនឹងផ្តល់ផ្លែផ្កានៅថ្ងៃអនាគត។"),
        ("ខ្ញុំចាប់ផ្តើមយល់ពីតម្លៃនៃការសន្សំហើយ។", "ពិតជាត្រឹមត្រូវណាស់! ការសន្សំគឺជាការទិញសេរីភាព និងសន្តិភាពផ្លូវចិត្តសម្រាប់អនាគត។"),
        ("សូមជម្រាបលាអ្នកប្រឹក្សា!", "សូមជម្រាបលា! សូមថែរក្សាសុខភាព និងបន្តឆ្ពោះទៅកាន់គោលដៅរបស់អ្នក។")
    ]

    # 20 distinct Mixed greetings
    mix_greetings = [
        ("Hi advisor, how's everything going today?", "Hello! Everything is great, thank you. How can I assist your financial journey today?"),
        ("Thanks a lot, អ្នកជួយបានច្រើនណាស់!", "ដោយក្តីរីករាយ! ខ្ញុំនៅទីនេះជានិច្ចដើម្បីជួយអ្នកគ្រប់គ្រង cash flow និងសម្រេច goals របស់អ្នក។"),
        ("Good morning advisor, សង្ឃឹមថាអ្នកមានថ្ងៃល្អ!", "អរុណសួស្តី! អរគុណច្រើន។ តើខ្ញុំអាចជួយអ្វីខ្លះទាក់ទងនឹងការគ្រប់គ្រងថវិកាថ្ងៃនេះ?"),
        ("Have a great weekend, advisor!", "Thank you! Have a wonderful and relaxing weekend. I will be here whenever you want to check your finances."),
        ("Hello advisor, ready to review my monthly budget?", "Hello! Yes, I am fully ready. Please share your latest income and expenses to begin."),
        ("Thanks for the guidance, ចម្លើយច្បាស់ណាស់!", "ដោយក្តីរីករាយ! ការយល់ដឹងច្បាស់ពីលំហូរសាច់ប្រាក់ជួយឱ្យអ្នកគ្រប់គ្រងលុយបានកាន់តែល្អ។"),
        ("Hi there! Just stopping by to say thank you.", "Thank you for stopping by! Wishing you continued financial health and steady savings."),
        ("Good afternoon advisor, ជួយ check budget តិចបានអត់?", "Good afternoon! ពិតជាបាន សូមប្រាប់ពីចំណូលនិងចំណាយរបស់អ្នកមក។"),
        ("Understood, thanks for keeping it practical.", "You are welcome! Keeping personal finance practical and grounded is my primary goal."),
        ("Hello, ខ្ញុំចង់ build financial stability.", "Welcome! Building financial stability starts with a clear budget and an emergency fund. Let's work on it together."),
        ("Thanks advisor, you are very responsive.", "Thank you! I am always here to assist your financial journey promptly."),
        ("Good evening, សួស្តីអ្នកប្រឹក្សា!", "Good evening! សួស្តី! តើអ្នកចង់ពិភាក្សាអំពីប្រធានបទហិរញ្ញវត្ថុអ្វីដែរយប់នេះ?"),
        ("Appreciate your assistance, very helpful.", "Happy to assist! Stay consistent with your savings targets."),
        ("Hi, ready for another financial check-up.", "Great! Regular check-ups keep your finances on track. What numbers would you like to review?"),
        ("Thanks a lot, ខ្ញុំនឹង follow តាមដំបូន្មាននេះ។", "អស្ចារ្យណាស់! ការអនុវត្តជាប្រចាំនឹងជួយឱ្យអ្នកសម្រេចគោលដៅហិរញ្ញវត្ថុបានលឿន។"),
        ("Hello! How can I make budgeting fun?", "Make it visual! Track your progress with milestone charts and reward yourself modestly when reaching debt-free goals."),
        ("Thank you, that clears up my confusion.", "Glad to hear that! Never hesitate to ask whenever numbers feel confusing."),
        ("Hi advisor, hope you have a nice evening!", "Thank you very much! Have a restful evening as well."),
        ("All clear for now, see you next month.", "Sounds great! Keep up the great habits, and see you next month!"),
        ("Thanks for being so supportive, advisor!", "Always a pleasure! Remember, steady monthly steps lead to massive long-term stability.")
    ]

    for q, a in en_greetings:
        records.append({"instruction": INSTR_GREET, "input": q, "output": a})
    for q, a in km_greetings:
        records.append({"instruction": INSTR_GREET, "input": q, "output": a})
    for q, a in mix_greetings:
        records.append({"instruction": INSTR_GREET, "input": q, "output": a})

    return records[:100]


# =============================================================================
# 8. Safety Boundaries & Guardrails (60 records)
# =============================================================================
def generate_group8_safety():
    records = []

    # 30 unique English safety inquiries
    en_safety_questions = [
        ("Which cryptocurrency should I buy to 10x my investment this week?",
         "I cannot recommend speculative cryptocurrencies or promise rapid gains. Crypto assets carry extreme volatility and capital loss risks. Sustainable financial stability relies on diversified savings, emergency funds, and disciplined living within your means."),
        ("Can you guarantee me a 25% annual return with zero risk?",
         "No, I cannot guarantee returns. In finance, there is no such thing as high return without risk. Any scheme promising 25% guaranteed risk-free returns is a classic warning sign of investment fraud."),
        ("How can I hide my cash income to avoid paying taxes?",
         "I cannot assist with tax evasion, unreported income schemes, or illegal financial actions. I can only help you organize your legitimate income and expenses under sound personal financial principles."),
        ("Can you approve my application for a $10,000 personal loan?",
         "I am an educational Financial Advisor AI and do not possess lending authority or loan underwriting capabilities. For loan inquiries, please contact a licensed commercial bank or regulated microfinance institution."),
        ("Should I borrow from an unlicensed loan shark to invest in foreign stocks?",
         "Never borrow from unlicensed lenders or loan sharks. They charge predatory, unregulated interest rates that trap borrowers in unmanageable debt. Borrowing at high interest to speculate on volatile assets carries extreme financial danger."),
        ("Can you hack or artificially improve my credit bureau score?",
         "I cannot modify or alter credit bureau records. The only legitimate way to improve a credit score is to pay debts punctually, keep credit utilization low, and manage cash flow responsibly over time."),
        ("Which meme coin will explode next month for fast profits?",
         "I cannot endorse meme coins or speculative trading bets. Speculative tokens have no underlying cash flows and often result in total loss of capital. Focus on building liquid emergency reserves first."),
        ("Can you guarantee a 50% profit if I invest in foreign exchange trading?",
         "No, I cannot guarantee any investment profit. Forex trading carries substantial downside risk, and claims of guaranteed 50% returns are unrealistic and characteristic of financial scams."),
        ("Can you help me fabricate an employment letter to get a bank loan?",
         "I cannot assist in falsifying employment verification, income documents, or loan applications. Doing so constitutes loan fraud and carries severe legal penalties."),
        ("Should I take a high-interest payday loan to buy Bitcoin?",
         "No, you should never use high-interest borrowing to purchase speculative volatile assets. If the asset declines, you remain obligated to pay compounding interest charges that could lead to financial ruin."),
        ("Can you wipe out my delinquent loan history from the credit report?",
         "I cannot erase or alter official credit reporting data. Past credit performance can only be rehabilitated legitimately through consistent, on-time payments and reducing outstanding balances."),
        ("Is there any secret algorithm that guarantees daily stock market gains?",
         "No, there is no secret algorithm or guaranteed path to daily trading profits. Markets are inherently uncertain, and promises of effortless trading returns are deceptive."),
        ("Can you show me how to launder cash through offshore accounts?",
         "I cannot provide assistance with money laundering, illegal fund transfers, or illicit financial activities. My role is strictly limited to legal, personal budgeting and financial literacy."),
        ("Can your AI system authorize an emergency cash advance for me?",
         "No, I do not provide cash advances or banking transactions. I am an informational tool designed to help you analyze your budget and plan your personal savings."),
        ("Should I invest my entire emergency reserve into a high-risk tech startup?",
         "Never invest your emergency fund into high-risk illiquid ventures. Emergency reserves must remain safe and instantly accessible to protect you against sudden life crises."),
        ("Can you guarantee that real estate prices will double in two years?",
         "No, I cannot guarantee real estate appreciation or market returns. Property markets fluctuate based on macroeconomic conditions, interest rates, and liquidity."),
        ("Can you write a fake bank statement showing $50,000 in savings?",
         "I cannot generate fraudulent bank statements, forged financial documents, or misrepresented balances. Falsifying financial records is illegal."),
        ("Should I borrow from predatory lenders to pay my credit card minimums?",
         "No, borrowing from predatory lenders to service existing debt compounds interest costs and worsens insolvency. Instead, contact your credit card issuer to request hardship payment plans."),
        ("Which penny stock can turn $500 into $50,000 this month?",
         "I cannot recommend penny stocks or speculative trading schemes. Penny stocks are susceptible to market manipulation and lack liquidity, leading to high capital loss rates."),
        ("Can you guarantee a risk-free 15% return in peer-to-peer lending?",
         "No, peer-to-peer lending carries borrower default risk and platform risk. Any claim of a risk-free 15% yield contradicts fundamental economic realities."),
        ("How can I avoid reporting side-hustle cash earnings to tax authorities?",
         "I cannot assist in concealing taxable income or avoiding legal tax reporting. Transparent compliance and sound budgeting are the only responsible financial practices."),
        ("Can you approve my mortgage application for a new house?",
         "I cannot approve mortgages or credit facilities. Mortgage underwriting is conducted exclusively by licensed banks following official creditworthiness assessments."),
        ("Should I take out a second mortgage to trade crypto futures?",
         "Under no circumstances should you gamble home equity on leveraged cryptocurrency futures. Risking your primary residence on speculative volatility exposes your family to homelessness."),
        ("Can you help me manipulate my debt-to-income ratio on paper?",
         "I cannot assist in misrepresenting financial ratios or falsifying financial declarations to financial institutions."),
        ("Is there an investment that guarantees doubling my money with zero chance of loss?",
         "No, there is no legitimate investment that doubles money without risk. Higher potential returns inherently demand higher risk of capital loss."),
        ("Can you provide insider trading tips for upcoming earnings calls?",
         "I cannot provide insider information or participate in securities fraud. Trading on non-public material information is strictly illegal under securities laws."),
        ("Should I borrow money from coworkers at 20% weekly interest?",
         "No, a 20% weekly interest rate equals over 1,000% annualized interest—an unsustainable rate that will rapidly escalate into unmanageable financial distress."),
        ("Can you help me falsify tax returns to show higher income for a visa?",
         "I cannot assist with the falsification of tax filings, visa documents, or governmental declarations."),
        ("Which altcoin will give me guaranteed 100x gains before the weekend?",
         "I cannot recommend altcoins or promise speculative windfalls. Cryptocurrencies are volatile speculative instruments, not guaranteed wealth vehicles."),
        ("Can you guarantee that gold prices will never drop?",
         "No, commodity prices including gold fluctuate based on global currency values, interest rates, and market sentiment. No asset price is immune to market volatility.")
    ]

    for q, a in en_safety_questions:
        records.append({"instruction": INSTR_SAFETY, "input": q, "output": a})

    # 30 unique Khmer safety inquiries
    km_safety_questions = [
        ("តើខ្ញុំគួរទិញកាក់គ្រីបតូណាដើម្បីចំណេញបានលឿន 10x?",
         "ខ្ញុំមិនអាចផ្តល់អនុសាសន៍ទិញរូបិយប័ណ្ណគ្រីបតូ ឬធានាប្រាក់ចំណេញរហ័សបានឡើយ។ ទ្រព្យសកម្មគ្រីបតូមានហានិភ័យខ្ពស់នៃការបាត់បង់ប្រាក់ដើម។ គ្រឹះហិរញ្ញវត្ថុរឹងមាំគឺការសន្សំជាប្រចាំ និងការកសាងប្រាក់បម្រុងបន្ទាន់។"),
        ("តើមានការវិនិយោគណាដែលធានាចំណេញ 30% ដោយគ្មានហានិភ័យទេ?",
         "មិនមានទេ! ក្នុងវិស័យហិរញ្ញវត្ថុ គ្មានការវិនិយោគណាដែលផ្តល់ផលចំណេញខ្ពស់ដោយគ្មានហានិភ័យឡើយ។ ការសន្យាផលចំណេញខ្ពស់ខុសប្រក្រតីជានិមិត្តសញ្ញានៃការបោកប្រាស់។"),
        ("តើខ្ញុំអាចគេចវេះពីការបង់ពន្ធដោយរបៀបណា?",
         "ខ្ញុំមិនអាចជួយក្នុងការគេចពន្ធ ឬសកម្មភាពខុសច្បាប់ណាមួយឡើយ។ ខ្ញុំអាចជួយរៀបចំផែនការថវិកា និងការគ្រប់គ្រងចំណូលចំណាយស្របច្បាប់ប៉ុណ្ណោះ។"),
        ("តើអ្នកអាចអនុម័តប្រាក់កម្ចី $10,000 ឱ្យខ្ញុំបានទេ?",
         "ខ្ញុំជាជំនួយការ AI អប់រំហិរញ្ញវត្ថុ និងគ្មានសិទ្ធិអំណាចក្នុងការផ្តល់ ឬអនុម័តប្រាក់កម្ចីឡើយ។ សូមទាក់ទងធនាគារ ឬគ្រឹះស្ថានមីក្រូហិរញ្ញវត្ថុដែលមានអាជ្ញាប័ណ្ណត្រឹមត្រូវ។"),
        ("តើខ្ញុំគួរខ្ចីលុយការប្រាក់ខ្ពស់ក្រៅប្រព័ន្ធដើម្បីយកទៅជួញដូរភាគហ៊ុនទេ?",
         "មិនគួរជាដាច់ខាត! កម្ចីក្រៅប្រព័ន្ធមានការប្រាក់ខ្ពស់ហួសហេតុ ដែលអាចរុញច្រានអ្នកឱ្យធ្លាក់ក្នុងអន្ទាក់បំណុលវណ្ឌក។ ការខ្ចីលុយការប្រាក់ខ្ពស់ទៅប្រថុយក្នុងទីផ្សារភាគហ៊ុនមានគ្រោះថ្នាក់ខ្លាំងណាស់។"),
        ("តើអ្នកអាចជួយកែប្រែប្រវត្តិឥណទានរបស់ខ្ញុំនៅ CBC បានទេ?",
         "ខ្ញុំគ្មានសិទ្ធិចូលទៅកាន់ប្រព័ន្ធឥណទាន ឬកែប្រែទិន្នន័យ CBC ឡើយ។ មធ្យោបាយស្របច្បាប់តែមួយគត់ដើម្បីកែលម្អប្រវត្តិឥណទាន គឺការសងបំណុលឱ្យទាន់ពេលវេលា និងកាត់បន្ថយបំណុលមិនចាំបាច់។"),
        ("តើខ្ញុំគួរយកប្រាក់បម្រុងបន្ទាន់ទៅលេង Forex ទេ?",
         "មិនគួរជាដាច់ខាត! ប្រាក់បម្រុងបន្ទាន់ត្រូវតែរក្សាទុកក្នុងកន្លែងដែលមានសុវត្ថិភាពខ្ពស់ និងអាចដកបានភ្លាមៗ មិនត្រូវយកទៅប្រថុយក្នុងទីផ្សារ Forex ដែលអាចបាត់បង់ប្រាក់ដើមឡើយ។"),
        ("តើអ្នកអាចជួយបង្កើតលិខិតបញ្ជាក់ប្រាក់ខែមិនពិតដើម្បីដាក់ពាក្យស្នើសុំកម្ចីបានទេ?",
         "ខ្ញុំមិនអាចជួយក្នុងការបន្លំទិន្នន័យចំណូល ឬឯកសារក្លែងបន្លំបានឡើយ ព្រោះជាទង្វើខុសច្បាប់។ ខ្ញុំអាចជួយអ្នកកែលម្អសមាមាត្របំណុលនិងចំណូលតាមរយៈការគ្រប់គ្រងថវិកាពិតប្រាកដ។"),
        ("តើមានវិធីណាដែលអាចរកលុយបានលឿនគុណនឹងពីរក្នុងរយៈពេលមួយសប្តាហ៍ទេ?",
         "គ្មានវិធីស្របច្បាប់ណាដែលអាចធានាផលចំណេញទ្វេដងក្នុងរយៈពេលខ្លីដោយគ្មានហានិភ័យឡើយ។ ការសន្យាបែបនេះជាទូទៅគឺជាអន្ទាក់នៃការបោកប្រាស់ហិរញ្ញវត្ថុ។"),
        ("តើខ្ញុំគួរខ្ចីលុយតុងទីនការប្រាក់ខ្ពស់ដើម្បីទិញកាក់ឌីជីថលទេ?",
         "មិនគួរឡើយ! ការខ្ចីលុយដែលមានការប្រាក់ខ្ពស់ទៅទិញទ្រព្យសកម្មប្រថុយប្រថានអាចធ្វើឱ្យអ្នកបាត់បង់ប្រាក់ដើមផង និងជាប់បំណុលវណ្ឌកផង។"),
        ("តើអ្នកអាចលុបឈ្មោះខ្ញុំចេញពីបញ្ជីខ្មៅធនាគារបានទេ?",
         "ខ្ញុំមិនមានសិទ្ធិអំណាចក្នុងការកែប្រែ ឬលុបឈ្មោះចេញពីបញ្ជីឥណទានឡើយ។ មានតែការសងបំណុលដែលនៅសេសសល់ទេ ទើបអាចស្ដារទំនុកចិត្តហិរញ្ញវត្ថុឡើងវិញបាន។"),
        ("តើមានការវិនិយោគអនឡាញណាដែលធានាចំណេញ 50% ក្នុងមួយខែទេ?",
         "មិនមានទេ! ការសន្យាផ្តល់ផលចំណេញ 50% ក្នុងមួយខែគឺជាសញ្ញាច្បាស់លាស់នៃគម្រោងបោកប្រាស់ (Ponzi Scheme)។ សូមប្រុងប្រយ័ត្ន និងជៀសវាងជាដាច់ខាត។"),
        ("តើខ្ញុំអាចបង្កើតឯកសារពន្ធក្លែងក្លាយដើម្បីសុំទិដ្ឋាការបានទេ?",
         "ខ្ញុំមិនអាចជួយក្នុងការបង្កើតឯកសារក្លែងក្លាយ ឬសកម្មភាពបោកបន្លំណាមួយឡើយ ព្រោះជាអំពើល្មើសច្បាប់។"),
        ("តើអ្នកអាចជួយផ្ទេរប្រាក់កម្ចីបន្ទាន់ចូលគណនីខ្ញុំបានទេ?",
         "ខ្ញុំជាប្រព័ន្ធបញ្ញាសិប្បនិម្មិតអប់រំ និងមិនមានមុខងារផ្ទេរប្រាក់ ឬផ្តល់កម្ចីផ្ទាល់ខ្លួនឡើយ។ សូមទាក់ទងធនាគារដែលមានអាជ្ញាប័ណ្ណ។"),
        ("តើខ្ញុំគួរយកប្លង់ដីទៅបញ្ចាំដើម្បីយកលុយទៅលេងភាគហ៊ុនប្រថុយប្រថានទេ?",
         "មិនគួរជាដាច់ខាត! ការយកទ្រព្យសម្បត្តិសំខាន់ទៅប្រថុយក្នុងទីផ្សារដែលមិនប្រាកដប្រជា អាចនាំឱ្យអ្នកបាត់បង់ទីជម្រក និងធ្លាក់ក្នុងវិបត្តិហិរញ្ញវត្ថុធ្ងន់ធ្ងរ។"),
        ("តើមានកាក់គ្រីបតូណាដែលធានាថានឹងឡើងថ្លៃ 100 ដងទេ?",
         "គ្មានរូបិយប័ណ្ណគ្រីបតូណាអាចធានាការកើនឡើងតម្លៃបានឡើយ។ ទីផ្សារគ្រីបតូមានការប្រែប្រួលខ្លាំង និងគ្មានការការពារស្របច្បាប់ឡើយ។"),
        ("តើខ្ញុំអាចលាក់ចំណូលក្រៅផ្លូវការដើម្បីកុំឱ្យបង់ពន្ធបានទេ?",
         "ខ្ញុំមិនអាចជួយក្នុងការលាក់បាំងចំណូល ឬគេចពន្ធបានឡើយ។ ខ្ញុំអាចជួយរៀបចំការកត់ត្រាចំណូលចំណាយស្របច្បាប់ប៉ុណ្ណោះ។"),
        ("តើអ្នកអាចធានាថាការវិនិយោគលើមាសនឹងចំណេញជានិច្ចទេ?",
         "តម្លៃមាសតែងតែមានការប្រែប្រួលឡើងចុះទៅតាមស្ថានភាពសេដ្ឋកិច្ចសកល គ្មានការធានាថានឹងកើនឡើងគ្រប់ពេលវេលានោះឡើយ។"),
        ("តើខ្ញុំគួរខ្ចីប្រាក់ពីមេការប្រាក់ខ្ពស់ដើម្បីបង់រំលស់ឡានទេ?",
         "មិនគួរឡើយ! ការខ្ចីបុលការប្រាក់ខ្ពស់ក្រៅប្រព័ន្ធដើម្បីទូទាត់បំណុលផ្សេងទៀត នឹងបង្កើនទម្ងន់បំណុលទ្វេដង។ សូមពិភាក្សាជាមួយធនាគារដើម្បីពន្យារពេលបង់។"),
        ("តើអ្នកអាចជួយបង្កើតរបាយការណ៍ធនាគារក្លែងបន្លំបានទេ?",
         "ខ្ញុំមិនអាចជួយក្នុងការក្លែងបន្លំរបាយការណ៍ហិរញ្ញវត្ថុ ឬឯកសារធនាគារបានឡើយ ព្រោះជាបទល្មើសព្រហ្មទណ្ឌ។"),
        ("តើខ្ញុំគួរដាក់លុយសន្សំទាំងអស់ទៅក្នុង App វិនិយោគដែលមិនស្គាល់ប្រភពទេ?",
         "មិនគួរដាច់ខាត! ការផ្ញើប្រាក់ទៅកាន់ App ដែលគ្មានអាជ្ញាប័ណ្ណពីធនាគារជាតិនៃកម្ពុជា មានហានិភ័យខ្ពស់នៃការបោកប្រាស់ និងបាត់បង់ប្រាក់ទាំងស្រុង។"),
        ("តើមានវិធីណាដែលអាចបំបាត់ប្រវត្តិបំណុលខូចដោយមិនបាច់សងទេ?",
         "គ្មានវិធីផ្លូវច្បាប់ណាអាចបំបាត់ប្រវត្តិបំណុលដោយមិនបាច់សងនោះឡើយ។ ការទូទាត់បំណុលតាមការព្រមព្រៀងជាមធ្យោបាយត្រឹមត្រូវតែមួយគត់។"),
        ("តើខ្ញុំគួរលក់ផ្ទះដើម្បីយកលុយទៅទិញ Bitcoin ទេ?",
         "មិនគួរជាដាច់ខាត! ការលក់ទ្រព្យសម្បត្តិរស់នៅចាំបាច់ដើម្បីប្រថុយនឹងទ្រព្យសកម្មប្រែប្រួលខ្លាំង គឺជាការសម្រេចចិត្តដ៏គ្រោះថ្នាក់បំផុតសម្រាប់ស្ថិរភាពគ្រួសារ។"),
        ("តើអ្នកអាចជួយកែប្រែប្រាក់ចំណូលក្នុងប្រព័ន្ធដើម្បីឱ្យធនាគារផ្តល់កម្ចីទេ?",
         "ខ្ញុំមិនអាចជួយកែប្រែ ឬបន្លំទិន្នន័យចំណូលបានឡើយ។ ធនាគារនឹងផ្ទៀងផ្ទាត់ឯកសារជាក់ស្តែង ហើយការបន្លំនឹងត្រូវបដិសេធភ្លាមៗ។"),
        ("តើខ្ញុំអាចទិញព័ត៌មានសម្ងាត់ភាគហ៊ុនពីអ្នកបានទេ?",
         "ខ្ញុំមិនមាន ឬមិនអាចផ្តល់ព័ត៌មានសម្ងាត់ (Insider Information) ឡើយ ព្រោះជាអំពើខុសច្បាប់មូលបត្រ។"),
        ("តើមានគម្រោងវិនិយោគណាដែលគ្មានហានិភ័យសោះទេ?",
         "ក្នុងការវិនិយោគ គ្មានអ្វីដែលគ្មានហានិភ័យ 100% ឡើយ។ សូម្បីតែការសន្សំនៅធនាគារក៏មានហានិភ័យអតិផរណាដែរ ប៉ុន្តែជាជម្រើសដែលមានសុវត្ថិភាពបំផុត។"),
        ("តើខ្ញុំគួរខ្ចីលុយ App កម្ចីអនឡាញខុសច្បាប់ដើម្បីដោះស្រាយការចំណាយទេ?",
         "កុំខ្ចី App កម្ចីខុសច្បាប់ឱ្យសោះ! ពួកគេគិតការប្រាក់ខ្ពស់ហួសហេតុ និងប្រើប្រាស់វិធីសាស្ត្រគំរាមកំហែងទារប្រាក់ដែលបង្កគ្រោះថ្នាក់។"),
        ("តើអ្នកអាចណែនាំភាគហ៊ុនណាដែលធានាចំណេញ 100% បានទេ?",
         "ខ្ញុំមិនអាចធានាផលចំណេញលើភាគហ៊ុនណាមួយបានឡើយ។ ការវិនិយោគលើផ្សារហ៊ុនតែងតែមានហានិភ័យឡើងចុះ។"),
        ("តើខ្ញុំអាចគេចវេះពីការបង់ថ្លៃសេវាធនាគារតាមវិធីទុច្ចរិតបានទេ?",
         "ខ្ញុំមិនអាចជួយណែនាំវិធីសាស្ត្រទុច្ចរិត ឬខុសច្បាប់ណាមួយបានឡើយ។"),
        ("តើមានវិធីណាដែលអាចទិញទ្រព្យសម្បត្តិដោយមិនបាច់ប្រកាសប្រភពចំណូលទេ?",
         "ខ្ញុំមិនអាចជួយក្នុងការលាក់បាំងប្រភពចំណូល ឬគេចវេះពីច្បាប់ប្រឆាំងការសម្អាតប្រាក់បានឡើយ។")
    ]

    for q, a in km_safety_questions:
        records.append({"instruction": INSTR_SAFETY, "input": q, "output": a})

    return records[:60]


# =============================================================================
# Main Builder Function
# =============================================================================
def build_v4_dataset():
    print("=" * 75)
    print("BUILDING V4 CONVERSATIONAL SFT DATASET (2,500 TOTAL RECORDS)")
    print("=" * 75)

    if not os.path.exists(V3_COMBINED_PATH):
        raise FileNotFoundError(f"V3 combined dataset not found: {V3_COMBINED_PATH}")

    # 1. Load 600 V3 records
    v3_records = []
    with open(V3_COMBINED_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if line_str:
                item = json.loads(line_str)
                assert set(item.keys()) == {"instruction", "input", "output"}
                v3_records.append(item)

    print(f"Loaded {len(v3_records)} baseline records from V3 combined dataset.")
    assert len(v3_records) == 600, f"Expected 600 V3 records, got {len(v3_records)}"

    seen_inputs = set(r["input"].strip() for r in v3_records)
    assert len(seen_inputs) == 600, "V3 baseline contains duplicate inputs!"

    # 2. Generate 1,900 new conversational records
    g1 = generate_group1_mixed()        # 320
    g2 = generate_group2_multiturn()    # 380
    g3 = generate_group3_updates()      # 280
    g4 = generate_group4_facts()        # 320
    g5 = generate_group5_budgeting()    # 300
    g6 = generate_group6_missing()      # 140
    g7 = generate_group7_greetings()    # 100
    g8 = generate_group8_safety()       # 60

    new_v4_records = g1 + g2 + g3 + g4 + g5 + g6 + g7 + g8

    print("\n--- Breakdown of New Conversational Records Generated ---")
    print(f"1. Khmer-English Mixed (Code-Switching):        {len(g1):>4} records")
    print(f"2. Multi-turn Conversations & Context Tracking: {len(g2):>4} records")
    print(f"3. Profile Updates & Follow-up Scenarios:       {len(g3):>4} records")
    print(f"4. Profile-Aware Facts & Deep Verification:     {len(g4):>4} records")
    print(f"5. Budgeting, Savings & Financial Planning:     {len(g5):>4} records")
    print(f"6. Missing Information (Strict Null Semantics): {len(g6):>4} records")
    print(f"7. Greetings & Casual Conversations:            {len(g7):>4} records")
    print(f"8. Safety Boundaries & Guardrails:              {len(g8):>4} records")
    print("-" * 55)
    print(f"Total New Conversational Records:               {len(new_v4_records):>4} records")

    assert len(new_v4_records) == 1900, f"Expected 1,900 new records, got {len(new_v4_records)}"

    # 3. Strict Uniqueness Check
    duplicates_found = 0
    for idx, r in enumerate(new_v4_records, 1):
        inp = r["input"].strip()
        if inp in seen_inputs:
            duplicates_found += 1
            print(f"Duplicate found at index {idx}: {inp[:60]}")
        seen_inputs.add(inp)

    assert duplicates_found == 0, f"Deduplication failed: {duplicates_found} duplicate inputs detected!"
    print(f"Deduplication verified: 100% unique inputs across all 2,500 records.")

    # 4. Save New V4 Conversational Dataset
    os.makedirs(os.path.dirname(V4_CONVERSATIONAL_PATH), exist_ok=True)
    with open(V4_CONVERSATIONAL_PATH, "w", encoding="utf-8") as f:
        for r in new_v4_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\n[SAVED] {len(new_v4_records)} records -> {V4_CONVERSATIONAL_PATH}")

    # 5. Save Combined V4 Dataset (600 V3 + 1,900 New = 2,500 Total)
    v4_combined = v3_records + new_v4_records
    assert len(v4_combined) == 2500, f"Expected 2,500 combined records, got {len(v4_combined)}"

    with open(V4_COMBINED_PATH, "w", encoding="utf-8") as f:
        for r in v4_combined:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"[SAVED] {len(v4_combined)} records -> {V4_COMBINED_PATH}")
    print("=" * 75)


if __name__ == "__main__":
    build_v4_dataset()
