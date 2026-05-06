from datetime import datetime
from extension import db
from flask_login import UserMixin

from app.models.associations import role_permissions

class Permission(UserMixin, db.Model):
    __tablename__ = "permissions"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(64), unique=True, nullable=False, index=True)
    module = db.Column(db.String(64), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    descriptions = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relation-Ship
    roles = db.relationship("Role", secondary=role_permissions, back_populates="permissions")

    def __repr__(self):
        return f"<Permission {self.code}>"
