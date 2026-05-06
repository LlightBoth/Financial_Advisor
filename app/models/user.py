from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash,check_password_hash

# Create Database model From Code -> Table
from extension import db
from app.models.associations import user_roles, user_plans, user_histories


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(30), nullable=False)
    full_name = db.Column(db.String(80), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    refresh_token = db.Column(db.Text, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relation-Ship
    roles = db.relationship("Role", secondary=user_roles, back_populates="users")
    plans = db.relationship("Plan", secondary=user_plans, back_populates="users")
    histories = db.relationship("History", secondary=user_histories, back_populates="users")


    # Methods To Help
    def set_password(self, pw): 
        # Generate_Hash_Password
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        # return true/false with password check
        return check_password_hash(self.password_hash, pw)
    
    def has_role(self, role_name):
        return any(role.name == role_name for role in self.roles)
    
    def get_permission_codes(self):
        return [perm.code for role in self.roles for perm in role.permission]
    
    def has_permission(self, permission_code):
        return permission_code in self.get_permission_codes()
    
    def __repr__(self):
        return f"<User {self.username}>"