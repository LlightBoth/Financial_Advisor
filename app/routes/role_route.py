from flask import Blueprint, render_template, redirect, url_for, abort, flash, request
from app.forms.role_forms import RoleForm, EditRoleForm, ConfirmDeleteForm
from flask_login import login_required, current_user

from app.services.user_services import UserServices
from app.services.role_services import RoleServices
from app.services.permission_services import PermissionServices
from app.services.association_services import AssociationServices

from app.security.role_check import role_admin_only
from app.security.cookie import check_cookie_token


role_bp = Blueprint("roles", __name__, url_prefix="/roles")

# Middleware route
@role_bp.before_request
def check_token():
    check_cookie_token(current_user)
    role_admin_only()


@role_bp.route("/")
@login_required
def index():
    roles = RoleServices.get_all_roles()
    
    return render_template("roles/index.html", roles=roles)

@role_bp.route("/create", methods=["GET","POST"])
@login_required
def create():
    form = RoleForm()
    permissions = PermissionServices.get_all_permissions()

    if form.validate_on_submit():
        permissions = request.form.getlist("permission_ids")
        role_data = {
            "name" : form.name.data,
            "descriptions" : form.descriptions.data,
            "permissions": permissions
        }
        created_role = RoleServices.create_role(role_data)
        return redirect(url_for('roles.index'))

    return render_template("roles/create.html", form=form, permissions=permissions)

@role_bp.route("/<int:role_id>")
@login_required
def detail(role_id):
    role = RoleServices.get_role_id(role_id)
    users = UserServices.get_all()
    current_permission = role.permissions

    if role is None:
        abort(404)

    return render_template("roles/detail.html", role=role, users=users, current_permission=current_permission)

@role_bp.route("/<int:role_id>/edit", methods=["GET", "POST"])
@login_required
def edit(role_id):
    role = RoleServices.get_role_id(role_id)
    permissions = PermissionServices.get_all_permissions()

    if role is None:
        abort(404)

    form = EditRoleForm(original_role=role, obj=role)  
    current_permission_ids = [p.id for p in role.permissions]

    if form.validate_on_submit():
        permissions = request.form.getlist("permission_ids")
        data = {
            "name": form.name.data,
            "descriptions": form.descriptions.data,
            "permissions": permissions
        }
        RoleServices.update(role, data)

        flash("updated successfully!", "success")
        return redirect(url_for("roles.index"))

    return render_template("roles/edit.html",form = form, role = role, permissions=permissions, current_permission_ids=current_permission_ids)

@role_bp.route("/<int:role_id>/delete", methods=["GET"])
@login_required
def delete_confirm(role_id):
    role = RoleServices.get_role_id(role_id)
    if role is None:
        abort(404)

    form = ConfirmDeleteForm()
    return render_template("roles/delete_confirm.html", form=form, role=role)


@role_bp.route("/<int:role_id>/delete", methods=["POST"])
@login_required
def delete(role_id):
    role = RoleServices.get_role_id(role_id)
    if role is None:
        abort(404)

    RoleServices.delete(role)

    flash("Role deleted successfully!", "success")
    return redirect(url_for("roles.index"))