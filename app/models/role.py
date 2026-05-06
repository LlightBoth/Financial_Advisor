from datetime import datetime
from extension import db
from flask_login import UserMixin

from app.models.associations import user_roles, role_permissions


class Role(UserMixin, db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    descriptions = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


    # Relation-Ship
    users = db.relationship("User", secondary=user_roles, back_populates="roles")
    permissions = db.relationship("Permission", secondary=role_permissions, back_populates="roles")

    def has_permission(self, permission_code):
        return any(p.code == permission_code for p in self.permission_code)

    def __repr__(self):
        return f"<Role {self.name}>"
