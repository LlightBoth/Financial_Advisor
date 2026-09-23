from app.models.ai_chat import AIChat, AIMessage

class AIChatBotServices:
    @staticmethod
    def get_all_AI_Chats():
        return AIChat.query.all()

    @staticmethod
    def get_user_ai_chat(user_id: int):
        return AIChat.query.filter(AIChat.users.any(id=user_id)).all()

    @staticmethod
    def get_user_ai_chat_count(user_id: int):
        return AIMessage.query.join(AIChat).filter(
            AIChat.users.any(id=user_id),
            AIMessage.is_ai.is_(False)
        ).count()
