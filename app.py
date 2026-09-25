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
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import gradio as gr

# Import model inference and normalizer functions
from training.serve_llm import (
    load_model, generate_response, is_safety_violation, is_educational_query,
    EXTRACTION_INSTRUCTION, EXPLANATION_INSTRUCTION, EXPLANATION_INSTRUCTION_KM,
    SAFETY_INSTRUCTION, SAFETY_INSTRUCTION_KM, EDUCATION_INSTRUCTION, EDUCATION_INSTRUCTION_KM,
    DATA_BOUNDARY_INSTRUCTION, DATA_BOUNDARY_INSTRUCTION_KM,
    EXPERT_SYSTEM_AUTHORITY_INSTRUCTION, EXPERT_SYSTEM_AUTHORITY_INSTRUCTION_KM,
    GENERAL_GUIDANCE_INSTRUCTION, GENERAL_GUIDANCE_INSTRUCTION_KM,
    BASE_MODEL_ID
)
from training.llm_output_normalizer import (
    normalize_llm_output, normalize_and_verify_response,
    detect_language, CANONICAL_FIELDS, detect_debt_status, detect_employment_status
)

# 1. Initialize Model
print("Initializing Financial Consultant AI model for Hugging Face Space...")
load_model()


# ZeroGPU decorated synchronous generation entrypoint for REST API
@spaces.GPU
def run_generation(instruction: str, user_input: str, max_new_tokens: int = 256) -> str:
    return generate_response(instruction, user_input, max_new_tokens=max_new_tokens)


def _process_chat_logic(message: str, existing_profile: dict = None, lang: str = None) -> dict:
    if not message or not message.strip():
        return {"response": "", "type": "empty", "slots": {}}

    clean_msg = message.strip()
    active_lang = lang or detect_language(clean_msg)
    profile = existing_profile or {}

    # 1. Greeting Check (Dynamic generation with sampling for natural variety)
    is_greeting = bool(re.search(
        r"^(hello|hi|hey|greetings|good\s+(morning|afternoon|evening)|howdy|សួស្តី|ជំរាបសួរ|ជម្រាបសួរ)[.!?\s]*$",
        clean_msg,
        re.IGNORECASE
    ))
    if is_greeting:
        if active_lang == "km":
            instr = (
                "អ្នកគឺជា Financial Consultant AI (ជំនួយការ AI ប្រឹក្សាហិរញ្ញវត្ថុ) សម្រាប់ពន្យល់លទ្ធផលនៃប្រព័ន្ធអ្នកជំនាញប្រឹក្សាហិរញ្ញវត្ថុ។ "
                "សូមឆ្លើយតបការសួស្តីដោយរួសរាយ និងខ្លី (១-២ ល្បះ)។ សួរថាអាចជួយអ្វីខ្លះទាក់ទងនឹងការរៀបចំថវិកា ការសន្សំ ឬសំណួរហិរញ្ញវត្ថុ។ "
                "មិនត្រូវលើកឡើងពីតួលេខហិរញ្ញវត្ថុណាមួយឡើយ។"
            )
        else:
            instr = (
                "You are the explanation assistant for a rule-based Financial Consulting Expert System. "
                "Your identity is Financial Consultant AI. "
                "Respond warmly and concisely: greet the user as Financial Consultant AI, "
                "and ask how you can help with budgeting, savings, or financial planning today. "
                "Do not claim to be human. Do not mention financial figures or external sources."
            )
        resp = generate_response(instr, clean_msg, max_new_tokens=60, do_sample=True, temperature=0.7)
        resp = normalize_and_verify_response(resp, user_input=clean_msg, lang=active_lang)
        return {"response": resp, "type": "greeting", "slots": {}}

    # 2. Safety Boundary Check
    if is_safety_violation(clean_msg):
        instr = f"{SAFETY_INSTRUCTION_KM if active_lang == 'km' else SAFETY_INSTRUCTION}\n{DATA_BOUNDARY_INSTRUCTION_KM if active_lang == 'km' else DATA_BOUNDARY_INSTRUCTION}"
        resp = generate_response(instr, clean_msg, max_new_tokens=120)
        resp = normalize_and_verify_response(resp, user_input=clean_msg, lang=active_lang)
        return {"response": resp, "type": "safety_refusal", "slots": {}}

    # 3. Data Source / Provenance Check
    is_data_source_q = bool(re.search(
        r"(where\s+(does|do|did)\s+(the\s+chatbot|you)\s+get\s+(my|the\s+user['’]?s?)\s+(financial\s+)?(information|data|income|profile)"
        r"|where\s+did\s+you\s+get\s+my\s+income|how\s+do\s+you\s+know\s+my\s+income|what\s+data\s+do\s+you\s+use"
        r"|do\s+you\s+access\s+my\s+(social\s+media|facebook|instagram|bank\s+account|browsing|external\s+transaction)"
        r"|access\s+(my\s+)?(social\s+media|bank\s+account))",
        clean_msg,
        re.IGNORECASE
    ))
    if is_data_source_q:
        instr = (
            f"You are the explanation assistant for a rule-based Financial Consulting Expert System.\n"
            f"{DATA_BOUNDARY_INSTRUCTION_KM if active_lang == 'km' else DATA_BOUNDARY_INSTRUCTION}\n"
            f"Explain clearly that you only use financial information provided by the user through this application, "
            f"and never access social media, bank accounts, or external transaction systems."
            if active_lang != "km" else
            f"អ្នកគឺជា Financial Consultant AI។\n{DATA_BOUNDARY_INSTRUCTION_KM}\n"
            f"សូមពន្យល់ថា អ្នកប្រើតែព័ត៌មានដែលអ្នកប្រើប្រាស់បានផ្តល់តាមរយៈកម្មវិធីនេះប៉ុណ្ណោះ និងមិនចូលប្រើបណ្តាញសង្គម ឬគណនីធនាគារឡើយ។"
        )
        resp = generate_response(instr, clean_msg, max_new_tokens=100)
        resp = normalize_and_verify_response(resp, user_input=clean_msg, lang=active_lang)
        return {"response": resp, "type": "data_provenance", "slots": {}}

    # 4. Expert System Override Refusal
    is_override_q = bool(re.search(
        r"ignore\s+(the\s+)?(expert\s+system|rules|deterministic)|tell\s+me\s+your\s+own\s+(financial\s+)?(assessment|advice|opinion|recommendation)"
        r"|មិនបាច់ខ្វល់ពីប្រព័ន្ធអ្នកជំនាញ|ផ្តល់ការវាយតម្លៃផ្ទាល់ខ្លួន",
        clean_msg,
        re.IGNORECASE
    ))
    if is_override_q:
        instr = (
            "You are Financial Consultant AI for the Financial Consulting Expert System. "
            "Decline politely: explain that the deterministic Financial Consulting Expert System is the authoritative source "
            "for calculations and verified recommendations. Your role is strictly to explain those results."
            if active_lang != "km" else
            "អ្នកគឺជា Financial Consultant AI សម្រាប់ពន្យល់លទ្ធផលរបស់ប្រព័ន្ធអ្នកជំនាញប្រឹក្សាហិរញ្ញវត្ថុ។ "
            "សូមបដិសេធដោយសុភាព និងពន្យល់ថា ប្រព័ន្ធអ្នកជំនាញគឺជាប្រភពផ្លូវការសម្រាប់ការគណនា និងអនុសាសន៍។"
        )
        resp = generate_response(instr, clean_msg, max_new_tokens=90)
        resp = normalize_and_verify_response(resp, user_input=clean_msg, lang=active_lang)
        return {"response": resp, "type": "expert_system_override_refusal", "slots": {}}

    # 5. Concept / Educational Check
    if is_educational_query(clean_msg):
        instr = f"{EDUCATION_INSTRUCTION_KM if active_lang == 'km' else EDUCATION_INSTRUCTION}\n{DATA_BOUNDARY_INSTRUCTION_KM if active_lang == 'km' else DATA_BOUNDARY_INSTRUCTION}"
        resp = generate_response(instr, clean_msg, max_new_tokens=140)
        resp = normalize_and_verify_response(resp, user_input=clean_msg, lang=active_lang)
        return {"response": resp, "type": "financial_education", "slots": {}}

    # 6. Extraction & Numbers
    has_numbers = bool(re.search(r"\d", clean_msg))
    debt_mentioned = detect_debt_status(clean_msg) is not None
    emp_mentioned = detect_employment_status(clean_msg) is not None

    if not has_numbers and not debt_mentioned and not emp_mentioned:
        normalized_slots = {k: None for k in CANONICAL_FIELDS}
    else:
        raw_out = generate_response(EXTRACTION_INSTRUCTION, clean_msg, max_new_tokens=75)
        normalized_slots = normalize_llm_output(raw_out, clean_msg)

    inc = normalized_slots.get("monthly_income")
    exp = normalized_slots.get("monthly_expense")
    goal = normalized_slots.get("goal_cost")

    if inc is not None or exp is not None or goal is not None:
        items = []
        if inc is not None: items.append(f"Income: ${inc:,.2f}/mo")
        if exp is not None: items.append(f"Expenses: ${exp:,.2f}/mo")
        if goal is not None: items.append(f"Goal: ${goal:,.2f}")
        summary_str = ", ".join(items)

        if inc is not None and exp is not None:
            cf = inc - exp
            sign = "+" if cf >= 0 else "-"
            resp = (
                f"Recorded verified profile: {summary_str}. Net Cash Flow: {sign}${abs(cf):,.2f}/month. "
                f"How would you like to plan or allocate your savings?"
                if active_lang != "km" else
                f"បានកត់ត្រាទិន្នន័យហិរញ្ញវត្ថុ៖ {summary_str}។ លំហូរសាច់ប្រាក់សុទ្ធ៖ {sign}${abs(cf):,.2f}/ខែ។ "
                f"តើអ្នកចង់ឱ្យខ្ញុំជួយរៀបចំផែនការ ឬបែងចែកការសន្សំយ៉ាងដូចម្តេចដែរ?"
            )
        else:
            resp = (
                f"Recorded: {summary_str}. "
                f"{'Please provide your monthly expenses to evaluate your cash flow.' if exp is None else 'Please provide your monthly income.'}"
                if active_lang != "km" else
                f"បានកត់ត្រា៖ {summary_str}។ "
                f"{'សូមផ្តល់ព័ត៌មានអំពីការចំណាយប្រចាំខែ ដើម្បីគណនាលំហូរសាច់ប្រាក់។' if exp is None else 'សូមផ្តល់ព័ត៌មានអំពីប្រាក់ចំណូលប្រចាំខែ។'}"
            )
        resp = normalize_and_verify_response(resp, user_input=clean_msg, context_profile=normalized_slots, lang=active_lang)
        return {"response": resp, "type": "financial_profile_extracted", "slots": normalized_slots}

    # 7. General Conversational Guidance (dynamic sampling)
    instr = (
        f"{GENERAL_GUIDANCE_INSTRUCTION_KM}\n{DATA_BOUNDARY_INSTRUCTION_KM}\n{EXPERT_SYSTEM_AUTHORITY_INSTRUCTION_KM}"
        if active_lang == "km" else
        f"{GENERAL_GUIDANCE_INSTRUCTION}\n{DATA_BOUNDARY_INSTRUCTION}\n{EXPERT_SYSTEM_AUTHORITY_INSTRUCTION}"
    )
    resp = generate_response(instr, clean_msg, max_new_tokens=100, do_sample=True, temperature=0.7)
    resp = normalize_and_verify_response(resp, user_input=clean_msg, context_profile=profile, lang=active_lang)
    return {"response": resp, "type": "general_guidance", "slots": normalized_slots}


# 2. Gradio Web Interface (ZeroGPU Decorated)
@spaces.GPU
def gradio_chat(user_msg, history):
    if not user_msg or not user_msg.strip():
        return ""
    result = _process_chat_logic(user_msg)
    return result.get("response", "")


# Synchronous ZeroGPU entrypoint for REST API /chat
@spaces.GPU
def run_chat_service(message: str, existing_profile: dict = None, lang: str = None) -> dict:
    return _process_chat_logic(message, existing_profile=existing_profile, lang=lang)


demo = gr.ChatInterface(
    fn=gradio_chat,
    title="💰 Financial Consulting Expert System (24/7 Cloud)",
    description="Fine-tuned Qwen2.5-1.5B model serving bilingual personal finance guidance (English & Khmer).",
    examples=[
        "My monthly income is $2500 and expense is $1800",
        "Explain the 50/30/20 budget rule",
        "តើក្បួន 50/30/20 ជាអ្វី?",
        "Should I buy Bitcoin?",
    ],
    cache_examples=False,
)

# 3. Mount Custom REST API Endpoints directly onto Gradio's internal FastAPI app
# NOTE: Routes are defined as synchronous `def` (NOT `async def`) because ZeroGPU's
# @spaces.GPU decorator does not support coroutines and raises NotImplementedError.
api_app = demo.app

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
        "service": "Financial Consulting Expert System",
        "system_identity": "Financial Consultant AI",
        "base_model": BASE_MODEL_ID,
        "adapter": "financial_advisor_ai_v4",
        "device": "cuda" if has_cuda else "cpu",
        "vram_allocated_gb": vram,
    }


@api_app.post("/extract")
def extract_endpoint(payload: dict):
    text = (payload.get("text") or "").strip()
    if not text:
        return JSONResponse(status_code=400, content={"error": "Missing 'text' field"})

    raw_out = run_generation(EXTRACTION_INSTRUCTION, text, max_new_tokens=150)
    normalized_slots = normalize_llm_output(raw_out, text)
    return {
        "success": True,
        "raw_output": raw_out,
        "slots": normalized_slots,
    }


@api_app.post("/explain")
def explain_endpoint(data: dict):
    lang = data.get("language") or "en"
    income = data.get("monthly_income")
    expense = data.get("monthly_expense")
    net_cf = data.get("net_cashflow")
    if net_cf is None and income is not None and expense is not None:
        net_cf = income - expense

    debt_desc = data.get("debt_status")
    if not debt_desc:
        if data.get("debt_present") is True:
            debt_desc = "debt"
        elif data.get("debt_present") is False:
            debt_desc = "no debt"
        else:
            debt_desc = "unknown"

    advice_str = data.get("advice") or data.get("conclusion") or "Maintain balanced finances."

    inc_str = f"${income:,.2f}" if income is not None else "unknown"
    exp_str = f"${expense:,.2f}" if expense is not None else "unknown"
    if net_cf is not None:
        sign = "+" if net_cf >= 0 else "-"
        net_cf_str = f"{sign}${abs(net_cf):,.2f}"
    else:
        net_cf_str = "unknown"

    if lang == "km":
        debt_km = "មានបំណុល" if debt_desc == "debt" else ("គ្មានបំណុល" if debt_desc == "no debt" else "មិនទាន់ដឹង (unknown)")
        profile_str = (
            f"ទិន្នន័យហិរញ្ញវត្ថុដែលបានផ្ទៀងផ្ទាត់: ចំណូលប្រចាំខែ: {inc_str}, "
            f"ចំណាយប្រចាំខែ: {exp_str}, "
            f"លំហូរសាច់ប្រាក់សុទ្ធ: {net_cf_str}, "
            f"ស្ថានភាពបំណុល: {debt_km}។ "
            f"អនុសាសន៍ដែលបានផ្ទៀងផ្ទាត់: {advice_str}"
        )
    else:
        profile_str = (
            f"Verified application financial context: Monthly Income: {inc_str}, "
            f"Monthly Expense: {exp_str}, "
            f"Net Cash Flow: {net_cf_str}, "
            f"Debt Status: {debt_desc}. "
            f"Verified Advice: {advice_str}"
        )

    base_instr = EXPLANATION_INSTRUCTION_KM if lang == "km" else EXPLANATION_INSTRUCTION
    boundary = DATA_BOUNDARY_INSTRUCTION_KM if lang == "km" else DATA_BOUNDARY_INSTRUCTION
    authority = EXPERT_SYSTEM_AUTHORITY_INSTRUCTION_KM if lang == "km" else EXPERT_SYSTEM_AUTHORITY_INSTRUCTION
    instr = f"{base_instr}\n{boundary}\n{authority}"

    explanation = run_generation(instr, profile_str, max_new_tokens=85)
    context_prof = {
        "monthly_income": income,
        "monthly_expense": expense,
        "net_cashflow": net_cf,
        "debt_status": debt_desc if debt_desc != "unknown" else None,
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
def chat_endpoint(data: dict):
    message = (data.get("message") or "").strip()
    if not message:
        return JSONResponse(status_code=400, content={"error": "Message cannot be empty"})

    lang = data.get("language")
    existing_profile = data.get("existing_profile") or {}

    result = run_chat_service(message, existing_profile=existing_profile, lang=lang)
    return {
        "success": True,
        "type": result.get("type", "chat_response"),
        "language": lang or detect_language(message),
        "slots": result.get("slots", {}),
        "response": result.get("response", ""),
    }


# Native Gradio Launch (Official Hugging Face ZeroGPU entrypoint)
if __name__ == "__main__":
    demo.launch()
