from app.models.plan import Plan
from extension import db
from sqlalchemy import func


class PlanServices:
    @staticmethod
    def get_all_total_plan():
        return Plan.query.all()
    
    @staticmethod
    def get_all_plan(current_user):
        return Plan.query.filter(Plan.users.any(id=current_user.id)).all()
    
    @staticmethod
    def get_filter_plan(current_user, status_value=None, sort_value=None):
        query = Plan.query.filter(Plan.users.any(id=current_user.id))
        
        # Filter by status if provided (and ignore 'general' if it means "all")
        if status_value and status_value != "general":
            # Convert string parameter to boolean if plan.value is a Boolean field
            is_complete = True if status_value == "complete" else False
            query = query.filter(Plan.value == is_complete)

        # Filter by day/price if provided
        if sort_value == "price":
            query = query.order_by(Plan.goal_cost.desc())
        elif sort_value == "day":
            query = query.order_by(Plan.created_at.desc())
        else:
            # Default sort by date ascending ('day')
            query = query.order_by(Plan.created_at.asc())
            
        return query.all()
    
    @staticmethod
    def get_user_all_plan_count(current_user):
        return Plan.query.filter(Plan.users.any(id=current_user.id)).count()
    
    @staticmethod
    def get_user_all_plan_total(current_user):
        total = db.session.query(func.sum(Plan.goal_cost)).filter(Plan.users.any(id=current_user.id)).scalar()
        return total or 0
    
    @staticmethod
    def get_plan_id(plan_id: int, user_id: int = None):
        query = Plan.query.filter(Plan.id == plan_id)
        if user_id is not None:
            query = query.filter(Plan.users.any(id=user_id))
        return query.first()
    
    @staticmethod
    def create_plan(data: dict, user):
        try:
            plan = Plan(
                goal=data["goal"],
                goal_cost=data["goal_cost"],
                in_between=data["in_between"],
                description=data.get("description", ""),
                value=data.get("value", True),
            )
            plan.users.append(user)
            db.session.add(plan)
            db.session.commit()
            return plan
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def update_plan(plan: Plan, data: dict):
        try:
            plan.description = data.get("description", plan.description)
            plan.value = data.get("value", plan.value)
            plan.goal = data["goal"]
            plan.goal_cost = data["goal_cost"]
            plan.in_between = data["in_between"]
            db.session.commit()
            return plan
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def delete_plan(plan: Plan):
        try:
            db.session.delete(plan)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            raise