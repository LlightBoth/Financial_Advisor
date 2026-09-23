from extension import db
from app.models.notification import Notification


class NotificationServices:

    @staticmethod
    def create_notification(
        user_id,
        title,
        message,
        notification_type="system",
        link=None
    ):
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=notification_type,
            link=link,
            is_read=False
        )

        db.session.add(notification)
        db.session.commit()

        return notification

    @staticmethod
    def cleanup_old_notifications(user_id, keep=100):

        notifications = (
            Notification.query
            .filter_by(user_id=user_id)
            .order_by(Notification.created_at.desc())
            .offset(keep)
            .all()
        )

        for notification in notifications:
            db.session.delete(notification)

        db.session.commit()


    @staticmethod
    def get_user_notifications(user_id, limit=3):
        return (
            Notification.query
            .filter(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .all()
        )


    @staticmethod
    def get_unread_count(user_id):
        return (
            Notification.query
            .filter(
                Notification.user_id == user_id,
                Notification.is_read.is_(False)
            )
            .count()
        )


    @staticmethod
    def mark_as_read(notification_id, user_id):

        notification = (
            Notification.query
            .filter_by(
                id=notification_id,
                user_id=user_id
            )
            .first()
        )

        if not notification:
            return None

        if not notification.is_read:
            notification.is_read = True
            db.session.commit()

        return notification



    @staticmethod
    def mark_all_as_read(user_id):
        updated_count = (
            Notification.query
            .filter(
                Notification.user_id == user_id,
                Notification.is_read.is_(False)
            )
            .update(
                {"is_read": True},
                synchronize_session=False
            )
        )

        db.session.commit()

        return updated_count
