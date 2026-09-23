from app.models import Rule
from flask_login import current_user


class EmptyAdvice:
    certainty = 0.0
    advice = []
    conclusion = "No recommendations are currently available."


class AdvisorServices:
    @staticmethod
    def _evaluate_condition(condition, facts):
        actual_value = facts.get(condition.fact)

        if actual_value is None:
            return False

        if condition.value_fact:
            expected_value = facts.get(condition.value_fact)
        else:
            expected_value = condition.value

        if expected_value is None:
            return False

        try:
            if condition.operator in ("greater_than", ">"):
                return actual_value > expected_value

            if condition.operator in ("greater_than_or_equal", ">="):
                return actual_value >= expected_value

            if condition.operator in ("less_than", "<"):
                return actual_value < expected_value

            if condition.operator in ("less_than_or_equal", "<="):
                return actual_value <= expected_value

            if condition.operator in ("equal", "equals", "=="):
                return actual_value == expected_value

            if condition.operator in ("not_equal", "!="):
                return actual_value != expected_value

            if condition.operator == "contains":
                return expected_value in actual_value

            if condition.operator == "in":
                return actual_value in expected_value

        except (TypeError, ValueError):
            return False

        return False

    @staticmethod
    def _rule_matches(rule, facts):
        # A rule without conditions is treated as a general rule.
        if not rule.conditions:
            return True

        # All conditions belonging to a rule must match.
        return all(
            AdvisorServices._evaluate_condition(condition, facts)
            for condition in rule.conditions
        )

    @staticmethod
    def persoal_analyse(data: dict):
        goal_cost = float(data.get("goal_cost", 0.0))
        income = float(data.get("income", 0.0))
        expense = float(data.get("expense", 0.0))
        marital_status = data.get("marital_status", "Single")

        if income <= 0:
            return {
                "income": income,
                "expense": expense,
                "goal_cost": goal_cost,
                "marital_status": marital_status,
                "monthly_surplus": 0.0,
                "remain_percentage": 0.0,
                "expense_percentage": 0.0,
                "target_certainty": 0.0,
                "get_advice": EmptyAdvice(),
                "matched_rules": []
            }

        monthly_surplus = income - expense
        remain_percentage = monthly_surplus / income
        expense_percentage = expense / income

        # Facts available to the rule engine.
        facts = {
            "monthly_income": income,
            "monthly_expense": expense,
            "monthly_surplus": monthly_surplus,
            "savings_rate": remain_percentage,
            "expense_rate": expense_percentage,
            "marital_status": marital_status,
            "goal_cost": goal_cost,
        }

        # Load all rules.
        rules = Rule.query.order_by(Rule.id.asc()).all()

        # Evaluate every rule against the user's financial facts.
        matched_rules = [
            rule
            for rule in rules
            if AdvisorServices._rule_matches(rule, facts)
        ]

        # Highest certainty first.
        matched_rules.sort(
            key=lambda rule: rule.certainty,
            reverse=True
        )

        # Keep the highest-certainty recommendation for compatibility
        # with templates that expect advice["get_advice"].
        best_rule = (
            matched_rules[0]
            if matched_rules
            else EmptyAdvice()
        )

        return {
            "income": income,
            "expense": expense,
            "goal_cost": goal_cost,
            "marital_status": marital_status,
            "monthly_surplus": monthly_surplus,
            "remain_percentage": remain_percentage * 100,
            "expense_percentage": expense_percentage * 100,
            "target_certainty": getattr(best_rule, "certainty", 0.0),
            "get_advice": best_rule,
            "matched_rules": matched_rules,
            "facts": facts,
        }
