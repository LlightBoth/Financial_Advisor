# check_user.py — run this directly with: python check_user.py
from app import create_app
from app.models.user import User

app = create_app()
with app.app_context():
    u = User.query.filter_by(email="admin123@gmail.com").first()
    print(u)
    print(u.check_password("Admin123"))