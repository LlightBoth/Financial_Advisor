import json
import os

from app.models.fact import Fact
from app.models.rule import Rule, RuleCondition
from extension import db


# ============================================================
# Project root:
# Financial_Advisor/
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)


# ============================================================
# JSON files
# ============================================================

FACTS_FILE = os.path.join(
    BASE_DIR,
    "app",
    "data",
    "facts.json"
)

RULES_FILE = os.path.join(
    BASE_DIR,
    "app",
    "data",
    "rules.json"
)


# ============================================================
# JSON Loader
# ============================================================

def load_json_file(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


# ============================================================
# Seed Facts
# ============================================================

def seed_system_facts():
    data = load_json_file(FACTS_FILE)

    facts_data = (
        data.get("facts", data)
        if isinstance(data, dict)
        else data
    )

    for fact_data in facts_data:

        existing = Fact.query.filter_by(
            tags=fact_data["tags"]
        ).first()

        if not existing:
            fact = Fact(
                tags=fact_data["tags"],
                description=fact_data["description"],
                type=fact_data["type"],
                value=fact_data.get("value"),
            )

            db.session.add(fact)

        else:
            existing.description = fact_data["description"]
            existing.type = fact_data["type"]
            existing.value = fact_data.get("value")

    db.session.commit()

    print(f"Seeded {len(facts_data)} facts.")


# ============================================================
# Seed Rules
# ============================================================

def seed_system_rules():
    data = load_json_file(RULES_FILE)

    rules_data = data.get("rules", [])

    for rule_data in rules_data:

        # ----------------------------------------------------
        # Find existing rule
        # ----------------------------------------------------

        rule = Rule.query.filter_by(
            name=rule_data["name"]
        ).first()

        # ----------------------------------------------------
        # Create rule if it doesn't exist
        # ----------------------------------------------------

        if not rule:
            rule = Rule(
                name=rule_data["name"],
                conclusion=rule_data["conclusion"],
                certainty=rule_data["certainty"],
                advice=rule_data["advice"],
            )

            db.session.add(rule)
            db.session.flush()

        # ----------------------------------------------------
        # Update existing rule
        # ----------------------------------------------------

        else:
            rule.conclusion = rule_data["conclusion"]
            rule.certainty = rule_data["certainty"]
            rule.advice = rule_data["advice"]

        # ----------------------------------------------------
        # Remove old conditions
        # ----------------------------------------------------

        RuleCondition.query.filter_by(
            rule_id=rule.id
        ).delete(
            synchronize_session=False
        )

        # ----------------------------------------------------
        # Add new conditions
        #
        # A condition must have:
        #
        #   fact + operator + value_fact
        #
        # OR
        #
        #   fact + operator + value
        #
        # Examples:
        #
        # {
        #     "fact": "monthly_income",
        #     "operator": "greater_than",
        #     "value_fact": "monthly_expense"
        # }
        #
        # {
        #     "fact": "has_savings",
        #     "operator": "equals",
        #     "value": true
        # }
        # ----------------------------------------------------

        for condition_data in rule_data.get("conditions", []):

            # Required fields for every condition
            required_fields = [
                "fact",
                "operator",
            ]

            missing_fields = [
                field
                for field in required_fields
                if field not in condition_data
            ]

            if missing_fields:
                raise ValueError(
                    f"Invalid condition in rule "
                    f"'{rule_data['name']}': "
                    f"missing {missing_fields}. "
                    f"Condition: {condition_data}"
                )

            # ------------------------------------------------
            # Condition must have either:
            #
            # value_fact
            # OR
            # value
            # ------------------------------------------------

            has_value_fact = (
                "value_fact" in condition_data
                and condition_data["value_fact"] is not None
            )

            has_value = (
                "value" in condition_data
            )

            if not has_value_fact and not has_value:
                raise ValueError(
                    f"Invalid condition in rule "
                    f"'{rule_data['name']}': "
                    f"condition must contain either "
                    f"'value_fact' or 'value'. "
                    f"Condition: {condition_data}"
                )

            # ------------------------------------------------
            # Prevent both from being supplied accidentally
            # ------------------------------------------------

            if has_value_fact and has_value:
                raise ValueError(
                    f"Invalid condition in rule "
                    f"'{rule_data['name']}': "
                    f"condition cannot contain both "
                    f"'value_fact' and 'value'. "
                    f"Condition: {condition_data}"
                )

            # ------------------------------------------------
            # Create RuleCondition
            # ------------------------------------------------

            condition = RuleCondition(
                rule_id=rule.id,
                fact=condition_data["fact"],
                operator=condition_data["operator"],
                value_fact=condition_data.get("value_fact"),
                value=condition_data.get("value"),
            )

            db.session.add(condition)

    db.session.commit()

    print(f"Seeded {len(rules_data)} rules.")


# ============================================================
# Seed Complete Financial System
# ============================================================

def seed_financial_system():
    seed_system_facts()
    seed_system_rules()

    print("Financial system seed completed successfully.")
