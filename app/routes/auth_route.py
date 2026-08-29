from flask import Blueprint, render_template, flash, redirect, url_for, make_response, session, request
from flask_login import login_user, logout_user, login_required, current_user

from app.forms.auth_forms import LoginForm, RegisterForm, ForgotPasswordForm
from app.services.auth_services import AuthService
from app.services.user_services import UserServices
from app.security.role_check import get_current_user_role
from app.security.cookie import get_cookie, remove_cookie

import secrets
import time
from app.security.limiter import limiter


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute; 20 per hour")
def login():
    form = LoginForm() 

    if form.validate_on_submit():
        # AuthService returns a User object + access/refresh tokens
        user, access_token, refresh_token = AuthService.login_user(
            form.email.data, form.password.data
        )

        if user:
            # print("LOGIN SUCCESS")
            # print("USER:", user.username)

            login_user(user, remember=form.is_remember.data)
            flash("Login successful", "success")

            # Decide redirect dynamically based on user's highest permitted landing module
            if user.has_role("admin"):
                redirect_url = url_for("dashboards.empIndex")
            elif user.has_permission("user.view"):
                redirect_url = url_for("users.index")
            elif user.has_permission("rule.view"):
                redirect_url = url_for("rules.index")
            elif user.has_permission("role.view"):
                redirect_url = url_for("roles.index")
            elif user.has_permission("fact.view"):
                redirect_url = url_for("facts.index")
            else:
                redirect_url = url_for("dashboards.userIndex")

            # Give user new session token
            session["refresh_token"] = refresh_token

            # RETURN with cookies
            return get_cookie(redirect_url, access_token, refresh_token)

        flash("Invalid credentials", "danger")

    return render_template("auth/login.html", form=form)



@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("5 per minute; 10 per hour")
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


## Decorate OTP Email
def generate_otp_email(otp_code):
    # Plain text version for non-HTML email clients
    text_body = f"Your Financial Consultant OTP verification code is: {otp_code}. This code expires in 5 minutes."

    # Professional HTML version
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; background-color: #f4f6f8; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="table-layout: fixed;">
            <tr>
                <td align="center" style="padding: 40px 10px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 500px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); overflow: hidden;">
                        
                        <!-- Header Banner -->
                        <tr>
                            <td align="center" style="background-color: #0f172a; padding: 24px; color: #ffffff;">
                                <h1 style="margin: 0; font-size: 20px; font-weight: 600; letter-spacing: 0.5px;">Financial Consultant</h1>
                            </td>
                        </tr>

                        <!-- Main Content -->
                        <tr>
                            <td style="padding: 32px 24px; text-align: center;">
                                <h2 style="margin: 0 0 12px 0; font-size: 18px; color: #1e293b; font-weight: 600;">Verification Code</h2>
                                <p style="margin: 0 0 24px 0; font-size: 14px; color: #64748b; line-line: 1.5;">
                                    Please use the following One-Time Password (OTP) to complete your password reset. This code will expire in <strong>5 minutes</strong>.
                                </p>
                                
                                <!-- OTP Badge Box -->
                                <div style="display: inline-block; background-color: #f1f5f9; border: 1px dashed #cbd5e1; border-radius: 6px; padding: 16px 32px; margin-bottom: 24px;">
                                    <span style="font-family: 'Courier New', Courier, monospace; font-size: 32px; font-weight: 700; letter-spacing: 6px; color: #0f172a;">{otp_code}</span>
                                </div>

                                <p style="margin: 0; font-size: 13px; color: #94a3b8; line-height: 1.4;">
                                    If you did not request this verification code, please ignore this email or contact support.
                                </p>
                            </td>
                        </tr>

                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #f8fafc; padding: 16px 24px; text-align: center; border-top: 1px solid #e2e8f0;">
                                <p style="margin: 0; font-size: 12px; color: #94a3b8;">
                                    &copy; Financial Consultant App. All rights reserved.
                                </p>
                            </td>
                        </tr>
                        
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    return text_body, html_body


###    Email OTP and Session   ###
def get_session(user_email):
    """
    Helper function to generate OTP and set up session timer.
    Sends email via Google OAuth (AuthService.send_email).
    Returns True if successful, False if email dispatch failed.
    """
    otp_code = str(secrets.randbelow(900000) + 100000)  # Cryptographically secure 6-digit OTP
    text_body, html_body = generate_otp_email(otp_code)

    # Dispatch email via Gmail API
    email_sent = AuthService.send_email(
        to=user_email, 
        subject="Your Verification Code - Financial Consultant", 
        body=text_body,
        html=html_body
    )

    # Only set session keys if the Gmail API request succeeded
    if email_sent:
        session["pending_user_email"] = user_email
        session["generated_otp"] = otp_code
        session["otp_expiry"] = time.time() + 300  # 5 minutes expiry
        session.pop("otp_verified", None)          # Ensure state is unverified until checked
        return True
    
    return False
### -------------------- ###

@auth_bp.route('/forgot_password', methods=['GET', 'POST'])
@limiter.limit("3 per minute; 5 per hour")
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user_email = form.email.data
        user = AuthService.find_user_email(user_email)

        if user:
            # Check if Gmail API delivered the message successfully
            if get_session(user.email):
                flash('If an account exists with that email, a password reset code has been sent.', 'info')
                return redirect(url_for('auth.verify_otp'))
            else:
                flash('An error occurred while sending the email. Please try again later.', 'danger')
                return redirect(url_for('auth.forgot_password'))
        else:
            # Flash standard security message to prevent user enumeration
            flash('If an account exists with that email, a password reset code has been sent.', 'info')
            return redirect(url_for('auth.forgot_password'))

    return render_template('auth/forgot_password.html', form=form)

@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
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

    return render_template('auth/verify_otp.html')


@auth_bp.route('/resend-otp', methods=['POST'])
@limiter.limit("1 per minute; 3 per hour")
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
@limiter.limit("5 per minute")
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
    session.pop("refresh_token", None)
    session.clear()
    AuthService.logout_user(current_user)
    return remove_cookie()