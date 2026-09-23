import json
import os

from app.models.fact import Fact
from app.models.rule import Rule, RuleCondition
from extension import db


# ============================================================
# Step 7D Consultant Fact Taxonomy
# ============================================================

CONSULTANT_FACTS = [
    {
        "fact_key": "income_positive",
        "tags": "income_positive",
        "category": "INFLOW",
        "data_type": "boolean",
        "origin": "derived",
        "type": "boolean",
        "value": False,
        "description": "User has positive monthly cash inflow (monthly_income > 0.0)."
    },
    {
        "fact_key": "income_zero",
        "tags": "income_zero",
        "category": "INFLOW",
        "data_type": "boolean",
        "origin": "derived",
        "type": "boolean",
        "value": False,
        "description": "User has zero monthly incoming cash inflow (monthly_income == 0.0)."
    },
    {
        "fact_key": "employment_status",
        "tags": "employment_status",
        "category": "INFLOW",
        "data_type": "string",
        "origin": "input",
        "type": "string",
        "value": "employed",
        "description": "Self-reported employment standing ('employed' or 'not employed')."
    },
    {
        "fact_key": "cashflow_deficit",
        "tags": "cashflow_deficit",
        "category": "CASHFLOW",
        "data_type": "boolean",
        "origin": "derived",
        "type": "boolean",
        "value": False,
        "description": "Total monthly expenses exceed monthly income (net_cashflow < 0.0)."
    },
    {
        "fact_key": "cashflow_balanced",
        "tags": "cashflow_balanced",
        "category": "CASHFLOW",
        "data_type": "boolean",
        "origin": "derived",
        "type": "boolean",
        "value": False,
        "description": "Monthly income exactly equals monthly expenses (net_cashflow == 0.0)."
    },
    {
        "fact_key": "cashflow_surplus",
        "tags": "cashflow_surplus",
        "category": "CASHFLOW",
        "data_type": "boolean",
        "origin": "derived",
        "type": "boolean",
        "value": False,
        "description": "Monthly income exceeds monthly expenses (net_cashflow > 0.0)."
    },
    {
        "fact_key": "expense_tier_tight",
        "tags": "expense_tier_tight",
        "category": "EXPENDITURE",
        "data_type": "boolean",
        "origin": "derived",
        "type": "boolean",
        "value": False,
        "description": "Living expenses consume 80% or more of positive income (expense_ratio >= 0.80)."
    },
    {
        "fact_key": "expense_tier_balanced",
        "tags": "expense_tier_balanced",
        "category": "EXPENDITURE",
        "data_type": "boolean",
        "origin": "derived",
        "type": "boolean",
        "value": False,
        "description": "Living expenses consume between 50% and 80% of income (0.50 <= expense_ratio < 0.80)."
    },
    {
        "fact_key": "expense_tier_flexible",
        "tags": "expense_tier_flexible",
        "category": "EXPENDITURE",
        "data_type": "boolean",
        "origin": "derived",
        "type": "boolean",
        "value": False,
        "description": "Living expenses consume less than 50% of positive income (expense_ratio < 0.50)."
    },
    {
        "fact_key": "spending_habit",
        "tags": "spending_habit",
        "category": "EXPENDITURE",
        "data_type": "string",
        "origin": "input",
        "type": "string",
        "value": "average spend",
        "description": "Self-reported perception of discretionary spending intensity ('big spend' or 'average spend')."
    },
    {
        "fact_key": "debt_present",
        "tags": "debt_present",
        "category": "LIABILITY",
        "data_type": "boolean",
        "origin": "derived",
        "type": "boolean",
        "value": False,
        "description": "User has reported active debt obligations."
    },
    {
        "fact_key": "debt_free",
        "tags": "debt_free",
        "category": "LIABILITY",
        "data_type": "boolean",
        "origin": "derived",
        "type": "boolean",
        "value": True,
        "description": "User has reported no active debt obligations."
    },
    {
        "fact_key": "goal_cost_present",
        "tags": "goal_cost_present",
        "category": "MILESTONE",
        "data_type": "boolean",
        "origin": "derived",
        "type": "boolean",
        "value": False,
        "description": "User has defined a positive target milestone goal cost (goal_cost > 0.0)."
    },
]


# ============================================================
# Step 7D Canonical Financial Consultant Rules
# ============================================================

CONSULTANT_RULES = [
    # Category 1: CASHFLOW_DEFICIT_MANAGEMENT (Priority: 100)
    {
        "rule_id": "DEFICIT_WITH_DEBT",
        "name": "Operating Deficit With Active Debt",
        "category": "CASHFLOW_DEFICIT_MANAGEMENT",
        "priority": 100,
        "certainty": 1.00,
        "match_operator": "ALL",
        "conditions": [
            {"field": "net_cashflow", "operator": "<", "value": 0},
            {"field": "debt_present", "operator": "==", "value": True}
        ],
        "conclusion_en": "Operating Cashflow Deficit with Active Debt Obligations",
        "conclusion_km": "ឱនភាពលំហូរសាច់ប្រាក់ប្រតិបត្តិការ ជាមួយកាតព្វកិច្ចបំណុលសកម្ម",
        "advice_en": "Monthly expenses exceed income while debt obligations are present. Restructure non-essential spending immediately and prioritize minimum debt obligations to avoid compounding fees.",
        "advice_km": "ការចំណាយប្រចាំខែលើសពីប្រាក់ចំណូល ខណៈពេលដែលមានកាតព្វកិច្ចបំណុល។ សូមរៀបចំរចនាសម្ព័ន្ធការចំណាយមិនចាំបាច់ឡើងវិញជាបន្ទាន់ និងផ្តល់អាទិភាពដល់ការទូទាត់បំណុលអប្បបរមា ដើម្បីជៀសវាងការកើនឡើងនៃថ្លៃសេវា។",
        "knowledge_refs": ["K001", "K002", "K014"]
    },
    {
        "rule_id": "DEFICIT_NO_DEBT",
        "name": "Operating Cashflow Deficit",
        "category": "CASHFLOW_DEFICIT_MANAGEMENT",
        "priority": 100,
        "certainty": 1.00,
        "match_operator": "ALL",
        "conditions": [
            {"field": "net_cashflow", "operator": "<", "value": 0},
            {"field": "debt_present", "operator": "==", "value": False}
        ],
        "conclusion_en": "Operating Cashflow Deficit",
        "conclusion_km": "ឱនភាពលំហូរសាច់ប្រាក់ប្រតិបត្តិការ",
        "advice_en": "Monthly expenses exceed income. Review recurring living expenditures to restore cash flow to a positive balance before committing to new financial goals.",
        "advice_km": "ការចំណាយប្រចាំខែលើសពីប្រាក់ចំណូល។ ពិនិត្យឡើងវិញនូវការចំណាយប្រចាំថ្ងៃ ដើម្បីស្តារលំហូរសាច់ប្រាក់ឱ្យមានតុល្យភាពវិជ្ជមាន មុនពេលប្តេជ្ញាចិត្តចំពោះគោលដៅហិរញ្ញវត្ថុថ្មីៗ។",
        "knowledge_refs": ["K001", "K002"]
    },
    {
        "rule_id": "INCOME_ZERO_UNEMPLOYED",
        "name": "Absence of Active Income Inflow",
        "category": "CASHFLOW_DEFICIT_MANAGEMENT",
        "priority": 100,
        "certainty": 1.00,
        "match_operator": "ALL",
        "conditions": [
            {"field": "income_zero", "operator": "==", "value": True},
            {"field": "employment_status", "operator": "==", "value": "not employed"}
        ],
        "conclusion_en": "Absence of Active Income Inflow",
        "conclusion_km": "អវត្តមាននៃលំហូរប្រាក់ចំណូលសកម្ម",
        "advice_en": "No regular earned income is reported. Restrict spending strictly to survival necessities while focusing on emergency income sources or community assistance.",
        "advice_km": "មិនមានប្រាក់ចំណូលទៀងទាត់ត្រូវបានរាយការណ៍ទេ។ សូមកាត់បន្ថយការចំណាយត្រឹមតែតម្រូវការចាំបាច់បំផុត ខណៈពេលស្វែងរកប្រភពចំណូលបន្ទាន់ ឬជំនួយសហគមន៍។",
        "knowledge_refs": ["K001", "K002"]
    },

    # Category 2: OPERATING_BREAK_EVEN (Priority: 80)
    {
        "rule_id": "BREAK_EVEN_ZERO_MARGIN",
        "name": "Break-Even Cashflow With Zero Margin",
        "category": "OPERATING_BREAK_EVEN",
        "priority": 80,
        "certainty": 1.00,
        "match_operator": "ALL",
        "conditions": [
            {"field": "net_cashflow", "operator": "==", "value": 0},
            {"field": "income_positive", "operator": "==", "value": True}
        ],
        "conclusion_en": "Break-Even Cashflow with Zero Operating Margin",
        "conclusion_km": "លំហូរសាច់ប្រាក់ស្មើចំណាយ (គ្មានរឹមសល់)",
        "advice_en": "Exactly 100% of income is consumed by expenses. While not in deficit, any unexpected cost poses a borrowing risk. Seek minor spending adjustments to establish an initial cash buffer.",
        "advice_km": "ប្រាក់ចំណូល ១០០% ត្រូវបានចំណាយអស់។ ទោះបីជាមិនមានឱនភាពក៏ដោយ ការចំណាយមិនរំពឹងទុកណាមួយអាចបង្កហានិភ័យនៃការខ្ចីបុល។ សូមកែសម្រួលការចំណាយបន្តិចបន្តួចដើម្បីបង្កើតសតិបណ្ដោះអាសន្ន។",
        "knowledge_refs": ["K001", "K003"]
    },
    {
        "rule_id": "TIGHT_MARGIN_HIGH_EXPENSE",
        "name": "Narrow Operating Margin (Tight Budget)",
        "category": "OPERATING_BREAK_EVEN",
        "priority": 80,
        "certainty": 0.70,
        "match_operator": "ALL",
        "conditions": [
            {"field": "net_cashflow", "operator": ">", "value": 0},
            {"field": "expense_ratio", "operator": ">=", "value": 0.80},
            {"field": "debt_present", "operator": "==", "value": False}
        ],
        "conclusion_en": "Narrow Operating Margin (Tight Budget)",
        "conclusion_km": "រឹមប្រតិបត្តិការតឹងតែង (ថវិកាតឹង)",
        "advice_en": "Operating cash flow is positive, but living costs consume 80% or more of income. Consider identifying flexible expenses to increase your monthly buffer against unplanned shocks.",
        "advice_km": "លំហូរសាច់ប្រាក់ប្រតិបត្តិការមានវិជ្ជមាន ប៉ុន្តែការចំណាយប្រចាំថ្ងៃស្រូបយក ៨០% ឬច្រើនជាងនេះនៃប្រាក់ចំណូល។ ពិចារណាកាត់បន្ថយការចំណាយមិនចាំបាច់ ដើម្បីបង្កើនប្រាក់បម្រុង។",
        "knowledge_refs": ["K004", "K005", "K007"]
    },

    # Category 3: DEBT_SERVICING_ACCELERATION (Priority: 60)
    {
        "rule_id": "SURPLUS_WITH_DEBT_SERVICING",
        "name": "Positive Cashflow With Active Debt Obligations",
        "category": "DEBT_SERVICING_ACCELERATION",
        "priority": 60,
        "certainty": 0.85,
        "match_operator": "ALL",
        "conditions": [
            {"field": "net_cashflow", "operator": ">", "value": 0},
            {"field": "debt_present", "operator": "==", "value": True}
        ],
        "conclusion_en": "Positive Cashflow with Active Debt Obligations",
        "conclusion_km": "លំហូរសាច់ប្រាក់វិជ្ជមាន ជាមួយកាតព្វកិច្ចបំណុលសកម្ម",
        "advice_en": "A sustainable cash flow surplus exists. Consider dedicating a significant portion of this surplus toward structured debt payoff (e.g., targeting highest-interest obligations first).",
        "advice_km": "មានអតិរេកលំហូរសាច់ប្រាក់ប្រកបដោយនិរន្តរភាព។ ពិចារណាបែងចែកផ្នែកធំនៃអតិរេកនេះឆ្ពោះទៅរកការទូទាត់បំណុលដែលមានរចនាសម្ព័ន្ធ (ឧ. ផ្តោតលើបំណុលដែលមានការប្រាក់ខ្ពស់ជាងគេមុន)។",
        "knowledge_refs": ["K004", "K008", "K014"]
    },

    # Category 4: STABLE_BUFFER_BUILDING (Priority: 40)
    {
        "rule_id": "BALANCED_BUDGET_BUFFER_BUILDING",
        "name": "Balanced Operating Budget",
        "category": "STABLE_BUFFER_BUILDING",
        "priority": 40,
        "certainty": 0.85,
        "match_operator": "ALL",
        "conditions": [
            {"field": "net_cashflow", "operator": ">", "value": 0},
            {"field": "expense_ratio", "operator": ">=", "value": 0.50},
            {"field": "expense_ratio", "operator": "<", "value": 0.80},
            {"field": "debt_present", "operator": "==", "value": False}
        ],
        "conclusion_en": "Balanced Operating Budget",
        "conclusion_km": "ថវិកាប្រតិបត្តិការមានតុល្យភាព",
        "advice_en": "Your living expenses are well-balanced (consuming between 50% and 80% of income). If you do not yet have an emergency reserve, prioritize building 3 to 6 months of essential living expenses.",
        "advice_km": "ការចំណាយប្រចាំថ្ងៃរបស់អ្នកមានតុល្យភាពល្អ (ចន្លោះពី ៥០% ទៅ ៨០% នៃប្រាក់ចំណូល)។ ប្រសិនបើអ្នកមិនទាន់មានប្រាក់បម្រុងបន្ទាន់ទេ សូមផ្តល់អាទិភាពដល់ការសន្សំប្រាក់សម្រាប់ ៣ ទៅ ៦ ខែនៃការចំណាយចាំបាច់។",
        "knowledge_refs": ["K004", "K008", "K013"]
    },

    # Category 5: GOAL_CAPITAL_ACCUMULATION (Priority: 20)
    {
        "rule_id": "FLEXIBLE_BUDGET_CAPITAL_GROWTH",
        "name": "Substantial Operating Surplus & Capital Growth",
        "category": "GOAL_CAPITAL_ACCUMULATION",
        "priority": 20,
        "certainty": 0.70,
        "match_operator": "ALL",
        "conditions": [
            {"field": "net_cashflow", "operator": ">", "value": 0},
            {"field": "expense_ratio", "operator": "<", "value": 0.50},
            {"field": "debt_present", "operator": "==", "value": False}
        ],
        "conclusion_en": "Substantial Operating Surplus & Capital Accumulation",
        "conclusion_km": "អតិរេកប្រតិបត្តិការច្រើន និងការប្រមូលផ្តុំទុន",
        "advice_en": "Living expenses consume less than 50% of income, creating strong savings capacity. Allocate your surplus toward your stated milestone goals and long-term financial objectives.",
        "advice_km": "ការចំណាយប្រចាំថ្ងៃប្រើប្រាស់តិចជាង ៥០% នៃប្រាក់ចំណូល ដែលបង្កើតបានសមត្ថភាពសន្សំយ៉ាងរឹងមាំ។ បែងចែកអតិរេករបស់អ្នកឆ្ពោះទៅរកគោលដៅហិរញ្ញវត្ថុដែលបានគ្រោងទុក។",
        "knowledge_refs": ["K004", "K009", "K010"]
    }
]


# ============================================================
CANONICAL_KB_VERSION = "financial-kb-v1.0"

CANONICAL_RULE_IDS = frozenset([
    "DEFICIT_WITH_DEBT",
    "DEFICIT_NO_DEBT",
    "INCOME_ZERO_UNEMPLOYED",
    "BREAK_EVEN_ZERO_MARGIN",
    "TIGHT_MARGIN_HIGH_EXPENSE",
    "SURPLUS_WITH_DEBT_SERVICING",
    "BALANCED_BUDGET_BUFFER_BUILDING",
    "FLEXIBLE_BUDGET_CAPITAL_GROWTH",
])

CANONICAL_FACT_KEYS = frozenset([f["fact_key"] for f in CONSULTANT_FACTS])


# ============================================================
# Seed Functions
# ============================================================

def seed_consultant_facts():
    """Seeds and reconciles the 13 canonical consultant facts without deleting legacy facts."""
    for f_data in CONSULTANT_FACTS:
        existing = Fact.query.filter(
            (Fact.fact_key == f_data["fact_key"]) | (Fact.tags == f_data["tags"])
        ).first()

        if not existing:
            fact = Fact(
                fact_key=f_data["fact_key"],
                category=f_data["category"],
                data_type=f_data["data_type"],
                origin=f_data["origin"],
                tags=f_data["tags"],
                description=f_data["description"],
                type=f_data["type"],
                value=f_data["value"],
                kb_version=CANONICAL_KB_VERSION,
            )
            db.session.add(fact)
        else:
            existing.fact_key = f_data["fact_key"]
            existing.category = f_data["category"]
            existing.data_type = f_data["data_type"]
            existing.origin = f_data["origin"]
            existing.description = f_data["description"]
            existing.kb_version = CANONICAL_KB_VERSION

    # Preserve all legacy facts while guaranteeing kb_version is NULL
    Fact.query.filter(
        (Fact.fact_key.is_(None)) | (~Fact.fact_key.in_(CANONICAL_FACT_KEYS))
    ).update({"kb_version": None}, synchronize_session=False)

    db.session.commit()
    print(f"Seeded/verified {len(CONSULTANT_FACTS)} Step 7F canonical consultant facts.")


def seed_consultant_rules():
    """Seeds the 8 canonical consultant rules, tags with financial-kb-v1.0, and deactivates legacy rules."""
    # 1. Deactivate all legacy rules and ensure kb_version is NULL (zero destruction)
    Rule.query.filter(
        (Rule.rule_id.is_(None)) | (~Rule.rule_id.in_(CANONICAL_RULE_IDS))
    ).update({"is_active": False, "kb_version": None}, synchronize_session=False)

    # 2. Reconcile and activate the 8 canonical rules
    for r_data in CONSULTANT_RULES:
        rule = Rule.query.filter_by(rule_id=r_data["rule_id"]).first()

        if not rule:
            # Check if matching by name exists
            rule = Rule.query.filter_by(name=r_data["name"]).first()

        if not rule:
            rule = Rule(
                rule_id=r_data["rule_id"],
                name=r_data["name"],
                category=r_data["category"],
                priority=r_data["priority"],
                certainty=r_data["certainty"],
                match_operator=r_data["match_operator"],
                conditions_json=r_data["conditions"],
                conclusion_en=r_data["conclusion_en"],
                conclusion_km=r_data["conclusion_km"],
                advice_en=r_data["advice_en"],
                advice_km=r_data["advice_km"],
                knowledge_refs=r_data["knowledge_refs"],
                conclusion=r_data["conclusion_en"],
                advice=r_data["advice_en"],
                is_active=True,
                kb_version=CANONICAL_KB_VERSION,
            )
            db.session.add(rule)
            db.session.flush()
        else:
            rule.rule_id = r_data["rule_id"]
            rule.name = r_data["name"]
            rule.category = r_data["category"]
            rule.priority = r_data["priority"]
            rule.certainty = r_data["certainty"]
            rule.match_operator = r_data["match_operator"]
            rule.conditions_json = r_data["conditions"]
            rule.conclusion_en = r_data["conclusion_en"]
            rule.conclusion_km = r_data["conclusion_km"]
            rule.advice_en = r_data["advice_en"]
            rule.advice_km = r_data["advice_km"]
            rule.knowledge_refs = r_data["knowledge_refs"]
            rule.conclusion = r_data["conclusion_en"]
            rule.advice = r_data["advice_en"]
            rule.is_active = True
            rule.kb_version = CANONICAL_KB_VERSION

        # Clear and sync RuleCondition entities for compatibility with older query tools
        RuleCondition.query.filter_by(rule_id=rule.id).delete(synchronize_session=False)
        for cond_data in r_data["conditions"]:
            rc = RuleCondition(
                rule_id=rule.id,
                fact=cond_data["field"],
                operator=cond_data["operator"],
                value=cond_data.get("value"),
                value_fact=cond_data.get("value_fact")
            )
            db.session.add(rc)

    db.session.commit()
    print(f"Seeded/verified {len(CONSULTANT_RULES)} Step 7F canonical consultant rules.")


def seed_financial_system():
    """Main seed entry point called during app initialization."""
    seed_consultant_facts()
    seed_consultant_rules()
    print("Step 7F financial system seed completed successfully.")
