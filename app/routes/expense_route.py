from flask import Blueprint, render_template, redirect, url_for, abort, flash
from flask_login import login_required, current_user

from app.forms.expense_forms import (
    ExpenseForm,
    EditExpenseForm,
    ExpenseDeleteForm
)

from app.services.expense_services import ExpenseServices
from app.security.cookie import check_cookie_token

from datetime import date


expense_bp = Blueprint("expenses", __name__, url_prefix="/expenses")


# --------------------------------------------------
# Middleware
# --------------------------------------------------
@expense_bp.before_request
def check_token():
    # check_cookie_token(current_user)
    pass


# --------------------------------------------------
# Expense List
# --------------------------------------------------
@expense_bp.route("/")
@login_required
def index():
    expenses = ExpenseServices.get_all_expense(current_user)
    return render_template("expenses/index.html", expenses=expenses, today=date.today())


# --------------------------------------------------
# Expense Detail
# --------------------------------------------------
@expense_bp.route("/<int:expense_id>")
@login_required
def detail(expense_id):
    expense = ExpenseServices.get_expense_id(expense_id, current_user.id)
    if expense is None:
        abort(404)
    return render_template("expenses/detail.html", expense=expense)


# --------------------------------------------------
# Create Expense
# --------------------------------------------------
@expense_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    form = ExpenseForm()

    if form.validate_on_submit():
        data = {
            "amount": form.amount.data,
            "description": form.description.data,
            "category": form.category.data,
            "expense_date": form.expense_date.data,
            "recurring_period": form.recurring_period.data,
        }

        expense = ExpenseServices.create_expense(data, current_user)
        flash(f"Expense '${expense.amount:.2f}' created successfully!", "success")
        return redirect(url_for("expenses.index"))

    return render_template("expenses/create.html", form=form)


# --------------------------------------------------
# Edit Expense
# --------------------------------------------------
@expense_bp.route("/<int:expense_id>/edit", methods=["GET", "POST"])
@login_required
def edit(expense_id):
    expense = ExpenseServices.get_expense_id(expense_id, current_user.id)
    if expense is None:
        abort(404)

    form = EditExpenseForm(original_expense=expense, obj=expense)

    if form.validate_on_submit():
        data = {
            "amount": form.amount.data,
            "description": form.description.data,
            "category": form.category.data,
            "expense_date": form.expense_date.data,
            "recurring_period": form.recurring_period.data,
        }

        ExpenseServices.update_expense(expense, data)
        flash(f"Expense '${expense.amount:.2f}' updated successfully!", "success")
        return redirect(url_for("expenses.index"))

    return render_template("expenses/edit.html", form=form, expense=expense)


# --------------------------------------------------
# Delete Confirmation
# --------------------------------------------------
@expense_bp.route("/<int:expense_id>/delete", methods=["GET"])
@login_required
def delete_confirm(expense_id):
    expense = ExpenseServices.get_expense_id(expense_id, current_user.id)
    if expense is None:
        abort(404)

    form = ExpenseDeleteForm()
    return render_template("expenses/delete_confirm.html", expense=expense, form=form)


# --------------------------------------------------
# Delete Expense
# --------------------------------------------------
@expense_bp.route("/<int:expense_id>/delete", methods=["POST"])
@login_required
def delete(expense_id):
    expense = ExpenseServices.get_expense_id(expense_id, current_user.id)
    if expense is None:
        abort(404)

    form = ExpenseDeleteForm()
    if form.validate_on_submit():
        ExpenseServices.delete_expense(expense)
        flash("Expense deleted successfully!", "success")
    return redirect(url_for("expenses.index"))