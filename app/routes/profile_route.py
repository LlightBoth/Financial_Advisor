from flask import Blueprint, abort, render_template, url_for, flash, redirect
from flask_login import current_user, login_required

from app.forms.user_forms import EditProfileForm, ChangePasswordProfileForm
from app.models.user import User
from app.security.cookie import check_cookie_token
from app.security.role_check import check_route_permission
from app.services.user_services import UserServices
from app.services.plan_services import PlanServices
from app.services.income_services import IncomeServices
from app.services.expense_services import ExpenseServices

profile_bp = Blueprint("profiles", __name__, url_prefix="/profiles")


# Middleware route
@profile_bp.before_request
def check_token():
    check_cookie_token(current_user)
    check_route_permission()


# ----- Employee Route -----
@profile_bp.route("/emp")
@login_required
def empIndex():
    form = EditProfileForm(obj=current_user)
    emp_plan_count = PlanServices.get_user_all_plan_count(current_user)

    return render_template(
        "profiles/empIndex.html",
        form=form,
        current_user=current_user,
        emp_plan_count=emp_plan_count
    )


@profile_bp.route("/emp/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
def edit_emp_profile(user_id):
    if user_id != current_user.id and not current_user.has_role("admin"):
        abort(404)

    emp = UserServices.get_by_id(user_id)
    if emp is None:
        abort(404)

    form = EditProfileForm(obj=emp)
    emp_plan_count = PlanServices.get_user_all_plan_count(current_user)

    if form.validate_on_submit():
        data = {
            "username": form.username.data,
            "email": form.email.data
        }

        UserServices.update(emp, data)
        flash("Profile updated successfully.", "success")
        return redirect(url_for("profiles.edit_emp_profile", user_id=emp.id))

    return render_template(
        "profiles/empIndex.html",
        form=form,
        current_user=emp,
        emp_plan_count=emp_plan_count
    )


@profile_bp.route("/emp/<int:user_id>/change_pw", methods=["GET", "POST"])
@login_required
def edit_emp_password(user_id):
    if user_id != current_user.id and not current_user.has_role("admin"):
        abort(404)

    emp = UserServices.get_by_id(user_id)
    if emp is None:
        abort(404)

    form = ChangePasswordProfileForm()

    if form.validate_on_submit():
        current_password = form.current_password.data
        new_password = form.new_password.data
        confirm_password = form.confirm_password.data

        if not emp.check_password(current_password):
            flash("Invalid current password.", "warning")
            return redirect(url_for("profiles.edit_emp_password", user_id=emp.id))

        if new_password != confirm_password:
            flash("Passwords do not match.", "warning")
            return redirect(url_for("profiles.edit_emp_password", user_id=emp.id))

        UserServices.update(emp, data={}, password=new_password)
        flash("Password updated successfully.", "success")
        return redirect(url_for("settings.empIndex"))

    return render_template(
        "settings/empIndex.html",
        form=form,
        current_user=emp
    )


# ----- User Client Route -----
@profile_bp.route("/")
@login_required
def userIndex():
    form = EditProfileForm(obj=current_user)
    user_plan_count = PlanServices.get_user_all_plan_count(current_user)
    total_income = IncomeServices.get_income_total(current_user)
    total_expense = ExpenseServices.get_expense_total(current_user)

    sum_saving = total_income - total_expense
    if sum_saving > 0 and total_income > 0:
        sum_saving_rate = (sum_saving * 100) / total_income
    else:
        sum_saving_rate = 0.0
        
    return render_template(
        "profiles/userIndex.html",
        form=form,
        current_user=current_user,
        sum_saving_rate=sum_saving_rate,
        user_plan_count=user_plan_count,
    )


@profile_bp.route("/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
def edit_profile(user_id):
    if user_id != current_user.id and not current_user.has_role("admin"):
        abort(404)

    user = UserServices.get_by_id(user_id)
    if user is None:
        abort(404)

    form = EditProfileForm(obj=user)
    user_plan_count = PlanServices.get_user_all_plan_count(current_user)
    total_income = IncomeServices.get_income_total(current_user)
    total_expense = ExpenseServices.get_expense_total(current_user)

    sum_saving = total_income - total_expense
    if sum_saving > 0 and total_income > 0:
        sum_saving_rate = (sum_saving * 100) / total_income
    else:
        sum_saving_rate = 0.0

    if form.validate_on_submit():
        data = {
            "username": form.username.data,
            "email": form.email.data
        }

        UserServices.update(user, data)
        flash("Profile updated successfully.", "success")
        return redirect(url_for("profiles.edit_profile", user_id=user.id))

    return render_template(
        "profiles/userIndex.html",
        form=form,
        current_user=user,
        user_plan_count=user_plan_count,
        sum_saving_rate=sum_saving_rate
    )


@profile_bp.route("/<int:user_id>/change_pw", methods=["GET", "POST"])
@login_required
def edit_password(user_id):
    if user_id != current_user.id and not current_user.has_role("admin"):
        abort(404)

    user = UserServices.get_by_id(user_id)
    if user is None:
        abort(404)

    form = ChangePasswordProfileForm()

    if form.validate_on_submit():
        current_password = form.current_password.data
        new_password = form.new_password.data
        confirm_password = form.confirm_password.data

        if not user.check_password(current_password):
            flash("Invalid current password.", "warning")
            return redirect(url_for("profiles.edit_password", user_id=user.id))

        if new_password != confirm_password:
            flash("Passwords do not match.", "warning")
            return redirect(url_for("profiles.edit_password", user_id=user.id))

        UserServices.update(user, data={}, password=new_password)
        flash("Password updated successfully.", "success")
        return redirect(url_for("settings.userIndex"))

    return render_template(
        "settings/userIndex.html",
        form=form,
        current_user=user
    )
