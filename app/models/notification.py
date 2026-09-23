from datetime import datetime
from extension import db


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    title = db.Column(db.String(150), nullable=False)

    message = db.Column(db.Text, nullable=False)

    # Example:
    # income, expense, plan, ai, warning, system
    type = db.Column(
        db.String(30),
        nullable=False,
        default="system"
    )

    # Optional URL to the related page
    link = db.Column(
        db.String(255),
        nullable=True
    )

    is_read = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    user = db.relationship(
        "User",
        back_populates="notifications"
    )

    def __repr__(self):
        return f"<Notification {self.id}: {self.title}>"
