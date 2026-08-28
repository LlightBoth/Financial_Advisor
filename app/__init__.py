import flask
from flask_migrate import Migrate
from config import Config
from extension import db, csrf, login_manager
# from werkzeug.middleware.proxy_fix import ProxyFix
# from app.security.anti_dos import prevent_dos
from sqlalchemy import text


# Initail App
def create_app(config_class: type[Config] = Config):
    app = flask.Flask(__name__)
    app.config.from_object(config_class)
    migrate = Migrate(app, db)

    
    # Initialize DB,CSRF For App
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    # prevent_dos.init_app(app)

    # Register Jinja global helpers
    from app.utils.template_helpers import user_has_role, user_has_permission, is_management_user, get_management_url
    app.jinja_env.globals.update(
        user_has_role=user_has_role,
        user_has_permission=user_has_permission,
        is_management_user=is_management_user,
        get_management_url=get_management_url,
    )

    # Optional setting
    login_manager.login_view = "auth.login" # Blueprint.rout name
    login_manager.login_message = "Please login to view this page"
    login_manager.login_message_category = "warning"

    # This function tells Flask-login how to load a user from a session
    @login_manager.user_loader
    def load_user(user_id):
        user = User.query.get(int(user_id))
        return user
    

    # Register blueprints Server-Side
    from app.routes.user_routes import user_bp
    from app.routes.auth_route import auth_bp
    from app.routes.role_route import role_bp
    from app.routes.permission_route import permission_bp
    from app.routes.fact_route import fact_bp
    from app.routes.rule_route import rule_bp

    # Register blueprints Client-Side
    from app.routes.plan_route import plan_bp
    from app.routes.advisor_route import advisor_bp
    from app.routes.loan_route import loan_bp
    from app.routes.dashboard_route import dashboard_bp
    from app.routes.history_route import history_bp
    from app.routes.setting_route import setting_bp
    from app.routes.profile_route import profile_bp
    from app.routes.income_route import income_bp
    from app.routes.expense_route import expense_bp
    from app.routes.bot_route import bot_bp

    app.register_blueprint(user_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(role_bp)
    app.register_blueprint(permission_bp)
    app.register_blueprint(fact_bp)
    app.register_blueprint(rule_bp)
    app.register_blueprint(plan_bp)
    app.register_blueprint(advisor_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(setting_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(loan_bp)
    app.register_blueprint(income_bp)
    app.register_blueprint(expense_bp)
    app.register_blueprint(bot_bp)

    # Root landing page for visitors
    @app.route("/")
    def home():
        return flask.render_template("landing.html")

    # Create Table
    with app.app_context():
        from app.models.user import User
        from app.models.plan import Plan
        from app.models.role import Role
        from app.models.permission import Permission
        from app.models.fact import Fact
        from app.models.rule import Rule

        # db.drop_all()
        db.create_all()

        # === Add Data To DB Column ===
        # Add few role in db
        roles = [
            "user",
            "admin",
            "editor"
        ]

        for role_name in roles:
            # Check if role already exists
            if not Role.query.filter_by(name=role_name).first():
                role = Role(name=role_name)
                db.session.add(role)
    
        admin_role = Role.query.filter_by(name="admin").first()

        user_admin = User.query.filter_by(username="admin").first()
        if not user_admin:
            user_admin = User(
                username="admin",
                email="admin123@gmail.com",
                full_name="admin",
            )
            user_admin.set_password("Admin123")
            user_admin.roles.append(admin_role)
            db.session.add(user_admin)

        user2_admin = User.query.filter_by(full_name="Dara").first()
        if not user2_admin:
            user2_admin = User(
                username="Dara",
                email="dara123@gmail.com",
                full_name="Dara",
            )
            user2_admin.set_password("Dara123")
            user2_admin.roles.append(admin_role)
            db.session.add(user2_admin)

        db.session.commit()

        # Seed full system permissions across all modules
        from app.security.seed_permissions import seed_system_permissions
        seed_system_permissions()
    
    return app
