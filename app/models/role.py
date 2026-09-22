from datetime import datetime
from extension import db
from app.models.associations import user_roles, role_permissions


class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    descriptions = db.Column(db.String(120), nullable=True)
    is_system_role = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    users = db.relationship("User", secondary=user_roles, back_populates="roles")
    permissions = db.relationship("Permission", secondary=role_permissions, back_populates="roles")

    def has_permission(self, code):
        return any(p.code == code for p in self.permissions)

    def __repr__(self):
        return f"<Role {self.name}>"
