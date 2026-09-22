from datetime import datetime
from extension import db
from app.models.associations import user_plans


class Plan(db.Model):
    __tablename__ = "plans"

    id = db.Column(db.Integer, primary_key=True)
    goal = db.Column(db.String(80), nullable=False)
    in_between = db.Column(db.Date, nullable=False)
    goal_cost = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(120), nullable=False)
    income = db.Column(db.Float, nullable=False)
    expense = db.Column(db.Float, nullable=False)
    martial_status = db.Column(db.String(20), nullable=False)
    employment_status = db.Column(db.String(40), nullable=False)
    debt_status = db.Column(db.String(40), nullable=False)
    spending_habit = db.Column(db.String(40), nullable=False)
    value = db.Column(db.Boolean, default=False, nullable=False)

    debt_amount = db.Column(db.Numeric(12, 2), nullable=True)
    has_budget = db.Column(db.Boolean, default=False, nullable=False)
    saving = db.Column(db.Float, nullable=True)

    last_completed = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    users = db.relationship("User", secondary=user_plans, back_populates="plans")

    def __repr__(self):
        return f"<Plan {self.goal}>"