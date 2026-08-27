from app.models import Rule, Fact
from app.services.history_services import HistoryServices
from flask_login import current_user

class EmptyAdvice:
    certainty = 0.0
    advice = "No advice available"
    conclusion = "No conclusion"

class AdvisorServices:
    @staticmethod
    def get_advise(data: dict):
        goal_cost = data.get("goal_cost", 0)
        income = data.get("income", 0)
        expense = data.get("expense", 0)
        marital_status = data.get("marital_status", "")

        def clean_value(val):
            if not val or "unspecified" in str(val).lower() or val in ["Prefer not to say", ""]:
                return ""
            return val

        is_employed = clean_value(data.get("is_employed", ""))
        is_debt = clean_value(data.get("is_debt", ""))
        is_spending = clean_value(data.get("is_spending", ""))

        if income <= 0:
            return {
                "income": income,
                "expense": expense,
                "marital_status": marital_status,
                "is_employed": is_employed,
                "is_debt": is_debt,
                "is_spending": is_spending,
                "remain_percentage": 0,
                "expense_percentage": 0,
                "get_advice": EmptyAdvice()
            }

        # Calculate percentages
        remain_percentage = (income - expense) / income  # This is SAVINGS POTENTIAL
        expense_percentage = expense / income

        # Cetatinty Factor Formula
        certainty_factor = (income - expense) / goal_cost

        # -------------------------------------------------------------
        # Map Certainty Directly from SAVINGS POTENTIAL (remain_percentage)
        # -------------------------------------------------------------
        # < 0.25 (25%)  --> 0.25 Certainty Tier
        # 0.25 to 0.75 --> 0.50 Certainty Tier
        # > 0.75 (75%)  --> 0.75 Certainty Tier
        if certainty_factor < 0.25:
            target_certainty = 0.25
        elif certainty_factor <= 0.75:
            target_certainty = 0.50
        else:
            target_certainty = 0.75

        user_tags = {tag for tag in [is_employed, is_debt, is_spending] if tag != ""}

        def get_no_conditions_rule():
            # Query 'No Condition' rule matching the calculated certainty tier
            rule = Rule.query.filter(~Rule.facts.any(), Rule.certainty == target_certainty).first()
            if not rule:
                rule = Rule.query.filter(~Rule.facts.any()).first()
            return rule if rule else EmptyAdvice()

        # SCENARIO 27: No behavioral conditions selected
        if len(user_tags) == 0:
            best_rule = get_no_conditions_rule()
        else:
            # Query database rules matching target_certainty
            candidate_rules = Rule.query.filter(Rule.certainty == target_certainty).all()

            # Fallback to all rules if no exact certainty match exists
            if not candidate_rules:
                candidate_rules = Rule.query.all()

            candidates = []
            for r in candidate_rules:
                rule_tags = {f.tags for f in r.facts}
                matches = len(user_tags.intersection(rule_tags))
                
                if matches > 0:
                    candidates.append((matches, r))

            if candidates:
                candidates.sort(key=lambda x: x[0], reverse=True)
                best_rule = candidates[0][1]
            else:
                best_rule = get_no_conditions_rule()

        advice_data = {
            "goal_cost": goal_cost,
            "income": income,
            "expense": expense,
            "marital_status": marital_status,
            "is_employed": is_employed,
            "is_debt": is_debt,
            "is_spending": is_spending,
            "remain_percentage": remain_percentage * 100,
            "expense_percentage": expense_percentage * 100,
            "get_advice": best_rule
        }

        HistoryServices.create(advice_data, current_user)
        return advice_data


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