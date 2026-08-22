from flask import Blueprint, render_template, redirect, url_for, abort, flash
from flask_login import login_required, current_user

from app.forms.income_forms import (
    IncomeForm,
    EditIncomeForm,
    IncomeDeleteForm
)

from app.services.income_services import IncomeServices
from app.security.cookie import check_cookie_token
from app.security.role_check import check_route_permission

from datetime import date


income_bp = Blueprint("incomes", __name__, url_prefix="/incomes")


# Middleware
@income_bp.before_request
def check_token():
    check_cookie_token(current_user)
    check_route_permission()


# --------------------------------------------------
# Income List
# --------------------------------------------------
@income_bp.route("/")
@login_required
def index():
    incomes = IncomeServices.get_all_income(current_user)
    return render_template("incomes/index.html", incomes=incomes, today=date.today())


# --------------------------------------------------
# Income Detail
# --------------------------------------------------
@income_bp.route("/<int:income_id>")
@login_required
def detail(income_id):
    income = IncomeServices.get_income_id(income_id, current_user.id)
    if income is None:
        abort(404)
    return render_template("incomes/detail.html", income=income)


# --------------------------------------------------
# Create Income
# --------------------------------------------------
@income_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    form = IncomeForm()

    if form.validate_on_submit():
        data = {
            "amount": form.amount.data,
            "description": form.description.data,
            "category": form.category.data,
            "income_date": form.income_date.data,
            "recurring_period": form.recurring_period.data,
        }

        income = IncomeServices.create_income(data, current_user)
        flash(f"Income '${income.amount:.2f}' created successfully!", "success")
        return redirect(url_for("incomes.index"))

    return render_template("incomes/create.html", form=form)


# --------------------------------------------------
# Edit Income
# --------------------------------------------------
@income_bp.route("/<int:income_id>/edit", methods=["GET", "POST"])
@login_required
def edit(income_id):
    income = IncomeServices.get_income_id(income_id, current_user.id)
    if income is None:
        abort(404)
    form = EditIncomeForm(original_income=income, obj=income)

    if form.validate_on_submit():
        data = {
            "amount": form.amount.data,
            "description": form.description.data,
            "category": form.category.data,
            "income_date": form.income_date.data,
            "recurring_period": form.recurring_period.data,
        }

        IncomeServices.update_income(income, data)
        flash(f"Income '${income.amount:.2f}' updated successfully!", "success")
        return redirect(url_for("incomes.index"))

    return render_template(
        "incomes/edit.html",
        form=form,
        income=income
    )


# --------------------------------------------------
# Delete Confirmation
# --------------------------------------------------
@income_bp.route("/<int:income_id>/delete", methods=["GET"])
@login_required
def delete_confirm(income_id):
    income = IncomeServices.get_income_id(income_id, current_user.id)
    if income is None:
        abort(404)
    form = IncomeDeleteForm()

    return render_template(
        "incomes/delete_confirm.html",
        form=form,
        income=income
    )


# --------------------------------------------------
# Delete Income
# --------------------------------------------------
@income_bp.route("/<int:income_id>/delete", methods=["POST"])
@login_required
def delete(income_id):
    income = IncomeServices.get_income_id(income_id, current_user.id)
    if income is None:
        abort(404)
    
    form = IncomeDeleteForm()
    if form.validate_on_submit():
        IncomeServices.delete_income(income)
        flash("Income deleted successfully!", "success")
    return redirect(url_for("incomes.index"))