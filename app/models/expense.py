from datetime import datetime
from extension import db

from .associations import user_expenses


class Expense(db.Model):
    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True)

    # Expense information
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    description = db.Column(db.String(255), nullable=True)

    # Food, Transportation, Housing, Utilities,
    # Education, Healthcare, Shopping, Entertainment,
    # Debt, Other
    category = db.Column(db.String(50), nullable=False)

    # Date the expense was made
    expense_date = db.Column(db.Date, nullable=False)

    # Monthly / Yearly / Weekly
    recurring_period = db.Column(db.String(20), nullable=True)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationship
    users = db.relationship("User", secondary=user_expenses, back_populates="expenses")
    

    def __repr__(self):
        return f"<Expense {self.amount} - {self.category}>"