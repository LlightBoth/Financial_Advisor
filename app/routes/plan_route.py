from flask import Blueprint, render_template, redirect, url_for, abort, flash, request
from flask_login import login_required, current_user
from app.forms.plan_forms import PlanForm, EditPlanForm, ConfirmDeleteForm

from app.services.plan_services import PlanServices, PlanAnalysisService
from app.security.cookie import check_cookie_token
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
    saving_type = request.args.get("saving_type", "general")

    plans = PlanServices.get_filter_plan(current_user, status_value=status_value, sort_value=sort_value, saving_type=saving_type)
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
    if request.method == "POST":
        valid = form.validate_on_submit()

        if not valid:
            print("VALIDATION FAILED")

        else:
            data = {
                "goal": form.goal.data,
                "goal_cost": form.goal_cost.data,
                "description": form.description.data,

                "income": form.income.data,
                "expense": form.expense.data,
                "debt_amount": form.debt_amount.data or 0,
                "saving_amount": form.saving.data or 0,
                "saving_type": form.saving_type.data,
                "has_budget": form.has_budget.data,

                "marital_status": form.marital_status.data,
                "employment_status": form.employment_status.data,
                "debt_status": form.debt_status.data,
                "spending_habit": form.spending_habit.data,

                "in_between": form.in_between.data,
            }
            try:
                plan = PlanServices.create_plan(data, current_user)
                flash(f"Plan '{plan.goal}' created successfully!", "success")
                return redirect(url_for("plans.index"))
            except Exception as e:
                flash(f"Error creating plan: {str(e)}", "danger")

    return render_template(
        "plans/create.html",
        form=form
    )


@plan_bp.route("/<int:plan_id>/edit", methods=["GET", "POST"])
@login_required
def edit(plan_id):
    plan = PlanServices.get_plan_id(plan_id, current_user.id)

    if plan is None:
        abort(404)

    form = EditPlanForm(original_plan=plan, obj=plan)
    if request.method == "GET":
        form.saving.data = plan.saving_amount

    if form.validate_on_submit():
        data = {
            "goal": form.goal.data,
            "goal_cost": form.goal_cost.data,
            "description": form.description.data,
            "income": form.income.data,
            "expense": form.expense.data,
            "debt_amount": form.debt_amount.data or 0,
            "saving_amount": form.saving.data,
            "saving_type": form.saving_type.data,
            "has_budget": form.has_budget.data,
            "marital_status": form.marital_status.data,
            "employment_status": form.employment_status.data,
            "debt_status": form.debt_status.data,
            "spending_habit": form.spending_habit.data,
            "is_active": form.is_active.data,
        }
        try:
            # Update plan
            PlanServices.update_plan(plan, data)

            flash(f"Plan '{plan.goal}' updated successfully!","success")
            return redirect(url_for("plans.index"))
        except Exception as e:
            flash(f"Error updating plan: {str(e)}", "danger")

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
        flash("Plan deleted successfully!", "success")
    return redirect(url_for("plans.index"))



@plan_bp.post("/<int:plan_id>/save")
@login_required
def add_saving(plan_id):
    plan = PlanServices.get_plan_id(plan_id, current_user.id)
    if plan is None:
        abort(404)
    amount = request.form.get("amount", type=float)

    if not amount or amount <= 0:
        flash("Please enter a valid saving amount.", "danger")
        return redirect(url_for("plans.detail", plan_id=plan.id))

    try:
        PlanServices.add_saving(
            plan,
            amount,
            current_user
        )

        flash(
            f"${amount:,.2f} added to your savings.",
            "success"
        )

    except ValueError as e:
        flash(str(e), "danger")

    return redirect(
        url_for("plans.detail", plan_id=plan.id)
    )
