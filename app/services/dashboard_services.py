from app.models.plan import Plan
from app.models.user import User
from app.models.income import Income
from app.models.expense import Expense

import random
from datetime import date, datetime, timezone
from config import Config
from extension import db
from sqlalchemy import func, extract

class DashboardServices:
    @staticmethod
    def emp_get_all_users():
        return User.query.count()
    
    @staticmethod
    def emp_get_all_incomes():
        return Income.query.count()
    
    @staticmethod
    def emp_get_all_expenses():
        return Expense.query.count()
    
    # @staticmethod
    # def emp_get_all_analyse_advisor():
    #     return History.query.count()
    
    @staticmethod
    def emp_get_all_active_users():
        return User.query.filter(User.is_active==True).all()
    
    @staticmethod
    def emp_get_all_users_registered():
        results = db.session.query(
            func.strftime('%Y-%m', User.created_at).label('month'),
            func.count(User.id).label('count')
        ).group_by(
            func.strftime('%Y-%m', User.created_at)
        ).order_by(
            func.strftime('%Y-%m', User.created_at)
        ).all()

        return [
            {
                "month": row.month,
                "count": row.count
            }
            for row in results
        ]
        
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
    def user_monthly_cashflow(user_id: int) -> list:
        """
        Generates month-by-month Income, Expense, and Net Cash Flow for current year.
        Returns: [['Jan', 4500, 3200, 1300], ...]
        """
        months_map = {
            1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun', 
            7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
        }
        
        current_year = datetime.now(timezone.utc).year

        # 1. Aggregate monthly incomes for current year using .any(id=user_id)
        incomes = (
            db.session.query(
                extract('month', Income.income_date).label('month'),
                func.sum(Income.amount).label('total')
            )
            .filter(
                Income.users.any(id=user_id),
                extract('year', Income.income_date) == current_year
            )
            .group_by('month')
            .all()
        )

        # 2. Aggregate monthly expenses for current year using .any(id=user_id)
        expenses = (
            db.session.query(
                extract('month', Expense.expense_date).label('month'),
                func.sum(Expense.amount).label('total')
            )
            .filter(
                Expense.users.any(id=user_id),
                extract('year', Expense.expense_date) == current_year
            )
            .group_by('month')
            .all()
        )

        inc_dict = {int(r.month): float(r.total or 0) for r in incomes if r.month}
        exp_dict = {int(r.month): float(r.total or 0) for r in expenses if r.month}

        chart_data = []
        for m_num in range(1, 13):
            inc = inc_dict.get(m_num, 0.0)
            exp = exp_dict.get(m_num, 0.0)
            net = inc - exp
            if inc > 0 or exp > 0:
                chart_data.append([months_map[m_num], inc, exp, net])

        return chart_data if chart_data else [["Jan", 0.0, 0.0, 0.0]]


    @staticmethod
    def user_all_saving_plan(user_id: int) -> list:
        """Fetches active plans formatted with completion status and metrics."""
        all_plans = Plan.query.filter(Plan.users.any(id=user_id)).all()
        today = datetime.now(timezone.utc).date()
        
        plan_list = []
        for plan in all_plans:
            saved_val = float(plan.saving or 0)
            goal_val = float(plan.goal_cost or 0)
            
            if plan.in_between:
                total_days = (plan.in_between - today).days
            else:
                total_days = 30

            total_days = max(total_days, 1)
            is_completed_today = plan.last_completed and plan.last_completed.date() == today

            plan_list.append({
                "id": plan.id,
                "name": plan.goal,
                "saved": saved_val,
                "goal": goal_val,
                "daily": round(goal_val / total_days, 2),
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

        if plan.saving >= plan.goal_cost:
            plan.value = True
        
        db.session.commit()
        
        return {
            "message": "Complete the task"
        }