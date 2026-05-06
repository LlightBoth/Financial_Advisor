from flask import Blueprint, render_template, redirect, url_for, abort, flash
from flask_login import login_required, current_user
from app.forms.plan_forms import PlanForm, EditPlanForm, ConfirmDeleteForm

from app.services.plan_services import PlanServices
from app.security.cookie import check_cookie_token

from datetime import date


plan_bp = Blueprint("plans", __name__, url_prefix="/plans")

# Middleware 
@plan_bp.before_request
def check_token():
    check_cookie_token(current_user)

@plan_bp.route("/")
@login_required
def index():
    plans = PlanServices.get_all_plan(current_user)
    return render_template("plans/index.html", plans=plans, today=date.today())

@plan_bp.route("/<int:plan_id>")
@login_required
def detail(plan_id):
    plan = PlanServices.get_plan_id(plan_id)
    if plan is None:
        abort(404)
    return render_template("plans/detail.html", plan=plan)

@plan_bp.route("/create", methods=["GET","POST"])
@login_required
def create():
    form = PlanForm()

    if form.validate_on_submit():

        data = {
            "goal": form.goal.data,
            "in_between": form.in_between.data,
            "goal_cost": form.goal_cost.data,
            "description": form.description.data,
            "value": form.value.data,
        }

        plan = PlanServices.create_plan(data, current_user)
        flash(f"plan '{plan.goal}' created successfully!", "success")

        return redirect(url_for("plans.index"))

    return render_template("plans/create.html", form=form)


@plan_bp.route("/<int:plan_id>/edit", methods=["GET","POST"])
@login_required
def edit(plan_id):
    plan = PlanServices.get_plan_id(plan_id)
    if plan is None:
        abort(404)
    
    form = EditPlanForm(original_plan=plan, obj=plan)

    if form.validate_on_submit():

        data = {
            "goal": form.goal.data,
            "in_between": form.in_between.data,
            "goal_cost": form.goal_cost.data,
            "description": form.description.data,
            "value": form.value.data,
        }

        PlanServices.update_plan(plan, data)
        flash(f"plan '{plan.goal}' updated successfully!", "success")
        return redirect(url_for("plans.index"))

    return render_template("plans/edit.html", form=form, plan=plan)


@plan_bp.route("/<int:plan_id>/delete", methods=["GET"])
@login_required
def delete_confirm(plan_id):
    plan = PlanServices.get_plan_id(plan_id)
    if plan is None:
        abort(404)

    form = ConfirmDeleteForm()
    return render_template("plans/delete_confirm.html", form=form, plan=plan)


@plan_bp.route("/<int:plan_id>/delete", methods=["POST"])
@login_required
def delete(plan_id):
    plan = PlanServices.get_plan_id(plan_id)
    if plan is None:
        abort(404)

    PlanServices.delete_plan(plan)

    flash("plan deleted successfully!", "success")
    return redirect(url_for("plans.index"))