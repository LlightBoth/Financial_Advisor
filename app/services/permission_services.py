from typing import Optional, List

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
        permission = Permission(
            code = data["code"].lower(),
            name = data["name"].lower(),
            module = data["module"].capitalize(),
            descriptions = data["descriptions"].lower(),
        )

        db.session.add(permission)
        db.session.commit()
        return permission
    
    @staticmethod
    def update(permission: Permission,data: dict):
        permission.code = data["code"].lower()
        permission.name = data["name"].lower()
        permission.module = data["module"].capitalize()
        permission.descriptions = data["descriptions"].lower()
        
        db.session.commit()
        return permission
    
    @staticmethod
    def delete(permission: Permission):
        db.session.delete(permission)
        db.session.commit()
        