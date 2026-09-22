from app.models.permission import Permission
from app.models.role import Role
from extension import db

# Complete, standardized permissions for all application modules
SYSTEM_PERMISSIONS = [
    # Users Module
    {"code": "user.view", "name": "View Users", "module": "Users", "descriptions": "Allows viewing user accounts and profiles."},
    {"code": "user.create", "name": "Create User", "module": "Users", "descriptions": "Allows registering and creating new user accounts."},
    {"code": "user.edit", "name": "Edit User", "module": "Users", "descriptions": "Allows modifying user details, roles, and status."},
    {"code": "user.delete", "name": "Delete User", "module": "Users", "descriptions": "Allows removing user accounts from the system."},

    # Roles Module
    {"code": "role.view", "name": "View Roles", "module": "Roles", "descriptions": "Allows viewing system roles and permissions."},
    {"code": "role.create", "name": "Create Role", "module": "Roles", "descriptions": "Allows defining new roles with custom permissions."},
    {"code": "role.edit", "name": "Edit Role", "module": "Roles", "descriptions": "Allows modifying role names and permission assignments."},
    {"code": "role.delete", "name": "Delete Role", "module": "Roles", "descriptions": "Allows removing roles from the system."},

    # Rules Module
    {"code": "rule.view", "name": "View Rules", "module": "Rules", "descriptions": "Allows viewing financial recommendation rules."},
    {"code": "rule.create", "name": "Create Rule", "module": "Rules", "descriptions": "Allows adding new financial logic rules."},
    {"code": "rule.edit", "name": "Edit Rule", "module": "Rules", "descriptions": "Allows modifying existing financial rules."},
    {"code": "rule.delete", "name": "Delete Rule", "module": "Rules", "descriptions": "Allows deleting financial logic rules."},

    # Facts Module
    {"code": "fact.view", "name": "View Facts", "module": "Facts", "descriptions": "Allows viewing system financial facts and parameters."},
    {"code": "fact.create", "name": "Create Fact", "module": "Facts", "descriptions": "Allows creating new financial facts."},
    {"code": "fact.edit", "name": "Edit Fact", "module": "Facts", "descriptions": "Allows editing existing financial facts."},
    {"code": "fact.delete", "name": "Delete Fact", "module": "Facts", "descriptions": "Allows deleting financial facts."},

    # Admin Dashboard Module
    {"code": "dashboard.admin.view", "name": "View Admin Dashboard", "module": "Admin Dashboard", "descriptions": "Allows viewing employee & system-wide analytics dashboard (/dashboards/emp)."},

    # Client Dashboard Module
    {"code": "dashboard.client.view", "name": "View Client Dashboard", "module": "Client Dashboard", "descriptions": "Allows viewing personal savings & financial dashboard (/dashboards/)."},

    # Plans Module
    {"code": "plan.view", "name": "View Plans", "module": "Plans", "descriptions": "Allows viewing savings and financial plans."},
    {"code": "plan.create", "name": "Create Plan", "module": "Plans", "descriptions": "Allows creating savings and financial plans."},
    {"code": "plan.edit", "name": "Edit Plan", "module": "Plans", "descriptions": "Allows editing existing financial plans."},
    {"code": "plan.delete", "name": "Delete Plan", "module": "Plans", "descriptions": "Allows deleting financial plans."},

    # Incomes Module
    {"code": "income.view", "name": "View Incomes", "module": "Incomes", "descriptions": "Allows viewing recorded income entries."},
    {"code": "income.create", "name": "Record Income", "module": "Incomes", "descriptions": "Allows recording new income entries."},
    {"code": "income.edit", "name": "Edit Income", "module": "Incomes", "descriptions": "Allows updating existing income entries."},
    {"code": "income.delete", "name": "Delete Income", "module": "Incomes", "descriptions": "Allows deleting income entries."},

    # Expenses Module
    {"code": "expense.view", "name": "View Expenses", "module": "Expenses", "descriptions": "Allows viewing expense records."},
    {"code": "expense.create", "name": "Record Expense", "module": "Expenses", "descriptions": "Allows recording new expenses."},
    {"code": "expense.edit", "name": "Edit Expense", "module": "Expenses", "descriptions": "Allows editing existing expenses."},
    {"code": "expense.delete", "name": "Delete Expense", "module": "Expenses", "descriptions": "Allows deleting expense records."},

    # Loans Module
    {"code": "loan.view", "name": "View Loans", "module": "Loans", "descriptions": "Allows viewing loan calculations and schedules."},
    {"code": "loan.create", "name": "Create Loan", "module": "Loans", "descriptions": "Allows creating and simulating loan applications."},
    {"code": "loan.edit", "name": "Edit Loan", "module": "Loans", "descriptions": "Allows modifying loan details."},
    {"code": "loan.delete", "name": "Delete Loan", "module": "Loans", "descriptions": "Allows removing loan records."},

    # Histories Module
    {"code": "history.view", "name": "View Histories", "module": "Histories", "descriptions": "Allows viewing audit and transaction history."},
    {"code": "history.delete", "name": "Delete History", "module": "Histories", "descriptions": "Allows purging transaction history logs."},

    # Advisors Module
    {"code": "advisor.view", "name": "View Advisor", "module": "Advisors", "descriptions": "Allows generating financial advisor recommendations."},

    # Settings Module
    {"code": "setting.view", "name": "View Settings", "module": "Settings", "descriptions": "Allows viewing system and account settings."},
    {"code": "setting.edit", "name": "Edit Settings", "module": "Settings", "descriptions": "Allows modifying preferences and settings."},
]


def seed_system_permissions():
    """
    Seeds all standard system permissions into the database.
    Deletes legacy 'Permissions', 'General', and old generic 'Dashboard' entries.
    """
    admin_role = Role.query.filter_by(name="admin").first()

    # 1. Purge legacy Permissions / General / old generic Dashboard entries
    legacy_perms = Permission.query.filter(
        (Permission.module.in_(["Permissions", "Permission", "General", "Dashboard"])) |
        (Permission.code.like("permission.%")) |
        (Permission.code == "reports.export") |
        (Permission.code == "dashboard.view")
    ).all()
    for lp in legacy_perms:
        db.session.delete(lp)
    db.session.commit()

    # 2. Seed active module permissions
    for perm_data in SYSTEM_PERMISSIONS:
        existing = Permission.query.filter_by(code=perm_data["code"]).first()
        if not existing:
            perm = Permission(
                code=perm_data["code"],
                name=perm_data["name"],
                module=perm_data["module"],
                descriptions=perm_data["descriptions"]
            )
            db.session.add(perm)
            
            if admin_role and perm not in admin_role.permissions:
                admin_role.permissions.append(perm)
        else:
            if existing.module != perm_data["module"]:
                existing.module = perm_data["module"]
            if admin_role and existing not in admin_role.permissions:
                admin_role.permissions.append(existing)

    db.session.commit()
