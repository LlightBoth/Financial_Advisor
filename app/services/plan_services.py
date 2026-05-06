from app.models.plan import Plan
from extension import db

class PlanServices:
    @staticmethod
    def get_all_plan(current_user):
        return Plan.query.filter(Plan.users.any(id=current_user.id)).all()
    
    @staticmethod
    def get_user_all_plan_count(current_user):
        return Plan.query.filter(Plan.users.any(id=current_user.id)).count()

    @staticmethod
    def get_plan_id(plan_id):
        return Plan.query.get(plan_id)
    
    @staticmethod
    def create_plan(data: dict, user: int):
        plan = Plan(
            goal = data["goal"],
            goal_cost = data["goal_cost"],
            in_between = data["in_between"],
            description = data["description"],
            value = data.get("value", True),
        )
        plan.users.append(user)

        db.session.add(plan)
        db.session.commit()
        return plan

    @staticmethod
    def update_plan(plan: Plan, data: dict):
        plan.description = data["description"]
        plan.value = data.get("value", True)
        plan.goal = data["goal"]
        plan.goal_cost = data["goal_cost"]
        plan.in_between = data["in_between"]

        db.session.commit()
        return plan

    @staticmethod
    def delete_plan(plan_id):
        db.session.delete(plan_id)
        db.session.commit()