from flask import Blueprint, render_template, request
from flask_login import login_required, current_user

from app.forms.advisor_forms import AdvisorForm
from app.services.advisor_services import AdvisorServices

from app.security.cookie import check_cookie_token
from app.security.role_check import role_user_only

advisor_bp = Blueprint("advisors", __name__, url_prefix="/advisors")


# Middleware route
@advisor_bp.before_request
def check_token():
    check_cookie_token(current_user)
    role_user_only()

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
        print(advice_rule)

    return render_template("advisors/index.html", form=form, advice=advice_rule)
