from flask import url_for


def user_has_role(user, role_name: str) -> bool:
    """Check if the user is authenticated and possesses the specified role."""
    if not user or not getattr(user, "is_authenticated", False):
        return False
    return any(r.name == role_name for r in getattr(user, "roles", []))


def user_has_permission(user, permission_code: str) -> bool:
    """Check if the user is authenticated and possesses the specified permission code."""
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if hasattr(user, "has_role") and user.has_role("admin"):
        return True
    if hasattr(user, "get_permission_codes"):
        return permission_code in user.get_permission_codes()
    return False


def is_management_user(user) -> bool:
    """Check if the user has administrative or management access to system modules."""
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if hasattr(user, "has_role") and user.has_role("admin"):
        return True
    management_perms = ["user.view", "role.view", "rule.view", "fact.view", "dashboard.view"]
    return any(user_has_permission(user, p) for p in management_perms)


def get_management_url(user) -> str:
    """Returns the primary management landing URL for the user based on granted permissions."""
    if not user or not getattr(user, "is_authenticated", False):
        return url_for("auth.login")
    if hasattr(user, "has_role") and user.has_role("admin"):
        return url_for("dashboards.empIndex")
    if user_has_permission(user, "dashboard.view"):
        return url_for("dashboards.empIndex")
    if user_has_permission(user, "user.view"):
        return url_for("users.index")
    if user_has_permission(user, "rule.view"):
        return url_for("rules.index")
    if user_has_permission(user, "role.view"):
        return url_for("roles.index")
    if user_has_permission(user, "fact.view"):
        return url_for("facts.index")
    return url_for("dashboards.empIndex")
