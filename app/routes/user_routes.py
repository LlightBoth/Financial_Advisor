from flask import Blueprint, render_template, redirect, url_for, abort, flash, request
from flask_login import login_required, current_user, logout_user
from app.forms.user_forms import UserCreateForm, UserEditForm, ConfirmDeleteForm
from app.services.user_services import UserServices
from app.services.role_services import RoleServices
from app.services.user_role_services import UserRoleServices
from app.security.role_check import check_route_permission


user_bp = Blueprint("users", __name__, url_prefix="/users")


# Middleware route: automatically enforces granular RBAC for all routes in blueprint
@user_bp.before_request
def check_token():
    check_route_permission()


@user_bp.route("/")
@login_required
def index():
    # Filter/Sort field
    sort_info = request.args.get("info", "fullname")
    role_by = request.args.get("role_by", "all")
    sort_by = request.args.get("sort_by", "desc")
    search_fullname = request.args.get("search", "")

    users = UserServices.get_filter_user(sort_info, role_by, sort_by, search_fullname)
    roles = RoleServices.get_all_roles()
    return render_template("users/index.html", users=users, roles=roles)


@user_bp.route("/<int:user_id>")
@login_required
def detail(user_id):
    user = UserServices.get_by_id(user_id)
    if user is None:
        abort(404)
    return render_template("users/detail.html", user=user)


@user_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    all_roles = RoleServices.get_all_roles()
    roles_choices = [(r.id, r.name) for r in all_roles]
    form = UserCreateForm(roles_choices)

    if form.validate_on_submit():
        data = {
            "username": form.username.data,
            "email": form.email.data,
            "full_name": form.full_name.data,
            "is_active": form.is_active.data,
        }
        password = form.password.data
        role_module_id = form.role_module.data

        user = UserServices.create(data, password)
        UserRoleServices.create_user_role(user.id, role_module_id)
        flash(f"User '{user.username}' created successfully!", "success")

        return redirect(url_for("users.index"))

    return render_template("users/create.html", form=form)


@user_bp.route("/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
def edit(user_id):
    user = UserServices.get_by_id(user_id)
    if user is None:
        abort(404)

    all_roles = RoleServices.get_all_roles()
    roles_choices = [(r.id, r.name) for r in all_roles]

    current_role_id = None
    if user.roles:
        current_role_id = user.roles[0].id

    form = UserEditForm(
        original_user=user,
        roles_choices=roles_choices,
        current_role_id=current_role_id,
        obj=user
    )

    if form.validate_on_submit():
        data = {
            "username": form.username.data,
            "email": form.email.data,
            "full_name": form.full_name.data,
            "is_active": form.is_active.data
        }
        password = form.password.data or None
        role_module_id = int(form.role_module.data)

        UserServices.update(user, data, password)
        success = UserRoleServices.update_role_user(user.id, role_module_id)
        if not success:
            flash("User role update failed!", "danger")
            return redirect(url_for("users.edit", user_id=user.id))
        
        flash(f"User '{user.username}' updated successfully!", "success")
        return redirect(url_for("users.index"))

    return render_template("users/edit.html", form=form, user=user)


@user_bp.route("/<int:user_id>/delete", methods=["GET"])
@login_required
def delete_confirm(user_id):
    user = UserServices.get_by_id(user_id)
    if user is None:
        abort(404)

    form = ConfirmDeleteForm()
    return render_template("users/delete_confirm.html", form=form, user=user)


@user_bp.route("/<int:user_id>/delete", methods=["POST"])
@login_required
def delete(user_id):
    user = UserServices.get_by_id(user_id)
    if user is None:
        abort(404)

    is_self = current_user.id == user.id
    UserServices.delete(user)

    if is_self:
        logout_user()
        return redirect(url_for("auth.login"))

    flash("User deleted successfully!", "success")
    return redirect(url_for("users.index"))
