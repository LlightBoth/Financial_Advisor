from typing import Optional

from app.models.user import User
from app.models.role import Role

from app.security.token import Token
from extension import db

class UserServices:
    @staticmethod
    def get_all():
        return User.query.all()

    @staticmethod 
    def get_by_id(user_id):
        return User.query.get(user_id)

    @staticmethod
    def create(data: dict, password: str):
        user = User (
            username = data["username"],
            email = data["email"],
            full_name = data["full_name"],
            is_active = data.get("is_active", True),
        )
        user.set_password(password)

        get_role = Role.query.filter_by(name = "user").first()
        if not get_role:
            raise ValueError("Role 'user' does not exist")
        user.roles.append(get_role)

        # Add User to Table
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def update(user: User, data: dict, password: Optional[str] =None):
        user.username = data.get("username") or user.username
        user.email = data.get("email") or user.email
        user.full_name = data.get("full_name") or user.full_name
        user.is_active = data.get("is_active", True)


        if password:
            user.set_password(password)

        db.session.commit()
        return user

    @staticmethod
    def delete(user):
        db.session.delete(user)
        db.session.commit()
