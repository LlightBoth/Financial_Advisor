from typing import Optional, List
from threading import Thread

from app.models.user import User
from app.services import UserServices

from werkzeug.security import check_password_hash
from sqlalchemy import text
from flask import make_response
from flask_mail import Message
from flask import current_app

# from http.cookies import mak

from app.security.token import Token
from extension import db
from app import mail

def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
            print("[INFO] Email sent successfully.")
        except Exception as e:
            print(f"[ERROR] Async email failed: {e}")


class AuthService:
    @staticmethod
    def login_user(email, password):
        find_user_email = User.query.filter_by(email=email).first()
        if find_user_email and find_user_email.check_password(password):
            # print("find_user_email", find_user_email)
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
        # print("offline_email", user)
        UserServices.update_user_offline(user)


    ### Helper function
    @staticmethod
    def find_user_email(email):
        user_email = User.query.filter_by(email=email).first()
        if user_email:
            # print("forgot_user_email_found")
            
            return user_email
        return None

    @staticmethod
    def send_email(to, subject, body, html=None):
        msg = Message(subject=subject, recipients=[to], body=body, html=html)
        app = current_app._get_current_object()
        
        # Dispatch email to background thread so HTTP worker doesn't freeze
        Thread(target=send_async_email, args=(app, msg)).start()
        return True

    
    @staticmethod
    def auth_role(user_role):
        if user_role == "user":
            return
        next

    
        