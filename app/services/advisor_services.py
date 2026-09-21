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

    @staticmethod
    def get_advise(data: dict):
        goal_cost = data.get("goal_cost", 0)
        income = data.get("income", 0)
        expense = data.get("expense", 0)
        martial_status = data.get("martial_status", "Single")
        is_employed = data.get("is_employed", "not employed")
        is_debt = data.get("is_debt", "no debt")
        is_spending = data.get("is_spending", "average spend")

        # Guard
        if income <= 0:
            return {
                "income": income,
                "expense": expense,
                "martial_status": martial_status,
                "is_employed": is_employed,
                "is_debt": is_debt,
                "is_spending": is_spending,
                "remain_percentage": 0,
                "expense_percentage": 0,
                "get_advice": EmptyAdvice()
            }

        # Percentages
        remain_percentage = (income - expense) / income
        expense_percentage = expense / income

        # Candidate rules
        candidate_rules = Rule.query.filter(Rule.certainty <= expense_percentage).all()
        if not candidate_rules:
            best_rule = EmptyAdvice()
        else:
            # Tags from user
            user_tags = {is_employed, is_debt, is_spending}

            # Score rules by matching tags
            def score_rule(rule):
                rule_tags = {f.tags for f in rule.facts}
                matches = user_tags.intersection(rule_tags)
                return len(matches), rule.certainty  # prioritize more matches, then higher certainty

            scored = [(score_rule(r), r) for r in candidate_rules]
            scored.sort(key=lambda x: (x[0][0], x[0][1]), reverse=True)  # most matches first

            best_rule = scored[0][1] if scored else None

            # Cap certainty at 1.0
            if best_rule:
                best_rule.certainty = min(best_rule.certainty, 1.0)

        advice_data = {
            "goal_cost": goal_cost,
            "income": income,
            "expense": expense,
            "martial_status": martial_status,
            "is_employed": is_employed,
            "is_debt": is_debt,
            "is_spending": is_spending,
            "remain_percentage": remain_percentage * 100,
            "expense_percentage": expense_percentage * 100,
            "get_advice": best_rule
        }
        
        # Save to history if current_user is authenticated
        try:
            from app.services.history_services import HistoryServices
            if current_user and current_user.is_authenticated:
                HistoryServices.create(advice_data, current_user)
        except Exception:
            pass

        return advice_data