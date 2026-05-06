from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

prevent_dos = Limiter(
    key_func= get_remote_address,
    default_limits=["100 per day"]
)