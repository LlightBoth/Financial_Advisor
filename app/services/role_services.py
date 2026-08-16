from app.models.role import Role
from app.services.association_services import AssociationServices
from extension import db


class RoleServices:
    @staticmethod
    def get_all_roles():
        return Role.query.all()

    @staticmethod
    def get_role_id(role_id):
        return Role.query.get(role_id)
    
    @staticmethod
    def create_role(data: dict):
        try:
            permission_ids = AssociationServices.get_role_permission(data)
            role = Role(
                name=data["name"].lower(),
                descriptions=data.get("descriptions", "").lower() if data.get("descriptions") else None,
                permissions=permission_ids
            )
            db.session.add(role)
            db.session.commit()
            return role
        except Exception:
            db.session.rollback()
            raise
    
    @staticmethod
    def update(role: Role, data: dict):
        try:
            permission_ids = AssociationServices.get_role_permission(data)
            role.name = data["name"].lower()
            role.descriptions = data.get("descriptions", "").lower() if data.get("descriptions") else None
            role.permissions = permission_ids
            db.session.commit()
            return role
        except Exception:
            db.session.rollback()
            raise
    
    @staticmethod
    def delete(role: Role):
        try:
            db.session.delete(role)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            raise