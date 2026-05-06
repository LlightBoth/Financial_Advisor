from flask import Blueprint, render_template, redirect, url_for, abort, flash
from flask_login import login_required, current_user
from app.forms.fact_forms import FactForm, EditFactForm, ConfirmDeleteForm

from app.services.fact_service import FactServices
from app.security.role_check import check_user_role
from app.security.cookie import check_cookie_token


fact_bp = Blueprint("facts", __name__, url_prefix="/facts")

# Middleware route
@fact_bp.before_request
def check_token():
    check_cookie_token(current_user)
    check_user_role()


@fact_bp.route("/")
@login_required
def index():
    facts = FactServices.get_all_fact()
    return render_template("facts/index.html", facts=facts)

@fact_bp.route("/<int:fact_id>")
@login_required
def detail(fact_id):
    fact = FactServices.get_fact_id(fact_id)
    if fact is None:
        abort(404)
    return render_template("facts/detail.html", fact=fact)

@fact_bp.route("/create", methods=["GET","POST"])
@login_required
def create():
    form = FactForm()

    if form.validate_on_submit():

        data = {
            "description": form.description.data,
            "value": form.value.data,
            "tags": form.tags.data,
        }

        fact = FactServices.create_fact(data)
        flash(f"fact '{fact.description}' created successfully!", "success")

        return redirect(url_for("facts.index"))

    return render_template("facts/create.html", form=form)


@fact_bp.route("/<int:fact_id>/edit", methods=["GET","POST"])
@login_required
def edit(fact_id):
    fact = FactServices.get_fact_id(fact_id)
    if fact is None:
        abort(404)
    
    form = FactForm(original_fact=fact, obj=fact)

    if form.validate_on_submit():

        data = {
            "description": form.description.data,
            "value": form.value.data,
            "tags": form.tags.data,
        }

        FactServices.update_fact(fact, data)
        flash(f"fact '{fact.description}' updated successfully!", "success")
        return redirect(url_for("facts.index"))

    return render_template("facts/edit.html", form=form, fact=fact)


@fact_bp.route("/<int:fact_id>/delete", methods=["GET"])
@login_required
def delete_confirm(fact_id):
    fact = FactServices.get_fact_id(fact_id)
    if fact is None:
        abort(404)

    form = ConfirmDeleteForm()
    return render_template("facts/delete_confirm.html", form=form, fact=fact)


@fact_bp.route("/<int:fact_id>/delete", methods=["POST"])
@login_required
def delete(fact_id):
    fact = FactServices.get_fact_id(fact_id)
    if fact is None:
        abort(404)

    FactServices.delete_fact(fact)

    flash("fact deleted successfully!", "success")
    return redirect(url_for("facts.index"))