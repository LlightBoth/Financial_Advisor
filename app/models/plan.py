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
    value = db.Column(db.Boolean, default=True, nullable=False)

    saving = db.Column(db.Float, default=0.0)
    last_completed = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    users = db.relationship("User", secondary=user_plans, back_populates="plans")

    def __repr__(self):
        return f"<Plan {self.goal}>"