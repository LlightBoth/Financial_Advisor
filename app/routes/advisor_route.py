from flask import Blueprint, render_template, request
from flask_login import login_required, current_user

from app.forms.advisor_forms import AdvisorForm
from app.services.advisor_services import AdvisorServices
from app.services.plan_services import PlanServices
from app.services.dashboard_services import DashboardServices

from app.security.cookie import check_cookie_token
# from app.security.role_check import role_user_only

advisor_bp = Blueprint("advisors", __name__, url_prefix="/advisors")


# Middleware route
@advisor_bp.before_request
def check_token():
    check_cookie_token(current_user)
    

@advisor_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    form = AdvisorForm()
    advice_rule = None

    if form.validate_on_submit():
        # Collect data
        data = {
            "goal_cost": form.goal_cost.data,
            "income": form.income.data,
            "expense": form.expense.data,
            "martial_status": form.martial_status.data,
            "is_employed": form.employment_status.data,
            "is_debt": form.debt_status.data,
            "is_spending": form.spending_habit.data,
        }
        advice_rule = AdvisorServices.get_advise(data)

    return render_template("advisors/index.html", form=form, advice=advice_rule)


@advisor_bp.route("/analyse", methods=["GET", "POST"])
@login_required
def analyseIndex():
    form = AdvisorForm()
    advice_rule = None
    total_plan = PlanServices.get_user_all_plan_total(current_user)

    if form.validate_on_submit():
        # Read directly from validated form fields (or fallback to request.form if not using WTForms fields)
        income = form.income.data if hasattr(form, 'income') else float(request.form.get("income", 0.0))
        expense = form.expense.data if hasattr(form, 'expense') else float(request.form.get("expense", 0.0))
        
        # Calculate goal_cost default if empty
        goal_cost_input = request.form.get("goal_cost")
        goal_cost = float(goal_cost_input) if goal_cost_input else income

        data = {
            "goal_cost": goal_cost,
            "income": income,
            "expense": expense,
            "marital_status": request.form.get("marital_status", request.form.get("martial_status", "")),
            "is_employed": request.form.get("employment_status", ""),
            "is_debt": request.form.get("debt_status", ""),
            "is_spending": request.form.get("spending_habit", ""),
        }

        print(f"data in route: {data}")

        advice_rule = AdvisorServices.get_advise(data)

        return render_template(
            "advisors/analyse.html",
            form=form,
            income=income,
            expense=expense,
            total_plan=total_plan,
            advice=advice_rule
        )

    # Initial GET Request or Invalid Form POST
    return render_template(
        "advisors/analyse.html",
        form=form,
        income=0.0,
        expense=0.0,
        total_plan=total_plan,
        advice=None
    )


@advisor_bp.route("/personal-analyse", methods=["POST"])
@login_required
def personalAnalyse():
    # Read values submitted by dashboard form
    income = float(request.form.get("income", 0.0))
    expense = float(request.form.get("expense", 0.0))
    data = {
        "income": income,
        "expense": expense,
        "marital_status": request.form.get("marital_status", "Single")
    }

    # Execute financial scan
    advice_result = AdvisorServices.persoal_analyse(data)

    # Fetch required dashboard variables
    total_plan = PlanServices.get_user_all_plan_total(current_user)
    sum_saving = income - expense
    sum_saving_rate = advice_result.get("remain_percentage", 0.0)
    user_plans = PlanServices.get_user_all_plan_total(current_user)

    return render_template(
        "advisors/analyse.html",  # Renders the updated template
        income=income,
        expense=expense,
        sum_saving=sum_saving,
        sum_saving_rate=sum_saving_rate,
        user_plans=user_plans,
        total_plan=total_plan,
        advice=advice_result
    )