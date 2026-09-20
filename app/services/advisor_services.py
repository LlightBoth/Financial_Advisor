from app.models import Rule, Fact
from flask_login import current_user

class EmptyAdvice:
    certainty = 0.0
    advice = "No advice available"
    conclusion = "No conclusion"

class AdvisorServices:

    @staticmethod
    def persoal_analyse(data: dict):
        goal_cost = data.get("goal_cost", 0.0)
        income = data.get("income", 0.0)
        expense = data.get("expense", 0.0)
        marital_status = data.get("marital_status", "Single")

        # Guard: Invalid or zero income
        if income <= 0:
            return {
                "income": income,
                "expense": expense,
                "goal_cost": goal_cost,
                "marital_status": marital_status,
                "remain_percentage": 0.0,
                "expense_percentage": 0.0,
                "target_certainty": 0.25,
                "get_advice": EmptyAdvice()
            }

        # Calculate cash flow percentages
        remain_percentage = (income - expense) / income  # Savings Potential
        expense_percentage = expense / income           # Expense Load

        # Determine Certainty Tier strictly based on Savings Potential
        if remain_percentage < 0.25:
            target_certainty = 0.25
        elif remain_percentage <= 0.75:
            target_certainty = 0.50
        else:
            target_certainty = 0.75

        # Query the "No Conditions" rule matching the target certainty tier
        best_rule = Rule.query.filter(
            ~Rule.facts.any(),
            Rule.certainty == target_certainty
        ).first()

        # Fallback if specific certainty tier isn't found
        if not best_rule:
            best_rule = Rule.query.filter(~Rule.facts.any()).first() or EmptyAdvice()

        advise_data = {
            "goal_cost": goal_cost,
            "income": income,
            "expense": expense,
            "marital_status": marital_status,
            "remain_percentage": remain_percentage * 100,
            "expense_percentage": expense_percentage * 100,
            "target_certainty": target_certainty,
            "get_advice": best_rule
        }

        return advise_data