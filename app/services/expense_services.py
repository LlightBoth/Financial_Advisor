from app.models.expense import Expense
from extension import db
from sqlalchemy import func


class ExpenseServices:
    @staticmethod
    def get_all_total_expense():
        return Expense.query.all()
    
    @staticmethod
    def get_all_expense(current_user):
        return Expense.query.filter(Expense.users.any(id=current_user.id)).all()

    @staticmethod
    def get_filter_expense(current_user, sort_value=None):
        query = Expense.query.filter(Expense.users.any(id=current_user.id))
    
        # Filter by date/amount if provided
        if sort_value == "general":
            query = query.order_by(Expense.created_at.asc())
        elif sort_value == "amount":
            query = query.order_by(Expense.amount.desc())
        elif sort_value == "date":
            query = query.order_by(Expense.created_at.desc())
        else:
            # Default sort by date ascending ('day')
            query = query.order_by(Expense.created_at.asc())
            
        return query.all()

    @staticmethod
    def get_expense_count(current_user):
        return Expense.query.filter(Expense.users.any(id=current_user.id)).count()
    
    @staticmethod
    def get_expense_total(current_user):
        return (
            db.session.query(func.sum(Expense.amount)).filter(Expense.users.any(id=current_user.id)).scalar()
            or 0
        )

    @staticmethod
    def get_expense_id(expense_id: int, user_id: int = None):
        query = Expense.query.filter(Expense.id == expense_id)
        if user_id is not None:
            query = query.filter(Expense.users.any(id=user_id))
        return query.first()

    @staticmethod
    def create_expense(data: dict, user):
        try:
            expense = Expense(
                amount=data["amount"],
                description=data.get("description"),
                category=data["category"],
                expense_date=data["expense_date"],
                recurring_period=data.get("recurring_period") or None,
            )
            expense.users.append(user)
            db.session.add(expense)
            db.session.commit()
            return expense
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def update_expense(expense: Expense, data: dict):
        try:
            expense.amount = data["amount"]
            expense.description = data.get("description")
            expense.category = data["category"]
            expense.expense_date = data["expense_date"]
            expense.recurring_period = data.get("recurring_period") or None
            db.session.commit()
            return expense
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def delete_expense(expense: Expense):
        try:
            db.session.delete(expense)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            raise