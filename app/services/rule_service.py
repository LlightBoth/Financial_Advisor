from app.models.rule import Rule
from app.services.association_services import AssociationServices
from extension import db


class RuleServices:
    @staticmethod
    def get_all_rule():
        return Rule.query.all()
    
    @staticmethod
    def get_rule_id(rule_id: int):
        return Rule.query.get(rule_id)
    
    @staticmethod
    def create_rule(data: dict):
        try:
            facts = AssociationServices.get_rule_fact(data)
            rule = Rule(
                conclusion=data["conclusion"],
                certainty=data["certainty"],
                advice=data["advice"],
                facts=facts
            )
            db.session.add(rule)
            db.session.commit()
            return rule
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def update_rule(rule: Rule, data: dict):
        try:
            rule.conclusion = data["conclusion"]
            rule.certainty = data["certainty"]
            rule.advice = data["advice"]

            if "facts" in data:
                rule.facts = AssociationServices.get_rule_fact(data)
            
            db.session.commit()
            return rule
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def delete_rule(rule: Rule):
        try:
            db.session.delete(rule)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            raise