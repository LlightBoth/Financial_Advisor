from flask import Blueprint, render_template, redirect, url_for, abort, flash, request
from flask_login import login_required, current_user
from app.forms.rule_forms import RuleForm, EditRuleForm, ConfirmDeleteForm

from app.services.rule_service import RuleServices
from app.services.fact_service import FactServices

from app.security.role_check import check_user_role
from app.security.cookie import check_cookie_token


rule_bp = Blueprint("rules", __name__, url_prefix="/rules")


# Middleware route
@rule_bp.before_request
def check_token():
    check_cookie_token(current_user)
    check_user_role()


@rule_bp.route("/")
@login_required
def index():
    rules = RuleServices.get_all_rule()
    return render_template("rules/index.html", rules=rules)

@rule_bp.route("/<int:rule_id>")
@login_required
def detail(rule_id):
    rule = RuleServices.get_rule_id(rule_id)
    if rule is None:
        abort(404)
    return render_template("rules/detail.html", rule=rule)


@rule_bp.route("/create", methods=["GET","POST"])
@login_required
def create():
    form = RuleForm()
    facts = FactServices.get_all_fact()

    if form.validate_on_submit():
        facts_selected = request.form.getlist("fact_ids")
        data = {
            "conclusion": form.conclusion.data,
            "certainty": form.certainty.data,
            "advice": form.advice.data,
            "facts": facts_selected,
        }

        rule = RuleServices.create_rule(data)

        flash(f"Rule '{rule.conclusion}' created successfully!", "success")

        return redirect(url_for("rules.index"))

    return render_template("rules/create.html", form=form, facts=facts)


@rule_bp.route("/<int:rule_id>/edit", methods=["GET","POST"])
@login_required
def edit(rule_id):
    rule = RuleServices.get_rule_id(rule_id)
    if rule is None:
        abort(404)
    
    form = RuleForm(original_rule=rule, obj=rule)
    facts = FactServices.get_all_fact()

    current_fact_ids = [fact.id for fact in rule.facts]

    if form.validate_on_submit():
        facts_selected = request.form.getlist("fact_ids")
        data = {
            "conclusion": form.conclusion.data,
            "certainty": form.certainty.data,
            "advice": form.advice.data,
            "facts": facts_selected,
        }

        RuleServices.update_rule(rule, data)
        flash(f"Rule '{rule.conclusion}' updated successfully!", "success")
        return redirect(url_for("rules.index"))

    return render_template("rules/edit.html", form=form, rule=rule, facts=facts, current_fact_ids=current_fact_ids)


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