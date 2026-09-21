from app.models.rule import Rule, RuleCondition
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
    def get_filter_rule(status_value=None, sort_by=None):
        query = Rule.query

        if status_value == "certainty":
            column = Rule.certainty
        else:
            # "all", "id", or anything else
            column = Rule.id

        if sort_by == "asc":
            query = query.order_by(column.asc())
        else:
            query = query.order_by(column.desc())

        return query.all()

    @staticmethod
    def create_rule(data: dict):
        try:
            rule = Rule(
                name=data["name"],
                conclusion=data["conclusion"],
                certainty=data["certainty"],
                advice=data["advice"],
            )

            db.session.add(rule)
            db.session.flush()

            # Create rule conditions
            for condition_data in data.get("conditions", []):
                condition = RuleCondition(
                    rule_id=rule.id,
                    fact=condition_data["fact"],
                    operator=condition_data["operator"],
                    value_fact=condition_data.get("value_fact"),
                    value=condition_data.get("value"),
                )

                db.session.add(condition)

            db.session.commit()

            return rule

        except Exception:
            db.session.rollback()
            raise


    @staticmethod
    def update_rule(rule: Rule, data: dict):
        try:
            rule.name = data["name"]
            rule.conclusion = data["conclusion"]
            rule.certainty = data["certainty"]
            rule.advice = data["advice"]

            # Remove existing conditions
            RuleCondition.query.filter_by(
                rule_id=rule.id
            ).delete(
                synchronize_session=False
            )

            # Re-create conditions
            for condition_data in data.get("conditions", []):
                condition = RuleCondition(
                    rule_id=rule.id,
                    fact=condition_data["fact"],
                    operator=condition_data["operator"],
                    value_fact=condition_data.get("value_fact"),
                    value=condition_data.get("value"),
                )

                db.session.add(condition)

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