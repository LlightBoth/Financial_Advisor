from flask import Blueprint, jsonify
from flask_login import login_required, current_user

from app.services.notification_services import NotificationServices


notification_bp = Blueprint(
    "notifications",
    __name__,
    url_prefix="/notifications"
)


@notification_bp.route("/mark-all-read", methods=["POST"])
@login_required
def mark_all_as_read():

    NotificationServices.mark_all_as_read(current_user.id)

    unread_count = NotificationServices.get_unread_count(
        current_user.id
    )

    return jsonify({
        "success": True,
        "unread_count": unread_count
    }), 200


@notification_bp.route("/<int:notification_id>/read", methods=["POST"])
@login_required
def mark_as_read(notification_id):

    notification = NotificationServices.mark_as_read(
        notification_id,
        current_user.id
    )

    if not notification:
        return jsonify({
            "success": False,
            "message": "Notification not found"
        }), 404

    unread_count = NotificationServices.get_unread_count(
        current_user.id
    )

    return jsonify({
        "success": True,
        "unread_count": unread_count
    })
