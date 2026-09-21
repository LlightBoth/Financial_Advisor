from app.models.audit_log import AuditLog
from extension import db


class AuditLogService:
    @staticmethod
    def get_all_audit_logs():
        """Retrieve all audit logs ordered by newest first."""
        return AuditLog.query.order_by(AuditLog.created_at.desc()).all()

    @staticmethod
    def get_audit_logs_id(log_id: int):
        """Fetch a single audit log record by primary key ID."""
        return db.session.get(AuditLog, log_id)
    
    @staticmethod
    def get_top_3_audit_logs():
        """Fetch top 3 recent audit logs."""
        return AuditLog.query.order_by(AuditLog.created_at.desc()).limit(3).all()

    @staticmethod
    def get_filtered_audit_logs(page: int = 1, per_page: int = 15, search: str = "", status: str = "", action: str = ""):
        """Paginate and filter audit log records for the UI index view."""
        query = AuditLog.query

        if status:
            query = query.filter(AuditLog.status == status)

        if action:
            query = query.filter(AuditLog.action == action)

        if search:
            if search.isdigit():
                query = query.filter(AuditLog.user_id == int(search))
            else:
                query = query.filter(AuditLog.action.ilike(f"%{search}%"))

        return query.order_by(AuditLog.created_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

    @staticmethod
    def create_audit_log(data: dict):
        """Safely record a new audit log event."""
        try:
            log = AuditLog(
                user_id=data.get("user_id"),
                action=data.get("action"),
                status=data.get("status"),
                ip_address=data.get("ip_address"),
                user_agent=data.get("user_agent")
            )
            db.session.add(log)
            db.session.commit()
            return log
        except Exception as e:
            db.session.rollback()
            raise e