from flask import Blueprint, render_template, redirect, url_for, abort, flash
from flask_login import login_required, current_user

from app.services.dashboard_services import DashboardServices

dashboard_bp = Blueprint("dashboards", __name__, url_prefix="/dashboards")


@dashboard_bp.route("/", methods=["GET"])
@login_required
def userIndex():
    sum_saving = DashboardServices.user_sum_saving(current_user.id)
    weekly_saving = DashboardServices.user_weekly_saving(current_user.id)

    # ensure a saving dict is always working and return value back
    if not weekly_saving:
        weekly_saving = {"Mon": 0, "Tue": 0, "Wed": 0, "Thu": 0, "Fri": 0, "Sat": 0, "Sun": 0}

    user_plans = DashboardServices.user_all_saving_plan(current_user.id)
    

    return render_template(
        "dashboards/index.html", 
        sum_saving = sum_saving, 
        weekly_saving = weekly_saving,
        user_plans = user_plans
        )


@dashboard_bp.route("/complete_task/<int:plan_id>/<int:amount>", methods=["POST"])
@login_required
def user_complete_task(plan_id, amount):
    try:
        DashboardServices.complete_daily_task(current_user.id, plan_id, amount)
        flash(f"Task completed!", "success")
    except ValueError as e:
        flash(str(e), "warning")
    
    return redirect(url_for("dashboards.userIndex"))


@dashboard_bp.route("/test/<int:plan_id>/<int:amount>", methods=["POST"])
@login_required
def user_test_saving(plan_id, amount):
    DashboardServices.test_saving(current_user.id, plan_id, amount)
    

@dashboard_bp.route("/emp", methods=["GET"])
@login_required
def empIndex():
    total_users = DashboardServices.emp_get_all_users()
    total_plans = DashboardServices.emp_get_all_plans()

    return render_template(
        "dashboards/empIndex.html",
        total_users = total_users,
        total_plans = total_plans
        )