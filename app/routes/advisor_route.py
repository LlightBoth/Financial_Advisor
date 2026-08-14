from flask import Blueprint, render_template, request
from flask_login import login_required, current_user

from app.forms.advisor_forms import AdvisorForm
from app.services.advisor_services import AdvisorServices
from app.services.plan_services import PlanServices

from app.security.cookie import check_cookie_token
from app.security.role_check import role_user_only

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
    # Get Total plan Amount
    total_plan = PlanServices.get_user_all_plan_total(current_user)

    # Force Flask to parse inputs as float (defaults to 0.0 if empty or missing)
    income = request.form.get("income", 0.0, type=float)
    expense = request.form.get("expense", 0.0, type=float)
    
    # Calculate goal_cost default AFTER converting income to float
    default_goal = income
    goal_cost = request.form.get("goal_cost", default_goal, type=float)

    if request.method == "POST":
        data = {
            "goal_cost": goal_cost,
            "income": income,
            "expense": expense,
            "martial_status": request.form.get("martial_status", "Single"),
            "is_employed": request.form.get("employment_status", "not employed"),
            "is_debt": request.form.get("debt_status", "no debt"),
            "is_spending": request.form.get("spending_habit", "average spend"),
        }
        
        advice_rule = AdvisorServices.get_advise(data)
        
        return render_template(
                "advisors/analyse.html",
                form=form,
                income=income,
                expense=expense,
                total_plan=total_plan,
                advice=advice_rule
            )

    return render_template(
        "advisors/analyse.html",
        form=form,
        income=income,
        expense=expense,
        total_plan=total_plan,
        advice=advice_rule
    )