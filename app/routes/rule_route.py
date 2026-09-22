from flask import Blueprint, render_template, redirect, url_for, abort, flash, request
from flask_login import login_required, current_user
from app.forms.rule_forms import RuleForm, EditRuleForm, ConfirmDeleteForm

from app.services.rule_service import RuleServices
from app.services.fact_service import FactServices

from app.security.role_check import check_route_permission
from app.security.cookie import check_cookie_token


rule_bp = Blueprint("rules", __name__, url_prefix="/rules")


# Middleware route
@rule_bp.before_request
def check_token():
    check_cookie_token(current_user)
    check_route_permission()


@rule_bp.route("/")
@login_required
def index():
    status_value = request.args.get("status", "all")
    sort_by = request.args.get("sort_by", "asc")

    rules = RuleServices.get_filter_rule(status_value, sort_by)
    return render_template("rules/index.html", rules=rules)

@rule_bp.route("/<int:rule_id>")
@login_required
def detail(rule_id):
    rule = RuleServices.get_rule_id(rule_id)
    if rule is None:
        abort(404)
    return render_template("rules/detail.html", rule=rule)

@rule_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    form = RuleForm()
    facts = FactServices.get_all_fact()

    if form.validate_on_submit():

        # Convert advice textarea into a list
        advice = [
            line.strip()
            for line in form.advice.data.splitlines()
            if line.strip()
        ]

        # Conditions should come from your condition fields
        conditions = []

        # Example expected form fields:
        #
        # fact_0
        # operator_0
        # value_fact_0
        # value_0
        #
        # fact_1
        # operator_1
        # value_fact_1
        # value_1

        index = 0

        while True:
            fact = request.form.get(f"fact_{index}")

            if not fact:
                break

            operator = request.form.get(f"operator_{index}")
            value_fact = request.form.get(f"value_fact_{index}")
            value = request.form.get(f"value_{index}")

            condition = {
                "fact": fact,
                "operator": operator,
            }

            if value_fact:
                condition["value_fact"] = value_fact
            elif value is not None and value != "":
                # Convert common boolean values
                if value.lower() == "true":
                    condition["value"] = True
                elif value.lower() == "false":
                    condition["value"] = False
                else:
                    condition["value"] = value

            conditions.append(condition)

            index += 1

        data = {
            "name": form.name.data,
            "conclusion": form.conclusion.data,
            "certainty": form.certainty.data,
            "advice": advice,
            "conditions": conditions,
        }

        rule = RuleServices.create_rule(data)

        flash(
            f"Rule '{rule.name}' created successfully!",
            "success"
        )

        return redirect(url_for("rules.index"))

    return render_template(
        "rules/create.html",
        form=form,
        facts=facts
    )


@rule_bp.route("/<int:rule_id>/edit", methods=["GET", "POST"])
@login_required
def edit(rule_id):
    rule = RuleServices.get_rule_id(rule_id)

    if rule is None:
        abort(404)

    form = EditRuleForm(
        original_rule=rule,
        obj=rule
    )

    facts = FactServices.get_all_fact()

    if form.validate_on_submit():

        # Convert advice textarea into a list
        advice = [
            line.strip()
            for line in form.advice.data.splitlines()
            if line.strip()
        ]

        conditions = []

        index = 0

        while True:
            fact = request.form.get(f"fact_{index}")

            if not fact:
                break

            operator = request.form.get(f"operator_{index}")
            value_fact = request.form.get(f"value_fact_{index}")
            value = request.form.get(f"value_{index}")

            condition = {
                "fact": fact,
                "operator": operator,
            }

            if value_fact:
                condition["value_fact"] = value_fact

            elif value is not None and value != "":
                if value.lower() == "true":
                    condition["value"] = True
                elif value.lower() == "false":
                    condition["value"] = False
                else:
                    condition["value"] = value

            conditions.append(condition)

            index += 1

        data = {
            "name": form.name.data,
            "conclusion": form.conclusion.data,
            "certainty": form.certainty.data,
            "advice": advice,
            "conditions": conditions,
        }

        RuleServices.update_rule(rule, data)

        flash(
            f"Rule '{rule.name}' updated successfully!",
            "success"
        )

        return redirect(url_for("rules.index"))

    # Existing conditions for edit page
    current_conditions = [
        {
            "fact": condition.fact,
            "operator": condition.operator,
            "value_fact": condition.value_fact,
            "value": condition.value,
        }
        for condition in rule.conditions
    ]

    return render_template(
        "rules/edit.html",
        form=form,
        rule=rule,
        facts=facts,
        current_conditions=current_conditions,
    )

@rule_bp.route("/<int:rule_id>/delete", methods=["GET"])
@login_required
def delete_confirm(rule_id):
    rule = RuleServices.get_rule_id(rule_id)
    if rule is None:
        abort(404)

    form = ConfirmDeleteForm()
    return render_template("rules/delete_confirm.html", form=form, rule=rule)


@rule_bp.route("/<int:rule_id>/delete", methods=["POST"])
@login_required
def delete(rule_id):
    rule = RuleServices.get_rule_id(rule_id)
    if rule is None:
        abort(404)

    RuleServices.delete_rule(rule)

    flash("rule deleted successfully!", "success")
    return redirect(url_for("rules.index"))