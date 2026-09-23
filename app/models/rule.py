import json
from typing import Any
from datetime import datetime
from sqlalchemy.types import TypeDecorator, TEXT

from extension import db
from app.models.associations import rule_facts


class SafeJSON(TypeDecorator):
    """
    Robust JSON TypeDecorator for SQLite and PostgreSQL.
    Safely serializes Python objects to JSON, and gracefully falls back
    to returning the raw string if json.loads() encounters legacy unquoted text,
    permanently preventing json.decoder.JSONDecodeError.
    """
    impl = TEXT
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        if isinstance(value, str):
            # Check if it's already a valid JSON string
            try:
                json.loads(value)
                return value
            except Exception:
                return json.dumps(value, ensure_ascii=False)
        return json.dumps(value, ensure_ascii=False)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            return value
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None
            try:
                return json.loads(value)
            except (ValueError, TypeError, json.decoder.JSONDecodeError):
                return value
        return value


class Rule(db.Model):
    __tablename__ = "rules"

    id = db.Column(db.Integer, primary_key=True)

    # Step 7D Identification & Categorization
    rule_id = db.Column(db.String(80), unique=True, nullable=True)  # e.g., "DEFICIT_WITH_DEBT"
    name = db.Column(db.String(100), nullable=True, default="Financial Rule")
    category = db.Column(db.String(80), nullable=True)             # e.g., "CASHFLOW_DEFICIT_MANAGEMENT"

    # Step 7D Deterministic Condition Logic
    conditions_json = db.Column(SafeJSON, nullable=True)           # List of predicate dicts
    match_operator = db.Column(db.String(10), nullable=False, default="ALL")  # ALL or ANY

    # Deterministic Ranking
    # Priority rank (10-100): CASHFLOW_DEFICIT=100, BREAK_EVEN=80, DEBT=60, BUFFER=40, CAPITAL=20
    priority = db.Column(db.Integer, nullable=False, default=50)

    # Knowledge Grounding Strength Metadata (0.50 - 1.00)
    # INVARIANT: NEVER used as an arithmetic threshold, filter, or tie-breaker!
    certainty = db.Column(db.Float, nullable=False, default=0.85)

    # Step 7D Bilingual Advisory Content
    conclusion_en = db.Column(db.Text, nullable=True)
    conclusion_km = db.Column(db.Text, nullable=True)
    advice_en = db.Column(SafeJSON, nullable=True)
    advice_km = db.Column(SafeJSON, nullable=True)

    # Knowledge Reference Metadata (e.g. ["K001", "K002", "K014"])
    knowledge_refs = db.Column(SafeJSON, nullable=True)

    # Rule Operational State & Knowledge Base Version (Step 7F)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    kb_version = db.Column(db.String(50), nullable=True)  # e.g., "financial-kb-v1.0"

    # Legacy attributes preserved for full backward compatibility
    conclusion = db.Column(db.String(255), nullable=False)
    advice = db.Column(SafeJSON, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    facts = db.relationship("Fact", secondary=rule_facts, back_populates="rules")
    conditions = db.relationship("RuleCondition", back_populates="rule", cascade="all, delete-orphan")

    def get_localized_conclusion(self, lang: str = "en") -> str:
        """Returns the conclusion in the requested language (defaults to en)."""
        if lang == "km" and self.conclusion_km:
            return self.conclusion_km
        return self.conclusion_en or self.conclusion

    def get_localized_advice(self, lang: str = "en") -> Any:
        """Returns the advice in the requested language (defaults to en)."""
        if lang == "km" and self.advice_km:
            return self.advice_km
        return self.advice_en or self.advice

    def __repr__(self):
        return f"<Rule {self.rule_id or self.id}: {self.name} (Priority={self.priority}, Certainty={self.certainty})>"


class RuleCondition(db.Model):
    __tablename__ = "rule_conditions"

    id = db.Column(db.Integer, primary_key=True)
    rule_id = db.Column(db.Integer, db.ForeignKey("rules.id", ondelete="CASCADE"), nullable=False)
    fact = db.Column(db.String(100), nullable=False)          # e.g., "monthly_income"
    operator = db.Column(db.String(50), nullable=False)      # e.g., "greater_than", "<"
    value_fact = db.Column(db.String(100), nullable=True)   # e.g., "monthly_expense"
    value = db.Column(SafeJSON, nullable=True)              # Literal value, e.g. true / false / 1000

    rule = db.relationship("Rule", back_populates="conditions")