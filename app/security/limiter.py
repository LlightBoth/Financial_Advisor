import os
import redis
from flask import has_request_context
from flask_login import current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

def get_user_or_ip():
    if has_request_context() and current_user and current_user.is_authenticated:
        return f"user:{current_user.id}"
    return get_remote_address()

# Retrieve URI from environment
REDIS_URL = os.getenv("REDIS_URL")
STORAGE_URI = "memory://"

# Safely test Redis connection before handing it to Flask-Limiter
if REDIS_URL:
    try:
        r = redis.from_url(REDIS_URL, socket_timeout=2)
        r.ping()  # Test connection
        STORAGE_URI = REDIS_URL
        print("--- [Flask-Limiter]: Successfully connected to Redis ---")
    except (redis.exceptions.ConnectionError, Exception) as e:
        print(f"--- [Flask-Limiter Warning]: Could not connect to Redis ({e}). Falling back to memory:// ---")
else:
    print("--- [Flask-Limiter]: No REDIS_URL found. Using memory:// ---")

limiter = Limiter(
    key_func=get_user_or_ip,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=STORAGE_URI,
    storage_options={"socket_connect_timeout": 5}
)