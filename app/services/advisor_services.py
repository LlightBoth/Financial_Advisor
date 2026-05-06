from app.models import Rule, Fact
from app.services.history_services import HistoryServices

from flask_login import current_user

class AdvisorServices:
    @staticmethod
    def get_advise(data: dict):
        goal_cost = data.get("goal_cost", 0)
        income = data.get("income", 0)
        expense = data.get("expense", 0)
        martial_status = data["martial_status"]
        is_employed = data.get("is_employed", "not employed")
        is_debt = data.get("is_debt", "no debt")
        is_spending = data.get("is_spending", "average spend")

        # Guard
        if income <= 0:
            class EmptyAdvice:
                certainty = 0
                advice = "No advice available"
                conclusion = "No conclusion"
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
            # fallback
            class EmptyAdvice:
                certainty = 0
                advice = "No advice available"
                conclusion = "No conclusion"
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
        
        # Save to history
        HistoryServices.create(advice_data, current_user)

        # Debug
        # for k, v in advice_data.items():
        #     print(f"DEBUG: {k} -> {v}")

        return advice_data
