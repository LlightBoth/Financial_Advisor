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
            "password": "Dara123",
            "role": admin_role,
        },
    ]

    for data in users:
        existing_user = User.query.filter(
            db.or_(
                User.username == data["username"],
                User.email == data["email"],
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
            is_active=True,
        )

        user.set_password(data["password"])

        if data["role"]:
            user.roles.append(data["role"])

        db.session.add(user)

    db.session.commit()


def seed_users_and_roles():
    seed_roles()
    seed_users()
