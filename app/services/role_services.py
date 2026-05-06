from typing import Optional, List

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
        permissiom_ids = AssociationServices.get_role_permission(data)
        role = Role(
            name = data["name"].lower(),
            descriptions = data["descriptions"].lower(),
            permissions = permissiom_ids
        )
        db.session.add(role)
        db.session.commit()
        return role
    
    @staticmethod
    def update(role: Role, data: dict):
        permissiom_ids = AssociationServices.get_role_permission(data)

        role.name = data["name"].lower()
        role.descriptions = data["descriptions"].lower()
        role.permissions = permissiom_ids

        db.session.commit()
        return role
    
    @staticmethod
    def delete(role: Role):
        db.session.delete(role)
        db.session.commit()