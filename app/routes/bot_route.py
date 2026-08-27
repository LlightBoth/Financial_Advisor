from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.security.cookie import check_cookie_token
from google import genai
from google.genai import types

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

@bot_bp.route('/chat', methods=['POST'])
@login_required
def chat():
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