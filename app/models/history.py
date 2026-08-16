from datetime import datetime
from extension import db
from app.models.associations import user_histories


class History(db.Model):
    __tablename__ = "histories"

    id = db.Column(db.Integer, primary_key=True)
    goal_cost = db.Column(db.Float, default=0.0)
    income = db.Column(db.Float, default=0.0)
    expense = db.Column(db.Float, default=0.0)
    martial_status = db.Column(db.String(50), nullable=True) 
    is_employed = db.Column(db.Boolean, default=False)
    is_debt = db.Column(db.Boolean, default=False)
    is_spending = db.Column(db.Boolean, default=False)
    remain_percentage = db.Column(db.Float, default=0.0)
    expense_percentage = db.Column(db.Float, default=0.0)
    get_advice = db.Column(db.Text, nullable=True)
    get_conclusion = db.Column(db.Text, nullable=True)
    get_certainty = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    users = db.relationship(
        "User",
        secondary=user_histories,
        back_populates="histories"
    )

    # Property alias to support correct spelling without breaking existing database column
    @property
    def marital_status(self):
        return self.martial_status

    @marital_status.setter
    def marital_status(self, val):
        self.martial_status = val

    def __repr__(self):
        return f"<History {self.id} Income:{self.income} Expense:{self.expense}>"