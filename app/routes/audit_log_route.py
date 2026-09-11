from flask import Blueprint, render_template, abort, request
from flask_login import login_required

from app.services.audit_log_services import AuditLogService
from app.security.limiter import limiter
from app.security.cookie import check_cookie_token

audit_log_bp = Blueprint("audit_logs", __name__, url_prefix="/audit_logs")

# Optional RBAC check: Ensure only admin roles can view audit logs
# @audit_log_bp.before_request
# @login_required
# def ensure_admin():
#     if not current_user.is_admin:
#         abort(403)


@audit_log_bp.route("/", methods=["GET"])
@login_required
@limiter.limit("30 per minute")  # Relaxed slightly for dashboard browsing
def index():
    # Extract query parameters from request URL
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "", type=str)
    status = request.args.get("status", "", type=str)
    action = request.args.get("action", "", type=str)

    # Fetch paginated & filtered records from your service layer
    pagination = AuditLogService.get_filtered_audit_logs(
        page=page, 
        per_page=15, 
        search=search, 
        status=status, 
        action=action
    )
    
    return render_template(
        "audit_logs/index.html",
        logs=pagination.items,
        pagination=pagination
    )


@audit_log_bp.route("/<int:log_id>", methods=["GET"])
@login_required
@limiter.limit("30 per minute")
def detail(log_id):
    audit_log = AuditLogService.get_audit_logs_id(log_id)
    if audit_log is None:
        abort(404)
    return render_template("audit_logs/detail.html", audit_log=audit_log)