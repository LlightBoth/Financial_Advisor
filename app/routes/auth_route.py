from flask import Blueprint, render_template, flash, redirect, url_for, make_response, session, request
from flask_login import login_user, logout_user, login_required, current_user

from app.forms.auth_forms import LoginForm, RegisterForm, ForgotPasswordForm
from app.services.auth_services import AuthService
from app.services.user_services import UserServices
from app.security.role_check import get_current_user_role
from app.security.cookie import get_cookie, remove_cookie

import secrets
import time
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
            print("LOGIN SUCCESS")
            print("USER:", user.username)

            login_user(user, remember=form.is_remember.data)
            flash("Login successful", "success")

            # Decide redirect based on role
            current_user_role = get_current_user_role()

            print("ROLE:", current_user_role)

            if current_user_role == "user":
                redirect_url = url_for("dashboards.userIndex")
            elif current_user_role == "editor":
                redirect_url = url_for("rules.index")
            else:
                redirect_url = url_for("dashboards.empIndex")

            print("REDIRECT:", redirect_url)

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


def get_session(user_email):
    """
    Helper function to generate OTP and set up session timer.
    Accepts a string email address (never a database object).
    """
    otp_code = str(secrets.randbelow(900000) + 100000)  # 6-digit OTP
    
    session["pending_user_email"] = user_email
    session["generated_otp"] = otp_code
    session["otp_expiry"] = time.time() + 300  # 5 minutes expiry
    session.pop("otp_verified", None)          # Ensure state is unverified until OTP is checked

    print(f"[DEBUG] Email: {user_email} | OTP: {otp_code}")


@auth_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user_email = form.email.data
        user = AuthService.find_user_email(user_email)

        # Flash standard message to prevent email enumeration attacks
        flash('If an account exists with that email, a password reset code has been sent.', 'info')

        if user:
            get_session(user.email)
            # TODO: Send password reset email here
            # send_otp_email(user.email, session['generated_otp'])
            return redirect(url_for('auth.verify_otp'))

    return render_template('auth/forgot_password.html', form=form)


@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    email = session.get('pending_user_email')

    if not email:
        flash('Session expired. Please request a new password reset.', 'error')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        user_otp = request.form.get('otp')
        saved_otp = session.get('generated_otp')
        otp_expiry = session.get('otp_expiry', 0)

        # 1. Check expiration
        if time.time() > otp_expiry:
            flash('The OTP code has expired. Please request a new one.', 'error')
            return redirect(url_for('auth.forgot_password'))

        # 2. Verify OTP code
        if user_otp and user_otp == saved_otp:
            # Clean up OTP data and authorize user to access reset-password
            session.pop('generated_otp', None)
            session.pop('otp_expiry', None)
            session['otp_verified'] = True  # ✅ Set authorization flag

            flash('Email verified successfully!', 'success')
            return redirect(url_for('auth.reset_password'))
        else:
            flash('Invalid OTP code. Please try again.', 'error')

    return render_template('auth/verify_otp.html', email=email)


@auth_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    user_email = session.get('pending_user_email')

    if not user_email:
        flash('Session expired. Please enter your email again.', 'error')
        return redirect(url_for('auth.forgot_password'))

    # Regenerate OTP with string email
    get_session(user_email)

    # TODO: Resend email here
    # send_otp_email(user_email, session['generated_otp'])

    flash('A new OTP code has been sent to your email address.', 'info')
    return redirect(url_for('auth.verify_otp'))


@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    user_email = session.get('pending_user_email')
    is_verified = session.get('otp_verified')

    # Security check: User MUST have verified their OTP first
    if not user_email or not is_verified:
        flash('Unauthorized access or session expired. Please verify your email.', 'error')
        return redirect(url_for('auth.forgot_password'))

    user = AuthService.find_user_email(user_email)
    if not user:
        flash('User account not found.', 'error')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not password or len(password) < 8:
            flash('Password must be at least 8 characters long.', 'error')
            return render_template('auth/new_password.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('auth/new_password.html')

        data = {
            "username": user.username,
            "full_name": user.full_name,
            "email": user.email,
            "is_active": user.is_active
        }

        # Update user password in database
        UserServices.update(user=user, data=data, password=password)

        # Clear remaining reset session flags
        session.pop('pending_user_email', None)
        session.pop('otp_verified', None)

        flash('Password reset successful! Please log in with your new password.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/new_password.html')


@auth_bp.route("/logout")
@login_required
def logout():
    # logout_user()
    AuthService.logout_user(current_user)
    return remove_cookie()