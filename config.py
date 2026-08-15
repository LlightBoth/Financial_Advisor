import os
from dotenv import load_dotenv
import sqlite3

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

### Load Environment VAriables
load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "my_secret_key_assignment")

    DB_PATH = os.path.join(BASE_DIR, "instance", "financial.db")

    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL")
        or f"sqlite:///{DB_PATH}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # CALL SERVER OTP 
    MAIL_SERVER = os.getenv("MAIL_SERVER")
    MAIL_PORT = os.getenv("MAIL_PORT")
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    
    MAIL_USERNAME = os.getenv("SENDER_MAIL")
    MAIL_PASSWORD = os.getenv("SENDER_PASSWORD")
    MAIL_DEFAULT_SENDER = ("Financial Consultant App", os.getenv("SENDER_MAIL"))

    # Helper method to write sqlite raw data
    def get_sqlite3_connection(self):
        conn = sqlite3.connect(self.DB_PATH, check_same_thread=False)
        return conn