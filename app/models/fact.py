from datetime import datetime

from extension import db
from app.models.associations import rule_facts


class Fact(db.Model):
    __tablename__ = "facts"

    id = db.Column(db.Integer, primary_key=True)

    # Core identification & metadata (Step 7D architecture)
    fact_key = db.Column(db.String(80), unique=True, nullable=True)
    category = db.Column(db.String(80), nullable=True)    # e.g., INFLOW, CASHFLOW, EXPENDITURE, LIABILITY, MILESTONE
    data_type = db.Column(db.String(30), nullable=True)   # e.g., boolean, numeric, string
    origin = db.Column(db.String(30), nullable=True)      # e.g., input, derived
    kb_version = db.Column(db.String(50), nullable=True)  # e.g., "financial-kb-v1.0"

    # Legacy attributes preserved for full backward compatibility
    tags = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(20), nullable=False, default="boolean")
    value = db.Column(db.JSON, nullable=True)

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

    rules = db.relationship(
        "Rule",
        secondary=rule_facts,
        back_populates="facts"
    )

    @property
    def key(self) -> str:
        """Returns fact_key or legacy tags."""
        return self.fact_key or self.tags

    def __repr__(self):
        return f"<Fact {self.key}>"