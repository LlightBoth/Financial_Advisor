from typing import Optional
from app.models.user import User
from app.models.role import Role
from extension import db


class UserServices:
    @staticmethod
    def get_all():
        return User.query.all()

    @staticmethod
    def get_filter_user(sort_info=None, role_by=None, sort_by=None, search_fullname=None):
        query = User.query

        # Filter by status
        if sort_info == "online":
            query = query.filter(User.is_active.is_(True))

        elif sort_info == "offline":
            query = query.filter(User.is_active.is_(False))

        # Filter by role
        if role_by == "user":
            query = query.filter(User.roles.any(name="user"))

        elif role_by == "editor":
            query = query.filter(User.roles.any(name="editor"))

        elif role_by == "manager":
            query = query.filter(User.roles.any(name="manager"))

        elif role_by == "admin":
            query = query.filter(User.roles.any(name="admin"))

        # Search fullname
        if search_fullname:
            query = query.filter(User.full_name.ilike(f"%{search_fullname}%"))

        # Sort
        if sort_info == "username":
            column = User.username
        elif sort_info == "fullname":
            column = User.full_name
        elif sort_info == "date":
            column = User.created_at
        else:
            column = User.created_at

        if sort_by == "asc":
            query = query.order_by(column.asc())
        else:
            query = query.order_by(column.desc())

        return query.all()




    @staticmethod 
    def get_by_id(user_id):
        return User.query.get(user_id)

    @staticmethod
    def create(data: dict, password: str):
        try:
            user = User(
                username=data["username"],
                email=data["email"],
                full_name=data["full_name"],
                is_active=data.get("is_active", True),
            )
            user.set_password(password)

            get_role = Role.query.filter_by(name="user").first()
            if not get_role:
                get_role = Role(name="user", descriptions="Standard User")
                db.session.add(get_role)
            user.roles.append(get_role)

            db.session.add(user)
            db.session.commit()
            return user
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def update(user: User, data: dict, password: Optional[str] = None):
        try:
            if "username" in data and data["username"]:
                user.username = data["username"]
            if "email" in data and data["email"]:
                user.email = data["email"]
            if "full_name" in data and data["full_name"]:
                user.full_name = data["full_name"]
            if "is_active" in data:
                user.is_active = data["is_active"]

            if password:
                user.set_password(password)

            db.session.commit()
            return user
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def update_user_online(user: User):
        try:
            user.is_active = True
            db.session.commit()
            return user
        except Exception:
            db.session.rollback()
            raise
    
    @staticmethod
    def update_user_offline(user: User):
        try:
            user.is_active = False
            db.session.commit()
            return user
        except Exception:
            db.session.rollback()
            raise
    
    @staticmethod
    def delete(user: User):
        try:
            db.session.delete(user)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            raise
