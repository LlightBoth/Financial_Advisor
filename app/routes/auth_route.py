from flask import Blueprint, render_template, flash, redirect, url_for, make_response
from flask_login import login_user, logout_user, login_required, current_user

from app.forms.auth_forms import LoginForm, RegisterForm
from app.services.auth_services import AuthService
from app.security.role_check import get_current_user_role
from app.security.cookie import get_cookie, remove_cookie
# from app.security.anti_dos import prevent_dos


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
# @prevent_dos.limit("10 per minute")
def login():
    form = LoginForm() 

    if form.validate_on_submit():
        # AuthService returns a User object + access/refresh tokens
        user, access_token, refresh_token = AuthService.login_user(
            form.email.data, form.password.data
        )

        if user:
            login_user(user, remember=form.is_remember.data)
            flash("Login successful", "success")

            # Decide redirect based on role
            current_user_role = get_current_user_role()

            if current_user_role == "user":
                redirect_url = url_for("dashboards.userIndex")
            elif current_user_role == "editor":
                redirect_url = url_for("rules.index")
            else:
                redirect_url = url_for("dashboards.empIndex")

            # ✅ RETURN with cookies
            return get_cookie(redirect_url, access_token, refresh_token)

        flash("Invalid credentials", "danger")

    return render_template("auth/login.html", form=form)



@auth_bp.route("/register", methods=["GET", "POST"])
# @prevent_dos.limit("10 per minute")
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        # Gather form data
        data = {
            "username": form.username.data,
            "full_name": form.full_name.data,
            "email": form.email.data,
            "is_active": form.is_active.data
        }
        password = form.password.data

        # Register user
        user = AuthService.register_user(data, password)
        if user:
            flash("Registration successful. Please login.", "success")
            return redirect(url_for("auth.login"))

        flash("Registration failed. Try again.", "danger")

    return render_template("auth/register.html", form=form)

@auth_bp.route("/logout")
@login_required
def logout():
    # logout_user()
    return remove_cookie()