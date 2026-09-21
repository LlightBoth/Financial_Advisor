from flask import Blueprint, render_template, redirect, url_for, abort, flash, request
from flask_login import login_required, current_user
from app.forms.plan_forms import PlanForm, EditPlanForm, ConfirmDeleteForm

from app.services.plan_services import PlanServices, PlanAnalysisService
from app.security.cookie import check_cookie_token
from app.utils.i18n import _
from app.security.role_check import check_route_permission

from datetime import date


plan_bp = Blueprint("plans", __name__, url_prefix="/plans")

# Middleware 
@plan_bp.before_request
def check_token():
    check_cookie_token(current_user)
    check_route_permission()

@plan_bp.route("/")
@login_required
def index():
    # Reads ?status= value from URL; defaults to 'general' if not provided
    status_value = request.args.get("status", "general")
    sort_value = request.args.get("sort", "day")

    plans = PlanServices.get_filter_plan(current_user, status_value=status_value, sort_value=sort_value)
    return render_template("plans/index.html", plans=plans, today=date.today())

@plan_bp.route("/<int:plan_id>")
@login_required
def detail(plan_id):
    plan = PlanServices.get_plan_id(plan_id,current_user.id)

    if plan is None:
        abort(404)

    analysis = PlanAnalysisService.analyze_plan(plan)

    return render_template(
        "plans/detail.html",
        plan=plan,
        facts=analysis["facts"],
        matched_rules=analysis["matched_rules"],
    )


@plan_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    form = PlanForm()

    if form.validate_on_submit():
        data = {
            # Step 1 - Strategy Framework
            "goal": form.goal.data,
            "goal_cost": form.goal_cost.data,
            "in_between": form.in_between.data,
            "description": form.description.data,
            "value": bool(form.value.data) if hasattr(form, "value") else False,

            # Financial information
            "income": form.income.data,
            "expense": form.expense.data,
            "debt_amount": form.debt_amount.data or 0,
            "savings_amount": form.savings_amount.data or 0,
            "has_budget": form.has_budget.data,

            # Step 2 - Financial Situation
            "martial_status": form.marital_status.data,
            "employment_status": form.employment_status.data,
            "debt_status": form.debt_status.data,
            "spending_habit": form.spending_habit.data,
        }

        plan = PlanServices.create_plan(data, current_user)
        flash(_("message.plan_created_success", goal=plan.goal), "success")
        return redirect(url_for("plans.index"))

    return render_template(
        "plans/create.html",
        form=form
    )


@plan_bp.route("/<int:plan_id>/edit", methods=["GET", "POST"])
@login_required
def edit(plan_id):
    plan = PlanServices.get_plan_id(plan_id,current_user.id)

    if plan is None:
        abort(404)

    form = EditPlanForm(original_plan=plan,obj=plan)

    if form.validate_on_submit():
        data = {
            # Step 1 - Strategy Framework
            "goal": form.goal.data,
            "goal_cost": form.goal_cost.data,
            "in_between": form.in_between.data,
            "description": form.description.data,
            "value": bool(form.value.data) if hasattr(form, "value") else False,

            # Financial information
            "income": form.income.data,
            "expense": form.expense.data,
            "debt_amount": form.debt_amount.data or 0,
            "savings_amount": form.savings_amount.data or 0,
            "has_budget": form.has_budget.data,

            # Step 2 - Financial Situation
            "martial_status": form.marital_status.data,
            "employment_status": form.employment_status.data,
            "debt_status": form.debt_status.data,
            "spending_habit": form.spending_habit.data,
        }

        PlanServices.update_plan(plan, data)
        flash(_("message.plan_updated_success", goal=plan.goal), "success")
        return redirect(url_for("plans.index"))

    return render_template(
        "plans/edit.html",
        form=form,
        plan=plan
    )



@plan_bp.route("/<int:plan_id>/delete", methods=["GET"])
@login_required
def delete_confirm(plan_id):
    plan = PlanServices.get_plan_id(plan_id, current_user.id)
    if plan is None:
        abort(404)

    form = ConfirmDeleteForm()
    return render_template("plans/delete_confirm.html", form=form, plan=plan)


@plan_bp.route("/<int:plan_id>/delete", methods=["POST"])
@login_required
def delete(plan_id):
    plan = PlanServices.get_plan_id(plan_id, current_user.id)
    if plan is None:
        abort(404)

    form = ConfirmDeleteForm()
    if form.validate_on_submit():
        PlanServices.delete_plan(plan)
        flash(_("message.plan_deleted_success"), "success")
    return redirect(url_for("plans.index"))