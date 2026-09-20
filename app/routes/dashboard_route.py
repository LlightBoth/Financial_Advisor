from flask import Blueprint, render_template, redirect, url_for, abort, flash
from flask_login import login_required, current_user

from app.services.dashboard_services import DashboardServices
from app.services.income_services import IncomeServices
from app.services.expense_services import ExpenseServices
from app.services.audit_log_services import AuditLogService
from app.security.role_check import role_admin_only
from app.security.cookie import check_cookie_token

dashboard_bp = Blueprint("dashboards", __name__, url_prefix="/dashboards")


from flask import render_template, abort
from flask_login import current_user, login_required
from app.services.dashboard_services import DashboardServices
from app.services.income_services import IncomeServices
from app.services.expense_services import ExpenseServices

@dashboard_bp.route("/", methods=["GET"])
@login_required
def userIndex():
    # Role / Permission Guard
    if not (
        current_user.has_role("admin") 
        or current_user.has_role("user")
        or current_user.is_authenticated
    ):
        abort(403)

    # Financial Summaries
    total_income = IncomeServices.get_income_total(current_user) or 0
    total_expense = ExpenseServices.get_expense_total(current_user) or 0

    if total_income > 0:
        sum_saving = total_income - total_expense
        sum_saving_rate = (sum_saving * 100) / total_income
    else:
        sum_saving = -total_expense
        sum_saving_rate = -100.0 if total_expense > 0 else 0.0

    # Chart Data & Active User Plans
    # weekly_saving = DashboardServices.user_weekly_saving(current_user.id) or {
    #     "Mon": 0, "Tue": 0, "Wed": 0, "Thu": 0, "Fri": 0, "Sat": 0, "Sun": 0
    # }
    
    monthly_cashflow = DashboardServices.user_monthly_cashflow(current_user.id)
    user_plans = DashboardServices.user_all_saving_plan(current_user.id)

    return render_template(
        "dashboards/index.html",
        sum_saving=sum_saving,
        sum_saving_rate=round(sum_saving_rate, 2),
        total_income=total_income,
        total_expense=total_expense,
        # weekly_saving=weekly_saving,
        monthly_cashflow=monthly_cashflow,
        user_plans=user_plans
    )


@dashboard_bp.route("/complete_task/<int:plan_id>/<float:amount>", methods=["POST"])
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
    


# Employee / Admin Dashboard Route
@dashboard_bp.route("/emp", methods=["GET"])
@login_required
def empIndex():
    if not current_user.has_role("admin") and not current_user.has_permission("dashboard.admin.view") and not current_user.has_permission("dashboard.emp.view"):
        abort(403)
    total_users = DashboardServices.emp_get_all_users()
    total_plans = DashboardServices.emp_get_all_plans()
    total_incomes = DashboardServices.emp_get_all_incomes()
    total_expenses = DashboardServices.emp_get_all_expenses()
    # total_anayses = DashboardServices.emp_get_all_analyse_advisor()
    total_active_users = DashboardServices.emp_get_all_active_users()
    monthly_users_registered = DashboardServices.emp_get_all_users_registered()

    # Fetch top 3 recent audit logs
    recent_logs = AuditLogService.get_top_3_audit_logs()

    return render_template(
        "dashboards/empIndex.html",
        total_users = total_users,
        total_plans = total_plans,
        total_incomes = total_incomes,
        total_expenses = total_expenses,
        # total_anayses = total_anayses,
        total_active_users=total_active_users,
        monthly_users_registered = monthly_users_registered,
        audit_logs= recent_logs,
        )