import flask
from flask_migrate import Migrate
from config import Config
from extension import db, csrf, login_manager
from werkzeug.middleware.proxy_fix import ProxyFix
from app.security.limiter import limiter
from sqlalchemy import text
import sys
from sqlalchemy.exc import OperationalError


# Initail App
def create_app(config_class: type[Config] = Config):
    app = flask.Flask(__name__)
    app.config.from_object(config_class)

    # Fix Remote IP reading behind Render's reverse proxy
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    migrate = Migrate(app, db)
    
    # Initialize DB,CSRF For App
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)

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
    from app.routes.audit_log_route import audit_log_bp

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
    app.register_blueprint(audit_log_bp)

    # Root landing page for visitors
    @app.route("/")
    @limiter.limit("5 per minute")
    def home():
        return flask.render_template("landing.html")


    # ---------------------- #
    #  Prevent/Rate Limiter  #
    # ---------------------- #
    @app.errorhandler(429)
    def ratelimit_handler(e):
        # Check if the request expects JSON (API calls, fetch, axios, postman)
        if flask.request.is_json or flask.request.accept_mimetypes.best == 'application/json':
            return flask.jsonify({
                "error": "Rate limit exceeded",
                "message": "You are making requests too quickly. Please wait a minute and try again."
            }), 429

        # Otherwise, assume it is a standard browser page/form submission
        return flask.redirect(flask.url_for('auth.login'))


    # --------------- #
    #   Create Table  #
    # --------------- #
    # Don't run seed script during migration generation
    if "migrate" not in sys.argv and "upgrade" not in sys.argv:
        with app.app_context():
            try:
                from app.models.user import User
                from app.models.plan import Plan
                from app.models.role import Role
                from app.models.permission import Permission
                from app.models.fact import Fact
                from app.models.rule import Rule
                from app.security.seed_permissions import seed_system_permissions

                db.create_all()

                roles = ["user", "admin", "editor"]
                for role_name in roles:
                    if not Role.query.filter_by(name=role_name).first():
                        db.session.add(Role(name=role_name))
                db.session.commit()

                admin_role = Role.query.filter_by(name="admin").first()

                if not User.query.filter_by(username="admin").first():
                    user_admin = User(
                        username="admin",
                        email="admin123@gmail.com",
                        full_name="admin",
                    )
                    user_admin.set_password("Admin123")
                    if admin_role:
                        user_admin.roles.append(admin_role)
                    db.session.add(user_admin)

                if not User.query.filter_by(full_name="Dara").first():
                    user2_admin = User(
                        username="Dara",
                        email="dara123@gmail.com",
                        full_name="Dara",
                    )
                    user2_admin.set_password("Dara123")
                    if admin_role:
                        user2_admin.roles.append(admin_role)
                    db.session.add(user2_admin)

                db.session.commit()

                # Seed permissions safely
                seed_system_permissions()

            except OperationalError:
                # Table mismatch/pending migration detected, skip seeding safely
                db.session.rollback()
                
    return app
