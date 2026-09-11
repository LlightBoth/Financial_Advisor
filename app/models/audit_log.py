from datetime import datetime, timezone
from extension import db

class AuditLog(db.Model):
    __tablename__ = "audit_logs" 

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )
    # For record users action (USER_LOGIN/USER_LOGOUT)
    action = db.Column(db.String(100), nullable=False)
    # For record status for action (SUCCESS/FAILED)
    status = db.Column(db.String(20), nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    user = db.relationship("User", backref="audit_logs")

    def __repr__(self):
        return f"<Audit Log: {self.action} {self.status}>"