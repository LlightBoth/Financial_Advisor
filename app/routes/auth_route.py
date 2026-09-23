import os
import requests
from flask import Blueprint, render_template, flash, redirect, url_for, make_response, session, request
from flask_login import login_user, logout_user, login_required, current_user

from app.forms.auth_forms import LoginForm, RegisterForm, ForgotPasswordForm
from app.services.auth_services import AuthService
from app.services.user_services import UserServices
from app.services.audit_log_services import AuditLogService
from app.security.cookie import get_cookie, remove_cookie
from app.utils.i18n import _
from app.security.token import Token
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

# Import your database models and extension
from app.models import User, Role
from extension import db

import secrets
import time
from app.security.limiter import limiter


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

from werkzeug.security import generate_password_hash


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
            flash(_("message.login_success"), "success")

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

            # Save user Log
            data = {
                "user_id": current_user.id,
                "action": "USER_LOGIN",
                "status": "SUCCESS",
                "ip_address": request.remote_addr,
                "user_agent": request.user_agent.string
            }
            AuditLogService.create_audit_log(data)

            # RETURN with cookies
            return get_cookie(redirect_url, access_token, refresh_token)

        # Save user Log
        user_id = current_user.id if current_user.is_authenticated else None
        data = {
            "user_id": user_id,
            "action": "USER_LOGIN",
            "status": "FAILED",
            "ip_address": request.remote_addr,
            "user_agent": request.user_agent.string
        }
        AuditLogService.create_audit_log(data)
        flash(_("message.login_failed"), "danger")

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
            # Save user Log
            log_data = {
                "user_id": user.id,
                "action": "USER_REGISTER",
                "status": "SUCCESS",
                "ip_address": request.remote_addr,
                "user_agent": request.user_agent.string
            }
            AuditLogService.create_audit_log(log_data)
            flash(_("message.registration_success"), "success")
            return redirect(url_for("auth.login"))
        
        # Save user Log
        log_data = {
            "user_id": None,
            "action": "USER_REGISTER",
            "status": "FAILED",
            "ip_address": request.remote_addr,
            "user_agent": request.user_agent.string
        }
        AuditLogService.create_audit_log(log_data)
        flash(_("message.registration_failed"), "danger")

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
                flash(_('message.password_reset_sent'), 'info')
                return redirect(url_for('auth.verify_otp'))
            else:
                flash(_('message.email_send_failed'), 'danger')
                return redirect(url_for('auth.forgot_password'))
        else:
            # Flash standard security message to prevent user enumeration
            flash(_('message.password_reset_sent'), 'info')
            return redirect(url_for('auth.forgot_password'))

    return render_template('auth/forgot_password.html', form=form)

@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def verify_otp():
    email = session.get('pending_user_email')

    if not email:
        flash(_('message.session_expired'), 'error')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        user_otp = request.form.get('otp')
        saved_otp = session.get('generated_otp')
        otp_expiry = session.get('otp_expiry', 0)

        # 1. Check expiration
        if time.time() > otp_expiry:
            flash(_('message.otp_expired'), 'error')
            return redirect(url_for('auth.forgot_password'))

        # 2. Verify OTP code
        if user_otp and user_otp == saved_otp:
            # Clean up OTP data and authorize user to access reset-password
            session.pop('generated_otp', None)
            session.pop('otp_expiry', None)
            session['otp_verified'] = True  # ✅ Set authorization flag

            flash(_('message.otp_verified'), 'success')
            return redirect(url_for('auth.reset_password'))
        else:
            flash(_('message.invalid_otp'), 'error')

    return render_template('auth/verify_otp.html')


@auth_bp.route('/resend-otp', methods=['POST'])
@limiter.limit("1 per minute; 3 per hour")
def resend_otp():
    user_email = session.get('pending_user_email')

    if not user_email:
        flash(_('message.session_expired_reenter'), 'error')
        return redirect(url_for('auth.forgot_password'))

    # Regenerate OTP with string email
    get_session(user_email)

    # TODO: Resend email here
    # send_otp_email(user_email, session['generated_otp'])

    flash(_('message.new_otp_sent'), 'info')
    return redirect(url_for('auth.verify_otp'))


@auth_bp.route('/reset-password', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def reset_password():
    user_email = session.get('pending_user_email')
    is_verified = session.get('otp_verified')

    # Security check: User MUST have verified their OTP first
    if not user_email or not is_verified:
        flash(_('message.unauthorized_reset'), 'error')
        return redirect(url_for('auth.forgot_password'))

    user = AuthService.find_user_email(user_email)
    if not user:
        flash(_('message.user_not_found'), 'error')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not password or len(password) < 8:
            flash(_('validation.password_min8'), 'error')
            return render_template('auth/new_password.html')

        if password != confirm_password:
            flash(_('validation.password_mismatch'), 'error')
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

        flash(_('message.password_reset_success'), 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/new_password.html')


# Allow HTTP for local testing (Do not use in production)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = os.getenv('OAUTHLIB_INSECURE_TRANSPORT', '1')
# Prevent "Scope has changed" crash when Google returns scopes in a different order
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'


def get_google_flow():
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    client_config = {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }
    # Standard identity scopes for Google Sign-In
    scopes = [
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email",
        "openid"
    ]
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI") or url_for("auth.google_callback", _external=True)
    return Flow.from_client_config(
        client_config=client_config,
        scopes=scopes,
        redirect_uri=redirect_uri
    )


@auth_bp.route("/google")
@auth_bp.route("/auth/google")
def google_login():
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

    if not client_id or not client_secret:
        flash(
            "Google Sign-In is not configured yet. Please add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to your .env file.",
            "warning"
        )
        return redirect(url_for("auth.login"))

    flow = get_google_flow()
    
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"  # Ensures Google returns a refresh_token every time
    )
    
    session["oauth_state"] = state
    if hasattr(flow, "code_verifier") and flow.code_verifier:
        session["code_verifier"] = flow.code_verifier

    return redirect(authorization_url)


@auth_bp.route("/google/callback")
@auth_bp.route("/auth/google/callback")
def google_callback():
    state = session.get("oauth_state")
    if not state or state != request.args.get("state"):
        flash("Invalid state parameter during authentication.", "danger")
        return redirect(url_for("auth.login"))

    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    if not client_id or not client_secret:
        flash("Google Sign-In is not configured yet.", "danger")
        return redirect(url_for("auth.login"))

    flow = get_google_flow()

    if "code_verifier" in session:
        flow.code_verifier = session.pop("code_verifier")

    try:
        flow.fetch_token(authorization_response=request.url)
    except Exception as e:
        session.pop("oauth_state", None)
        flash("Authentication expired or invalid. Please try logging in again.", "warning")
        return redirect(url_for("auth.login"))

    session.pop("oauth_state", None)

    credentials = flow.credentials
    request_session = requests.Session()
    cached_session = google_requests.Request(session=request_session)

    try:
        id_info = id_token.verify_oauth2_token(
            id_token=credentials.id_token,
            request=cached_session,
            audience=os.getenv("GOOGLE_CLIENT_ID"),
            clock_skew_in_seconds=10
        )
    except ValueError:
        flash("Invalid token received from Google.", "danger")
        return redirect(url_for("auth.login"))

    google_id = id_info.get("sub")
    email = id_info.get("email")
    full_name = id_info.get("name") or "Google User"
    username = email.split("@")[0]

    # Look up user in database
    user = User.query.filter((User.email == email) | (User.google_id == google_id)).first()

    if not user:
        dummy_password = generate_password_hash(os.urandom(24).hex())
        user = User(
            username=username,
            full_name=full_name,
            email=email,
            google_id=google_id,
            password_hash=dummy_password,
            is_active=True
        )

        default_role = Role.query.filter_by(name="user").first()
        if default_role:
            user.roles.append(default_role)

        db.session.add(user)
        db.session.commit()
    else:
        if not user.google_id:
            user.google_id = google_id
            db.session.commit()

    # 1. Log in user via Flask-Login
    session.permanent = True
    login_user(user, remember=True)

    # 2. Create Application Session Tokens
    access_token = Token.get_new_token()
    refresh_token = Token.generate_refresh_token(user)

    # Store token in session (matching standard login flow)
    session["refresh_token"] = refresh_token

    # 3. Create Audit Log
    data = {
        "user_id": user.id,
        "action": "USER_GOOGLE_LOGIN",
        "status": "SUCCESS",
        "ip_address": request.remote_addr,
        "user_agent": request.user_agent.string
    }
    AuditLogService.create_audit_log(data)

    flash("Successfully logged in with Google!", "success")

    # 4. Determine redirect URL based on role
    if user.has_role("admin"):
        redirect_url = url_for("dashboards.empIndex")
    else:
        redirect_url = url_for("dashboards.userIndex")

    # 5. Build response and set cookies cleanly
    response = redirect(redirect_url)
    response.set_cookie("access_token", access_token, httponly=True, path="/", samesite="Lax")
    response.set_cookie("refresh_token", refresh_token, httponly=True, path="/", samesite="Lax")

    return response

@auth_bp.route("/logout")
@login_required
def logout():
    # Save user Log
    data = {
        "user_id": current_user.id,
        "action": "USER_LOGOUT",
        "status": "SUCCESS",
        "ip_address": request.remote_addr,
        "user_agent": request.user_agent.string
    }
    AuditLogService.create_audit_log(data)

    # logout_user()
    session.pop("refresh_token", None)
    session.clear()
    AuthService.logout_user(current_user)
    return remove_cookie()