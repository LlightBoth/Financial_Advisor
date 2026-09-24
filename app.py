"""
Financial Advisor AI - Hugging Face Space App
Serves:
1. Interactive Gradio Web Chat UI for browser visitors.
2. REST API endpoints (/health, /chat, /extract, /explain) for the Financial Advisor Flask app.
"""

# 1. Hugging Face ZeroGPU MUST be imported first before any other package (especially torch)
try:
    import spaces
except ImportError:
    class MockSpaces:
        @staticmethod
        def GPU(func=None, **kwargs):
            if func is not None:
                return func
            def decorator(f):
                return f
            return decorator
    spaces = MockSpaces()

import os
import sys
import json
import time
import re
from typing import Dict, Any, Optional

# Add project root to sys.path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import torch
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import gradio as gr

# Import model inference and normalizer functions
from training.serve_llm import (
    load_model, generate_response, is_safety_violation, is_educational_query,
    EXTRACTION_INSTRUCTION, EXPLANATION_INSTRUCTION, EXPLANATION_INSTRUCTION_KM,
    SAFETY_INSTRUCTION, SAFETY_INSTRUCTION_KM, EDUCATION_INSTRUCTION, EDUCATION_INSTRUCTION_KM,
    BASE_MODEL_ID
)
from training.llm_output_normalizer import (
    normalize_llm_output, normalize_and_verify_response,
    detect_language, CANONICAL_FIELDS, detect_debt_status, detect_employment_status
)

# 1. Initialize Model
print("Initializing Financial Advisor AI model for Hugging Face Space...")
load_model()


@spaces.GPU
def run_generation(instruction: str, user_input: str, max_new_tokens: int = 256) -> str:
    """ZeroGPU decorated inference entrypoint."""
    return generate_response(instruction, user_input, max_new_tokens=max_new_tokens)

# 2. FastAPI Application for REST endpoints
api_app = FastAPI(title="Financial Advisor AI API")
api_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@api_app.get("/health")
def health():
    has_cuda = torch.cuda.is_available()
    vram = 0.0
    try:
        if has_cuda:
            vram = round(torch.cuda.memory_allocated(0) / (1024**3), 2)
    except Exception:
        vram = 0.0
    return {
        "status": "ok",
        "service": "Trained Financial Advisor AI",
        "base_model": BASE_MODEL_ID,
        "adapter": "financial_advisor_ai_v4",
        "device": "cuda" if has_cuda else "cpu",
        "vram_allocated_gb": vram,
    }


@api_app.post("/extract")
async def extract_endpoint(request: Request):
    data = await request.json()
    text = (data.get("text") or "").strip()
    if not text:
        return JSONResponse(status_code=400, content={"error": "Missing 'text' field"})

    raw_out = generate_response(EXTRACTION_INSTRUCTION, text, max_new_tokens=150)
    normalized_slots = normalize_llm_output(raw_out, text)
    return {
        "success": True,
        "raw_output": raw_out,
        "slots": normalized_slots,
    }


@api_app.post("/explain")
async def explain_endpoint(request: Request):
    data = await request.json()
    lang = data.get("language") or "en"
    income = data.get("monthly_income", 0.0)
    expense = data.get("monthly_expense", 0.0)
    net_cf = data.get("net_cashflow", income - expense)
    debt_desc = data.get("debt_status") or ("debt" if data.get("debt_present") else "no debt")
    if data.get("debt_assumed"):
        debt_desc = "not provided (assumed no debt)" if lang == "en" else "មិនបានបញ្ជាក់ (សន្មត់ថាគ្មានបំណុល)"
    advice_str = data.get("advice") or data.get("conclusion") or "Maintain balanced finances."

    sign = "+" if net_cf >= 0 else "-"
    if lang == "km":
        profile_str = (
            f"ទិន្នន័យហិរញ្ញវត្ថុ: ចំណូលប្រចាំខែ: ${income:,.2f}, "
            f"ចំណាយប្រចាំខែ: ${expense:,.2f}, "
            f"លំហូរសាច់ប្រាក់សុទ្ធ: {sign}${abs(net_cf):,.2f}, "
            f"ស្ថានភាពបំណុល: {debt_desc}។ "
            f"អនុសាសន៍ដែលបានផ្ទៀងផ្ទាត់: {advice_str}"
        )
    else:
        profile_str = (
            f"Financial Profile: Monthly Income: ${income:,.2f}, "
            f"Monthly Expense: ${expense:,.2f}, "
            f"Net Cash Flow: {sign}${abs(net_cf):,.2f}, "
            f"Debt Status: {debt_desc}. "
            f"Verified Advice: {advice_str}"
        )

    instr = EXPLANATION_INSTRUCTION_KM if lang == "km" else EXPLANATION_INSTRUCTION
    explanation = generate_response(instr, profile_str, max_new_tokens=85)
    context_prof = {
        "monthly_income": income,
        "monthly_expense": expense,
        "net_cashflow": net_cf,
        "debt_status": debt_desc,
    }
    explanation = normalize_and_verify_response(
        explanation,
        user_input=profile_str,
        context_profile=context_prof,
        lang=lang,
    )
    return {
        "success": True,
        "profile_str": profile_str,
        "language": lang,
        "explanation": explanation,
    }


@api_app.post("/chat")
async def chat_endpoint(request: Request):
    data = await request.json()
    message = (data.get("message") or "").strip()
    if not message:
        return JSONResponse(status_code=400, content={"error": "Message cannot be empty"})

    lang = data.get("language") or detect_language(message)
    existing_profile = data.get("existing_profile") or {}

    # 1. Safety Boundary Check
    if is_safety_violation(message):
        instr = SAFETY_INSTRUCTION_KM if lang == "km" else SAFETY_INSTRUCTION
        safety_resp = generate_response(instr, message, max_new_tokens=120)
        safety_resp = normalize_and_verify_response(safety_resp, user_input=message, lang=lang)
        return {
            "success": True,
            "type": "safety_refusal",
            "language": lang,
            "response": safety_resp,
        }

    # 2. Concept / Educational Check
    if is_educational_query(message):
        instr = EDUCATION_INSTRUCTION_KM if lang == "km" else EDUCATION_INSTRUCTION
        edu_resp = generate_response(instr, message, max_new_tokens=140)
        edu_resp = normalize_and_verify_response(edu_resp, user_input=message, lang=lang)
        return {
            "success": True,
            "type": "financial_education",
            "language": lang,
            "response": edu_resp,
        }

    # 3. Greeting Check
    is_greeting = bool(re.search(r"^(hello|hi|hey|greetings|good\s+(morning|afternoon|evening)|howdy|សួស្តី|ជំរាបសួរ|ជម្រាបសួរ)[.!?\s]*$", message.strip(), re.IGNORECASE))
    if is_greeting:
        greet_resp = (
            "សួស្តី! ខ្ញុំជាជំនួយការប្រឹក្សាហិរញ្ញវត្ថុ AI របស់អ្នក។ តើខ្ញុំអាចជួយអ្នកក្នុងការរៀបចំផែនការហិរញ្ញវត្ថុ ថវិកា ឬការសន្សំយ៉ាងដូចម្តេចដែរ?"
            if lang == "km"
            else "Hello! I am your Financial Advisor AI. How can I help you with your budgeting, savings, or financial planning today?"
        )
        return {
            "success": True,
            "type": "greeting",
            "language": lang,
            "response": greet_resp,
        }

    # 4. Fast-path & Fact Extraction
    has_numbers = bool(re.search(r"\d", message))
    debt_mentioned = detect_debt_status(message) is not None
    emp_mentioned = detect_employment_status(message) is not None

    if not has_numbers and not debt_mentioned and not emp_mentioned:
        normalized_slots = {k: None for k in CANONICAL_FIELDS}
    else:
        raw_out = generate_response(EXTRACTION_INSTRUCTION, message, max_new_tokens=75)
        normalized_slots = normalize_llm_output(raw_out, message)

    # Build contextual response
    profile_summary = []
    if normalized_slots.get("monthly_income"):
        profile_summary.append(f"Income: ${normalized_slots['monthly_income']:,.2f}")
    if normalized_slots.get("monthly_expense"):
        profile_summary.append(f"Expenses: ${normalized_slots['monthly_expense']:,.2f}")

    if profile_summary:
        resp_text = (
            f"ខ្ញុំបានកត់ត្រាព័ត៌មានហិរញ្ញវត្ថុរបស់អ្នក៖ {', '.join(profile_summary)}។"
            if lang == "km"
            else f"I have noted your financial details: {', '.join(profile_summary)}."
        )
    else:
        resp_text = (
            "សូមប្រាប់ខ្ញុំអំពីប្រាក់ចំណូល និងការចំណាយប្រចាំខែរបស់អ្នក ដើម្បីឱ្យខ្ញុំអាចជួយរៀបចំផែនការហិរញ្ញវត្ថុបានល្អបំផុត។"
            if lang == "km"
            else "Please share your monthly income and expenses so I can help analyze your financial health."
        )

    return {
        "success": True,
        "type": "financial_profile_extracted",
        "language": lang,
        "slots": normalized_slots,
        "response": resp_text,
    }


# 3. Gradio Web Interface
@spaces.GPU
def gradio_chat(user_msg, history):
    if not user_msg:
        return ""
    lang = detect_language(user_msg)
    if is_safety_violation(user_msg):
        instr = SAFETY_INSTRUCTION_KM if lang == "km" else SAFETY_INSTRUCTION
        return generate_response(instr, user_msg, max_new_tokens=120)
    elif is_educational_query(user_msg):
        instr = EDUCATION_INSTRUCTION_KM if lang == "km" else EDUCATION_INSTRUCTION
        return generate_response(instr, user_msg, max_new_tokens=140)
    else:
        raw = generate_response(EXTRACTION_INSTRUCTION, user_msg, max_new_tokens=75)
        slots = normalize_llm_output(raw, user_msg)
        inc = slots.get("monthly_income")
        exp = slots.get("monthly_expense")
        if inc or exp:
            items = []
            if inc: items.append(f"Income: ${inc:,.2f}")
            if exp: items.append(f"Expense: ${exp:,.2f}")
            return f"Recorded: {', '.join(items)}. Verified by Financial Advisor AI."
        return "I am your Financial Advisor AI. How can I assist with your budgeting and financial planning?"


demo = gr.ChatInterface(
    fn=gradio_chat,
    title="💰 Financial Advisor AI (24/7 Cloud)",
    description="Fine-tuned Qwen2.5-1.5B model serving bilingual personal finance guidance (English & Khmer).",
    examples=[
        "My monthly income is $2500 and expense is $1800",
        "Explain the 50/30/20 budget rule",
        "តើក្បួន 50/30/20 ជាអ្វី?",
        "Should I buy Bitcoin?",
    ],
    cache_examples=False,
)

# Mount Gradio onto FastAPI
app = gr.mount_gradio_app(api_app, demo, path="/")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    # Give any previous container process a moment to release the port
    time.sleep(1)
    uvicorn.run(app, host="0.0.0.0", port=port)
