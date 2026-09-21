from app.models.plan import Plan
from app.models.rule import Rule
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
                # Step 1
                goal=data["goal"],
                goal_cost=data["goal_cost"],
                in_between=data["in_between"],
                description=data.get("description", ""),
                value=data.get("value", False),

                # Financial information
                income=data.get("income"),
                expense=data.get("expense"),
                debt_amount=data.get("debt_amount"),
                has_budget=data.get("has_budget", False),


                # Step 2
                martial_status=data.get("martial_status", "Single"),
                employment_status=data.get("employment_status"),
                debt_status=data.get("debt_status"),
                spending_habit=data.get("spending_habit"),
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
            # Step 1
            plan.goal = data["goal"]
            plan.goal_cost = data["goal_cost"]
            plan.in_between = data["in_between"]

            plan.description = data.get(
                "description",
                plan.description
            )

            plan.value = data.get(
                "value",
                plan.value
            )

            # Financial information
            plan.income = data.get(
                "income",
                plan.income
            )

            plan.expense = data.get(
                "expense",
                plan.expense
            )
            plan.debt_amount = data.get(
                "debt_amount",
                plan.debt_amount
            )
            plan.has_budget = data.get(
                "has_budget",
                plan.has_budget
            )

            # Step 2
            plan.martial_status = data.get(
                "martial_status",
                plan.martial_status
            )

            plan.employment_status = data.get(
                "employment_status",
                plan.employment_status
            )

            plan.debt_status = data.get(
                "debt_status",
                plan.debt_status
            )

            plan.spending_habit = data.get(
                "spending_habit",
                plan.spending_habit
            )

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

        high_spending = (
            income > 0 and spending_ratio >= 0.80
        )

        low_spending = (
            income > 0 and spending_ratio <= 0.50
        )

        # -----------------------------------------
        # Employment
        # -----------------------------------------

        employment_status = str(
            getattr(plan, "employment_status", "") or ""
        ).strip().lower()

        employed = employment_status in {
            "employed",
            "self-employed",
            "self_employed",
        }

        # -----------------------------------------
        # Debt
        # -----------------------------------------

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

        debt_amount = float(
            getattr(plan, "debt_amount", 0) or 0
        )

        # -----------------------------------------
        # Savings
        # -----------------------------------------

        savings_amount = float(
            getattr(plan, "saving", 0) or 0
        )

        has_savings = savings_amount > 0

        # -----------------------------------------
        # Financial Goal
        # -----------------------------------------

        has_financial_goal = bool(
            getattr(plan, "goal", None)
            and plan.goal.strip()
        )

        # -----------------------------------------
        # Budget
        # -----------------------------------------

        has_budget = bool(
            getattr(plan, "has_budget", False)
        )

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

    # =====================================================
    # CONDITION EVALUATION
    # =====================================================

    @staticmethod
    def evaluate_condition(condition, fact_values):
        """
        Evaluate one RuleCondition.

        Supports:

            fact OPERATOR literal

        Example:
            has_debt == True

        And:

            fact OPERATOR another_fact

        Example:
            monthly_income > monthly_expense
        """

        left_value = fact_values.get(condition.fact)

        # -----------------------------------------
        # Determine right-hand value
        # -----------------------------------------

        if condition.value_fact:
            right_value = fact_values.get(
                condition.value_fact
            )
        else:
            right_value = condition.value

        operator = condition.operator

        # -----------------------------------------
        # Operators
        # -----------------------------------------

        if operator == "equals":
            return left_value == right_value

        if operator == "not_equals":
            return left_value != right_value

        if operator == "greater_than":
            return left_value > right_value

        if operator == "less_than":
            return left_value < right_value

        if operator == "greater_than_or_equal":
            return left_value >= right_value

        if operator == "less_than_or_equal":
            return left_value <= right_value

        # Unknown operator
        return False

    # =====================================================
    # RULE EVALUATION
    # =====================================================

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

    # =====================================================
    # ANALYZE PLAN
    # =====================================================

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
