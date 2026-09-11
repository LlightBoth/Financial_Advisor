import os
from flask import redirect, url_for, request, abort
from app.security.token import Token

def get_cookie(redirect_url, access_token=None, refresh_token=None):
    # Obtain the redirect response directly without re-wrapping in make_response
    res = redirect(redirect_url)
    
    # Enable secure cookies ONLY when running on HTTPS / Production
    is_secure = request.is_secure or os.getenv("FLASK_ENV") == "production"

    res.set_cookie(
        "access_token",
        access_token or "",
        httponly=True,
        secure=is_secure,
        samesite="Lax",
        path="/"
    )
    res.set_cookie(
        "refresh_token",
        refresh_token or "",
        httponly=True,
        secure=is_secure,
        samesite="Lax",
        path="/"
    )
    return res

def check_cookie_token(current_user=None):
    access_cookie = request.cookies.get("access_token")
    refresh_cookie = request.cookies.get("refresh_token")

    # Guard missing cookies
    if not access_cookie or not refresh_cookie:
        abort(403)

    # Return True/False from check_token safely
    is_valid = Token.check_token(current_user, refresh_cookie)
    if not is_valid:
        abort(403)


def remove_cookie():
    res = redirect(url_for("auth.login"))
    res.delete_cookie('access_token', path="/")
    res.delete_cookie('refresh_token', path="/")

    return res