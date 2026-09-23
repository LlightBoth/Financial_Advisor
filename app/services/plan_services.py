from datetime import date, timedelta
from app.models.plan import Plan
from app.models.rule import Rule
from flask import url_for
from app.services.notification_services import NotificationServices

from extension import db
from sqlalchemy import func, or_, and_
import math

class PlanServices:
    @staticmethod
    def get_all_total_plan():
        return Plan.query.all()
    
    @staticmethod
    def get_all_plan(current_user):
        return Plan.query.filter(Plan.users.any(id=current_user.id)).all()
    
    @staticmethod
    def get_filter_plan(current_user, status_value=None, sort_value=None, saving_type=None):
        query = Plan.query.filter(Plan.users.any(id=current_user.id))

        # Filter by status
        if status_value and status_value != "general":
            if status_value == "complete":
                query = query.filter(
                    or_(
                        Plan.value.is_(True),
                        and_(Plan.goal_cost > 0, Plan.saving >= Plan.goal_cost)
                    )
                )
            elif status_value == "incomplete":
                query = query.filter(
                    and_(
                        Plan.value.is_(False),
                        or_(Plan.saving.is_(None), Plan.goal_cost.is_(None), Plan.saving < Plan.goal_cost)
                    )
                )

        # Filter by saving type
        if saving_type and saving_type != "general":
            query = query.filter(Plan.saving_type == saving_type)

        # Sort
        if sort_value == "price":
            query = query.order_by(Plan.goal_cost.desc())
        elif sort_value == "day":
            query = query.order_by(Plan.created_at.desc())
        else:
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
    def add_saving(plan: Plan, amount: float, user: None):
        if amount <= 0:
            raise ValueError("Saving amount must be greater than zero.")

        current_saved = float(plan.saving or 0)
        goal_cost = float(plan.goal_cost or 0)

        plan.saving = current_saved + amount

        if plan.saving >= goal_cost:
            plan.saving = goal_cost
            plan.value = True

            # Add notification record
            NotificationServices.create_notification(
                user_id=user.id,
                title="Savings goal completed",
                message=f"You completed your savings goal: {plan.goal}.",
                notification_type="plan",
                link=url_for("plans.index")
            )


        db.session.commit()
        return plan
    
    
    @staticmethod
    def calculate_target_date(goal_cost, saving_amount, saving_type):
        if not goal_cost or goal_cost <= 0:
            return date.today() + timedelta(days=365)

        if not saving_amount or saving_amount <= 0:
            return date.today() + timedelta(days=365)

        if saving_type == "daily":
            days = math.ceil(goal_cost / saving_amount)
        elif saving_type in ("monthly", "manual"):
            months = goal_cost / saving_amount
            days = math.ceil(months * 30.4375)
        else:
            days = 365

        return date.today() + timedelta(days=days)


    @staticmethod
    def create_plan(data: dict, user):
        try:
            target_date = PlanServices.calculate_target_date(
                goal_cost=data["goal_cost"],
                saving_amount=data.get("saving_amount", 0),
                saving_type=data["saving_type"]
            )

            plan = Plan(
                goal=data["goal"],
                goal_cost=data["goal_cost"],
                in_between=target_date,
                description=data.get("description", ""),
                value=data.get("value", False),
                income=data.get("income", 0),
                expense=data.get("expense", 0),
                debt_amount=data.get("debt_amount", 0),
                has_budget=data.get("has_budget", False),
                saving_amount=data.get("saving_amount", 0),
                saving_type=data["saving_type"],
                marital_status=data.get("marital_status", "single"),
                employment_status=data.get("employment_status"),
                debt_status=data.get("debt_status"),
                spending_habit=data.get("spending_habit"),
            )

            plan.users.append(user)
            db.session.add(plan)

            # Add record to notification
            NotificationServices.create_notification(
                user_id=user.id,
                title="create new plan/goal",
                message=f"You make new savings goal: {plan.goal}.",
                notification_type="plan",
                link=url_for("plans.index")
            )

            db.session.commit()

            return plan

        except Exception:
            db.session.rollback()
            raise


    @staticmethod
    def update_plan(plan: Plan, data: dict, user=None):
        try:
            target_date = PlanServices.calculate_target_date(
                goal_cost=data["goal_cost"],
                saving_amount=data.get("saving_amount", 0),
                saving_type=data["saving_type"]
            )

            # =========================
            # Goal
            # =========================
            plan.goal = data["goal"]
            plan.goal_cost = data["goal_cost"]
            plan.in_between = target_date
            plan.description = data.get("description", plan.description)
            plan.value = data.get("value", plan.value)
            # =========================
            # Financial information
            # =========================
            plan.income = data.get("income", plan.income)
            plan.expense = data.get("expense", plan.expense)
            plan.debt_amount = data.get("debt_amount", plan.debt_amount)
            plan.saving_amount = data.get("saving_amount", plan.saving_amount)
            plan.saving_type = data["saving_type"]
            plan.has_budget = data.get("has_budget", plan.has_budget)

            # =========================
            # Personal information
            # =========================
            plan.marital_status = data.get("marital_status", plan.marital_status)
            plan.employment_status = data.get("employment_status", plan.employment_status)
            plan.debt_status = data.get("debt_status", plan.debt_status)
            plan.spending_habit = data.get("spending_habit", plan.spending_habit)

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


    

class PlanAnalysisService:

    @staticmethod
    def build_fact_values(plan):
        """
        Convert the user's Plan into the current values
        required by the rule engine.

        These values are NOT written back to the Fact table.
        The Fact table contains definitions shared by all users.
        """

        income = float(plan.income or 0)
        expense = float(plan.expense or 0)

        # -----------------------------------------
        # Income / Expense
        # -----------------------------------------

        has_income = income > 0
        has_expense = expense > 0

        # -----------------------------------------
        # Spending
        #
        # Adjust these thresholds to your own
        # definition of high/low spending.
        # -----------------------------------------

        spending_ratio = (
            expense / income
            if income > 0
            else 0
        )
        high_spending = (income > 0 and spending_ratio >= 0.80)
        low_spending = (income > 0 and spending_ratio <= 0.50)

        # Employment
        employment_status = str(
            getattr(plan, "employment_status", "") or ""
        ).strip().lower()

        employed = employment_status in {
            "employed",
            "self-employed",
            "self_employed",
        }
        # Debt
        debt_status = str(
            getattr(plan, "debt_status", "") or ""
        ).strip().lower()

        has_debt = debt_status not in {
            "",
            "none",
            "no",
            "no debt",
            "no_debt",
        }
        debt_amount = float(getattr(plan, "debt_amount", 0) or 0)
        # Savings
        savings_amount = float(
            getattr(plan, "saving", 0) or 0
        )
        has_savings = savings_amount > 0

        # Financial Goal
        has_financial_goal = bool(
            getattr(plan, "goal", None)
            and plan.goal.strip()
        )
        has_budget = bool(getattr(plan, "has_budget", False))

        return {
            "has_income": has_income,
            "monthly_income": income,
            "monthly_expense": expense,
            "has_expense": has_expense,

            "has_debt": has_debt,
            "debt_amount": debt_amount,

            "has_savings": has_savings,
            "savings_amount": savings_amount,

            "high_spending": high_spending,
            "low_spending": low_spending,

            "employed": employed,

            "has_financial_goal": has_financial_goal,
            "has_budget": has_budget,
        }

    # CONDITION EVALUATION
    @staticmethod
    def evaluate_condition(condition, facts):
        left_value = facts.get(condition.fact)

        # Get the expected/right-hand value
        if condition.value_fact:
            right_value = facts.get(condition.value_fact)
        else:
            right_value = condition.value

        # Missing fact/value means this condition does not match.
        if left_value is None or right_value is None:
            return False

        try:
            if condition.operator in ("greater_than", ">"):
                return left_value > right_value

            if condition.operator in ("greater_than_or_equal", ">="):
                return left_value >= right_value

            if condition.operator in ("less_than", "<"):
                return left_value < right_value

            if condition.operator in ("less_than_or_equal", "<="):
                return left_value <= right_value

            if condition.operator in ("equal", "equals", "=="):
                return left_value == right_value

            if condition.operator in ("not_equal", "!="):
                return left_value != right_value

            if condition.operator == "contains":
                return right_value in left_value

            if condition.operator == "in":
                return left_value in right_value

        except (TypeError, ValueError):
            return False

        return False

    # RULE EVALUATION

    @staticmethod
    def rule_matches(rule, fact_values):
        """
        A rule matches only if ALL of its conditions
        are satisfied.
        """

        if not rule.conditions:
            return False

        return all(
            PlanAnalysisService.evaluate_condition(
                condition,
                fact_values
            )
            for condition in rule.conditions
        )

    # ANALYZE PLAN
    @staticmethod
    def analyze_plan(plan):
        """
        Main method.

        Plan
          ↓
        Current fact values
          ↓
        Database rules
          ↓
        Matching rules
        """

        fact_values = (
            PlanAnalysisService.build_fact_values(plan)
        )

        # Load rules together with conditions.
        rules = Rule.query.all()

        matched_rules = []

        for rule in rules:

            if PlanAnalysisService.rule_matches(
                rule,
                fact_values
            ):
                matched_rules.append({
                    "id": rule.id,
                    "name": rule.name,
                    "certainty": rule.certainty,
                    "conclusion": rule.conclusion,
                    "advice": rule.advice,
                })

        return {
            "facts": fact_values,
            "matched_rules": matched_rules,
        }
