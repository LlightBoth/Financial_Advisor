from flask import Blueprint, render_template, url_for
from flask_login import current_user, login_required

from app.security.cookie import check_cookie_token
from app.security.role_check import check_user_role

from app.forms.user_forms import ChangePasswordProfileForm

setting_bp = Blueprint("settings", __name__, url_prefix="/settings")

# Middleware route
@setting_bp.before_request
def check_token():
    check_cookie_token(current_user)


@setting_bp.route("/")
@login_required
def userIndex():
    form = ChangePasswordProfileForm()
    return render_template("settings/userIndex.html", form=form, current_user=current_user)

@setting_bp.route("/emp")
@login_required
def empIndex():
    form = ChangePasswordProfileForm()
    return render_template("settings/empIndex.html", form=form, current_user=current_user)