from datetime import datetime

from extension import db
from app.models.associations import rule_facts

class Fact(db.Model):
    __tablename__ = "facts"

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(80), unique=True, nullable=False)
    value = db.Column(db.Boolean, default=True, nullable=False)
    tags = db.Column(db.String(80), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship
    rules = db.relationship("Rule", secondary=rule_facts, back_populates="facts")

    def __repr__(self):
        return f"<Fact {self.description}>"