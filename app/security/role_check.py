from flask import abort
from flask_login import current_user


def get_current_user_role():
    if not current_user.is_authenticated:
        return
    role_name = current_user.roles[0].name
    return role_name


def check_user_role():
    role_name = get_current_user_role()
    print(f'user access this route: {role_name}')
    if role_name not in ("admin", "editor"):
        abort(403)


def role_editor_only():
    user_role = get_current_user_role()
    if user_role != 'editor':
        abort(403)
    
    
def role_user_only():
    user_role = get_current_user_role()
    if user_role != 'user':
        abort(403)


def role_admin_only():
    role_name = get_current_user_role()
    if role_name != "admin":
        abort(403)
