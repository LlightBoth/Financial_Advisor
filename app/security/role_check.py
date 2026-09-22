from functools import wraps
from flask import abort, request
from flask_login import current_user


def get_current_user_role():
    if not current_user.is_authenticated or not current_user.roles:
        return None
    return current_user.roles[0].name


def check_user_role():
    role_name = get_current_user_role()
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


# Mapping of route endpoint functions to permission action names
ACTION_MAP = {
    "index": "view",
    "detail": "view",
    "create": "create",
    "edit": "edit",
    "delete": "delete",
    "delete_confirm": "delete",
}

# Module blueprint aliases (maps blueprint name to permission prefix)
MODULE_MAP = {
    "roles": "role",
    "users": "user",
    "rules": "rule",
    "facts": "fact",
    "plans": "plan",
    "incomes": "income",
    "expenses": "expense",
    "loans": "loan",
    "histories": "history",
    "advisors": "advisor",
    "settings": "setting",
    "dashboards": "dashboard",
}


def check_permission(permission_code):
    if not current_user.is_authenticated:
        abort(403)
    if not current_user.has_permission(permission_code):
        abort(403)


def check_route_permission():
    """
    Automatic RBAC middleware:
    Inspects request.endpoint and automatically checks the corresponding permission.
    Admins are always granted full access.
    """
    if not current_user.is_authenticated:
        abort(403)
    if current_user.has_role("admin"):
        return  # Admin bypasses all checks

    endpoint = request.endpoint or ""
    if "." not in endpoint:
        return

    blueprint, func = endpoint.split(".", 1)
    
    # Check if blueprint is a management module
    if blueprint not in MODULE_MAP and blueprint not in ("permission", "role", "user", "rule", "fact"):
        return

    module = MODULE_MAP.get(blueprint, blueprint)
    action = ACTION_MAP.get(func, func)

    # Check candidates: e.g. "permission.create", "permissions.create", "permission.view"
    candidates = [
        f"{module}.{action}",
        f"{blueprint}.{action}",
        f"{module}.{func}",
        f"{blueprint}.{func}",
        endpoint,
    ]

    has_perm = any(current_user.has_permission(c) for c in candidates)
    if not has_perm:
        abort(403)


def permission_required(permission_code):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            check_permission(permission_code)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
