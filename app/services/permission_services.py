from app.models.permission import Permission
from extension import db


class PermissionServices:
    @staticmethod
    def get_all_permissions():
        return Permission.query.all()
    
    @staticmethod
    def get_permission_id(permission_id):
        return Permission.query.get(permission_id)

    @staticmethod
    def create(data: dict):
        try:
            permission = Permission(
                code=data["code"].lower(),
                name=data["name"].lower(),
                module=data["module"].capitalize(),
                descriptions=data.get("descriptions", "").lower() if data.get("descriptions") else None,
            )
            db.session.add(permission)
            db.session.commit()
            return permission
        except Exception:
            db.session.rollback()
            raise
    
    @staticmethod
    def update(permission: Permission, data: dict):
        try:
            permission.code = data["code"].lower()
            permission.name = data["name"].lower()
            permission.module = data["module"].capitalize()
            permission.descriptions = data.get("descriptions", "").lower() if data.get("descriptions") else None
            db.session.commit()
            return permission
        except Exception:
            db.session.rollback()
            raise
    
    @staticmethod
    def delete(permission: Permission):
        try:
            db.session.delete(permission)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            raise