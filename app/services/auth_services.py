from typing import Optional, List

from app.models.user import User
from app.services import UserServices

from werkzeug.security import check_password_hash
from sqlalchemy import text
from flask import make_response
# from http.cookies import mak

from app.security.token import Token
from extension import db

class AuthService:
    @staticmethod
    def login_user(email, password):
        find_user_email = User.query.filter_by(email=email).first()
        if find_user_email and find_user_email.check_password(password):
            print("find_user_email", find_user_email)
            UserServices.update_user_online(find_user_email)
            access_token = Token.get_new_token()
            refresh_token = Token.generate_refresh_token(find_user_email)

            return find_user_email, access_token, refresh_token
        return None, None, None

    
    @staticmethod
    def register_user(data: dict, password):
        registered_user = UserServices.create(data, password)
        return registered_user


    @staticmethod
    def logout_user(user: User):
        print("offline_email", user)
        UserServices.update_user_offline(user)
    
    @staticmethod
    def auth_role(user_role):
        if user_role == "user":
            return
        next

    
        