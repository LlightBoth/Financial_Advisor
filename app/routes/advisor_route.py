from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user

from app.services.advisor_services import AdvisorServices
from app.services.plan_services import PlanServices
from google import genai
from google.genai import types

from app.security.limiter import limiter


from app.security.cookie import check_cookie_token
# from app.security.role_check import role_user_only

advisor_bp = Blueprint("advisors", __name__, url_prefix="/advisors")

# Middleware route
@advisor_bp.before_request
def check_token():
    check_cookie_token(current_user)

@advisor_bp.route("/personal-analyse", methods=["POST"])
@login_required
@limiter.limit("5 per minute")
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