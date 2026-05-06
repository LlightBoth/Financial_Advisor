from flask import Blueprint, render_template, abort, redirect, url_for, flash
from flask_login import login_required, current_user

from app.forms.history_forms import ConfirmDeleteForm
from app.services.history_services import HistoryServices

from app.security.cookie import check_cookie_token
from app.security.role_check import role_user_only

history_bp = Blueprint("history", __name__, url_prefix="/history")


# Middleware route
from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user

from app.services.history_services import HistoryServices
from app.security.cookie import check_cookie_token
from app.security.role_check import role_user_only

history_bp = Blueprint("history", __name__, url_prefix="/histories")


@history_bp.before_request
def check_token():
    check_cookie_token(current_user)
    role_user_only()


@history_bp.route('/')
@login_required
def index():
    histories = HistoryServices.get_all_history(current_user)
    return render_template("histories/index.html", histories=histories)


@history_bp.route('/<int:history_id>')
@login_required
def detail(history_id):
    form = ConfirmDeleteForm()
    history = HistoryServices.get_user_history_id(history_id, current_user)

    if form.validate_on_submit():
        HistoryServices.delete_history(history)
        return redirect(url_for('history.index'))

    return render_template("histories/detail.html", history=history, form=form)


@history_bp.route('/<int:history_id>/delete', methods=['GET'])
@login_required
def delete_confirm(history_id):
    history = HistoryServices.get_user_history_id(history_id, current_user)
    if not history:
        abort(404)
    form = ConfirmDeleteForm()  # Make sure a form class exist
    return render_template("histories/delete_confirm.html", history=history, form=form)

@history_bp.route('/<int:history_id>/delete', methods=['POST'])
@login_required
def delete(history_id):
    history = HistoryServices.get_user_history_id(history_id, current_user)
    if not history:
        abort(404)
    form = ConfirmDeleteForm()
    if form.validate_on_submit():
        HistoryServices.delete_history(history)
        flash("History deleted successfully", "success")
    return redirect(url_for("history.index"))