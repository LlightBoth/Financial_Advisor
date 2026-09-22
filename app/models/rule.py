from datetime import datetime

from extension import db
from app.models.associations import rule_facts


class Rule(db.Model):
    __tablename__ = "rules"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    conclusion = db.Column(db.String(255), nullable=False)
    certainty = db.Column(db.Float, nullable=False)
    advice = db.Column(db.JSON, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship
    facts = db.relationship("Fact", secondary=rule_facts, back_populates="rules")
    conditions = db.relationship("RuleCondition", back_populates="rule", cascade="all, delete-orphan")


    def __repr__(self):
        return f"<Rule {self.conclusion}>"


class RuleCondition(db.Model):
    __tablename__ = "rule_conditions"

    id = db.Column(db.Integer, primary_key=True)
    rule_id = db.Column(db.Integer, db.ForeignKey("rules.id", ondelete="CASCADE"), nullable=False)
    fact = db.Column(db.String(100), nullable=False)          # e.g., "monthly_income"
    operator = db.Column(db.String(50), nullable=False)      # e.g., "greater_than"
    value_fact = db.Column(db.String(100), nullable=True)   # e.g., "monthly_expense"
    value = db.Column(db.JSON, nullable=True)               # Literal value, e.g. true / false / 1000

    rule = db.relationship("Rule", back_populates="conditions")