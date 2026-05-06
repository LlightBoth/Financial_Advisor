from extension import db

# Server-Side
user_roles = db.Table(
    "user_roles",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("roles_id", db.Integer, db.ForeignKey("roles.id"), primary_key=True),
)

role_permissions = db.Table(
    "role_permissions",
    db.Column("role_id", db.Integer, db.ForeignKey("roles.id"), primary_key=True),
    db.Column("permission_id", db.Integer, db.ForeignKey("permissions.id"), primary_key=True),
)

rule_facts = db.Table(
    "rule_facts",
    db.Column("rule_id", db.Integer, db.ForeignKey("rules.id"), primary_key=True),
    db.Column("fact_id", db.Integer, db.ForeignKey("facts.id"), primary_key=True),
)

# Client-Side
user_plans = db.Table(
    "user_plans",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("plan_id", db.Integer, db.ForeignKey("plans.id"), primary_key=True),
)
user_histories = db.Table(
    "user_histories",
    db.Column("user_id", db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column("history_id", db.Integer, db.ForeignKey('histories.id'), primary_key=True)
)