from app.models.history import History
from app.models.user import User
from extension import db


class HistoryServices:
    @staticmethod
    def get_all_total_history():
        return History.query.all()
    
    @staticmethod
    def get_all_history(current_user):
        return History.query.filter(History.users.any(id=current_user.id)).order_by(History.created_at.desc()).all()

    @staticmethod
    def get_user_history_id(history_id: int, user):
        return History.query.filter(
            History.id == history_id,
            History.users.any(id=user.id)
        ).first()
    
    @staticmethod 
    def create(data: dict, current_user: User):
        try:
            advice_obj = data.get("get_advice")
            advice_text = getattr(advice_obj, "advice", str(advice_obj)) if advice_obj else ""
            conclusion_text = getattr(advice_obj, "conclusion", "") if advice_obj else ""
            certainty_val = getattr(advice_obj, "certainty", 0.0) if advice_obj else 0.0

            history = History(
                goal_cost=data.get("goal_cost", 0.0),
                income=data["income"],
                expense=data["expense"],
                martial_status=data.get("martial_status") or data.get("marital_status", "Single"),
                is_employed=True if data.get("is_employed") in (True, "employed") else False,
                is_debt=True if data.get("is_debt") in (True, "debt") else False,
                is_spending=True if data.get("is_spending") in (True, "big spend") else False,
                remain_percentage=data.get("remain_percentage", 0.0),
                expense_percentage=data.get("expense_percentage", 0.0),
                get_advice=advice_text,
                get_conclusion=conclusion_text,
                get_certainty=certainty_val,
            )

            history.users.append(current_user)
            db.session.add(history)
            db.session.commit()
            return history
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def delete_history(history: History):
        try:
            if history:
                db.session.delete(history)
                db.session.commit()
                return True
            return False
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def delete_all_history(user):
        try:
            user_histories_list = list(user.histories)
            for history_item in user_histories_list:
                db.session.delete(history_item)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            raise