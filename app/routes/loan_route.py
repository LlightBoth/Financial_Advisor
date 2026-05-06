from flask import Blueprint, render_template, request
from flask_login import login_required, current_user

from app.forms.loan_forms import LoanForm
from app.services.loan_services import LoanServices

from app.security.cookie import check_cookie_token
# from app.security.role_check import role_user_only

loan_bp = Blueprint("loans", __name__, url_prefix="/loans")


# Middleware route
@loan_bp.before_request
def check_token():
    check_cookie_token(current_user)
    # role_user_only()


@loan_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    form = LoanForm()
    advice_rule = None

    if form.validate_on_submit():
        # Collect data
        data = {
            "loan_goal": form.loan_goal.data,
            "loan_term": form.loan_term.data,
            "repayment_frequency": form.repayment_frequency.data,
            "loan_history": form.loan_history.data,
            "total_debt_amount": form.total_debt_amount.data,
            "income": form.income.data,
            "expense": form.expense.data,
            "martial_status": form.martial_status.data,
            "is_employed": form.employment_status.data,
            "is_debt": form.debt_status.data,
            "is_spending": form.spending_habit.data,
        }
        advice_rule = LoanServices.get_advise(data)
        print(advice_rule)

    return render_template("loans/index.html", form=form, advice=advice_rule)
