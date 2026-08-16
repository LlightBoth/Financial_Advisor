from flask import Blueprint, render_template, url_for, abort
from flask_login import current_user, login_required

from app.security.cookie import check_cookie_token
from app.security.role_check import check_route_permission
from app.forms.user_forms import ChangePasswordProfileForm

setting_bp = Blueprint("settings", __name__, url_prefix="/settings")


# Middleware route
@setting_bp.before_request
def check_token():
    # check_cookie_token(current_user)
    pass


@setting_bp.route("/")
@login_required
def userIndex():
    form = ChangePasswordProfileForm()
    return render_template("settings/userIndex.html", form=form, current_user=current_user)


@setting_bp.route("/emp")
@login_required
def empIndex():
    if not current_user.has_role("admin") and not current_user.has_permission("setting.view"):
        abort(403)
    form = ChangePasswordProfileForm()
    return render_template("settings/empIndex.html", form=form, current_user=current_user)