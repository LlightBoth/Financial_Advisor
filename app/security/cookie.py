from flask import redirect, url_for, make_response, request, abort

from app.security.token import Token

def get_cookie(redirect_url, access_token, refresh_token):
    res = make_response(redirect(redirect_url))
    res.set_cookie(
        "access_token",
        access_token,
        httponly=True,
        secure=True,
        samesite="Lax"
    )
    res.set_cookie(
        "access_token",
        access_token,
        httponly=True,
        secure=True,
        samesite="Lax"
    )
    return res


def check_cookie_token(current_user):
    acess_cookie = request.cookies.get('access_token')
    refresh_cookie = request.cookies.get('refresh_token')

    if acess_cookie and refresh_cookie:
        Token.check_token(current_user, refresh_cookie)
        return
    else:
        abort(403)


def remove_cookie():
    res = make_response(redirect(url_for("auth.login")))
    res.delete_cookie('access_token')
    res.delete_cookie('refresh_token')

    return res