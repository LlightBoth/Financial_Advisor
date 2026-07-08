import flask
from config import Config
from flask_migrate import Migrate
from extension import db, csrf, login_manager
# from werkzeug.middleware.proxy_fix import ProxyFix
# from app.security.anti_dos import prevent_dos
from sqlalchemy import text

def create_app(config_class: type[Config] = Config):
    app = flask.Flask(__name__)
    app.config.from_object(config_class)
    migrate = Migrate(app, db)


    # Allow Http-Header Package 
    # app.wsgi_app = ProxyFix( app.wsgi_app,
    #     x_for=1,    # X-Forwarded-For (IP)
    #     x_proto=1, # X-Forwarded-Proto (http/https)
    #     x_host=1,  # X-Forwarded-Host
    #     x_port=1,  # X-Forwarded-Port
    # )
    

    # Initialize DB,CSRF For App
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    # prevent_dos.init_app(app)

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

    # Add "/" so it goes to Users list
    @app.route("/")
    def home():
        return flask.redirect(flask.url_for("auth.login"))

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

        user2_admin = User.query.filter_by(username="Dara").first()
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
    
    return app
