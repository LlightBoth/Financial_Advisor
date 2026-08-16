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
            fact = Fact(
                description=data["description"].lower(),
                value=data.get("value", True),
                tags=data["tags"].lower()
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
            fact.description = data["description"].lower()
            fact.value = data.get("value", True)
            fact.tags = data["tags"].lower()
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