from app.models.rule import Rule
from app.services.association_services import AssociationServices
from extension import db


class RuleServices:
    @staticmethod
    def get_all_rule():
        return Rule.query.all()
    
    @staticmethod
    def get_rule_id(rule_id):
        return Rule.query.get(rule_id)
    
    @staticmethod
    def create_rule(data: dict):
        facts = AssociationServices.get_rule_fact(data)
        rule = Rule(
            conclusion = data["conclusion"],
            certainty = data["certainty"],
            advice = data["advice"],
            facts = facts
        )

        db.session.add(rule)
        db.session.commit()
        return rule

    @staticmethod
    def update_rule(rule: Rule, data: dict):

        rule.conclusion = data["conclusion"]
        rule.certainty = data["certainty"]
        rule.advice = data["advice"]

        if "facts" in data:
            rule.facts = AssociationServices.get_rule_fact(data)
        
        db.session.commit()
        return rule

    @staticmethod
    def delete_rule(rule):
        db.session.delete(rule)
        db.session.commit()