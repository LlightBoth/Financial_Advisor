import os
from dotenv import load_dotenv
import sqlite3

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

### Load Environment VAriables
load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "my_secret_key_assignment")

    INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
    os.makedirs(INSTANCE_DIR, exist_ok=True)

    DB_PATH = os.path.join(INSTANCE_DIR, "financial.db")

    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL")
        or f"sqlite:///{DB_PATH}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Helper method to write sqlite raw data
    def get_sqlite3_connection(self):
        conn = sqlite3.connect(self.DB_PATH, check_same_thread=False)
        return conn