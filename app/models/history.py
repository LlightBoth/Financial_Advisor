from datetime import datetime

from extension import db
from app.models.associations import user_histories

class History(db.Model):
    __tablename__ = "histories"

    id = db.Column(db.Integer, primary_key=True)
    goal_cost = db.Column(db.Float)
    income = db.Column(db.Float)
    expense = db.Column(db.Float)
    martial_status = db.Column(db.String(50)) 
    is_employed = db.Column(db.Boolean, default=False)
    is_debt = db.Column(db.Boolean, default=False)
    is_spending = db.Column(db.Boolean, default=False)
    remain_percentage = db.Column(db.Float)
    expense_percentage = db.Column(db.Float)
    get_advice = db.Column(db.Text)
    get_conclusion = db.Column(db.Text)
    get_certainty = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    users = db.relationship(
        "User",
        secondary=user_histories,
        back_populates="histories"
    )

    def __repr__(self):
        return f"<History {self.id} Income:{self.income} Expense:{self.expense}>"