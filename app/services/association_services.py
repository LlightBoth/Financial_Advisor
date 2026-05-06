from flask import request

from app.models.rule import Rule
from app.models.fact import Fact
from app.models.permission import Permission
from app.models.role import Role

from extension import db


class AssociationServices:
    @staticmethod
    def get_role_permission(data: dict):
        permission_id = [pid for pid in data["permissions"]]
        permissions = Permission.query.filter(Permission.id.in_(permission_id)).all()
        return permissions
    
    @staticmethod
    def get_rule_fact(data: dict):
        fact_id = [fid for fid in data["facts"]]
        facts = Fact.query.filter(Fact.id.in_(fact_id)).all()
        return facts
    
    @staticmethod
    def get_user_role(data: dict):
        pass
    