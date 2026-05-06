from typing import Optional

from app.models.history import History
from app.models.user import User

from extension import db


class HistoryServices:
    @staticmethod
    def get_all_history(current_user_id):
        return History.query.filter(History.users.any(id=current_user_id.id)).all()

    @staticmethod
    def get_user_history_id(history_id, user):
        return History.query.filter(
            History.id == history_id,
            History.users.any(id=user.id)
            ).first()
    
    @staticmethod 
    def create(data: dict, current_user: User):
        advice_obj = data["get_advice"]

        # If it’s your EmptyAdvice object, make sure fields exist
        advice_text = getattr(advice_obj, "advice", str(advice_obj))
        conclusion_text = getattr(advice_obj, "conclusion", "")
        certainty_val = getattr(advice_obj, "certainty", 0.0)

        history = History(
            goal_cost = data.get("goal_cost", 0.0),
            income = data["income"],
            expense = data["expense"],
            martial_status = data["martial_status"],
            is_employed = True if data.get("is_employed") == "employed" else False,
            is_debt = True if data.get("is_debt") == "debt" else False,
            is_spending = True if data.get("is_spending") == "big spend" else False,
            remain_percentage = data["remain_percentage"],
            expense_percentage = data["expense_percentage"],
            get_advice = advice_text,
            get_conclusion = conclusion_text,
            get_certainty = certainty_val,
        )

        # Add to user in history
        history.users.append(current_user)

        # Add to session and commit
        db.session.add(history)
        db.session.commit()
        return history

    @staticmethod
    def delete_history(history: History):
        """Delete a history object that already belongs to a user."""
        if history:
            db.session.delete(history)
            db.session.commit()
            return True
        return False