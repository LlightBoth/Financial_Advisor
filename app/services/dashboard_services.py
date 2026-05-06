from app.models.plan import Plan
from app.models.user import User

import random
from datetime import date, datetime
from config import Config
from extension import db

class DashboardServices:
    @staticmethod
    def emp_get_all_users():
        return User.query.count()
    
    @staticmethod
    def emp_get_all_plans():
        return Plan.query.count()


    @staticmethod
    def test_saving(user_id, plan_id, amount):
        # Filter plan by id
        saving_plan = Plan.query.filter(Plan.id == plan_id).first()

        if not saving_plan:
            raise ValueError("Plan not found")

        # Check if user is linked to this plan
        if not any(user.id == user_id for user in saving_plan.users):
            raise ValueError("User does not have access to this plan")

        # Update saving
        saving_plan.saving = amount
        db.session.commit()

    @staticmethod
    def user_sum_saving(user_id):
        query = """
            SELECT SUM(p.saving) as total
            FROM plans as p
            INNER JOIN user_plans as up
            ON up.plan_id = p.id 
            WHERE up.user_id = ?;
        """
        conn = Config().get_sqlite3_connection()
        cursor = conn.cursor()
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        conn.close()

        return result[0] if result and result[0] else 0 
    

    @staticmethod
    def user_weekly_saving(user_id):
        query = """
            SELECT strftime('%w', p.created_at) as weekday, SUM(p.saving) as total
            FROM plans as p
            INNER JOIN user_plans as up ON up.plan_id = p.id
            WHERE up.user_id = ?
            GROUP BY weekday;
        """
        conn = Config().get_sqlite3_connection()
        cursor = conn.cursor()
        cursor.execute(query, (user_id,))
        rows = cursor.fetchall()
        conn.close()

        week_data = {
            "Mon": 0, "Tue": 0, "Wed": 0,
            "Thu": 0, "Fri": 0, "Sat": 0, "Sun": 0,
        }

        map_day = {
            "1": "Mon", "2": "Tue", "3": "Wed",
            "4": "Thu", "5": "Fri", "6": "Sat", "0": "Sun",
        }

        for weekday, total in rows:
            day = map_day[weekday]
            week_data[day] = total or 0

        return week_data
    
    @staticmethod
    def user_all_saving_plan(user_id):
        all_plans = Plan.query.filter(Plan.users.any(id=user_id)).all()
        today = datetime.utcnow().date()
        
        plan_list = []
        for plan in all_plans:
            saved_val = float(plan.saving or 0)
            goal_val = float(plan.goal_cost or 0)
            
            # 1. Calculate the actual days remaining
            if plan.in_between:
                # plan.in_between (Date) - today (Date) = timedelta object
                delta = plan.in_between - today
                total_days = delta.days
            else:
                total_days = 30

            # 2. Safety check: avoid division by zero or negative days
            if total_days <= 0:
                total_days = 1
            
            # 3. Check if completed today for the checkbox/strikethrough
            is_completed_today = plan.last_completed and plan.last_completed.date() == today

            plan_list.append({
                "id": plan.id,
                "name": plan.goal,
                "saved": saved_val,
                "goal": goal_val,
                "daily": goal_val / total_days,
                "percent": min(int((saved_val / goal_val) * 100), 100) if goal_val > 0 else 0,
                "is_done": is_completed_today,
                "color": random.choice(['bg-primary', 'bg-success', 'bg-info', 'bg-warning', 'bg-secondary'])
            })
        return plan_list

    @staticmethod
    def complete_daily_task(user_id, plan_id, amount):
        # 1. Fetch the plan
        plan = Plan.query.get(plan_id)
        if not plan:
            raise ValueError("Plan not found")
        
        # 2. Check if the user has access
        if not any(u.id == user_id for u in plan.users):
            raise ValueError("Access denied")

        # 3. Prevent multiple completions in one day (UTC)
        # Using datetime.utcnow().date() ensures a consistent 24h reset period
        today = datetime.utcnow().date()
        if plan.last_completed and plan.last_completed.date() == today:
            raise ValueError("Daily task already completed today")
        
        # 4. Update and Save
        # min() ensures we never exceed the goal_cost
        plan.saving = min((plan.saving or 0) + amount, plan.goal_cost)
        plan.last_completed = datetime.utcnow()
        
        db.session.commit()
        
        return {
            "message": "Complete the task"
        }