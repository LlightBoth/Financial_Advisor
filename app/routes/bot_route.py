from datetime import datetime
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.models.ai_chat import AIChat, AIMessage
from extension import db
from app.security.cookie import check_cookie_token
from google import genai
from google.genai import types

from app.security.limiter import limiter

bot_bp = Blueprint("bots", __name__, url_prefix="/bots")
client = genai.Client()

FINANCIAL_SYSTEM_INSTRUCTION = """
You are a Financial AI Assistant. Your purpose is to provide short, high-value financial advice and analysis.

STRICT CONSTRAINTS:
1. ONLY answer questions directly related to finance, budgeting, personal wealth, taxation, market concepts, and investing.
2. REFUSE ALL non-financial topics completely. If a query is unrelated to finance, respond with EXACTLY: "I can only assist with finance, budgeting, tax, and investment inquiries."
3. FORMATTING: Provide ONLY short, key summaries focusing on actionable financial insights. Omit unnecessary fluff, greetings, conversational filler, and wordy explanations. Keep responses brief and structured.
"""

@bot_bp.before_request
def check_token():
    check_cookie_token(current_user)

@bot_bp.route("/")
@login_required
def index():
    return render_template("bots/index.html")

@bot_bp.route("/chat", methods=["POST"])
@login_required
@limiter.limit("3 per minute; 10 per hour")
def chat():
    try:
        data = request.get_json(silent=True) or {}

        user_message = data.get("message", "").strip()
        chat_id = data.get("chat_id")

        if not user_message:
            return jsonify({"error": "Message cannot be empty"}), 400

        # Find existing chat belonging to the current user
        ai_chat = None

        if chat_id:
            ai_chat = (
                AIChat.query
                .filter(
                    AIChat.id == chat_id,
                    AIChat.users.any(id=current_user.id)
                )
                .first()
            )

        # If no valid chat was supplied, create a new one
        if not ai_chat:
            ai_chat = AIChat(
                descriptions="Financial Assistant",
                counts=0
            )

            ai_chat.users.append(current_user)

            db.session.add(ai_chat)
            db.session.flush()

        # Load previous messages from this conversation
        messages = (
            AIMessage.query
            .filter_by(ai_id=ai_chat.id)
            .order_by(AIMessage.created_at.asc())
            .all()
        )

        sdk_history = [
            types.Content(
                role="model" if message.is_ai else "user",
                parts=[
                    types.Part.from_text(
                        text=message.content
                    )
                ]
            )
            for message in messages
        ]

        # Create Gemini conversation
        chat_instance = client.chats.create(
            model="gemini-3.6-flash",
            history=sdk_history,
            config=types.GenerateContentConfig(
                system_instruction=FINANCIAL_SYSTEM_INSTRUCTION,
                temperature=0.2
            )
        )

        # Send current message
        response = chat_instance.send_message(user_message)
        ai_response = response.text

        # Save user message
        db.session.add(
            AIMessage(
                ai_id=ai_chat.id,
                content=user_message,
                is_ai=False
            )
        )

        # Save AI message
        db.session.add(
            AIMessage(
                ai_id=ai_chat.id,
                content=ai_response,
                is_ai=True
            )
        )

        ai_chat.counts += 2
        ai_chat.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            "response": ai_response,
            "chat_id": ai_chat.id
        })

    except Exception as e:
        db.session.rollback()

        print(
            f"[Gemini API Error]: "
            f"{type(e).__name__} - {e}"
        )

        return jsonify({
            "error": "Unable to process your request."
        }), 500



@bot_bp.route("/chat/current", methods=["GET"])
@login_required
def current_chat():
    try:
        # Get the user's most recently updated conversation
        ai_chat = (
            AIChat.query
            .filter(AIChat.users.any(id=current_user.id))
            .order_by(AIChat.updated_at.desc())
            .first()
        )

        if not ai_chat:
            return jsonify({
                "chat_id": None,
                "messages": []
            })

        messages = (
            AIMessage.query
            .filter_by(ai_id=ai_chat.id)
            .order_by(AIMessage.created_at.asc())
            .all()
        )

        return jsonify({
            "chat_id": ai_chat.id,
            "messages": [
                {
                    "content": message.content,
                    "is_ai": message.is_ai,
                    "created_at": (
                        message.created_at.isoformat()
                        if message.created_at
                        else None
                    )
                }
                for message in messages
            ]
        })

    except Exception as e:
        print(
            f"[Chat History Error]: "
            f"{type(e).__name__} - {e}"
        )

        return jsonify({
            "error": "Unable to load conversation."
        }), 500



@bot_bp.route("/chat/<int:chat_id>", methods=["DELETE"])
@login_required
def delete_chat(chat_id):
    try:
        ai_chat = (
            AIChat.query
            .filter(
                AIChat.id == chat_id,
                AIChat.users.any(id=current_user.id)
            )
            .first()
        )

        if not ai_chat:
            return jsonify({
                "error": "Conversation not found."
            }), 404

        db.session.delete(ai_chat)
        db.session.commit()

        return jsonify({
            "success": True
        })

    except Exception as e:
        db.session.rollback()

        print(
            f"[Delete Chat Error]: "
            f"{type(e).__name__} - {e}"
        )

        return jsonify({
            "error": "Unable to delete conversation."
        }), 500


    
@bot_bp.route('/analyse', methods=['POST'])
@login_required
@limiter.limit("3 per minute; 10 per hour")
def analyse():
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        history = data.get('history', [])

        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400

        # Convert frontend history to Gemini SDK format (exclude the latest prompt)
        sdk_history = [
            types.Content(
                role=item['role'], 
                parts=[types.Part.from_text(text=item['content'])]
            )
            for item in history[:-1]  # Exclude current message
        ]

        # Initialize multi-turn chat with history
        chat_instance = client.chats.create(
            model='gemini-3.6-flash',
            history=sdk_history,
            config=types.GenerateContentConfig(
                system_instruction=FINANCIAL_SYSTEM_INSTRUCTION,
                temperature=0.2
            )
        )

        response = chat_instance.send_message(user_message)
        return jsonify({'response': response.text})

    except Exception as e:
        print(f"[Gemini API Error]: {type(e).__name__} - {e}")
        return jsonify({'error': f'Backend Error: {str(e)}'}), 500