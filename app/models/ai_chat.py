from datetime import datetime
from extension import db
from app.models.associations import user_ai


class AIChat(db.Model):
    __tablename__ = "ai_chats"

    id = db.Column(db.Integer, primary_key=True)
    descriptions = db.Column(db.Text, nullable=True)
    counts = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    users = db.relationship("User", secondary=user_ai, back_populates="ai_chats")
    messages = db.relationship("AIMessage", back_populates="ai_session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AI {self.id}>"


class AIMessage(db.Model):
    __tablename__ = "ai_messages"

    id = db.Column(db.Integer, primary_key=True)
    ai_id = db.Column(db.Integer, db.ForeignKey("ai_chats.id", ondelete="CASCADE"), nullable=False)
    
    # The actual message text
    content = db.Column(db.Text, nullable=False)
    
    # Option A: Using a Boolean (True = AI sent it, False = User sent it)
    is_ai = db.Column(db.Boolean, default=False, nullable=False)
    
    # Option B: Using a String (Alternative: "user" or "ai")
    # sender = db.Column(db.String(20), nullable=False) 

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationship back to the AI session
    ai_session = db.relationship("AIChat", back_populates="messages")

    def __repr__(self):
        speaker = "AI" if self.is_ai else "User"
        return f"<AIMessage {self.id} from {speaker}>"