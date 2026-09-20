from app.models.fact import Fact
from extension import db


class FactServices:
    @staticmethod
    def get_all_fact():
        return Fact.query.all()
    
    @staticmethod
    def get_fact_id(fact_id: int):
        return Fact.query.get(fact_id)
    
    @staticmethod
    def create_fact(data: dict):
        try:
            value = data.get("value")

            if data["type"] == "boolean":
                value = str(value).lower() == "true"

            elif data["type"] == "number":
                value = float(value)

            elif data["type"] == "string":
                value = str(value)

            fact = Fact(
                description=data["description"].lower(),
                tags=data["tags"].lower(),
                type=data["type"],
                value=value
            )

            db.session.add(fact)
            db.session.commit()

            return fact

        except Exception:
            db.session.rollback()
            raise


    @staticmethod
    def update_fact(fact: Fact, data: dict):
        try:
            value = data.get("value")

            if data["type"] == "boolean":
                value = str(value).lower() == "true"

            elif data["type"] == "number":
                value = float(value)

            elif data["type"] == "string":
                value = str(value)

            fact.description = data["description"].lower()
            fact.tags = data["tags"].lower()
            fact.type = data["type"]
            fact.value = value

            db.session.commit()

            return fact

        except Exception:
            db.session.rollback()
            raise


    @staticmethod
    def delete_fact(fact: Fact):
        try:
            db.session.delete(fact)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            raise