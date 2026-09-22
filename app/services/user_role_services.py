from typing import Optional, List

from app.models.user import User
from app.models.role import Role
from app.models.associations import user_roles
from extension import db

class UserRoleServices:
    @staticmethod
    def create_user_role(userId: int, roleId: int):
         # Load ORM objects
        user = db.session.get(User, userId)
        role = db.session.get(Role, roleId)
        if not user or not role:
            raise ValueError("Invalid user or role ID")
        

        # Assign role via ORM relationship
        user.roles.append(role)
        # Commit inside service
        db.session.commit()
    

    def update_role_user(userId: int, roleId: int):
        user = db.session.get(User, userId)
        role = db.session.get(Role, roleId)
        if not user or not role:
            raise ValueError("Invalid user or role ID")

        user.roles = [role] 

        db.session.add(user)
        db.session.commit()
        return user
