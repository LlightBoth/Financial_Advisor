import secrets
from flask import abort
from werkzeug.security import generate_password_hash, check_password_hash
from extension import db

from app.models.user import User

class Token:
    @staticmethod
    def get_new_token():
        return secrets.token_urlsafe(32)

    @staticmethod
    def generate_refresh_token(user: User):
        new_refresh_token = Token.get_new_token()
        user.refresh_token = generate_password_hash(new_refresh_token)
        db.session.commit()
        return new_refresh_token

    @staticmethod
    def check_token(user: User, rf_token: str) -> bool:
        if not user or not user.refresh_token or not rf_token:
            return abort(403)
        
        check_user_token = check_password_hash(user.refresh_token, rf_token)
        if not check_user_token:
            return abort(403)

    @staticmethod
    def rotate_refresh_token(user: User, old_token: str):
        if not Token.check_token(user, old_token):
            return None
        return Token.generate_refresh_token(user)

    @staticmethod
    def delete_token(user: User):
        user.refresh_token = None
        db.session.commit()
