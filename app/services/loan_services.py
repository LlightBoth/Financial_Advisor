from app.models import Rule, Fact
# from app.services.history_services import HistoryServices

from flask_login import current_user

class LoanServices:
    @staticmethod
    def get_advise(data: dict):
        loan_goal = data.get("loan_goal", 0)
        loan_term = data["loan_term"],
        repayment_frequency = data["repayment_frequency"],
        loan_history = data["loan_history"],
        total_debt_amount = data.get("total_debt_amount", 0)
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
                "loan_goal": loan_goal,
                "loan_term": loan_term,
                "repayment_frequency": repayment_frequency,
                "loan_history": loan_history,
                "total_debt_amount": total_debt_amount,
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

        advice_data = {
            "loan_goal": loan_goal,
            "loan_term": loan_term,
            "repayment_frequency": repayment_frequency,
            "loan_history": loan_history,
            "total_debt_amount": total_debt_amount,
            "income": income,
            "expense": expense,
            "martial_status": martial_status,
            "is_employed": is_employed,
            "is_debt": is_debt,
            "is_spending": is_spending,
            "remain_percentage": remain_percentage * 100,
            "expense_percentage": expense_percentage * 100
        }
        
        # Save to history
        # HistoryServices.create(advice_data, current_user)

        # Debug
        # for k, v in advice_data.items():
        #     print(f"DEBUG: {k} -> {v}")

        return advice_data
