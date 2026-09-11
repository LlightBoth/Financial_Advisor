import secrets
from flask import session
from werkzeug.security import generate_password_hash, check_password_hash
from extension import db
from app.models.user import User

class Token:
    @staticmethod
    def get_new_token():
        return secrets.token_urlsafe(32)

    @staticmethod
    def generate_refresh_token(user: User):
        # Ensure user exists and is a real model instance
        if not user or not hasattr(user, "id"):
            return None

        new_refresh_token = Token.get_new_token()
        user.refresh_token = generate_password_hash(new_refresh_token)
        db.session.commit()
        return new_refresh_token

    @staticmethod
    def check_token(user, rf_token: str) -> bool:
        # 1. Guard against None, AnonymousUserMixin, or unauthenticated state
        if not user or not getattr(user, "is_authenticated", False):
            return False

        # 2. Check if user model actually has a refresh token set
        hashed_rf_token = getattr(user, "refresh_token", None)
        if not hashed_rf_token or not rf_token:
            return False

        # 3. Verify hashed token against provided token
        if not check_password_hash(hashed_rf_token, rf_token):
            return False

        # 4. Check if session token matches (safely get session key without KeyError)
        session_rf_token = session.get("refresh_token")
        if not session_rf_token or session_rf_token != rf_token:
            return False

        return True

    @staticmethod
    def rotate_refresh_token(user, old_token: str):
        if not Token.check_token(user, old_token):
            return None
        return Token.generate_refresh_token(user)

    @staticmethod
    def delete_token(user):
        if user and hasattr(user, "refresh_token"):
            user.refresh_token = None
            db.session.commit()