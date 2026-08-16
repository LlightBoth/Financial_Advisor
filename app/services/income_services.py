from app.models.income import Income
from extension import db
from sqlalchemy import func


class IncomeServices:
    @staticmethod
    def get_all_total_income():
        return Income.query.all()
    
    @staticmethod
    def get_all_income(current_user):
        return Income.query.filter(Income.users.any(id=current_user.id)).all()

    @staticmethod
    def get_income_count(current_user):
        return Income.query.filter(Income.users.any(id=current_user.id)).count()
    
    @staticmethod
    def get_income_total(current_user):
        return (
            db.session.query(func.sum(Income.amount)).filter(Income.users.any(id=current_user.id)).scalar()
            or 0
        )

    @staticmethod
    def get_income_id(income_id: int, user_id: int = None):
        query = Income.query.filter(Income.id == income_id)
        if user_id is not None:
            query = query.filter(Income.users.any(id=user_id))
        return query.first()

    @staticmethod
    def create_income(data: dict, user):
        try:
            income = Income(
                amount=data["amount"],
                description=data.get("description"),
                category=data["category"],
                income_date=data["income_date"],
                recurring_period=data.get("recurring_period") or None,
            )
            income.users.append(user)
            db.session.add(income)
            db.session.commit()
            return income
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def update_income(income: Income, data: dict):
        try:
            income.amount = data["amount"]
            income.description = data.get("description")
            income.category = data["category"]
            income.income_date = data["income_date"]
            income.recurring_period = data.get("recurring_period") or None
            db.session.commit()
            return income
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def delete_income(income: Income):
        try:
            db.session.delete(income)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            raise