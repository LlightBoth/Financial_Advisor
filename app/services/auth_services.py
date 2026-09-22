import os
import base64
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.models.user import User
from app.services import UserServices

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# from http.cookies import mak

from app.security.token import Token
from extension import db
# from app import mail

# Scope Google api
SCOPES = [
    "https://www.googleapis.com/auth/gmail.send"
]

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
    def get_gmail_service():
        creds = None

        # 1. Try reading token.json (Local file OR Render Secret File)
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)

        # 2. Fallback: Read token string from Render Environment Variable
        elif os.getenv("GMAIL_TOKEN_JSON"):
            token_info = json.loads(os.getenv("GMAIL_TOKEN_JSON"))
            creds = Credentials.from_authorized_user_info(token_info, SCOPES)

        # 3. If credentials exist but expired, refresh them automatically
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        # 4. If credentials are missing or invalid
        if not creds or not creds.valid:
            raise RuntimeError(
                "[CRITICAL] token.json is missing or invalid! "
                "Please run generate_token.py locally first."
            )

        return build("gmail", "v1", credentials=creds)


    # This is send via SMTP
    @staticmethod
    def send_email(to, subject, body, html=None):
        try:
            service = AuthService.get_gmail_service()

            # Construct valid MIME format expected by Google API
            if html:
                mime_msg = MIMEMultipart("alternative")
                mime_msg.attach(MIMEText(body, "plain"))
                mime_msg.attach(MIMEText(html, "html"))
            else:
                mime_msg = MIMEText(body, "plain")

            mime_msg["to"] = to
            mime_msg["subject"] = subject

            # Base64url encode format for Gmail API payload
            raw_string = base64.urlsafe_b64encode(mime_msg.as_bytes()).decode()

            # Execute API call over HTTPS (Port 443)
            service.users().messages().send(
                userId="me",
                body={"raw": raw_string}
            ).execute()

            print(f"[SUCCESS] OTP email sent via Gmail API to {to}", flush=True)
            return True

        except Exception as e:
            print(f"[ERROR] Gmail API send failed: {e}", flush=True)
            return False
        
    @staticmethod
    def auth_role(user_role):
        if user_role == "user":
            return
        next

    
        