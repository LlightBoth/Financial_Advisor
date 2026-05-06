# Server-Side
from .user_routes import user_bp
from .auth_route import auth_bp
from .role_route import role_bp
from .permission_route import permission_bp
from .fact_route import fact_bp
from .rule_route import rule_bp

# Client-Side
from .dashboard_route import dashboard_bp
from .plan_route import plan_bp
from .advisor_route import advisor_bp
from .loan_route import loan_bp
from .history_route import history_bp
from .setting_route import setting_bp
from .profile_route import profile_bp