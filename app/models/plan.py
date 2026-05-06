from datetime import datetime
from flask_login import UserMixin

from .associations import user_plans
from extension import db

class Plan(UserMixin, db.Model):
    __tablename__ = "plans"

    id = db.Column(db.Integer, primary_key=True)
    goal = db.Column(db.String(80), unique=True, nullable=False)
    in_between = db.Column(db.Date, nullable=False)
    goal_cost = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(120), nullable=False)
    value = db.Column(db.Boolean, default=True, nullable=False)

    saving = db.Column(db.Float, default=0)
    last_completed = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship
    users = db.relationship("User", secondary=user_plans, back_populates="plans")

    def __repr__(self):
        return f"<Plan {self.description}>"