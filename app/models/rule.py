from datetime import datetime

from extension import db
from app.models.associations import rule_facts


class Rule(db.Model):
    __tablename__ = "rules"

    id = db.Column(db.Integer, primary_key=True)
    conclusion = db.Column(db.String(80), nullable=False)
    certainty = db.Column(db.Float, nullable=False)
    advice = db.Column(db.String(120), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship
    facts = db.relationship("Fact", secondary=rule_facts, back_populates="rules")


    def __repr__(self):
        return f"<Rule {self.conclusion}>"