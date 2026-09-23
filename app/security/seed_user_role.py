from datetime import datetime
from extension import db
from app.models.user import User
from app.models.role import Role


def seed_roles():
    role_names = ["user", "admin", "editor"]

    for role_name in role_names:
        role = Role.query.filter_by(name=role_name).first()

        if not role:
            db.session.add(Role(name=role_name))

    db.session.commit()

def seed_users():
    admin_role = Role.query.filter_by(name="admin").first()
    user_role = Role.query.filter_by(name="user").first()

    users = [
        {
            "username": "admin",
            "email": "admin123@gmail.com",
            "full_name": "Admin",
            "password": "Admin123",
            "role": admin_role,
        },
        {
            "username": "Dara",
            "email": "dara123@gmail.com",
            "full_name": "Dara",
            "password": "Dara123@",
            "role": admin_role,
        },

        # Seed users
        {
            "username": "Finn",
            "email": "finn@gmail.com",
            "full_name": "Finn",
            "password": "Finn123@",
            "role": user_role,
            "created_at": datetime(2026, 8, 15),
        },
        {
            "username": "Jake",
            "email": "jake@gmail.com",
            "full_name": "Jake",
            "password": "Jake123@",
            "role": user_role,
            "created_at": datetime(2026, 8, 2),
        },
        {
            "username": "Gumball",
            "email": "gumball@gmail.com",
            "full_name": "Gumball",
            "password": "Gumball123@",
            "role": user_role,
            "created_at": datetime(2026, 7, 20),
        },
        {
            "username": "Darwin",
            "email": "darwin@gmail.com",
            "full_name": "Darwin",
            "password": "Darwin123@",
            "role": user_role,
            "created_at": datetime(2026, 7, 5),
        },
        {
            "username": "Mordecai",
            "email": "mordecai@gmail.com",
            "full_name": "Mordecai",
            "password": "Mordecai123@",
            "role": user_role,
            "created_at": datetime(2026, 6, 22),
        },
        {
            "username": "Rigby",
            "email": "rigby@gmail.com",
            "full_name": "Rigby",
            "password": "Rigby123@",
            "role": user_role,
            "created_at": datetime(2026, 6, 10),
        },
        {
            "username": "Steven",
            "email": "steven@gmail.com",
            "full_name": "Steven",
            "password": "Steven123@",
            "role": user_role,
            "created_at": datetime(2026, 5, 28),
        },
        {
            "username": "Ben",
            "email": "ben@gmail.com",
            "full_name": "Ben",
            "password": "Ben123@",
            "role": user_role,
            "created_at": datetime(2026, 5, 15),
        },
        {
            "username": "Finnick",
            "email": "finnick@gmail.com",
            "full_name": "Finnick",
            "password": "Finnick123@",
            "role": user_role,
            "created_at": datetime(2026, 5, 3),
        },
        {
            "username": "Marceline",
            "email": "marceline@gmail.com",
            "full_name": "Marceline",
            "password": "Marceline123@",
            "role": user_role,
            "created_at": datetime(2026, 4, 18),
        },
    ]

    for data in users:
        existing_user = User.query.filter(
            db.or_(
                User.username == data["username"],
                User.email == data["email"],
                User.full_name == data["full_name"],
            )
        ).first()

        if existing_user:
            # Make sure the expected role exists
            if data["role"] and data["role"] not in existing_user.roles:
                existing_user.roles.append(data["role"])

            continue

        user = User(
            username=data["username"],
            email=data["email"],
            full_name=data["full_name"],
            is_active=False,
            created_at=data.get("created_at", datetime.utcnow()),
        )

        user.set_password(data["password"])

        if data["role"]:
            user.roles.append(data["role"])

        db.session.add(user)

    db.session.commit()


def seed_users_and_roles():
    seed_roles()
    seed_users()
