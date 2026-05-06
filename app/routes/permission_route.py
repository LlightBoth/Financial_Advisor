from flask import Blueprint, render_template, url_for, abort, flash, redirect
from flask_login import login_required, current_user

from app.services.permission_services import PermissionServices
from app.forms import PermissionCreateForm, PermissionEditForm, PermissionDeleteForm

from app.security.role_check import role_admin_only
from app.security.cookie import check_cookie_token


permission_bp = Blueprint("permissions", __name__, url_prefix="/permissions")

# Middleware route
@permission_bp.before_request
def check_token():
    check_cookie_token(current_user)
    role_admin_only()


@permission_bp.route("/")
@login_required
def index():
    permissions = PermissionServices.get_all_permissions()
    return render_template("permissions/index.html", permissions=permissions)

@permission_bp.route("/<int:permission_id>")
@login_required
def detail(permission_id):
    permission = PermissionServices.get_permission_id(permission_id)
    if permission is None:
        abort(404)
    return render_template("permissions/detail.html", permission=permission)

@permission_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    form = PermissionCreateForm()

    if form.validate_on_submit():
        data = {
            "code": form.code.data,
            "name": form.name.data,
            "module": form.module.data,
            "descriptions": form.descriptions.data
        }
        PermissionServices.create(data)
        flash("Applying permission successfully", "success")
        return redirect(url_for("permissions.index"))

    return render_template("permissions/create.html", form=form)

@permission_bp.route("/<int:permission_id>/edit", methods=["GET", "POST"])
@login_required
def edit(permission_id):
    permission = PermissionServices.get_permission_id(permission_id)
    if permission is None:
        abort(404)

    form = PermissionEditForm(original_permission=permission, obj=permission)

    if form.validate_on_submit():
        data = {
            "code": form.code.data,
            "name": form.name.data,
            "module": form.module.data,
            "descriptions": form.descriptions.data
        }
        PermissionServices.update(permission, data)
        flash("Updated permission successfully", "success")
        return redirect(url_for("permissions.index"))

    return render_template("permissions/edit.html", form=form)

@permission_bp.route("/<int:permission_id>/delete", methods=["GET"])
@login_required
def delete_confirm(permission_id):
    permission = PermissionServices.get_permission_id(permission_id)
    if permission is None:
        abort(404)

    form = PermissionDeleteForm()
    return render_template("permissions/delete_confirm.html", form=form, permission=permission)

@permission_bp.route("/<int:permission_id>/delete", methods=["POST"])
@login_required
def delete(permission_id):
    permission = PermissionServices.get_permission_id(permission_id)
    if permission is None:
        abort(404)

    PermissionServices.delete(permission)
    flash("Permission deleted successfully!", "success")
    return redirect(url_for("permissions.index"))
