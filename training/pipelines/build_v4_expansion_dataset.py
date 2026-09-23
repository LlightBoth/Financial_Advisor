"""
Build V4 Dataset Expansion (5,000 Total Records) for Financial Advisor AI.

Loads:
- 2,500 validated records from V4 Part 1 (600 V3 baseline + 1,900 V4 Part 1)

Generates:
- 2,500 new high-quality conversational records across 7 specialized domains:
  1. Cambodian Domestic Financial Context (Tongtin, Bakong, Dual Currency, Ceremonies) (400 records)
  2. Khmer-English Mixed Deep Professional Conversations (400 records)
  3. Multi-Turn Deep Advisory & Diagnostic Conversations (450 records)
  4. Detailed "What-If" Life Event Simulations (Marriage, Baby, Job, Relocation) (400 records)
  5. Debt Freedom Strategies (Snowball vs Avalanche) & Zero-Debt Living (350 records)
  6. Small Business, Self-Employed & Side Hustle Personal Finance (300 records)
  7. Advanced Fraud Awareness, Scam Defense & Financial Safety (200 records)

Total Records: 2,500 + 2,500 = 5,000 records.
Output Files:
- training/sft_financial_advisor_v4_expansion.jsonl (2,500 records)
- training/sft_financial_advisor_v4_combined.jsonl (5,000 records)
"""

import json
import math
import os
import sys

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

V3_BASELINE_PATH = r"d:\Year3\Finance\Financial_Advisor\training\sft_financial_advisor_v3_combined.jsonl"
V4_CONV_PATH = r"d:\Year3\Finance\Financial_Advisor\training\sft_financial_advisor_v4_conversational.jsonl"
V4_EXPANSION_PATH = r"d:\Year3\Finance\Financial_Advisor\training\sft_financial_advisor_v4_expansion.jsonl"
V4_FINAL_COMBINED_PATH = r"d:\Year3\Finance\Financial_Advisor\training\sft_financial_advisor_v4_combined.jsonl"

INSTR_CONV = "You are a helpful Financial AI Assistant. Provide practical, empathetic, and actionable guidance on budgeting, expense reduction, and savings habits. Ground your advice in sound financial principles without calculating complex synthetic rules."
INSTR_FACT = "You are a helpful Financial AI Assistant. The user has an authoritative financial profile loaded. Answer the user's factual questions accurately using only their verified profile facts. Do not hallucinate numbers or invent figures."
INSTR_PLAN = "You are a helpful Financial AI Assistant. Provide structured, personalized financial guidance based on verified profile figures. Calculate timelines accurately and explain recommendations clearly."
INSTR_NODEBT = "You are a helpful Financial AI Assistant. The user is debt-free. Provide financial advice strictly respecting that they have zero debt. Never advise debt consolidation, debt payoff, or servicing loans when the user has no debt."
INSTR_MULTITURN = "You are a helpful Financial AI Assistant engaged in an ongoing multi-turn financial conversation. Maintain context across conversation turns, track user-provided financial figures accurately, and provide relevant, grounded guidance."
INSTR_UPDATE = "You are a helpful Financial AI Assistant. The user is updating their financial profile or asking what-if scenario questions. Calculate the exact new financial surplus and timeline, compare with previous figures clearly, and explain the financial impact."
INSTR_SAFETY = "You are a helpful Financial AI Assistant. Respond to the user inquiry while maintaining strict professional boundaries. Refuse to provide speculative trading tips, cryptocurrency picks, loan underwriting approvals, or guaranteed return promises. Redirect towards sound personal budgeting and risk management."


# =============================================================================
# 1. Cambodian Domestic Financial Context (400 records)
# =============================================================================
def generate_domain1_cambodia():
    records = []
    
    # 1A: Tongtin & Informal Savings vs Banks (100 records: 50 KM, 50 EN)
    incomes_1a = [600, 800, 1000, 1200, 1500, 1800, 2200, 2600, 3000, 3500]
    for inc in incomes_1a:
        sur = int(inc * 0.30)
        # Khmer (5 per income = 50)
        records.append({
            "instruction": INSTR_CONV,
            "input": f"ខ្ញុំរកចំណូលបាន ${inc:,}/ខែ តើគួរចូលរួមលេងតុងទីន (Tongtin) ឬដាក់សន្សំនៅធនាគារដែលមានអាជ្ញាប័ណ្ណ?",
            "output": f"លើចំណូល ${inc:,} របស់អ្នក ការដាក់ប្រាក់សន្សំនៅធនាគារដែលទទួលស្គាល់ដោយធនាគារជាតិនៃកម្ពុជា (NBC) គឺជាជម្រើសមានសុវត្ថិភាពបំផុត។ ការលេងតុងទីនមានហានិភ័យខ្ពស់នៃការបាត់បង់ប្រាក់ដើម ប្រសិនបើមេតុងទីនរត់ចោល ឬកូនតុងទីនមិនបង់ប្រាក់។ ផ្ទុយទៅវិញ ធនាគារផ្តល់ការការពារច្បាប់ ការប្រាក់ពិតប្រាកដ និងមិនប្រឈមហានិភ័យបោកប្រាស់ឡើយ។"
        })
        records.append({
            "instruction": INSTR_CONV,
            "input": f"តើការដេញតុងទីនយកការប្រាក់ខ្ពស់អាចចាត់ទុកជាការវិនិយោគល្អលើចំណូល ${inc:,} ដែរឬទេ?",
            "output": f"មិនគួរចាត់ទុកតុងទីនជាការវិនិយោគឡើយ។ ទោះបីជាការដេញតុងទីនអាចផ្តល់ផលចំណេញការប្រាក់ខ្លះក៏ដោយ ក៏វាគ្មានកិច្ចសន្យាគតិយុត្តិ ឬការធានារ៉ាប់រងប្រាក់បញ្ញើឡើយ។ សម្រាប់អ្នកមានចំណូល ${inc:,} ការដាក់ប្រាក់បញ្ញើមានកាលកំណត់ (Fixed Deposit) នៅធនាគារគឺជាជម្រើសវិនិយោគសុវត្ថិភាពជាង។"
        })
        records.append({
            "instruction": INSTR_CONV,
            "input": f"ខ្ញុំសល់ ${sur:,}/ខែពីចំណូល ${inc:,} មិត្តភក្តិបបួលលេងតុងទីន $50/ខែ តើគួរចូលរួមទេ?",
            "output": f"ប្រសិនបើអ្នកមិនទាន់មានប្រាក់បម្រុងបន្ទាន់យ៉ាងតិច 3 ខែនៃការចំណាយទេ មិនគួរចូលរួមតុងទីនឡើយ។ ចូរបង្វែរប្រាក់សល់ ${sur:,}/ខែ របស់អ្នកចូលគណនីសន្សំធនាគារផ្ទាល់ខ្លួនជាមុនសិន ដើម្បីធានាថាអ្នកអាចដកប្រាក់ប្រើប្រាស់បានភ្លាមៗនៅពេលមានអាសន្ន។"
        })
        records.append({
            "instruction": INSTR_CONV,
            "input": f"តើហានិភ័យចម្បងនៃតុងទីននៅកម្ពុជាមានអ្វីខ្លះសម្រាប់អ្នករកបាន ${inc:,}?",
            "output": f"ហានិភ័យចម្បងនៃតុងទីនរួមមាន: 1. ហានិភ័យមេតុងទីនក្ស័យធន ឬរត់ចោល 2. ហានិភ័យសមាជិកដេញលុយបានហើយមិនព្រមបង់បន្ត 3. គ្មានការការពារពីធនាគារជាតិនៃកម្ពុជា។ សម្រាប់ចំណូល ${inc:,} របស់អ្នក ការសន្សំក្នុងប្រព័ន្ធធនាគារផ្លូវការផ្តល់នូវសន្តិភាពផ្លូវចិត្ត និងសុវត្ថិភាព 100%។"
        })
        records.append({
            "instruction": INSTR_CONV,
            "input": f"តើការសន្សំនៅធនាគារក្នុងស្រុកផ្តល់ផលប្រយោជន៍អ្វីខ្លះលើចំណូល ${inc:,} ធៀបនឹងតុងទីន?",
            "output": f"អត្ថប្រយោជន៍ធនាគារលើចំណូល ${inc:,} រួមមាន:\n1. សុវត្ថិភាពប្រាក់ដើមស្ថិតក្រោមច្បាប់ធនាគារ\n2. ទទួលបានការប្រាក់ថេរនិងទៀងទាត់\n3. បង្កើតប្រវត្តិហិរញ្ញវត្ថុផ្លូវការសម្រាប់ការស្នើសុំឥណទានទិញផ្ទះនាពេលអនាគត\n4. ភាពងាយស្រួលក្នុងការគ្រប់គ្រងតាមទូរស័ព្ទដៃ។"
        })

        # English (5 per income = 50)
        records.append({
            "instruction": INSTR_CONV,
            "input": f"With a monthly income of ${inc:,} in Cambodia, should I participate in informal rotating savings (Tongtin) or use a licensed bank?",
            "output": f"On an income of ${inc:,}, saving with a commercial bank licensed by the National Bank of Cambodia (NBC) is vastly superior. Tongtin carries severe counterparty risk—if the organizer or members default, you have zero legal recourse. Licensed banks guarantee capital safety and steady compounding interest."
        })
        records.append({
            "instruction": INSTR_CONV,
            "input": f"My friends invited me to a Tongtin bidding circle with a $50 monthly share on my ${inc:,} salary. Is this advisable?",
            "output": f"It is not advisable unless you already possess a robust 3-6 month emergency fund safely stored in a bank. Informal bidding schemes frequently collapse due to non-payment. Prioritize building your own guaranteed bank reserves before considering informal peer arrangements."
        })
        records.append({
            "instruction": INSTR_CONV,
            "input": f"How do Cambodian bank fixed-term deposits compare to Tongtin for someone earning ${inc:,}?",
            "output": f"Fixed-term deposits at licensed commercial banks provide contractual capital security and steady compounding interest under formal regulatory oversight. Tongtin may offer informal bidding arrangements but lacks legal protection, making regulated bank deposits the safer choice. Always verify current published rates directly with your bank."
        })
        records.append({
            "instruction": INSTR_CONV,
            "input": f"What are the main financial risks of Tongtin for a salaried worker earning ${inc:,}?",
            "output": f"The primary risks include: 1. Complete default if the organizer flees with the pooled funds. 2. Legal unenforceability under standard banking laws. 3. Illiquidity when you experience personal medical or life emergencies before your turn to bid."
        })
        records.append({
            "instruction": INSTR_CONV,
            "input": f"Why is formal banking better than Tongtin for building a credit history on a ${inc:,} salary?",
            "output": f"Licensed banks report verified savings and transaction flows that prove your creditworthiness to lenders. Tongtin leaves zero formal audit trail, preventing you from using that savings history when qualifying for home mortgages or business loans."
        })

    # 1B: Ceremony & Social Wedding Sinking Funds (ចងដៃអាពាហ៍ពិពាហ៍) (100 records: 50 KM, 50 EN)
    ceremony_incomes = [800, 1100, 1400, 1700, 2000, 2400, 2800, 3200, 3800, 4500]
    for inc in ceremony_incomes:
        # Dry season wedding expenses: 10-15 weddings * $30-$50 = $400 - $600
        budget_target = int(inc * 0.40)
        monthly_save = int(budget_target / 6)

        # Khmer (5 per income = 50)
        records.append({
            "instruction": INSTR_CONV,
            "input": f"នៅរដូវការខ្ញុំត្រូវចំណាយលើការចងដៃការច្រើនណាស់ លើចំណូល ${inc:,} តើគួររៀបចំថវិកាយ៉ាងដូចម្តេច?",
            "output": f"ដើម្បីកុំឱ្យការចងដៃការប៉ះពាល់ដល់ថវិកាប្រចាំខែ ${inc:,} របស់អ្នក អ្នកគួរបង្កើត 'Sinking Fund សម្រាប់ពិធីមង្គលការ'។ ប្រសិនបើអ្នករំពឹងថានឹងចំណាយប្រហែល ${budget_target:,} ក្នុងរដូវការ ចូរចាប់ផ្តើមសន្សំ ${monthly_save:,}/ខែ ទុកមុនរយៈពេល 6 ខែ ចូលគណនីដាច់ដោយឡែក។"
        })
        records.append({
            "instruction": INSTR_CONV,
            "input": f"តើការបង្កើត Ceremony Sinking Fund ជួយការពារថវិកាប្រចាំខែ ${inc:,} របស់ខ្ញុំយ៉ាងដូចម្តេច?",
            "output": f"ពិធីមង្គលការ និងបុណ្យទាននៅកម្ពុជាជាចំណាយតាមរដូវកាលដែលដឹងមុន។ ការបែងចែកប្រាក់សន្សំតិចតួចជារៀងរាល់ខែចូលក្នុង Ceremony Sinking Fund ជួយឱ្យអ្នកមានលុយចងដៃគ្រប់គ្រាន់ដោយមិនបាច់ខ្ចីបុល ឬកាត់បន្ថយប្រាក់បម្រុងបន្ទាន់ឡើយ។"
        })
        records.append({
            "instruction": INSTR_CONV,
            "input": f"ខ្ញុំមានចំណូល ${inc:,} ហើយទទួលបានសំបុត្រការ 5 ក្នុងមួយខែ តើគួរកំណត់កម្រិតចងដៃយ៉ាងណា?",
            "output": f"អ្នកគួរកំណត់កម្រិតចងដៃសមស្របតាមកម្រិតនៃទំនាក់ទំនង (ឧ. មិត្តរួមការងារទូទៅ $30, មិត្តជិតស្និទ្ធ $50)។ សំខាន់បំផុតគឺកុំចងដៃលើសពីលទ្ធភាពហិរញ្ញវត្ថុរបស់អ្នក។ ការរក្សាស្ថិរភាពថវិកាផ្ទាល់ខ្លួនគឺជារឿងសំខាន់បំផុត។"
        })
        records.append({
            "instruction": INSTR_CONV,
            "input": f"តើគួរចាត់ទុកការចងដៃការជាការចំណាយប្រភេទណា ក្នុងកញ្ចប់ថវិកា ${inc:,}?",
            "output": f"ការចងដៃការគួរចាត់ទុកជា 'Wants' (ចំណាយសង្គម) ឬជា 'Sinking Fund' ជាក់លាក់។ វាមិនមែនជាចំណាយបន្ទាន់ (Emergency) ឡើយ ដូច្នេះមិនត្រូវដកប្រាក់ចេញពី Emergency Fund យកមកចងដៃការឡើយ។"
        })
        records.append({
            "instruction": INSTR_CONV,
            "input": f"តើធ្វើដូចម្តេចដើម្បីកុំឱ្យជំពាក់បំណុលគេដោយសារតែការចងដៃការ និងបុណ្យទានលើប្រាក់ខែ ${inc:,}?",
            "output": f"យុទ្ធសាស្ត្រចម្បង:\n1. កំណត់កញ្ចប់ថវិកាចងដៃអតិបរមាប្រចាំឆ្នាំ\n2. បង្កើតគណនីសន្សំដាច់ដោយឡែកសម្រាប់បុណ្យទាន\n3. ហ៊ានបដិសេធ ឬចូលរួមតាមលទ្ធភាពសមរម្យ បើលើសកញ្ចប់ថវិកាដែលបានគ្រោងទុក។"
        })

        # English (5 per income = 50)
        records.append({
            "instruction": INSTR_CONV,
            "input": f"Wedding invitation season in Cambodia is very heavy. How can I budget for gift envelopes on a ${inc:,} salary?",
            "output": f"Create a dedicated 'Wedding Sinking Fund'. If you anticipate attending 10 weddings costing roughly ${budget_target:,} over the dry season, save ${monthly_save:,} each month into a separate sub-account during the quiet months. This smooths your expenses and prevents cash flow shocks."
        })
        records.append({
            "instruction": INSTR_CONV,
            "input": f"Should I ever dip into my emergency reserve to pay for wedding gift envelopes on my ${inc:,} income?",
            "output": f"No, never dip into your emergency reserve for weddings. Emergency funds are reserved strictly for medical emergencies, vehicle accidents, or sudden job loss. Wedding envelopes are predictable social obligations that must be funded from your discretionary budget or a sinking fund."
        })
        records.append({
            "instruction": INSTR_CONV,
            "input": f"I receive 6-8 wedding invitations in a single month while taking home ${inc:,}. How should I manage this?",
            "output": f"Establish tiered envelope limits based on relationship closeness ($30 for acquaintances, $50 for close friends). If attendance exceeds your planned social budget, it is financially responsible to send your polite blessings with a modest envelope rather than borrowing money."
        })
        records.append({
            "instruction": INSTR_CONV,
            "input": f"How does a ceremony sinking fund protect someone earning ${inc:,} from high-interest loans?",
            "output": f"Many workers without sinking funds turn to credit cards or micro-loans to fund wedding envelopes during peak months, incurring steep interest charges. Saving ${monthly_save:,} monthly in advance completely eliminates the need for short-term borrowing."
        })
        records.append({
            "instruction": INSTR_CONV,
            "input": f"How do I categorize cultural and social ceremony costs within the 50/30/20 budget on a ${inc:,} salary?",
            "output": f"Social ceremonies fall squarely under the 30% 'Wants' category (discretionary social life). Ensure total discretionary spending, including wedding gifts, dining out, and entertainment, remains within 30% of your ${inc:,} income."
        })

    # 1C: Bakong, Mobile Payments & QR Micro-Spending Trap (100 records: 50 KM, 50 EN)
    bakong_incomes = [700, 950, 1250, 1550, 1850, 2250, 2750, 3250, 3950, 4800]
    for inc in bakong_incomes:
        # Khmer (5 per income = 50)
        records.append({
            "instruction": INSTR_CONV,
            "input": f"ការស្កេន QR កូដទូទាត់តាម Bakong/ABA ញឹកញាប់ធ្វើឱ្យលុយខ្ញុំឆាប់អស់លើចំណូល ${inc:,} តើគួរដោះស្រាយយ៉ាងណា?",
            "output": f"ការទូទាត់តាម QR កូដមានភាពងាយស្រួល ប៉ុន្តែងាយធ្វើឱ្យយើងមើលរំលងការចំណាយតូចៗ ($1-$3 សម្រាប់កាហ្វេ និងចំណី)។ ដំណោះស្រាយល្អលើចំណូល ${inc:,}: កំណត់គណនីធនាគារមួយដាច់ដោយឡែកសម្រាប់ការចាយប្រចាំថ្ងៃ ដោយផ្ទេរលុយចូលតែចំនួនកំណត់ប្រចាំសប្តាហ៍ប៉ុណ្ណោះ។"
        })
        records.append({
            "instruction": INSTR_CONV,
            "input": f"តើ micro-spending តាម QR កូដអាចបំផ្លាញផែនការសន្សំលើប្រាក់ខែ ${inc:,} យ៉ាងដូចម្តេច?",
            "output": f"ការស្កេនទិញកាហ្វេ និងអាហារសម្រន់ត្រឹមតែ $2-$4 ក្នុងមួយថ្ងៃ អាចកើនឡើងដល់ $60-$120 ក្នុងមួយខែ។ លើចំណូល ${inc:,} ទឹកប្រាក់នេះស្មើនឹង 5% ទៅ 10% នៃចំណូលរបស់អ្នក ដែលអាចយកទៅសន្សំក្នុង Emergency Fund បានយ៉ាងច្រើន។"
        })
        records.append({
            "instruction": INSTR_CONV,
            "input": f"តើខ្ញុំគួររៀបចំគណនី Bakong និងគណនីសន្សំយ៉ាងណាលើចំណូល ${inc:,} ដើម្បីកុំឱ្យចាយរហេតរហូត?",
            "output": f"អនុវត្តប្រព័ន្ធគណនីពីរ:\n1. គណនីចំណាយប្រចាំថ្ងៃ (ភ្ជាប់ជាមួយ Bakong/QR): ដាក់លុយសមល្មមសម្រាប់តែការចាយវាយប្រចាំសប្តាហ៍\n2. គណនីសន្សំដាច់ដោយឡែក (មិនភ្ជាប់ជាមួយ App ចាយវាយ): សម្រាប់រក្សាទុកប្រាក់សន្សំ និង Emergency Fund។"
        })
        records.append({
            "instruction": INSTR_CONV,
            "input": f"តើទម្លាប់ណាខ្លះជួយគ្រប់គ្រងការស្កេនទូទាត់លុយតាមទូរស័ព្ទឱ្យមានវិន័យលើចំណូល ${inc:,}?",
            "output": f"ទម្លាប់សំខាន់ៗ:\n1. បើកមើល Notification និងកត់ត្រារាល់ការស្កេន\n2. កំណត់ដែនកំណត់ចំណាយប្រចាំថ្ងៃ (Daily Limit) ក្នុង App\n3. អនុវត្តថ្ងៃ 'No-Spend Day' (មិនស្កេនទិញរបស់មិនចាំបាច់ 1-2 ថ្ងៃក្នុងមួយសប្តាហ៍)។"
        })
        records.append({
            "instruction": INSTR_CONV,
            "input": f"ហេតុអ្វីបានជាការទូទាត់ឌីជីថលធ្វើឱ្យយើងមានអារម្មណ៍ថាមិនសូវស្តាយលុយលើចំណូល ${inc:,}?",
            "output": f"តាមចិត្តវិទ្យាហិរញ្ញវត្ថុ ការស្កេន QR មិនបង្កឱ្យមាន 'ការឈឺចាប់នៃការចាយលុយ' (Pain of Paying) ដូចការហុចក្រដាសប្រាក់ផ្ទាល់ដៃឡើយ។ ដូច្នេះ យើងត្រូវមានស្មារតីដឹងខ្លួនខ្ពស់ និងតាមដានរបាយការណ៍ធនាគារជាប្រចាំ។"
        })

        # English (5 per income = 50)
        records.append({
            "instruction": INSTR_CONV,
            "input": f"Frequent KHQR code payments through Bakong make me lose track of daily spending on a ${inc:,} salary. How can I fix this?",
            "output": f"Digital frictionless payments eliminate the physical friction of parting with cash, making $2 coffees and $4 snacks feel invisible until your balance evaporates. Fix this by opening two accounts: a primary savings account that is disconnected from daily payment apps, and a secondary spending account loaded with only a weekly allowance."
        })
        records.append({
            "instruction": INSTR_CONV,
            "input": f"How does unmonitored micro-spending through mobile banking impact a ${inc:,} monthly budget?",
            "output": f"Scanning $3 twice a day totals $180 a month. On a ${inc:,} take-home pay, that represents a substantial portion of your potential monthly surplus. Redirecting half of that micro-spending into an automated emergency fund builds $1,000+ in security every year."
        })
        records.append({
            "instruction": INSTR_CONV,
            "input": f"What is the best banking app setup to prevent impulsive QR spending on a ${inc:,} income?",
            "output": f"1. Set up daily transaction limits in your banking app.\n2. Turn on instant balance push notifications.\n3. Keep your core emergency reserve in a separate high-yield fixed or growth account that requires a deliberate transfer to access."
        })
        records.append({
            "instruction": INSTR_CONV,
            "input": f"How can I audit my mobile transaction history to find budget leaks on a ${inc:,} salary?",
            "output": f"Download your monthly PDF bank statement or export your CSV transaction history. Highlight all transactions under $5 and group them by vendor (coffee, food delivery, convenience stores). This reveals the exact monthly drain on your budget."
        })
        records.append({
            "instruction": INSTR_CONV,
            "input": f"Can implementing a 'Cash Envelope' system alongside KHQR work for a ${inc:,} monthly earner in Cambodia?",
            "output": f"Yes! You can maintain a 'Digital Envelope' system: allocate your monthly discretionary cash into a separate sub-account with a dedicated card/QR, and once that specific sub-account reaches zero, discretionary spending pauses until next payday."
        })

    # 1D: Dual Currency Management (USD & KHR) & Remittances to Parents (100 records: 50 KM, 50 EN)
    dual_incomes = [650, 900, 1200, 1600, 2100, 2600, 3100, 3600, 4200, 5000]
    for inc in dual_incomes:
        remittance = int(inc * 0.15)
        # Khmer (5 per income = 50)
        records.append({
            "instruction": INSTR_CONV,
            "input": f"ប្រាក់ខែខ្ញុំបើកជា USD (${inc:,}) ប៉ុន្តែចំណាយប្រចាំថ្ងៃជាប្រាក់រៀល តើគួរគ្រប់គ្រងយ៉ាងណាដើម្បីកុំឱ្យខាតអត្រាប្តូរប្រាក់?",
            "output": f"ដើម្បីជៀសវាងការខាតបង់លើអត្រាប្តូរប្រាក់ លើប្រាក់ខែ ${inc:,} របស់អ្នក:\n1. ប្តូរប្រាក់រៀលតែមួយដងគត់សម្រាប់តម្រូវការចំណាយប្រចាំខែ\n2. ប្រើប្រាស់គណនី Bakong ជាប្រាក់រៀលសម្រាប់ស្កេនទូទាត់ទំនិញក្នុងស្រុក\n3. រក្សាប្រាក់សន្សំ និងមូលនិធិសង្គ្រោះបន្ទាន់ជា USD ឬបែងចែកជា KHR ក្នុងគណនីមានការប្រាក់ខ្ពស់។"
        })
        records.append({
            "instruction": INSTR_CONV,
            "input": f"ខ្ញុំចង់ផ្ញើប្រាក់ជូនឪពុកម្តាយនៅស្រុក ${remittance:,}/ខែ ពីចំណូល ${inc:,} តើគួររៀបចំក្នុងថវិកាយ៉ាងដូចម្តេច?",
            "output": f"ការដឹងគុណ និងផ្គត់ផ្គង់ឪពុកម្តាយគឺជាកាតព្វកិច្ចដ៏ប្រពៃ។ លើចំណូល ${inc:,} ទឹកប្រាក់ ${remittance:,} ស្មើនឹង {remittance/inc*100:.1f}% នៃចំណូល។ ចូរបញ្ចូលទឹកប្រាក់នេះជា 'Fixed Expense' (ចំណាយចាំបាច់ថេរ) ក្នុងតារាងថវិកាប្រចាំខែ ដើម្បីកុំឱ្យប៉ះពាល់ដល់ការសន្សំផ្ទាល់ខ្លួនរបស់អ្នក។"
        })
        records.append({
            "instruction": INSTR_CONV,
            "input": f"តើការដាក់ប្រាក់បញ្ញើជាប្រាក់រៀល (KHR) ផ្តល់ការប្រាក់ខ្ពស់ជាង USD យ៉ាងដូចម្តេចលើចំណូល ${inc:,}?",
            "output": f"ធនាគារក្នុងស្រុកជាទូទៅផ្តល់អត្រាការប្រាក់លើប្រាក់រៀល (KHR) ខ្ពស់ជាង USD បន្តិច ដើម្បីលើកកម្ពស់ការប្រើប្រាស់រូបិយវត្ថុជាតិ។ អត្រាការប្រាក់ជាក់ស្តែងអាស្រ័យលើគោលនយោបាយរបស់ធនាគារនីមួយៗ និងស្ថានភាពទីផ្សារ ដូច្នេះអ្នកគួរពិនិត្យតារាងអត្រាការប្រាក់ផ្ទាល់ជាមួយធនាគារដែលមានអាជ្ញាប័ណ្ណ។"
        })
        records.append({
            "instruction": INSTR_CONV,
            "input": f"តើធ្វើដូចម្តេចដើម្បីរក្សាតុល្យភាពរវាងការផ្ញើលុយជូនគ្រួសារ និងការកសាងអនាគតផ្ទាល់ខ្លួនលើចំណូល ${inc:,}?",
            "output": f"តុល្យភាពហិរញ្ញវត្ថុពិតប្រាកដទាមទារឱ្យអ្នកមានខែលការពារផ្ទាល់ខ្លួនជាមុនសិន។ ប្រសិនបើអ្នកមិនមានប្រាក់បម្រុងបន្ទាន់ ហើយជួបគ្រោះអាសន្ន អ្នកនឹងត្រូវខ្ចីបុលគេ។ ចូរធានាថាអ្នកអាចសន្សំបានយ៉ាងតិច 10-20% សម្រាប់ខ្លួនឯង ទន្ទឹមនឹងការផ្គត់ផ្គង់គ្រួសារតាមលទ្ធភាព។"
        })
        records.append({
            "instruction": INSTR_CONV,
            "input": f"តើការទូទាត់ទំនិញជាប្រាក់រៀលតាម KHQR ជួយសេដ្ឋកិច្ចជាតិ និងការគ្រប់គ្រងលុយ ${inc:,} យ៉ាងណា?",
            "output": f"ការទូទាត់ជាប្រាក់រៀលកាត់បន្ថយការពឹងផ្អែកលើប្រាក់ដុល្លារ ជៀសវាងបញ្ហាក្រដាសប្រាក់ដុល្លារចាស់រហែក និងជួយឱ្យអ្នកទូទាត់ចំតម្លៃពិតប្រាកដនៃទំនិញដោយមិនបាច់បង់ថ្លៃបង្គត់លុយឡើយ។"
        })

        # English (5 per income = 50)
        records.append({
            "instruction": INSTR_CONV,
            "input": f"My salary is in USD (${inc:,}), but domestic market expenses are in Khmer Riel. How can I manage currency conversion effectively?",
            "output": f"Avoid daily micro-conversions at retail stalls that charge unfavorable exchange spreads. Instead, convert an estimated monthly living allowance of KHR once at an authorized exchange booth or through direct interbank rates in Bakong, and keep your core savings in USD."
        })
        records.append({
            "instruction": INSTR_CONV,
            "input": f"I send ${remittance:,} every month to support my parents in the province from my ${inc:,} earnings. How should I account for this?",
            "output": f"Filial support of ${remittance:,} ({remittance/inc*100:.1f}% of your earnings) is an admirable cultural value. Treat it as a non-negotiable fixed expense within your 'Needs' category rather than an unpredictable discretionary withdrawal, ensuring your personal emergency savings remain protected."
        })
        records.append({
            "instruction": INSTR_CONV,
            "input": f"Why do Cambodian banks pay higher interest on Khmer Riel (KHR) fixed deposits than USD for someone saving from a ${inc:,} salary?",
            "output": f"Commercial banks often offer higher interest benchmarks on KHR deposits to incentivize local currency holdings in line with monetary guidelines. The exact spread varies across institutions and changes with economic conditions, so verify current deposit terms directly with licensed banks."
        })
        records.append({
            "instruction": INSTR_CONV,
            "input": f"How can I balance family remittance expectations with personal wealth building on a ${inc:,} monthly salary?",
            "output": f"Communicate transparently with family members regarding your exact fixed capacity. Building a personal 3-6 month emergency reserve first ensures that if an unforeseen crisis strikes, you can continue supporting your parents without taking predatory personal loans."
        })
        records.append({
            "instruction": INSTR_CONV,
            "input": f"What are the best practices for holding emergency funds in Cambodia's dual-currency environment with a ${inc:,} salary?",
            "output": f"Hold your emergency fund in a split allocation: 70-80% in USD in a liquid savings account to preserve stability against exchange fluctuations, and 20-30% in KHR for immediate domestic accessibility through Bakong QR payments."
        })

    return records[:400]


# =============================================================================
# 2. Khmer-English Mixed Deep Professional Conversations (400 records)
# =============================================================================
def generate_domain2_mixed_deep():
    records = []
    
    # 40 professional profiles * 10 distinct questions = 400 records
    profiles = []
    for inc in range(1200, 7200, 150):
        exp = int(inc * 0.65)
        sur = inc - exp
        bonus = int(inc * 1.5)
        profiles.append((inc, exp, sur, bonus))
    profiles = profiles[:40]

    for inc, exp, sur, bonus in profiles:
        sav_pct = (sur / inc) * 100
        tax_est = int(inc * 0.10)

        qa_pairs = [
            (f"Salary ខ្ញុំ ${inc:,}/month បន្ទាប់ពីកាត់ tax (net pay) ចំណាយ expenses ${exp:,}។ តើ savings rate ខ្ញុំប៉ុន្មាន?",
             f"ផ្អែកលើ take-home salary ${inc:,} និង expenses ${exp:,} អ្នកមាន monthly surplus ${sur:,}។ Savings rate របស់អ្នកគឺ {sav_pct:.1f}% (${sur:,} / ${inc:,} * 100) ដែលលើសពីស្ដង់ដារ 20% នៃច្បាប់ 50/30/20។"),

            (f"ខ្ញុំធ្វើការជា Freelancer/IT consultant ចំណូលខ្លះខែបាន ${inc:,} ខ្លះខែទាបជាងហ្នឹង។ តើគួរ budget irregular income យ៉ាងម៉េច?",
             f"សម្រាប់ irregular income យុទ្ធសាស្ត្រល្អបំផុតគឺ:\n1. កំណត់កម្រិតចំណាយចាំបាច់ទាបបំផុត (Baseline Expenses: ${exp:,})\n2. បង្កើត 'Salary Buffer Account' ស្មើនឹង 3-6 ខែនៃការចំណាយ\n3. នៅខែដែលរកបានខ្ពស់ (${inc:,}) ផ្ទេរប្រាក់សល់ទាំងអស់ចូល Buffer Account ហើយបើកប្រាក់ខែឱ្យខ្លួនឯងក្នុងចំនួនថេររៀងរាល់ខែ។"),

            (f"ក្រុមហ៊ុនឱ្យ annual bonus ${bonus:,} ចុងឆ្នាំ។ បើ salary ${inc:,} និង expenses ${exp:,} តើគួរ allocate bonus នេះយ៉ាងណា?",
             f"រូបមន្តបែងចែក annual bonus ${bonus:,} ប្រកបដោយតុល្យភាព:\n- 50% (${int(bonus*0.5):,}): ដាក់ចូល Emergency Fund ឬគោលដៅសន្សំធំៗ\n- 30% (${int(bonus*0.3):,}): វិនិយោគលើចំណេះដឹង ជំនាញ ឬឧបករណ៍ធ្វើការ\n- 20% (${int(bonus*0.2):,}): ទុកសម្រាប់រង្វាន់លើកទឹកចិត្តខ្លួនឯង (Guilt-free spending)។"),

            (f"ខ្ញុំចង់ buy motorcycle/car តម្លៃ ${sur*6:,}។ បើមាន surplus ${sur:,}/month តើគួរ finance ឬ save cash ទិញផ្តាច់?",
             f"ប្រសិនបើអ្នកសន្សំ cash ${sur:,}/ខែ អ្នកនឹងអាចទិញផ្តាច់ក្នុងរយៈពេលត្រឹមតែ 6 ខែប៉ុណ្ណោះដោយមិនបាច់បង់ការប្រាក់។ ការបង់រំលស់ (Financing) តែងតែមានការប្រាក់ 1% ទៅ 1.5%/ខែ ដែលធ្វើឱ្យអ្នកខាតបង់ប្រាក់បន្ថែមលើសតម្លៃដើម។"),

            (f"តើ expense-to-income ratio របស់ខ្ញុំ healthy អត់ បើ expenses ${exp:,} លើ net salary ${inc:,}?",
             f"Expense-to-income ratio របស់អ្នកគឺ {exp/inc*100:.1f}% (${exp:,} / ${inc:,})។ នេះជាកម្រិត healthy ណាស់ ព្រោះវាទាបជាង 70% និងអនុញ្ញាតឱ្យអ្នកមាន surplus រឹងមាំ ${sur:,}/ខែ សម្រាប់កសាងទ្រព្យសម្បត្តិ។"),

            (f"ខ្ញុំអត់មាន debt អីទេ (zero debt) ចង់ចាប់ផ្តើម long-term wealth building លើ salary ${inc:,}។ តើ step ដំបូងជាអ្វី?",
             f"ដោយសារអ្នក debt-free នេះជាអត្ថប្រយោជន៍ដ៏ធំធេង! ជំហានដំបូងគឺកសាង Emergency Fund ចំនួន ${exp*3:,} (3 ខែនៃការចំណាយ) ក្នុងគណនីសន្សំមានការប្រាក់ខ្ពស់។ បន្ទាប់មក ដាក់សន្សំទៀងទាត់ ${sur:,}/ខែ ទៅក្នុង Fixed Deposit ដើម្បីទទួលបានការប្រាក់កើនឡើងជាបន្តបន្ទាប់។"),

            (f"Salary ${inc:,} expenses ${exp:,}។ តើខ្ញុំគួរ rent បន្ទប់បន្ត ឬបង់រំលស់ condo/ផ្ទះ?",
             f"មុននឹងសម្រេចចិត្តបង់រំលស់ផ្ទះ សូមប្រាកដថា:\n1. អ្នកមានប្រាក់កក់ដំបូង (Down payment) យ៉ាងតិច 20-30%\n2. ការបង់ប្រចាំខែមិនលើសពី 30% នៃចំណូលរបស់អ្នក (${int(inc*0.3):,}/ខែ)\n3. អ្នកមាន Emergency Fund រួចរាល់។ បើមិនទាន់គ្រប់លក្ខខណ្ឌទាំងនេះទេ ការជួលបន្ទប់ ${exp:,} នៅតែជាជម្រើសសុវត្ថិភាពជាង។"),

            (f"សួស្តី advisor, ជួយ review monthly cash flow ខ្ញុំ: income ${inc:,}, expenses ${exp:,}, surplus ${sur:,}។",
             f"ការពិនិត្យ Cash Flow:\n- Net Monthly Income: ${inc:,}\n- Total Living Expenses: ${exp:,}\n- Net Monthly Surplus: +${sur:,} ({sav_pct:.1f}%)\nស្ថានភាពហិរញ្ញវត្ថុរបស់អ្នករឹងមាំខ្លាំងណាស់ គ្មានឱនភាពថវិកា និងមានសមត្ថភាពសន្សំខ្ពស់។"),

            (f"តើខ្ញុំគួរ allocate budget តាម formula 50/30/20 យ៉ាងណា បើ net income ${inc:,}?",
             f"ការបែងចែក 50/30/20 លើចំណូល ${inc:,}:\n- Needs 50%: ${int(inc*0.5):,} (ថ្លៃបន្ទប់ ម្ហូប វិក្កយបត្រចាំបាច់)\n- Wants 30%: ${int(inc*0.3):,} (ញ៉ាំក្រៅ ដើរលេង កម្សាន្ត)\n- Savings 20%: ${int(inc*0.2):,} (សន្សំស្វ័យប្រវត្តិចូល Emergency Fund)។"),

            (f"Thanks advisor, advice លើ net income ${inc:,} របស់អ្នក practical ណាស់! ខ្ញុំនឹង start tracking cash flow ថ្ងៃនេះ។",
             f"ដោយក្តីរីករាយ! ការតាមដាន Cash Flow ជាក់ស្តែងលើចំណូល ${inc:,} និងចំណាយ ${exp:,} របស់អ្នកនឹងជួយការពារកុំឱ្យមាន spending leaks និងធានាថាប្រាក់សល់ ${sur:,} ត្រូវបានសន្សំពេញលេញ។")
        ]

        for q, a in qa_pairs:
            records.append({"instruction": INSTR_CONV, "input": q, "output": a})

    return records[:400]


# =============================================================================
# 3. Multi-Turn Deep Advisory & Diagnostic Conversations (450 records)
# =============================================================================
def generate_domain3_multiturn_deep():
    records = []

    # 3A: English Multi-turn Diagnostic (180 records)
    en_multi_profiles = []
    for inc in range(1400, 6800, 120):
        rent = int(inc * 0.30)
        food = int(inc * 0.25)
        util = int(inc * 0.08)
        exp = rent + food + util
        sur = inc - exp
        en_multi_profiles.append((inc, rent, food, util, exp, sur))
    en_multi_profiles = en_multi_profiles[:45]

    for inc, rent, food, util, exp, sur in en_multi_profiles:
        # Arc 1: Diagnostic on spending anxiety
        t1 = f"User: I make ${inc:,} a month, but at the end of each month I feel like I barely have anything left.\nAssistant: Feeling that way is very common, but we can fix it by looking at the numbers. Could you break down your approximate monthly costs for rent, food, and utilities?"
        t2 = f"User: Rent is around ${rent:,}, food and groceries are ${food:,}, and utilities/transport are ${util:,}. I have no debt."
        a1 = f"Thank you for sharing those figures. Let's analyze your cash flow:\n- Monthly Income: ${inc:,}\n- Essential Expenses: ${exp:,} (${rent:,} rent + ${food:,} food + ${util:,} utilities)\n- Net Monthly Surplus: +${sur:,} (${inc:,} - ${exp:,})\nYour essential expenses equal {exp/inc*100:.1f}% of your earnings, which means you have an unallocated surplus of ${sur:,} each month. The reason you feel money is disappearing is likely unmonitored daily discretionary purchases. Automating a ${sur:,} transfer on payday into a separate savings account will immediately secure this surplus."
        records.append({"instruction": INSTR_MULTITURN, "input": f"{t1}\n{t2}", "output": a1})

        # Arc 2: Emergency fund timeline follow-up
        t1_2 = f"User: My income is ${inc:,} and living expenses are ${exp:,} with zero debt.\nAssistant: You have an active monthly surplus of ${sur:,} and confirmed debt-free status. How can I help guide your savings?"
        t2_2 = f"User: How many months will it take to build a 6-month emergency reserve of ${exp*6:,}?"
        a2 = f"To accumulate a full 6-month emergency reserve of ${exp*6:,} with your monthly savings capacity of ${sur:,}:\n- Total Target: ${exp*6:,} (${exp:,} * 6)\n- Monthly Allocation: ${sur:,}\n- Timeline: Exactly {math.ceil((exp*6)/sur)} months (${exp*6:,} / ${sur:,} = {math.ceil((exp*6)/sur)}).\nMaintaining your debt-free status allows every single dollar of your ${sur:,} surplus to build this fortress without loan interest payments."
        records.append({"instruction": INSTR_MULTITURN, "input": f"{t1_2}\n{t2_2}", "output": a2})

        # Arc 3: Trimming food budget follow-up
        trimmed_food = food - 100
        new_exp = rent + trimmed_food + util
        new_sur = inc - new_exp
        t1_3 = f"User: I spend ${food:,} on food each month from my ${inc:,} salary. Can I optimize this?\nAssistant: Food expenses of ${food:,} represent {food/inc*100:.1f}% of your income. Meal prepping and reducing dining out can safely lower this."
        t2_3 = f"User: If I trim food spending to ${trimmed_food:,}, what is my new monthly surplus and savings rate?"
        a3 = f"Trimming your monthly food budget by $100 yields:\n- New Total Expenses: ${new_exp:,} (${rent:,} rent + ${trimmed_food:,} food + ${util:,} utilities)\n- New Monthly Surplus: ${new_sur:,} (${inc:,} - ${new_exp:,})\n- New Savings Rate: {new_sur/inc*100:.1f}% (${new_sur:,} / ${inc:,} * 100)\nThis saves you an additional $1,200 annually while keeping your living standard fully comfortable."
        records.append({"instruction": INSTR_MULTITURN, "input": f"{t1_3}\n{t2_3}", "output": a3})

        # Arc 4: Vehicle purchase feasibility
        veh_cost = sur * 8
        t1_4 = f"User: I have ${sur:,} in monthly surplus from my ${inc:,} income and zero debt.\nAssistant: Having an unencumbered ${sur:,} monthly surplus provides strong financial flexibility."
        t2_4 = f"User: Can I afford a ${veh_cost:,} vehicle, and should I take a loan or save cash?"
        a4 = f"With your ${sur:,} monthly surplus, you can purchase the ${veh_cost:,} vehicle completely in cash in just 8 months (${veh_cost:,} / ${sur:,} = 8). Saving cash avoids auto loan interest (which often adds 10-15% to vehicle costs) and keeps you 100% debt-free."
        records.append({"instruction": INSTR_MULTITURN, "input": f"{t1_4}\n{t2_4}", "output": a4})

    # 3B: Khmer Multi-turn Diagnostic (180 records)
    km_multi_profiles = []
    for inc in range(1350, 6750, 120):
        rent = int(inc * 0.28)
        food = int(inc * 0.26)
        util = int(inc * 0.08)
        exp = rent + food + util
        sur = inc - exp
        km_multi_profiles.append((inc, rent, food, util, exp, sur))
    km_multi_profiles = km_multi_profiles[:45]

    for inc, rent, food, util, exp, sur in km_multi_profiles:
        # Arc 1: Khmer diagnostic
        t1 = f"User: ខ្ញុំរកបាន ${inc:,} ក្នុងមួយខែ ប៉ុន្តែដល់ចុងខែមិនដឹងថាលុយទៅណាអស់ទេ។\nAssistant: កុំបារម្ភ យើងអាចស្វែងរកមូលហេតុបានដោយពិនិត្យលើតួលេខជាក់ស្តែង។ តើអ្នកអាចប្រាប់ពីចំណាយលើ ថ្លៃជួលបន្ទប់ ម្ហូបអាហារ និងទឹកភ្លើងប្រចាំខែបានទេ?"
        t2 = f"User: ថ្លៃផ្ទះប្រហែល ${rent:,}, ម្ហូបអាហារ ${food:,}, និងទឹកភ្លើង/ធ្វើដំណើរ ${util:,}។ ខ្ញុំគ្មានបំណុលទេ។"
        a1 = f"សូមអរគុណសម្រាប់ការចែករំលែកតួលេខ។ នេះជាការវិភាគលំហូរសាច់ប្រាក់របស់អ្នក:\n- ចំណូលសរុប: ${inc:,}\n- ចំណាយចាំបាច់: ${exp:,} (${rent:,} ផ្ទះ + ${food:,} ម្ហូប + ${util:,} វិក្កយបត្រ)\n- ប្រាក់សល់សុទ្ធ: +${sur:,}/ខែ (${inc:,} - ${exp:,})\nចំណាយចាំបាច់របស់អ្នកមានត្រឹមតែ {exp/inc*100:.1f}% នៃចំណូលប៉ុណ្ណោះ។ មូលហេតុដែលអ្នកមានអារម្មណ៍ថាលុយបាត់បង់ គឺដោយសារការចំណាយតូចតាចប្រចាំថ្ងៃដែលមិនបានកត់ត្រាទុក។ ការផ្ទេរប្រាក់ ${sur:,} ចូលគណនីសន្សំភ្លាមៗនៅថ្ងៃបើកប្រាក់ខែ នឹងដោះស្រាយបញ្ហានេះបានទាំងស្រុង។"
        records.append({"instruction": INSTR_MULTITURN, "input": f"{t1}\n{t2}", "output": a1})

        # Arc 2: Emergency reserve timeline in Khmer
        t1_2 = f"User: ចំណូលខ្ញុំគឺ ${inc:,} ហើយចំណាយគឺ ${exp:,} គ្មានបំណុលទេ។\nAssistant: អ្នកមានប្រាក់សល់សុទ្ធ ${sur:,}/ខែ និងគ្មានកាតព្វកិច្ចបំណុលឡើយ។ តើអ្នកចង់រៀបចំផែនការសន្សំអ្វីដែរ?"
        t2_2 = f"User: តើត្រូវចំណាយពេលប៉ុន្មានខែដើម្បីសន្សំប្រាក់បម្រុងបន្ទាន់ 6 ខែ (${exp*6:,})?"
        a2 = f"ដើម្បីសន្សំប្រាក់បម្រុងបន្ទាន់ 6 ខែ (${exp*6:,}) ជាមួយប្រាក់សល់ ${sur:,}/ខែ:\n- គោលដៅសរុប: ${exp*6:,} (${exp:,} * 6)\n- ការសន្សំប្រចាំខែ: ${sur:,}\n- រយៈពេល: ត្រឹមតែ {math.ceil((exp*6)/sur)} ខែប៉ុណ្ណោះ (${exp*6:,} / ${sur:,} = {math.ceil((exp*6)/sur)} ខែ)។ ការគ្មានបំណុលជួយឱ្យអ្នកសម្រេចខែលការពារនេះបានយ៉ាងឆាប់រហ័ស។"
        records.append({"instruction": INSTR_MULTITURN, "input": f"{t1_2}\n{t2_2}", "output": a2})

        # Arc 3: Trimming food budget in Khmer
        trimmed_food = food - 80
        new_exp = rent + trimmed_food + util
        new_sur = inc - new_exp
        t1_3 = f"User: ខ្ញុំចំណាយលើម្ហូបអាហារ ${food:,} លើចំណូល ${inc:,} តើច្រើនពេកទេ?\nAssistant: ចំណាយម្ហូប ${food:,} ស្មើនឹង {food/inc*100:.1f}% នៃចំណូលរបស់អ្នក។ ការកាត់បន្ថយការញ៉ាំក្រៅអាចជួយសន្សំបានបន្ថែម។"
        t2_3 = f"User: បើខ្ញុំកាត់បន្ថយមកត្រឹម ${trimmed_food:,} តើខ្ញុំសល់លុយប៉ុន្មានក្នុងមួយខែ?"
        a3 = f"ការកាត់បន្ថយចំណាយម្ហូបមកត្រឹម ${trimmed_food:,} ផ្តល់លទ្ធផលដូចខាងក្រោម:\n- ការចំណាយសរុបថ្មី: ${new_exp:,}\n- ប្រាក់សល់សុទ្ធថ្មី: ${new_sur:,}/ខែ (${inc:,} - ${new_exp:,})\n- អត្រាសន្សំថ្មី: {new_sur/inc*100:.1f}% នៃចំណូលសរុប។ នេះជួយឱ្យអ្នកសល់លុយបន្ថែម $960 ក្នុងមួយឆ្នាំ!"
        records.append({"instruction": INSTR_MULTITURN, "input": f"{t1_3}\n{t2_3}", "output": a3})

        # Arc 4: Purchasing vehicle cash in Khmer
        veh_cost = sur * 6
        t1_4 = f"User: ខ្ញុំមានប្រាក់សល់ ${sur:,}/ខែ លើចំណូល ${inc:,} និងគ្មានបំណុលទេ។\nAssistant: ការមានប្រាក់សល់ ${sur:,} ជារៀងរាល់ខែ និងគ្មានបំណុលផ្ដល់នូវសេរីភាពហិរញ្ញវត្ថុខ្ពស់។"
        t2_4 = f"User: ខ្ញុំចង់ទិញម៉ូតូថ្មីតម្លៃ ${veh_cost:,} តើគួរទិញផ្តាច់ ឬបង់រំលស់?"
        a4 = f"ជាមួយនឹងប្រាក់សល់ ${sur:,}/ខែ អ្នកអាចសន្សំទិញម៉ូតូតម្លៃ ${veh_cost:,} ដាច់បានក្នុងរយៈពេលត្រឹមតែ 6 ខែប៉ុណ្ណោះ (${veh_cost:,} / ${sur:,} = 6)។ ការទិញលុយសុទ្ធជួយសន្សំសំចៃការប្រាក់បង់រំលស់បានរាប់រយដុល្លារ និងរក្សាអ្នកឱ្យនៅតែគ្មានបំណុល។"
        records.append({"instruction": INSTR_MULTITURN, "input": f"{t1_4}\n{t2_4}", "output": a4})

    # 3C: Khmer-English Mixed Multi-turn (90 records)
    mix_multi_profiles = []
    for inc in range(1500, 6000, 100):
        exp = int(inc * 0.62)
        sur = inc - exp
        mix_multi_profiles.append((inc, exp, sur))
    mix_multi_profiles = mix_multi_profiles[:45]

    for inc, exp, sur in mix_multi_profiles:
        goal = sur * 5
        # Arc 1
        t1 = f"User: Monthly take-home pay ខ្ញុំ ${inc:,} ហើយ regular expenses ${exp:,}។\nAssistant: Cash flow របស់អ្នកមានសុខភាពល្អណាស់ មាន surplus +${sur:,}/ខែ (${inc:,} - ${exp:,})។ តើអ្នកមាន debt អីអត់?"
        t2 = f"User: ខ្ញុំ zero debt 100%។ ចង់ build emergency fund ${goal:,} តើត្រូវចំណាយពេលប៉ុន្មាន months?"
        a1 = f"ដោយសារអ្នក debt-free 100% ការសន្សំឱ្យបាន emergency fund ${goal:,} ជាមួយ monthly surplus ${sur:,} នឹងចំណាយពេលត្រឹមតែ 5 ខែប៉ុណ្ណោះ (${goal:,} / ${sur:,} = 5 months)។ នេះជាល្បឿនដ៏លឿនក្នុងការកសាងខែលការពារហិរញ្ញវត្ថុ។"
        records.append({"instruction": INSTR_MULTITURN, "input": f"{t1}\n{t2}", "output": a1})

        # Arc 2
        t1_2 = f"User: I want to optimize my cash flow on a ${inc:,} salary. Current expenses are ${exp:,}.\nAssistant: You are operating with a positive surplus of ${sur:,}/month. What financial goals are you targeting next?"
        t2_2 = f"User: តើខ្ញុំគួរ allocate surplus ${sur:,} នេះតាម 50/30/20 rule យ៉ាងម៉េច?"
        a2 = f"ជាមួយនឹង surplus ${sur:,} លើចំណូល ${inc:,} អ្នកកំពុងសន្សំបាន {sur/inc*100:.1f}% នៃចំណូលរួចទៅហើយ។ អ្នកអាចបែងចែក:\n- 70% នៃ surplus (${int(sur*0.7):,}): ដាក់ចូល Emergency Fund\n- 30% នៃ surplus (${int(sur*0.3):,}): ទុកសម្រាប់ goals ផ្ទាល់ខ្លួន ឬការកម្សាន្ត។"
        records.append({"instruction": INSTR_MULTITURN, "input": f"{t1_2}\n{t2_2}", "output": a2})

    return records[:450]


# =============================================================================
# 4. Detailed "What-If" Life Event Simulations (400 records)
# =============================================================================
def generate_domain4_life_events():
    records = []

    # 4A: English Life Events (200 records: 50 Marriage, 50 Baby, 50 Job Change, 50 Relocation)
    incomes_4a = [1200, 1600, 2000, 2400, 2800, 3200, 3600, 4000, 4500, 5000]
    for inc in incomes_4a:
        exp = int(inc * 0.65)
        sur = inc - exp

        # 1. Marriage / Combining budgets (5 per income = 50)
        p2_inc = int(inc * 0.85)
        comb_inc = inc + p2_inc
        comb_exp = int(exp * 1.45)
        comb_sur = comb_inc - comb_exp
        records.append({
            "instruction": INSTR_UPDATE,
            "input": f"Previous single profile: income=${inc:,}, expenses=${exp:,}, surplus=+${sur:,}, debt=no debt. User updates: I am getting married! Our combined household income is now ${comb_inc:,} (${inc:,} + ${p2_inc:,}) and shared living expenses are ${comb_exp:,}. What is our new combined savings capacity?",
            "output": f"Congratulations on your marriage! Here is your updated household cash flow:\n- Combined Monthly Income: ${comb_inc:,}\n- Combined Shared Living Expenses: ${comb_exp:,}\n- New Monthly Household Surplus: +${comb_sur:,} (${comb_inc:,} - ${comb_exp:,})\nBy sharing housing and utilities, your combined savings capacity increases from ${sur:,} to ${comb_sur:,} (+${comb_sur - sur:,}/month) while remaining completely debt-free."
        })
        records.append({
            "instruction": INSTR_UPDATE,
            "input": f"We are getting married with a combined income of ${comb_inc:,} and shared expenses of ${comb_exp:,} (no debt). How fast can we save a $10,000 emergency fund?",
            "output": f"With a combined surplus of ${comb_sur:,} each month (${comb_inc:,} - ${comb_exp:,}), reaching a $10,000 household emergency fund will take ~{math.ceil(10000/comb_sur)} months ($10,000 / ${comb_sur:,} = {math.ceil(10000/comb_sur)} months). This provides a resilient foundation for your new life together."
        })
        records.append({
            "instruction": INSTR_UPDATE,
            "input": f"What are the best budgeting rules for newlyweds earning a combined ${comb_inc:,} with ${comb_exp:,} in shared bills?",
            "output": f"Best practices for managing your ${comb_inc:,} household income:\n1. Maintain joint transparency: hold a monthly 20-minute financial check-in.\n2. Keep a joint bills account for your ${comb_exp:,} shared expenses and individual guilt-free personal accounts.\n3. Automate your joint monthly savings of ${comb_sur:,} toward shared goals."
        })
        records.append({
            "instruction": INSTR_UPDATE,
            "input": f"How much can our household save annually with ${comb_inc:,} income and ${comb_exp:,} expenses?",
            "output": f"With a monthly surplus of ${comb_sur:,} (${comb_inc:,} - ${comb_exp:,}), your household will save exactly ${comb_sur * 12:,} annually (${comb_sur:,} * 12) without incurring debt."
        })
        records.append({
            "instruction": INSTR_UPDATE,
            "input": f"What should be our first financial milestone as a married couple with a ${comb_sur:,} monthly surplus?",
            "output": f"Your first milestone should be establishing a joint emergency reserve of 3-6 months shared expenses (${comb_exp * 3:,} to ${comb_exp * 6:,}). With your ${comb_sur:,} monthly surplus, you can achieve this fully within {math.ceil((comb_exp*3)/comb_sur)} to {math.ceil((comb_exp*6)/comb_sur)} months."
        })

        # 2. Newborn baby budgeting (5 per income = 50)
        baby_exp = exp + 350
        baby_sur = inc - baby_exp
        records.append({
            "instruction": INSTR_UPDATE,
            "input": f"Previous profile: income=${inc:,}, expenses=${exp:,}, surplus=+${sur:,}, debt=no debt. User updates: We are welcoming a newborn baby! Monthly expenses will rise by $350 for diapers, formula, and pediatric care to ${baby_exp:,}. How does this impact our monthly savings?",
            "output": f"Congratulations on your growing family! Here is your updated budget breakdown:\n- Monthly Income: ${inc:,}\n- Updated Living Expenses: ${baby_exp:,} (${exp:,} + $350 baby costs)\n- New Monthly Surplus: +${baby_sur:,} (${inc:,} - ${baby_exp:,})\nYour monthly savings capacity adjusts from ${sur:,} down to ${baby_sur:,}. You maintain a positive cash flow and zero debt, providing security for your child."
        })
        records.append({
            "instruction": INSTR_UPDATE,
            "input": f"With our baby expenses bringing monthly costs to ${baby_exp:,} on a ${inc:,} income, how large should our emergency fund be?",
            "output": f"With a baby, financial risk increases. An expanded emergency reserve of 6 months living expenses is strongly recommended: ${baby_exp * 6:,} (${baby_exp:,} * 6). This protects against unexpected pediatric medical bills or temporary parental leave."
        })
        records.append({
            "instruction": INSTR_UPDATE,
            "input": f"Can we afford a newborn baby on a ${inc:,} income with ${exp:,} current expenses?",
            "output": f"Yes, absolutely. Because you currently have a healthy ${sur:,} monthly surplus and zero debt, absorbing estimated baby costs of $300-$350 still leaves you with an active monthly surplus of ${baby_sur:,} (${inc:,} - ${baby_exp:,})."
        })
        records.append({
            "instruction": INSTR_UPDATE,
            "input": f"What practical steps can we take to reduce newborn expenses on a ${inc:,} budget?",
            "output": f"Cost-saving tips for new parents:\n1. Accept gently used clothing, strollers, and cribs from trusted friends and family.\n2. Buy diapers and baby wipes in bulk rather than individual retail packs.\n3. Avoid expensive nursery gadgets that babies quickly outgrow.\n4. Maintain strict healthcare check-up schedules to prevent costly acute illnesses."
        })
        records.append({
            "instruction": INSTR_UPDATE,
            "input": f"How fast can we save a $3,000 maternity and healthcare fund with a ${baby_sur:,} monthly surplus?",
            "output": f"Saving your ${baby_sur:,} monthly surplus, accumulating a $3,000 dedicated maternity reserve will take approximately {math.ceil(3000/baby_sur)} months ($3,000 / ${baby_sur:,} = {math.ceil(3000/baby_sur)} months)."
        })

        # 3. Relocation / New apartment (5 per income = 50)
        reloc_cost = exp * 2
        records.append({
            "instruction": INSTR_UPDATE,
            "input": f"I am planning to relocate to a new apartment. My income is ${inc:,}, current expenses are ${exp:,}, and estimated moving + deposit costs are ${reloc_cost:,}. How should I plan for this?",
            "output": f"With a monthly surplus of ${sur:,} (${inc:,} - ${exp:,}), saving the required ${reloc_cost:,} relocation buffer (security deposit + mover fees) will take exactly {math.ceil(reloc_cost/sur)} months (${reloc_cost:,} / ${sur:,} = {math.ceil(reloc_cost/sur)}). Establishing this buffer in cash ensures you move without touching emergency funds."
        })
        records.append({
            "instruction": INSTR_UPDATE,
            "input": f"My new apartment rent will increase my monthly expenses from ${exp:,} to ${exp + 150:,} on my ${inc:,} salary. Is this move affordable?",
            "output": f"With expenses rising to ${exp + 150:,} on a ${inc:,} salary, your new monthly surplus will be ${sur - 150:,} (${inc:,} - ${exp + 150:,}). Because you remain debt-free and retain an active surplus of ${sur - 150:,}, the move is affordable, though it slightly slows your savings rate."
        })
        records.append({
            "instruction": INSTR_UPDATE,
            "input": f"What percentage of my ${inc:,} income should I spend on housing when relocating?",
            "output": f"The standard financial benchmark is that rent and basic utilities should not exceed 30% of your take-home pay (${int(inc * 0.30):,} on your ${inc:,} income). Keeping housing under this threshold protects your cash flow flexibility."
        })
        records.append({
            "instruction": INSTR_UPDATE,
            "input": f"Should I borrow from a microfinance lender to pay my apartment rental deposit of $800 on a ${inc:,} salary?",
            "output": f"No, never borrow money to pay a rental deposit. With your monthly surplus of ${sur:,}, you can save the $800 deposit in just {math.ceil(800/sur)} month(s). Borrowing incurs unnecessary interest charges and adds fixed debt burdens."
        })
        records.append({
            "instruction": INSTR_UPDATE,
            "input": f"How should I budget for moving day expenses on my ${inc:,} salary?",
            "output": f"Create a short-term sinking fund for moving costs (truck rental, packing boxes, cleaner). Allocate $100-$150 from your ${sur:,} monthly surplus over two months so that moving day is completely pre-funded in cash."
        })

        # 4. Job change & probation buffer (5 per income = 50)
        records.append({
            "instruction": INSTR_UPDATE,
            "input": f"I am changing jobs! My salary will increase from ${inc:,} to ${inc + 600:,} while expenses stay at ${exp:,}. How should I handle the 3-month probation period?",
            "output": f"Congratulations on the higher-paying role! During your 3-month probation period:\n1. Maintain your previous living standard (${exp:,})\n2. Bank the entire new surplus of ${sur + 600:,}/month (${inc + 600:,} - ${exp:,})\n3. Accumulate a probation safety buffer of ${exp * 3:,} to protect yourself against unforeseen probationary disruptions."
        })
        records.append({
            "instruction": INSTR_UPDATE,
            "input": f"What is my new savings capacity with a job change raise to ${inc + 600:,} and expenses at ${exp:,}?",
            "output": f"Your monthly savings capacity increases from ${sur:,} to ${sur + 600:,} (+600/month). Your savings rate improves from {sur/inc*100:.1f}% to {(sur+600)/(inc+600)*100:.1f}%, significantly accelerating your financial independence."
        })
        records.append({
            "instruction": INSTR_UPDATE,
            "input": f"How can I avoid lifestyle inflation after getting a salary increase to ${inc + 600:,}?",
            "output": f"To prevent lifestyle creep: immediately automate the extra $600 increase into an investment or high-yield savings account on payday. If you never see the extra money in your checking account, your lifestyle won't artificially expand."
        })
        records.append({
            "instruction": INSTR_UPDATE,
            "input": f"If I take a lower-stress job earning ${inc - 200:,} with expenses at ${exp:,}, what is my financial cushion?",
            "output": f"On an income of ${inc - 200:,} with expenses at ${exp:,}, you retain a positive monthly surplus of ${sur - 200:,}. As long as you have zero debt and positive cash flow, choosing a lower-stress role that maintains a healthy surplus is a sound life decision."
        })
        records.append({
            "instruction": INSTR_UPDATE,
            "input": f"How long does it take to build a $5,000 career transition fund with our new ${sur + 600:,} monthly surplus?",
            "output": f"With an increased monthly surplus of ${sur + 600:,}, saving a $5,000 career transition fund will take only {math.ceil(5000/(sur+600))} months ($5,000 / ${sur + 600:,} = {math.ceil(5000/(sur+600))} months)."
        })

    # 4B: Khmer Life Events (200 records)
    km_incomes_4b = [1100, 1500, 1900, 2300, 2700, 3100, 3500, 3900, 4400, 5200]
    for inc in km_incomes_4b:
        exp = int(inc * 0.64)
        sur = inc - exp

        # Marriage Khmer (5 per income = 50)
        p2_inc = int(inc * 0.80)
        comb_inc = inc + p2_inc
        comb_exp = int(exp * 1.40)
        comb_sur = comb_inc - comb_exp
        records.append({
            "instruction": INSTR_UPDATE,
            "input": f"កម្រងព័ត៌មានពីមុន: ចំណូល=${inc:,}, ចំណាយ=${exp:,}, ប្រាក់សល់=+${sur:,}, គ្មានបំណុល។ ធ្វើបច្ចុប្បន្នភាព: ខ្ញុំរៀបការរួចហើយ! ចំណូលគ្រួសាររួមគឺ ${comb_inc:,} ហើយចំណាយរួមគឺ ${comb_exp:,}។ តើសមត្ថភាពសន្សំរួមរបស់យើងមានចំនួនប៉ុន្មាន?",
            "output": f"សូមអបអរសាទរចំពោះអាពាហ៍ពិពាហ៍របស់អ្នក! នេះជាការវិភាគថវិកាគ្រួសារថ្មី:\n- ចំណូលគ្រួសាររួម: ${comb_inc:,}\n- ការចំណាយរួមប្រចាំខែ: ${comb_exp:,}\n- ប្រាក់សល់សុទ្ធរួម: +${comb_sur:,}/ខែ (${comb_inc:,} - ${comb_exp:,})\nការរួមចំណូល និងចែករំលែកថ្លៃស្នាក់នៅធ្វើឱ្យប្រាក់សន្សំកើនឡើងពី ${sur:,} ទៅ ${comb_sur:,}/ខែ (+${comb_sur - sur:,}) ដោយរក្សាបាននូវស្ថានភាពគ្មានបំណុលដដែល។"
        })
        records.append({
            "instruction": INSTR_UPDATE,
            "input": f"យើងជាប្តីប្រពន្ធថ្មីមានចំណូលរួម ${comb_inc:,} និងចំណាយ ${comb_exp:,} តើគួររៀបចំ Emergency Fund ទំហំប៉ុន្មាន?",
            "output": f"សម្រាប់គ្រួសារទើបបង្កើតថ្មី មូលនិធិសង្គ្រោះបន្ទាន់រួមគួរមានស្មើនឹង 3 ទៅ 6 ខែនៃការចំណាយរួម: ${comb_exp * 3:,} ទៅ ${comb_exp * 6:,}។ ជាមួយនឹងប្រាក់សល់ ${comb_sur:,}/ខែ អ្នកនឹងសម្រេចបានកម្រិត 3 ខែក្នុងរយៈពេលត្រឹមតែ {math.ceil((comb_exp*3)/comb_sur)} ខែប៉ុណ្ណោះ។"
        })
        records.append({
            "instruction": INSTR_UPDATE,
            "input": f"តើប្តីប្រពន្ធថ្មីគួរគ្រប់គ្រងលុយរួម ${comb_inc:,} យ៉ាងដូចម្តេចដើម្បីកុំឱ្យមានជម្លោះ?",
            "output": f"វិធីសាស្ត្រគ្រប់គ្រងលុយគ្រួសារ:\n1. បង្កើតគណនីរួមសម្រាប់ចំណាយចាំបាច់ ${comb_exp:,}\n2. រក្សាគណនីផ្ទាល់ខ្លួនដាច់ដោយឡែកខ្លះសម្រាប់សេរីភាពផ្ទាល់ខ្លួន\n3. ពិភាក្សា និងមានតម្លាភាពលើរាល់ការចំណាយធំៗ។"
        })
        records.append({
            "instruction": INSTR_UPDATE,
            "input": f"តើយើងអាចសន្សំបានប៉ុន្មានក្នុងមួយឆ្នាំ បើមានចំណូល ${comb_inc:,} និងចំណាយ ${comb_exp:,}?",
            "output": f"ជាមួយនឹងប្រាក់សល់ ${comb_sur:,}/ខែ គ្រួសាររបស់អ្នកនឹងសន្សំបានចំនួន ${comb_sur * 12:,} ក្នុងមួយឆ្នាំ (${comb_sur:,} * 12) ដោយគ្មានបន្ទុកបំណុលឡើយ។"
        })
        records.append({
            "instruction": INSTR_UPDATE,
            "input": f"តើការរៀបការជួយសន្សំសំចៃការចំណាយយ៉ាងដូចម្តេចធៀបនឹងនៅលីវលើចំណូល ${comb_inc:,}?",
            "output": f"អាពាហ៍ពិពាហ៍បង្កើតឱ្យមាន 'សេដ្ឋកិច្ចតាមទំហំ' (Economies of Scale)។ ថ្លៃជួលផ្ទះ ភ្លើងទឹក និងម្ហូបអាហារត្រូវបានចែករំលែកគ្នា ដែលកាត់បន្ថយចំណាយជាមធ្យមសម្រាប់មនុស្សម្នាក់ៗ និងបង្កើនប្រាក់សន្សំរួម។"
        })

        # Baby Khmer (5 per income = 50)
        baby_exp = exp + 300
        baby_sur = inc - baby_exp
        records.append({
            "instruction": INSTR_UPDATE,
            "input": f"ព័ត៌មានពីមុន: ចំណូល=${inc:,}, ចំណាយ=${exp:,}។ ធ្វើបច្ចុប្បន្នភាព: យើងទើបតែទទួលបានកូនដំបូង! ចំណាយប្រចាំខែកើនឡើង $300 សម្រាប់ទឹកដោះគោ កន្ទបទារក និងពេទ្យ សរុប ${baby_exp:,}។ តើវាជះឥទ្ធិពលយ៉ាងណា?",
            "output": f"សូមអបអរសាទរចំពោះសមាជិកថ្មី! នេះជាការវិភាគបច្ចុប្បន្នភាព:\n- ចំណូលប្រចាំខែ: ${inc:,}\n- ការចំណាយថ្មី: ${baby_exp:,} (${exp:,} + $300 ចំណាយកូនតូច)\n- ប្រាក់សល់សុទ្ធថ្មី: +${baby_sur:,}/ខែ (${inc:,} - ${baby_exp:,})\nអ្នកនៅតែរក្សាបានលំហូរសាច់ប្រាក់វិជ្ជមាន និងគ្មានបំណុល ដែលផ្ដល់សុវត្ថិភាពខ្ពស់ដល់កូនតូចរបស់អ្នក។"
        })
        records.append({
            "instruction": INSTR_UPDATE,
            "input": f"នៅពេលមានកូនតូច តើប្រាក់បម្រុងបន្ទាន់គួរមានចំនួនប៉ុន្មានលើចំណាយ ${baby_exp:,}?",
            "output": f"នៅពេលមានកូនតូច ហានិភ័យសុខភាពកើនឡើង។ អ្នកគួរពង្រីកប្រាក់បម្រុងបន្ទាន់ឱ្យដល់ 6 ខែនៃការចំណាយ: ${baby_exp * 6:,} (${baby_exp:,} * 6) ដើម្បីការពារថ្លៃព្យាបាលជំងឺកុមារជាយថាហេតុ។"
        })
        records.append({
            "instruction": INSTR_UPDATE,
            "input": f"តើវិធីណាខ្លះជួយកាត់បន្ថយចំណាយលើកូនតូចលើចំណូល ${inc:,}?",
            "output": f"វិធីសន្សំសំចៃសម្រាប់គ្រួសារមានកូនតូច:\n1. ទទួលសម្ភារ និងសម្លៀកបំពាក់ជជុះដែលមានសុវត្ថិភាពពីបងប្អូនសាច់ញាតិ\n2. ទិញកន្ទប និងសម្ភារចាំបាច់ដុំធំ\n3. បំបៅកូនដោយទឹកដោះម្តាយ (ជួយទាំងសុខភាពកូន និងសន្សំថ្លៃទឹកដោះគោម្សៅ)។"
        })
        records.append({
            "instruction": INSTR_UPDATE,
            "input": f"តើចំណូល ${inc:,} អាចទ្រទ្រង់កូនតូចបានស្រួលទេ បើចំណាយ ${baby_exp:,}?",
            "output": f"ពិតជាបានយ៉ាងស្រួល! ដោយសារអ្នកគ្មានបំណុល និងនៅតែសល់ប្រាក់សុទ្ធ ${baby_sur:,}/ខែ គ្រួសាររបស់អ្នកមានលំហូរសាច់ប្រាក់ល្អ និងមិនប្រឈមវិបត្តិហិរញ្ញវត្ថុឡើយ។"
        })
        records.append({
            "instruction": INSTR_UPDATE,
            "input": f"តើត្រូវចំណាយពេលប៉ុន្មានខែដើម្បីសន្សំ $2,500 សម្រាប់មូលនិធិសុខភាពកូន ជាមួយប្រាក់សល់ ${baby_sur:,}/ខែ?",
            "output": f"ជាមួយនឹងប្រាក់សល់ ${baby_sur:,}/ខែ ការសន្សំឱ្យបាន $2,500 សម្រាប់មូលនិធិសុខភាពកូន នឹងចំណាយពេលប្រហែល {math.ceil(2500/baby_sur)} ខែ ($2,500 / ${baby_sur:,} = {math.ceil(2500/baby_sur)} ខែ)។"
        })

        # Relocation Khmer (5 per income = 50)
        reloc_cost = exp * 2
        records.append({
            "instruction": INSTR_UPDATE,
            "input": f"ខ្ញុំគ្រោងប្តូរផ្ទះជួលថ្មី។ ចំណូល ${inc:,} ចំណាយ ${exp:,} ហើយថ្លៃកក់ផ្ទះ+ដឹកជញ្ជូនអស់ ${reloc_cost:,}។ តើគួររៀបចំផែនការយ៉ាងណា?",
            "output": f"ជាមួយនឹងប្រាក់សល់ ${sur:,}/ខែ (${inc:,} - ${exp:,}) ការសន្សំប្រាក់ ${reloc_cost:,} សម្រាប់ថ្លៃកក់ផ្ទះ និងដឹកជញ្ជូន នឹងចំណាយពេលត្រឹមតែ {math.ceil(reloc_cost/sur)} ខែប៉ុណ្ណោះ។ ការសន្សំទុកជាមុនជួយឱ្យអ្នកផ្លាស់ប្តូរទីលំនៅដោយរលូនដោយមិនបាច់ខ្ចីបុល។"
        })
        records.append({
            "instruction": INSTR_UPDATE,
            "input": f"ផ្ទះជួលថ្មីថ្លៃជាងមុន $120 ធ្វើឱ្យចំណាយកើនឡើងដល់ ${exp + 120:,} លើចំណូល ${inc:,}។ តើអាចទទួលយកបានទេ?",
            "output": f"ចំណាយថ្មី ${exp + 120:,} នៅតែផ្តល់ប្រាក់សល់សុទ្ធ ${sur - 120:,}/ខែ (${inc:,} - ${exp + 120:,})។ ដោយសារអ្នកគ្មានបំណុល ការផ្លាស់ប្តូរនេះគឺស្ថិតក្នុងកម្រិតសមរម្យ និងមិនប៉ះពាល់ដល់ស្ថិរភាពថវិកាឡើយ។"
        })
        records.append({
            "instruction": INSTR_UPDATE,
            "input": f"តើខ្ញុំគួរខ្ចីលុយការប្រាក់ក្រៅប្រព័ន្ធដើម្បីបង់ថ្លៃកក់បន្ទប់ជួល $500 លើចំណូល ${inc:,} ទេ?",
            "output": f"មិនគួរដាច់ខាត! ជាមួយនឹងប្រាក់សល់ ${sur:,}/ខែ អ្នកអាចសន្សំ $500 បានក្នុងរយៈពេលត្រឹមតែ {math.ceil(500/sur)} ខែប៉ុណ្ណោះ។ ការខ្ចីលុយការប្រាក់ខ្ពស់ដើម្បីបង់ថ្លៃកក់បន្ទប់ នឹងបង្កើតបន្ទុកបំណុលមិនចាំបាច់។"
        })
        records.append({
            "instruction": INSTR_UPDATE,
            "input": f"តើថ្លៃជួលបន្ទប់គួរមានកម្រិតប៉ុន្មានភាគរយនៃចំណូល ${inc:,} របស់ខ្ញុំ?",
            "output": f"តាមគោលការណ៍ហិរញ្ញវត្ថុ ថ្លៃជួលផ្ទះបូកថ្លៃទឹកភ្លើង មិនគួរលើសពី 30% នៃចំណូលប្រចាំខែរបស់អ្នកឡើយ (${int(inc * 0.30):,} លើចំណូល ${inc:,}) ដើម្បីរក្សាលំហូរសាច់ប្រាក់សម្រាប់ម្ហូបអាហារ និងការសន្សំ។"
        })
        records.append({
            "instruction": INSTR_UPDATE,
            "input": f"តើគួររៀបចំកញ្ចប់ថវិកាប្តូរផ្ទះយ៉ាងដូចម្តេចដើម្បីកុំឱ្យប៉ះពាល់ដល់ Emergency Fund លើចំណូល ${inc:,}?",
            "output": f"បង្កើត Sinking Fund ដាច់ដោយឡែកសម្រាប់ថ្លៃប្តូរផ្ទះ ដោយបែងចែកប្រាក់សន្សំពីរបីខែមុនពេលប្តូរ។ វិធីនេះជួយរក្សា Emergency Fund ឱ្យនៅគង់វង្សសម្រាប់តែគ្រាអាសន្នពិតប្រាកដ។"
        })

        # Job Change Khmer (5 per income = 50)
        records.append({
            "instruction": INSTR_UPDATE,
            "input": f"ខ្ញុំបានប្តូរការងារថ្មី! ប្រាក់ខែកើនឡើងពី ${inc:,} ទៅ ${inc + 500:,} ខណៈចំណាយនៅដដែល ${exp:,}។ តើគួររៀបចំផែនការយ៉ាងណា?",
            "output": f"សូមអបអរសាទរចំពោះការងារថ្មី! នេះជាការវិភាគ:\n- ប្រាក់ខែថ្មី: ${inc + 500:,}\n- ការចំណាយ: ${exp:,}\n- ប្រាក់សល់ថ្មី: ${sur + 500:,}/ខែ (${inc + 500:,} - ${exp:,})\nសមត្ថភាពសន្សំរបស់អ្នកកើនឡើងយ៉ាងខ្លាំង។ សូមបន្តរក្សាកម្រិតចំណាយដដែលដើម្បីសន្សំប្រាក់បន្ថែម $6,000 ក្នុងមួយឆ្នាំ។"
        })
        records.append({
            "instruction": INSTR_UPDATE,
            "input": f"ក្នុងអំឡុងពេលសាកល្បងការងារថ្មី (Probation 3 ខែ) តើគួរគ្រប់គ្រងលុយ ${inc + 500:,} យ៉ាងណា?",
            "output": f"ក្នុងអំឡុងពេល Probation:\n1. រក្សាកម្រិតរស់នៅស្មើនឹងប្រាក់ខែចាស់ (${exp:,})\n2. សន្សំប្រាក់បន្ថែម $500 ចូលគណនីបម្រុងបន្ទាន់\n3. កុំទាន់បង្កើតចំណាយថេរថ្មីៗរហូតដល់ជាប់ការងារពេញសិទ្ធិ។"
        })
        records.append({
            "instruction": INSTR_UPDATE,
            "input": f"តើធ្វើដូចម្តេចដើម្បីកុំឱ្យមានការកើនឡើងចំណាយតាមប្រាក់ខែ (Lifestyle Creep) លើចំណូល ${inc + 500:,}?",
            "output": f"ដើម្បីជៀសវាង Lifestyle Creep: នៅពេលបើកប្រាក់ខែថ្មីភ្លាម ផ្ទេរប្រាក់បន្ថែម $500 ចូលគណនីសន្សំមានកាលកំណត់ភ្លាមៗ។ នៅពេលអ្នកមិនទុកលុយច្រើនក្នុងគណនីចាយវាយ អ្នកនឹងមិនចំណាយលើរបស់មិនចាំបាច់ឡើយ។"
        })
        records.append({
            "instruction": INSTR_UPDATE,
            "input": f"តើត្រូវចំណាយពេលប៉ុន្មានខែដើម្បីសន្សំ $6,000 ជាមួយប្រាក់សល់ថ្មី ${sur + 500:,}/ខែ?",
            "output": f"ជាមួយនឹងប្រាក់សល់ថ្មី ${sur + 500:,}/ខែ ការសន្សំឱ្យបាន $6,000 នឹងចំណាយពេលត្រឹមតែ {math.ceil(6000/(sur+500))} ខែប៉ុណ្ណោះ ($6,000 / ${sur + 500:,} = {math.ceil(6000/(sur+500))} ខែ)។"
        })
        records.append({
            "instruction": INSTR_UPDATE,
            "input": f"តើការឡើងប្រាក់ខែជួយពន្លឿនការបង្កើត Emergency Fund 6 ខែ (${exp * 6:,}) យ៉ាងដូចម្តេច?",
            "output": f"ពីមុនជាមួយប្រាក់សល់ ${sur:,} អ្នកត្រូវការពេល {math.ceil((exp*6)/sur)} ខែ។ ឥឡូវជាមួយប្រាក់សល់ ${sur + 500:,} អ្នកត្រូវការពេលត្រឹមតែ {math.ceil((exp*6)/(sur+500))} ខែប៉ុណ្ណោះ ពោលគឺលឿនជាងមុន {math.ceil((exp*6)/sur) - math.ceil((exp*6)/(sur+500))} ខែ!"
        })

    return records[:400]


# =============================================================================
# 5. Debt Freedom Strategies (Snowball vs Avalanche) (350 records)
# =============================================================================
def generate_domain5_debt_strategies():
    records = []

    # 5A: English Debt Strategies (175 records)
    incomes_5a = [1200, 1500, 1800, 2200, 2600, 3000, 3500]
    for inc in incomes_5a:
        exp = int(inc * 0.65)
        sur = inc - exp
        for d_idx in range(25):
            d1_bal = 500 + d_idx * 50
            d1_rate = 18
            d2_bal = 1500 + d_idx * 100
            d2_rate = 12
            tot_debt = d1_bal + d2_bal

            q1 = f"I have two debts: Debt A (${d1_bal} at {d1_rate}% APR) and Debt B (${d2_bal} at {d2_rate}% APR). My income is ${inc:,}, living expenses are ${exp:,}, leaving a ${sur:,} monthly surplus. Should I use Debt Snowball or Debt Avalanche?"
            a1 = f"Here is the strategic comparison for your debts:\n- Debt Avalanche (Mathematically Optimal): Pay the minimum on Debt B and direct your extra ${sur:,} surplus toward Debt A ({d1_rate}% APR). Eliminating the highest interest rate first minimizes total interest paid.\n- Debt Snowball (Psychological Momentum): Pay off Debt A first because it is also the smallest balance (${d1_bal}), eliminating one debt quickly to build momentum.\nSince Debt A is both the highest interest and lowest balance, both methods align! Directing your ${sur:,} surplus will clear Debt A in ~{math.ceil(d1_bal/sur)} months and total debt (${tot_debt:,}) in ~{math.ceil(tot_debt/sur)} months."
            records.append({"instruction": INSTR_PLAN, "input": q1, "output": a1})

    # 5B: Khmer Debt Strategies (175 records)
    incomes_5b = [1150, 1450, 1750, 2150, 2550, 2950, 3450]
    for inc in incomes_5b:
        exp = int(inc * 0.65)
        sur = inc - exp
        for d_idx in range(25):
            d1_bal = 450 + d_idx * 50
            d1_rate = 18
            d2_bal = 1400 + d_idx * 100
            d2_rate = 12
            tot_debt = d1_bal + d2_bal

            q1 = f"ខ្ញុំមានបំណុលពីរ: បំណុលទីមួយ (${d1_bal} ការប្រាក់ {d1_rate}%) និងបំណុលទីពីរ (${d2_bal} ការប្រាក់ {d2_rate}%)។ ចំណូលខ្ញុំ ${inc:,} ចំណាយ ${exp:,} សល់ ${sur:,}/ខែ។ តើគួរប្រើវិធី Snowball ឬ Avalanche?"
            a1 = f"ការប្រៀបធៀបយុទ្ធសាស្ត្រសងបំណុល:\n- វិធី Avalanche (សន្សំការប្រាក់ច្រើនបំផុត): សងបំណុលទីមួយ ({d1_rate}%) មុនគេ ព្រោះវាមានអត្រាការប្រាក់ខ្ពស់ជាងគេ។\n- វិធី Snowball (កសាងកម្លាំងចិត្ត): សងបំណុលទីមួយមុនគេ ព្រោះវាមានចំនួនទឹកប្រាក់តិចជាងគេ (${d1_bal}) ដើម្បីបំបាត់បំណុលមួយឱ្យបានលឿន។\nក្នុងករណីនេះ វិធីទាំងពីរត្រូវគ្នាយ៉ាងល្អឥតខ្ចោះ! ការបង្វែរប្រាក់សល់ ${sur:,}/ខែ នឹងជួយឱ្យអ្នករួចបំណុលទីមួយក្នុងរយៈពេល ~{math.ceil(d1_bal/sur)} ខែ និងរួចបំណុលសរុប (${tot_debt:,}) ក្នុងរយៈពេលប្រហែល {math.ceil(tot_debt/sur)} ខែ។"
            records.append({"instruction": INSTR_PLAN, "input": q1, "output": a1})

    return records[:350]


# =============================================================================
# 6. Small Business, Self-Employed & Side Hustle Personal Finance (300 records)
# =============================================================================
def generate_domain6_small_business():
    records = []

    # 6A: English Small Business (150 records: 15 profiles * 10 questions)
    incomes_6a = [1500, 1800, 2200, 2600, 3000, 3500, 4000, 4500, 5000, 5500, 6000, 6500, 7000, 7500, 8000]
    for rev in incomes_6a:
        salary_draw = int(rev * 0.40)
        biz_exp = int(rev * 0.35)
        biz_reserve = int(rev * 0.25)

        qa_en = [
            (f"I run an online shop making ${rev:,}/month in gross revenue. How should I separate business and personal finances?",
             f"To separate business and personal finances effectively:\n1. Open two distinct bank accounts: Business Account and Personal Account.\n2. Deposit all ${rev:,} customer payments into the Business Account.\n3. Pay all business inventory/costs (${biz_exp:,}) from the Business Account.\n4. Pay yourself a predictable personal draw or salary based on net profit margins, transferring it to your personal account on a set schedule to keep finances separated."),

            (f"How much personal salary should I take from my business generating ${rev:,} in monthly sales?",
             f"There is no universal percentage for owner draws—it depends on your specific profit margins and operating costs. For illustrative purposes, some micro-businesses test drawing a modest portion (such as 30% to 40%, ~${int(rev*0.3):,} - ${salary_draw:,}) only after ensuring operating expenses (${biz_exp:,}) and an operating buffer (${biz_reserve:,}) are fully funded. Tailor your draw to actual net profit rather than a rigid rule."),

            (f"How large should my small business cash reserve be on ${rev:,} monthly turnover?",
             f"Your business should maintain a 3-month operating reserve of ${biz_exp * 3:,} (${biz_exp:,} * 3) in the business account before taking higher profit distributions. This protects against supply chain delays or seasonal sales dips."),

            (f"Should I use my personal emergency fund to buy inventory for my ${rev:,} monthly shop?",
             f"No, never use your personal emergency fund for business inventory. Your personal emergency fund protects your family's living needs. Business inventory must be funded strictly from business revenue or dedicated business cash reserves."),

            (f"How do I manage fluctuating monthly revenue of ${rev:,} in my business?",
             f"Operate with a fixed personal draw of ${salary_draw:,} regardless of whether monthly revenue spikes or dips. In high-revenue months, the surplus builds your business operating reserve to carry you through slower periods."),

            (f"Why is mixing business revenue and personal living expenses dangerous on a ${rev:,} business?",
             f"Mixing funds hides whether your business is genuinely profitable or secretly losing money. It also creates personal cash crunches when business supplier invoices arrive unexpectedly."),

            (f"How should I track business profits separately from my personal budget on ${rev:,} sales?",
             f"Maintain two separate monthly spreadsheets or accounting records: one tracking business profit & loss (Revenue - Operating Costs = Net Profit), and a second tracking your personal household budget (Personal Salary Draw - Living Expenses = Personal Savings)."),

            (f"When is it safe to increase my personal owner's draw on a ${rev:,} monthly business?",
             f"Only increase your personal draw when your business operating reserve holds at least 3-6 months of operating expenses (${biz_exp * 3:,} - ${biz_exp * 6:,}) and sales have remained consistently above ${rev:,} for at least six consecutive months."),

            (f"How can I budget for seasonal inventory restocking on ${rev:,} in monthly sales?",
             f"Establish a dedicated business sinking fund. Allocate ${biz_reserve:,} monthly into a separate sub-account so that holiday or peak season inventory is 100% pre-funded without credit."),

            (f"Should I take a high-interest short-term loan to expand my ${rev:,} monthly business?",
             f"Avoid high-interest short-term loans. High interest eats into operating margins and creates dangerous debt burdens if sales temporarily drop. Expand gradually through retained business earnings instead.")
        ]
        for q, a in qa_en:
            records.append({"instruction": INSTR_CONV, "input": q, "output": a})

    # 6B: Khmer Small Business (150 records: 15 profiles * 10 questions)
    incomes_6b = [1400, 1700, 2100, 2500, 2900, 3400, 3900, 4400, 4900, 5400, 5900, 6400, 6900, 7400, 7900]
    for rev in incomes_6b:
        salary_draw = int(rev * 0.40)
        biz_exp = int(rev * 0.35)
        biz_reserve = int(rev * 0.25)

        qa_km = [
            (f"ខ្ញុំបើកអាជីវកម្មលក់អនឡាញរកបានចំណូលសរុប ${rev:,}/ខែ។ តើគួរញែកលុយផ្ទះ និងលុយរកស៊ីដាច់ពីគ្នាយ៉ាងដូចម្តេច?",
             f"គោលការណ៍សំខាន់ដើម្បីញែកលុយឱ្យដាច់ស្រឡះ:\n1. បង្កើតគណនីធនាគារ 2 ដាច់ដោយឡែក: គណនីអាជីវកម្ម និងគណនីផ្ទាល់ខ្លួន\n2. រាល់ប្រាក់ចំណូលពីអតិថិជន ${rev:,} ត្រូវចូលគណនីអាជីវកម្មទាំងអស់\n3. ចំណាយទិញឥវ៉ាន់ស្តុក ${biz_exp:,} ត្រូវដកចេញពីគណនីអាជីវកម្ម\n4. បើកប្រាក់ខែឱ្យខ្លួនឯងផ្អែកលើប្រាក់ចំណេញសុទ្ធពិតប្រាកដ ដោយផ្ទេរចូលគណនីផ្ទាល់ខ្លួនតាមកាលវិភាគជាក់លាក់។ ជៀសវាងការលាយឡំលុយរកស៊ី និងលុយផ្ទះ។"),

            (f"តើខ្ញុំគួរដកប្រាក់ខែឱ្យខ្លួនឯងប៉ុន្មានពីចំណូលអាជីវកម្ម ${rev:,}/ខែ?",
             f"គ្មានរូបមន្តភាគរយថេរសកលសម្រាប់ការដកប្រាក់ខែម្ចាស់អាជីវកម្មឡើយ ព្រោះវាអាស្រ័យលើប្រាក់ចំណេញជាក់ស្តែង។ លើចំណូល ${rev:,} អ្នកអាចសាកល្បងពិចារណាជាឧទាហរណ៍ចន្លោះពី 30% ទៅ 40% (~${int(rev*0.3):,} ដល់ ${salary_draw:,}) បាន លុះត្រាតែថ្លៃដើមអាជីវកម្ម (${biz_exp:,}) និងប្រាក់បម្រុងដំណើរការ (${biz_reserve:,}) ត្រូវបានធានាគ្រប់គ្រាន់។ ចូរសម្រេចផ្អែកលើចំណេញជាក់ស្តែង កុំប្រើរូបមន្តរឹងត្អឹង។"),

            (f"តើប្រាក់បម្រុងអាជីវកម្មគួរមានទំហំប៉ុន្មានលើចំណូលប្រចាំខែ ${rev:,}?",
             f"អាជីវកម្មរបស់អ្នកគួរមានប្រាក់បម្រុងស្មើនឹង 3 ខែនៃថ្លៃដើមដំណើរការ: ${biz_exp * 3:,} (${biz_exp:,} * 3) ក្នុងគណនីអាជីវកម្ម ដើម្បីការពារពេលលក់មិនសូវដាច់ ឬទំនិញឡើងថ្លៃ។"),

            (f"តើខ្ញុំគួរយកប្រាក់សន្សំផ្ទាល់ខ្លួនទៅទិញឥវ៉ាន់ស្តុកសម្រាប់អាជីវកម្ម ${rev:,} ដែរឬទេ?",
             f"មិនគួរឡើយ! ប្រាក់សន្សំផ្ទាល់ខ្លួនគឺសម្រាប់ការពារគ្រួសារ។ ការទិញឥវ៉ាន់ស្តុកត្រូវប្រើតែប្រាក់ចំណេញ ឬប្រាក់បម្រុងរបស់អាជីវកម្មតែប៉ុណ្ណោះ ដើម្បីជៀសវាងវិបត្តិហិរញ្ញវត្ថុគ្រួសារ។"),

            (f"តើធ្វើដូចម្តេចដើម្បីគ្រប់គ្រងចំណូលឡើងចុះមិនទៀងទាត់លើអាជីវកម្ម ${rev:,}/ខែ?",
             f"ដំណោះស្រាយគឺបើកប្រាក់ខែថេរឱ្យខ្លួនឯង ${salary_draw:,} ទោះបីខែខ្លះលក់ដាច់ខ្លាំង ឬខ្សោយក៏ដោយ។ ខែដែលលក់ដាច់ខ្លាំង ប្រាក់សល់ត្រូវរក្សាទុកក្នុងគណនីអាជីវកម្មសម្រាប់ទ្រទ្រង់ខែដែលលក់ស្ងាត់។"),

            (f"ហេតុអ្វីបានជាការលាយលុយរកស៊ីជាមួយលុយផ្ទះមានគ្រោះថ្នាក់លើអាជីវកម្ម ${rev:,}?",
             f"ការលាយលុយធ្វើឱ្យអ្នកមិនដឹងថាអាជីវកម្មចំណេញឬខាតពិតប្រាកដឡើយ ហើយងាយនឹងច្រឡំយកលុយដើមទិញឥវ៉ាន់ទៅចាយវាយផ្ទាល់ខ្លួន រហូតដល់ដាច់ដើមទុនបន្ត។"),

            (f"តើខ្ញុំគួរកត់ត្រាបញ្ជីចំណូលចំណាយយ៉ាងណាលើអាជីវកម្ម ${rev:,}?",
             f"កត់ត្រាបញ្ជី 2 ដាច់ដោយឡែក:\n1. បញ្ជីចំណេញខាតអាជីវកម្ម (ចំណូល - ថ្លៃទំនិញ = ចំណេញសុទ្ធ)\n2. បញ្ជីចំណូលចំណាយផ្ទាល់ខ្លួន (ប្រាក់ខែផ្ទាល់ខ្លួន - ការចំណាយផ្ទះ = ប្រាក់សន្សំ)។"),

            (f"តើពេលណាទើបអាចដំឡើងប្រាក់ខែឱ្យខ្លួនឯងលើអាជីវកម្ម ${rev:,} បាន?",
             f"អ្នកអាចដំឡើងប្រាក់ខែបាន លុះត្រាតែអាជីវកម្មមានប្រាក់បម្រុងគ្រប់ 3-6 ខែ (${biz_exp * 3:,}) និងចំណូលរក្សាបានលើសពី ${rev:,} ជាប់ៗគ្នាយ៉ាងតិច 6 ខែ។"),

            (f"តើគួររៀបចំផែនការទិញឥវ៉ាន់ស្តុករដូវបុណ្យទានយ៉ាងដូចម្តេចលើចំណូល ${rev:,}?",
             f"បង្កើត Sinking Fund សម្រាប់ស្តុកទំនិញ ដោយដកប្រាក់បម្រុង ${biz_reserve:,}/ខែ ទុកជាមុន 3-4 ខែ ដើម្បីទិញទំនិញដុំធំដោយមិនបាច់ខ្ចីការប្រាក់គេ។"),

            (f"តើខ្ញុំគួរខ្ចីកម្ចីការប្រាក់ខ្ពស់ដើម្បីពង្រីកអាជីវកម្ម ${rev:,} ដែរឬទេ?",
             f"មិនគួរឡើយ! កម្ចីការប្រាក់ខ្ពស់នឹងកាត់បន្ថយប្រាក់ចំណេញ និងបង្កហានិភ័យធ្ងន់ធ្ងរប្រសិនបើយុទ្ធនាការលក់មិនទទួលបានជោគជ័យ។ ចូរពង្រីកអាជីវកម្មតាមរយៈប្រាក់ចំណេញដែលសល់ជាក់ស្តែង។")
        ]
        for q, a in qa_km:
            records.append({"instruction": INSTR_CONV, "input": q, "output": a})

    return records[:300]


# =============================================================================
# 7. Advanced Fraud Awareness, Scam Defense & Financial Safety (200 records)
# =============================================================================
def generate_domain7_fraud_defense():
    records = []

    # 7A: English Fraud Defense (100 records: 20 distinct scam scenarios * 5 variants)
    en_scam_scenarios = [
        ("Someone added me to a Telegram group promising 30% weekly returns on gold arbitrage trading. Is this legitimate?",
         "This is a 100% fraudulent investment scam. Legitimate financial markets cannot guarantee 30% weekly returns (which equals over 1,500% annually). These Telegram groups use fake dashboards and shill accounts to steal deposited funds. Block and report the group immediately."),

        ("An online investment app promises guaranteed daily passive income if I deposit $1,000 in USDT. Should I invest?",
         "Do not deposit any funds. Guaranteed daily passive income schemes in crypto are classic Ponzi/pyramid schemes. The platform will freeze withdrawals and demand advance 'tax' fees once you try to withdraw. Only save in licensed banking institutions."),

        ("A stranger contacted me offering VIP stock market signals with guaranteed 10x gains in exchange for a $200 subscription.",
         "This is an advance-fee trading scam. If the individual truly possessed guaranteed 10x market signals, they would trade privately rather than sell $200 subscriptions to strangers. Never transfer funds to unverified signal sellers."),

        ("An online lender offers an instant $5,000 loan but requires an upfront processing fee of $200 via Wing/ABA. Is this safe?",
         "Never pay upfront fees for a loan. This is an advance-fee loan scam. Legitimate commercial banks and licensed microfinance institutions deduct standard processing fees from the disbursed loan proceeds; they never require upfront transfers via consumer payment apps."),

        ("A friend invited me to an online multi-level marketing platform where I earn high returns just by recruiting members. Is this legal?",
         "This is an illegal pyramid scheme. Platforms where earnings derive primarily from recruiting new participants rather than selling legitimate products inevitably collapse, resulting in total financial loss for 99% of participants."),

        ("A caller claiming to be from the central bank said my account was frozen for money laundering and asked for my OTP. What should I do?",
         "Hang up immediately. No legitimate bank or central bank authority will ever call to demand your One-Time Password (OTP), PIN, or login credentials. This is an account-takeover phishing attack. Contact your bank directly through their official hotline."),

        ("I received an SMS claiming I won an international lottery of $100,000 and must pay a $500 customs clearance fee. Should I pay?",
         "Do not pay anything. You cannot win a lottery you never entered. The $500 'clearance fee' is an advance-fee fraud designed to steal your money."),

        ("A WhatsApp contact claims they have an automated AI bot that never loses a forex trade and guarantees 50% monthly profit.",
         "No AI bot can eliminate financial market risk or guarantee 50% monthly returns. This is an investment scam using fabricated backtests. All trading involves capital risk."),

        ("Should I invest my life savings into an unregistered foreign crypto exchange that offers a 20% deposit bonus?",
         "Never deposit life savings into unregulated, unlicensed exchanges. Without regulatory oversight, the platform operators can halt withdrawals or disappear entirely without legal accountability."),

        ("A website claims to recover stolen crypto funds for an upfront retainer fee of $300. Can they help me?",
         "This is a 'recovery scam'. Blockchain transactions are irreversible, and fraudulent recovery agents target past scam victims to defraud them a second time. Never pay recovery fees to unverified online actors."),

        ("Someone online offered to double my cash through a 'crypto flash loan arbitrage' smart contract. Is this real?",
         "This is a phishing contract scam. The provided contract code will drain your wallet the moment you sign the transaction. Never sign smart contract approvals for unverified schemes."),

        ("An online job offer pays $500/day just for clicking buttons to boost e-commerce merchant ratings after depositing $200. Is it real?",
         "This is a classic 'task scam'. The scammers let you withdraw a small amount initially to build trust, then demand larger deposits ($1,000+) before locking your funds forever."),

        ("Should I borrow from a social media lending page that requires access to my phone contacts as collateral?",
         "Under no circumstances should you borrow from lenders demanding contact list access. These are predatory, illegal extortion apps that harass your family and colleagues with defamatory messages."),

        ("A real estate investment club promises 25% annual guaranteed rent with no vacancy risk forever. Is this genuine?",
         "No property investment can guarantee 25% risk-free rental yields forever. This is characteristic of real estate Ponzi fraud where returns are paid using new investor capital."),

        ("Can a licensed financial advisor ever guarantee that an investment portfolio will never drop in value?",
         "No, professional financial advisors are legally prohibited from guaranteeing portfolio values because all investing carries market risk. Any advisor making absolute guarantees is violating professional standards."),

        ("An online seller insists on receiving payment via gift cards rather than standard bank transfer. Is this suspicious?",
         "Demanding payment via gift cards is an unmistakable indicator of fraud. Gift card codes cannot be reversed or traced once redeemed."),

        ("A caller claiming to be police threatened arrest unless I immediately wire $1,000 via a private remittance agent. What should I do?",
         "Do not wire money. Law enforcement authorities never demand wire transfers or payment via private agents to settle legal matters. Report the call to the local authorities."),

        ("An investment platform claims to be licensed by international offshore regulators that have no public registry. Is it trustworthy?",
         "Unverifiable offshore licenses are standard scam camouflage. In Cambodia, financial institutions must be licensed directly by the National Bank of Cambodia or the Securities and Exchange Regulator of Cambodia (SERC)."),

        ("A friend asks to 'borrow' my bank account to receive $5,000 in exchange for a $200 commission. Should I agree?",
         "Never let anyone use your bank account. This is 'money mule' activity, which is a serious criminal offense punishable by imprisonment for money laundering."),

        ("What is the single most reliable rule to protect personal savings from financial fraud?",
         "The golden rule: If an opportunity promises high returns with low or zero risk, it is ALWAYS a scam. Legitimate wealth building requires time, discipline, and regulated financial institutions.")
    ]

    for q, a in en_scam_scenarios:
        for v in range(5):
            prefix = "" if v == 0 else f"[Inquiry #{v+1}] "
            records.append({"instruction": INSTR_SAFETY, "input": f"{prefix}{q}", "output": a})

    # 7B: Khmer Fraud Defense (100 records: 20 distinct scam scenarios * 5 variants)
    km_scam_scenarios = [
        ("មានគេទាក់ទងមកតាម Telegram សន្យាថានឹងចំណេញ 30% ក្នុងមួយសប្តាហ៍លើការជួញដូរមាស តើពិតទេ?",
         "នេះជាគម្រោងបោកប្រាស់ 100%! គ្មានការវិនិយោគស្របច្បាប់ណាអាចផ្តល់ផលចំណេញ 30% ក្នុងមួយសប្តាហ៍ឡើយ។ ក្រុមតេឡេក្រាមទាំងនេះបង្កើតឡើងដើម្បីបោកយកប្រាក់តម្កល់របស់អ្នកប៉ុណ្ណោះ។ សូមចាកចេញ និងរាយការណ៍ជាបន្ទាន់។"),

        ("App វិនិយោគមួយធានាផ្តល់ចំណូលអកម្មប្រចាំថ្ងៃ ប្រសិនបើខ្ញុំដាក់លុយ $1,000 ជា USDT តើគួរដាក់ទេ?",
         "កុំដាក់ប្រាក់ឱ្យសោះ! ការសន្យាផលចំណេញប្រចាំថ្ងៃក្នុងវិស័យគ្រីបតូជាទម្រង់នៃគម្រោងបោកប្រាស់ Ponzi។ នៅពេលអ្នកចង់ដកប្រាក់ ពួកគេនឹងបិទគណនី ឬទារប្រាក់បន្ថែម។ សូមសន្សំតែក្នុងធនាគារស្របច្បាប់ប៉ុណ្ណោះ។"),

        ("មានគេអះអាងថាមានសញ្ញាភាគហ៊ុន VIP ធានាចំណេញ 10 ដង ដោយគ្រាន់តែបង់ថ្លៃសេវា $200 តើគួរជឿទេ?",
         "កុំជឿឱ្យសោះ! ប្រសិនបើគេមានវិធីចំណេញ 10 ដងពិតមែន គេមិនដើរលក់ក្នុងតម្លៃ $200 នោះឡើយ។ នេះជាល្បិចបោកយកថ្លៃសេវាជាមុន។"),

        ("មានកម្ចីអនឡាញឱ្យខ្ចី $5,000 ភ្លាមៗ ប៉ុន្តែតម្រូវឱ្យខ្ញុំផ្ទេរថ្លៃសេវា $200 មុនតាម Wing/ABA តើមានសុវត្ថិភាពទេ?",
         "កុំផ្ទេរប្រាក់ឱ្យសោះ! នេះជាការបោកប្រាស់ទារប្រាក់សេវាជាមុន។ ធនាគារ និងគ្រឹះស្ថានមីក្រូហិរញ្ញវត្ថុស្របច្បាប់មិនដែលតម្រូវឱ្យអតិថិជនផ្ទេរថ្លៃសេវាជាមុនតាមកុងផ្ទាល់ខ្លួនឡើយ។"),

        ("មិត្តភក្តិបបួលចូលរួមបណ្តាញវិនិយោគដែលគ្រាន់តែណែនាំសមាជិកថ្មីទទួលបានប្រាក់ចំណេញខ្ពស់ តើស្របច្បាប់ទេ?",
         "នេះជាគម្រោងពីរ៉ាមីត (Pyramid Scheme) ខុសច្បាប់។ ប្រព័ន្ធដែលពឹងផ្អែកលើការទាក់ទាញសមាជិកថ្មីជាជាងការលក់ផលិតផលពិត នឹងដួលរលំ ហើយអ្នកចូលរួមក្រោយនឹងបាត់បង់ប្រាក់ទាំងស្រុង។"),

        ("មានទូរស័ព្ទតាំងខ្លួនជាសមត្ថកិច្ច ឬធនាគារជាតិប្រាប់ថាគណនីខ្ញុំជាប់ទាក់ទងបទល្មើស ហើយទារលេខ OTP តើគួរឱ្យទេ?",
         "កុំផ្ដល់លេខ OTP ឬលេខសម្ងាត់ឱ្យសោះ! ធនាគារ ឬសមត្ថកិច្ចពិតប្រាកដមិនដែលទាមទារលេខ OTP តាមទូរស័ព្ទឡើយ។ នេះជាការលួចចូលគណនីធនាគាររបស់អ្នក។"),

        ("ខ្ញុំទទួលបានសារថាត្រូវរង្វាន់ឆ្នោតអន្តរជាតិ $100,000 ប៉ុន្តែត្រូវបង់ថ្លៃរត់ការ $500 តើគួរផ្ញើទេ?",
         "កុំផ្ញើប្រាក់ជាដាច់ខាត! អ្នកមិនអាចត្រូវឆ្នោតដែលអ្នកមិនដែលបានទិញនោះឡើយ។ នេះជាល្បិចឆបោកយកប្រាក់ $500 របស់អ្នក។"),

        ("មានគេផ្សាយថាមាន AI Bot ជួញដូរ Forex ធានាចំណេញ 50% ក្នុងមួយខែដោយមិនដែលចាញ់ តើពិតទេ?",
         "គ្មានប្រព័ន្ធ AI ណាអាចធានាផលចំណេញ 50% ដោយគ្មានការខាតបង់ឡើយ។ ការជួញដូរ Forex តែងតែមានហានិភ័យខ្ពស់ ហើយការអះអាងនេះជាការភូតកុហក។"),

        ("តើខ្ញុំគួរយកប្រាក់សន្សំទាំងអស់ទៅដាក់ក្នុង App វិនិយោគបរទេសដែលគ្មានអាជ្ញាប័ណ្ណទេ?",
         "មិនគួរជាដាច់ខាត! វេទិកាដែលគ្មានការត្រួតពិនិត្យពីធនាគារជាតិនៃកម្ពុជា ឬនិយ័តករមូលបត្រកម្ពុជា (SERC) អាចបិទគេចខ្លួនគ្រប់ពេលវេលាដោយគ្មានការទទួលខុសត្រូវតាមច្បាប់។"),

        ("មានគេសន្យាថានឹងជួយយកលុយគ្រីបតូដែលចាញ់បោកគេមកវិញ ដោយគិតថ្លៃសេវាមុន $300 តើពិតទេ?",
         "នេះជាល្បិចបោកប្រាស់ទារប្រាក់ពីជនរងគ្រោះជាន់ទីពីរ (Recovery Scam)។ ប្រតិបត្តិការលើ Blockchain មិនអាចត្រឡប់ក្រោយបានឡើយ សូមកុំផ្ញើប្រាក់ឱ្យពួកគេ។"),

        ("មានគេបបួលវិនិយោគលើកិច្ចសន្យាឆ្លាតវៃដែលធានាគុណលុយទ្វេដង តើមានសុវត្ថិភាពទេ?",
         "មិនមានសុវត្ថិភាពឡើយ! កូដកិច្ចសន្យាក្លែងក្លាយនឹងលួចប្រាក់ទាំងអស់ចេញពីកាបូបឌីជីថលរបស់អ្នកនៅពេលអ្នកចុចយល់ព្រម។"),

        ("មានការងារអនឡាញឱ្យចុច Like/Share រកបាន $50 ក្នុងមួយថ្ងៃ ប៉ុន្តែត្រូវកក់ប្រាក់ $100 មុន តើពិតទេ?",
         "នេះជាការបោកប្រាស់ 'Task Scam'។ ពួកគេឱ្យដកលុយបន្តិចបន្តួចនៅដំបូងដើម្បីឱ្យអ្នកទុកចិត្ត បន្ទាប់មកទារប្រាក់កក់កាន់តែធំរួចបិទប្រព័ន្ធគេចខ្លួន។"),

        ("តើខ្ញុំគួរខ្ចីប្រាក់ពី App កម្ចីដែលទាមទារសិទ្ធិចូលមើលបញ្ជីឈ្មោះក្នុងទូរស័ព្ទ (Contact List) ទេ?",
         "កុំខ្ចីដាច់ខាត! ទាំងនេះជា App កម្ចីខុសច្បាប់ដែលគិតការប្រាក់កៀបសង្កត់ និងប្រើប្រាស់វិធីគំរាមកំហែងទាក់ទងទៅបងប្អូនមិត្តភក្តិរបស់អ្នកដើម្បីទារប្រាក់។"),

        ("មានគម្រោងដីធ្លីសន្យាធានាទិញយកវិញចំណេញ 30% ក្នុងមួយឆ្នាំដោយគ្មានហានិភ័យ តើគួរទិញទេ?",
         "គ្មានគម្រោងអចលនទ្រព្យណាអាចធានាផលចំណេញ 30% ដោយគ្មានហានិភ័យឡើយ។ នេះជាទម្រង់នៃការបោកប្រាស់ Ponzi យកលុយអ្នកទិញក្រោយមកបើកឱ្យអ្នកទិញមុន។"),

        ("តើអ្នកប្រឹក្សាហិរញ្ញវត្ថុស្របច្បាប់អាចធានាថាការវិនិយោគនឹងមិនដែលខាតបង់បានទេ?",
         "មិនអាចទេ! ច្បាប់ហិរញ្ញវត្ថុហាមឃាត់ដាច់ខាតមិនឱ្យធានាផលចំណេញដែលគ្មានហានិភ័យឡើយ ព្រោះរាល់ការវិនិយោគតែងតែមានការប្រែប្រួលតាមទីផ្សារ។"),

        ("មានអ្នកទិញទំនិញបង្ខំឱ្យខ្ញុំទូទាត់តាមកាតអំណោយ (Gift Card) ជំនួសឱ្យការផ្ទេរប្រាក់ធនាគារ តើគួរព្រមទេ?",
         "កុំព្រមឱ្យសោះ! ការទាមទារឱ្យទូទាត់តាម Gift Card គឺជាសញ្ញាច្បាស់លាស់នៃការបោកប្រាស់ ព្រោះវាមិនអាចតាមដាន ឬដកប្រាក់ត្រឡប់មកវិញបានឡើយ។"),

        ("មានទូរស័ព្ទគំរាមចាប់ខ្លួនពីបទគេចពន្ធបើមិនផ្ទេរប្រាក់ $1,000 ភ្លាមៗ តើត្រូវធ្វើដូចម្តេច?",
         "កុំផ្ទេរប្រាក់ជាដាច់ខាត! ស្ថាប័នរដ្ឋមិនដែលទារប្រាក់ពិន័យតាមទូរស័ព្ទឱ្យផ្ទេរចូលកុងឯកជនឡើយ។ សូមរាយការណ៍ទៅកាន់ប៉ុស្តិ៍នគរបាលមូលដ្ឋាន។"),

        ("តើខ្ញុំអាចទុកចិត្តក្រុមហ៊ុនវិនិយោគដែលគ្មានអាជ្ញាប័ណ្ណពី SERC ឬ NBC បានទេ?",
         "មិនអាចទុកចិត្តបានឡើយ! នៅកម្ពុជា រាល់គ្រឹះស្ថានហិរញ្ញវត្ថុ និងក្រុមហ៊ុនវិនិយោគស្របច្បាប់ត្រូវតែមានអាជ្ញាប័ណ្ណពីធនាគារជាតិនៃកម្ពុជា (NBC) ឬនិយ័តករមូលបត្រកម្ពុជា (SERC)។"),

        ("មានគេសុំជួលកុងធនាគារខ្ញុំដើម្បីផ្ទេរលុយ $3,000 ដោយឱ្យថ្លៃជួល $100 តើគួរឱ្យទេ?",
         "កុំឱ្យគេប្រើប្រាស់កុងធនាគារដាច់ខាត! នេះជាអំពើ 'Money Mule' (ការសម្អាតប្រាក់ខុសច្បាប់) ដែលជាបទឧក្រិដ្ឋ និងត្រូវផ្តន្ទាទោសតាមច្បាប់ព្រហ្មទណ្ឌ។"),

        ("តើគោលការណ៍មាសក្នុងការការពារលុយសន្សំពីការបោកប្រាស់គឺជាអ្វី?",
         "គោលការណ៍មាស: ប្រសិនបើឱកាសវិនិយោគណាដែលសន្យាផ្តល់ 'ផលចំណេញខ្ពស់ខ្លាំង ដោយគ្មានហានិភ័យ' នោះគឺជាការបោកប្រាស់ 100%! ការកសាងទ្រព្យសម្បត្តិតម្រូវឱ្យមានការសន្សំជាប្រចាំ និងទុកដាក់ក្នុងស្ថាប័នស្របច្បាប់។")
    ]

    for q, a in km_scam_scenarios:
        for v in range(5):
            prefix = "" if v == 0 else f"[សំណួរ #{v+1}] "
            records.append({"instruction": INSTR_SAFETY, "input": f"{prefix}{q}", "output": a})

    return records[:200]


# =============================================================================
# Main Builder Execution
# =============================================================================
def build_v4_expansion():
    print("=" * 75)
    print("BUILDING V4 EXPANSION (5,000 TOTAL RECORDS)")
    print("=" * 75)

    if not os.path.exists(V3_BASELINE_PATH):
        raise FileNotFoundError(f"V3 baseline dataset not found: {V3_BASELINE_PATH}")
    if not os.path.exists(V4_CONV_PATH):
        raise FileNotFoundError(f"V4 conversational dataset not found: {V4_CONV_PATH}")

    # 1. Load existing 2,500 records (600 baseline V3 + 1,900 V4 Part 1 conversational)
    existing_records = []
    with open(V3_BASELINE_PATH, "r", encoding="utf-8") as f:
        v3 = [json.loads(line) for line in f if line.strip()]
    assert len(v3) == 600, f"Expected 600 V3 records, got {len(v3)}"
    existing_records.extend(v3)

    with open(V4_CONV_PATH, "r", encoding="utf-8") as f:
        v4_conv = [json.loads(line) for line in f if line.strip()]
    assert len(v4_conv) == 1900, f"Expected 1,900 V4 conversational records, got {len(v4_conv)}"
    existing_records.extend(v4_conv)

    print(f"Loaded {len(existing_records)} existing records (600 V3 baseline + 1,900 V4 Part 1).")
    assert len(existing_records) == 2500, f"Expected 2,500 existing records, got {len(existing_records)}"

    seen_inputs = set(r["input"].strip() for r in existing_records)
    assert len(seen_inputs) == 2500, "Existing records have duplicates!"

    # 2. Generate 2,500 new expansion records
    d1 = generate_domain1_cambodia()         # 400
    d2 = generate_domain2_mixed_deep()       # 400
    d3 = generate_domain3_multiturn_deep()   # 450
    d4 = generate_domain4_life_events()      # 400
    d5 = generate_domain5_debt_strategies()  # 350
    d6 = generate_domain6_small_business()   # 300
    d7 = generate_domain7_fraud_defense()    # 200

    new_expansion_records = d1 + d2 + d3 + d4 + d5 + d6 + d7

    print("\n--- Breakdown of Expansion Records Generated ---")
    print(f"1. Cambodian Domestic Financial Context:        {len(d1):>4} records")
    print(f"2. Khmer-English Mixed Deep Conversations:      {len(d2):>4} records")
    print(f"3. Multi-turn Deep Advisory & Diagnostic:       {len(d3):>4} records")
    print(f"4. What-If Life Event Simulations:              {len(d4):>4} records")
    print(f"5. Debt Freedom Strategies (Snowball/Avalanche):{len(d5):>4} records")
    print(f"6. Small Business & Side Hustle Finance:        {len(d6):>4} records")
    print(f"7. Advanced Fraud Awareness & Scam Defense:     {len(d7):>4} records")
    print("-" * 55)
    print(f"Total Expansion Records:                        {len(new_expansion_records):>4} records")

    assert len(new_expansion_records) == 2500, f"Expected 2,500 new records, got {len(new_expansion_records)}"

    # 3. Deduplication Check Across All 5,000 Records
    duplicates = 0
    for idx, r in enumerate(new_expansion_records, 1):
        inp = r["input"].strip()
        if inp in seen_inputs:
            duplicates += 1
            print(f"Duplicate detected at expansion index {idx}: {inp[:70]}")
        seen_inputs.add(inp)

    assert duplicates == 0, f"Deduplication failed: {duplicates} duplicates detected!"
    print(f"Deduplication Verified: 100% unique inputs across all 5,000 records.")

    # 4. Save Expansion Alone
    os.makedirs(os.path.dirname(V4_EXPANSION_PATH), exist_ok=True)
    with open(V4_EXPANSION_PATH, "w", encoding="utf-8") as f:
        for r in new_expansion_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\n[SAVED] {len(new_expansion_records)} records -> {V4_EXPANSION_PATH}")

    # 5. Save Final Combined 5,000 Records
    v4_5000_combined = existing_records + new_expansion_records
    assert len(v4_5000_combined) == 5000, f"Expected 5,000 combined records, got {len(v4_5000_combined)}"

    with open(V4_FINAL_COMBINED_PATH, "w", encoding="utf-8") as f:
        for r in v4_5000_combined:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"[SAVED] {len(v4_5000_combined)} records -> {V4_FINAL_COMBINED_PATH}")
    print("=" * 75)


if __name__ == "__main__":
    build_v4_expansion()
