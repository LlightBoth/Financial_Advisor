"""
Financial Advisor - Local Trained Financial Advisor AI Inference Server
Running in .venv_train environment on NVIDIA RTX 4060 GPU.
"""

import os
import sys
import json
import re
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler, ThreadingHTTPServer
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
    from peft import PeftModel
except ImportError as e:
    print("=" * 65)
    print(" [ERROR] Missing required AI libraries to run the local LLM server.")
    print(f" Details: {e}")
    print("\n Please install the required AI dependencies by running:")
    print("     pip install -r requirements-llm.txt")
    print("=" * 65)
    sys.exit(1)

# Add project root to sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from training.llm_output_normalizer import normalize_llm_output, normalize_and_verify_response

HOST = "127.0.0.1"
PORT = 5006

BASE_MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"
# Active Adapter: V4 (Trained Financial Advisor AI v4)
ADAPTER_DIR = os.path.join(BASE_DIR, "training", "output", "financial_advisor_ai_v4")
# Rollback Option: V2 (financial_advisor_ai_v1)
V2_ROLLBACK_ADAPTER_DIR = os.path.join(BASE_DIR, "training", "output", "financial_advisor_ai_v1")

EXTRACTION_INSTRUCTION = (
    "Extract the user's financial profile from the provided text into a JSON object with keys: "
    "monthly_income, monthly_expense, goal_cost, employment_status, debt_status, spending_habit, "
    "marital_status. Set unmentioned fields to null. Do not invent values."
)

EXPLANATION_INSTRUCTION = (
    "Based on the verified financial consultant evaluation, provide a clear 2 to 4 sentence explanation "
    "titled 'Understanding Your Recommendation'. Explain the user's financial situation and why the advice "
    "is relevant. If information was missing, note that an assumption was used. Do not include technical rule "
    "names, scores, or internal system details."
)

EXPLANATION_INSTRUCTION_KM = (
    "ដោយផ្អែកលើការវាយតម្លៃរបស់អ្នកប្រឹក្សាហិរញ្ញវត្ថុដែលមានសុពលភាព សូមពន្យល់ដោយសង្ខេបពី ២ ទៅ ៤ ប្រយោគអំពីស្ថានភាពហិរញ្ញវត្ថុរបស់អ្នកប្រើប្រាស់ "
    "និងមូលហេតុដែលអនុសាសន៍នេះមានប្រយោជន៍ ដោយប្រើភាសាខ្មែរសាមញ្ញ ធម្មជាតិ និងងាយយល់។ មិនត្រូវបង្ហាញឈ្មោះកូដបច្ចេកទេស ឬពិន្ទុប្រព័ន្ធឡើយ។"
)

MISSING_INFO_INSTRUCTION = (
    "Analyze the user's financial statement. Identify known parameters, specify what critical information "
    "is missing or ambiguous, and explain what additional details are required for a complete financial "
    "assessment without guessing values."
)

MISSING_INFO_INSTRUCTION_KM = (
    "វិភាគទិន្នន័យហិរញ្ញវត្ថុរបស់អ្នកប្រើប្រាស់។ បញ្ជាក់ព័ត៌មានដែលបានដឹង និងចង្អុលបង្ហាញព័ត៌មានសំខាន់ៗដែលនៅខ្វះ (ដូចជា ចំណូល ឬចំណាយ) "
    "ដោយប្រើភាសាខ្មែរសាមញ្ញ ងាយយល់ និងមិនត្រូវស្មានតម្លៃដែលគ្មាននោះឡើយ។"
)

EDUCATION_INSTRUCTION = (
    "Explain the personal finance concept in simple, accessible language. Do not calculate personal metrics "
    "or give specific investment advice."
)

EDUCATION_INSTRUCTION_KM = (
    "ពន្យល់អំពីគោលគំនិតហិរញ្ញវត្ថុផ្ទាល់ខ្លួន (ការរៀបចំថវិកា ចំណូល-ចំណាយ ការសន្សំ គោលដៅហិរញ្ញវត្ថុ ការគ្រប់គ្រងបំណុល ឬមូលនិធិសង្គ្រោះបន្ទាន់) "
    "ជាភាសាខ្មែរធម្មជាតិ សាមញ្ញ ងាយយល់ និងមានប្រយោជន៍។ មិនត្រូវផ្តល់អនុសាសន៍វិនិយោគជាក់លាក់ឡើយ។"
)

SAFETY_INSTRUCTION = (
    "Respond to the user inquiry while maintaining strict professional boundaries. Refuse to provide specific "
    "stock picks, loan approvals, credit underwriting, tax evasion schemes, or unverified financial guarantees. "
    "Explain what you can help with."
)

SAFETY_INSTRUCTION_KM = (
    "ឆ្លើយតបទៅកាន់សំណួររបស់អ្នកប្រើប្រាស់ដោយប្រកាន់ខ្ជាប់នូវក្រមសីលធម៌វិជ្ជាជីវៈ។ បដិសេធយ៉ាងម៉ឺងម៉ាត់ចំពោះការផ្តល់អនុសាសន៍ទិញភាគហ៊ុន ឬគ្រីបតូជាក់លាក់ "
    "ការអនុម័តប្រាក់កម្ចី ការដាក់ពិន្ទុឥណទាន ឬការធានាហិរញ្ញវត្ថុ។ ពន្យល់ពីអ្វីដែលអ្នកអាចជួយបាន ដូចជាការរៀបចំថវិកា និងការសន្សំ។"
)

GENERAL_GUIDANCE_INSTRUCTION_KM = (
    "អ្នកគឺជាជំនួយការ AI ប្រឹក្សាហិរញ្ញវត្ថុដ៏មានប្រយោជន៍។ សូមផ្តល់ការណែនាំអំពីហិរញ្ញវត្ថុផ្ទាល់ខ្លួនជាភាសាខ្មែរធម្មជាតិ សាមញ្ញ ខ្លី និងមានប្រយោជន៍ខ្ពស់។ ចៀសវាងពាក្យពេចន៍ដែលមិនចាំបាច់។"
)

# Global model state
tokenizer = None
model = None
model_lock = threading.Lock()


def load_model():
    global tokenizer, model
    print("=" * 60)
    print("Loading Trained Financial Advisor AI model...")
    print(f"Base: {BASE_MODEL_ID}")
    print(f"Adapter: {ADAPTER_DIR}")

    try:
        tokenizer = AutoTokenizer.from_pretrained(ADAPTER_DIR, local_files_only=True, trust_remote_code=True)
    except Exception:
        tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID, trust_remote_code=True)

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    has_cuda = torch.cuda.is_available()
    base_model = None
    if has_cuda:
        try:
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_use_double_quant=True,
            )
            base_model = AutoModelForCausalLM.from_pretrained(
                BASE_MODEL_ID,
                quantization_config=bnb_config,
                device_map="auto",
                dtype=torch.bfloat16,
                trust_remote_code=True,
            )
        except Exception as e:
            print(f"[WARN] 4-bit CUDA quantization failed ({e}). Loading in float16 on GPU...")
            try:
                base_model = AutoModelForCausalLM.from_pretrained(
                    BASE_MODEL_ID,
                    device_map="auto",
                    torch_dtype=torch.float16,
                    trust_remote_code=True,
                )
            except Exception as e2:
                print(f"[WARN] CUDA load failed ({e2}). Falling back to CPU...")
                base_model = None

    if base_model is None:
        print("[INFO] CUDA GPU not detected or unavailable. Loading base model on CPU (float32)...")
        base_model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL_ID,
            device_map="cpu",
            dtype=torch.float32,
            trust_remote_code=True,
        )

    model = PeftModel.from_pretrained(base_model, ADAPTER_DIR)
    model.eval()

    device = next(model.parameters()).device
    vram_str = f" VRAM allocated: {torch.cuda.memory_allocated(0) / (1024**3):.2f} GB" if has_cuda else ""
    print(f"[READY] Model loaded on {device}.{vram_str}")
    print(f"Server starting on http://{HOST}:{PORT}")
    print("=" * 60)


last_generation_metrics = {}


def generate_response(instruction: str, user_input: str, max_new_tokens: int = 256) -> str:
    global last_generation_metrics
    t_tok_start = time.perf_counter()
    messages = [
        {"role": "system", "content": instruction},
        {"role": "user", "content": user_input},
    ]
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    device = next(model.parameters()).device
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    input_tokens = int(inputs.input_ids.shape[1])
    t_tok_end = time.perf_counter()

    with model_lock:
        with torch.no_grad():
            t_gen_start = time.perf_counter()
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=[tokenizer.eos_token_id, 151645, 151643],
            )
            if torch.cuda.is_available():
                torch.cuda.synchronize()
            t_gen_end = time.perf_counter()

    total_tokens = int(outputs[0].shape[0])
    output_tokens = total_tokens - input_tokens

    t_dec_start = time.perf_counter()
    gen_text = tokenizer.decode(outputs[0][input_tokens:], skip_special_tokens=True).strip()
    t_dec_end = time.perf_counter()

    tokenization_ms = (t_tok_end - t_tok_start) * 1000.0
    generation_ms = (t_gen_end - t_gen_start) * 1000.0
    decoding_ms = (t_dec_end - t_dec_start) * 1000.0
    tokens_per_sec = output_tokens / (generation_ms / 1000.0) if generation_ms > 0 else 0.0

    last_generation_metrics = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "tokenization_ms": round(tokenization_ms, 2),
        "generation_ms": round(generation_ms, 2),
        "decoding_ms": round(decoding_ms, 2),
        "tokens_per_second": round(tokens_per_sec, 2),
        "total_model_ms": round(tokenization_ms + generation_ms + decoding_ms, 2),
    }
    return gen_text


def is_safety_violation(text: str) -> bool:
    """Checks for speculative trading, crypto picks, stock tips, loan underwriting, or guaranteed returns."""
    patterns = [
        r"\b(cryptocurrency|crypto|bitcoin|btc|ethereum|eth|doge|altcoin|memecoin)\b",
        r"\b(double\s+(my\s+)?(money|\$\d+|investment))\b",
        r"\b(stock\s+(pick|picks|tip|tips|recommendation|buy))\b",
        r"\bwhich\s+(stock|coin|crypto)\s+should\s+i\s+buy\b",
        r"\bguarantee(d)?\s+(return|profit|gain)\b",
        r"\b(get\s+rich\s+quick|100x|10x)\b",
        r"\b(evade\s+tax|tax\s+evasion|hide\s+money)\b",
        r"\b(credit\s+score|approve\s+(my\s+)?loan|underwriting|loan\s+approval)\b",
        # Khmer patterns:
        r"គ្រីបតូ|ប៊ីតខញ|bitcoin|btc|ភាគហ៊ុន|ទិញភាគហ៊ុន|ទិញកាក់|ក្លាយជាអ្នកមាន|គេចពន្ធ|ធានាផលចំណេញ",
        r"អនុម័តប្រាក់កម្ចី|បដិសេធប្រាក់កម្ចី|ពិន្ទុឥណទាន|ឱ្យខ្ចីប្រាក់",
    ]
    for p in patterns:
        if re.search(p, text, re.IGNORECASE):
            return True
    return False


def is_educational_query(text: str) -> bool:
    """Detects general conceptual questions about personal finance."""
    patterns = [
        r"\bwhat\s+is\s+(the\s+)?(difference|meaning|concept|definition)\b",
        r"\bhow\s+does\s+(compound\s+interest|cash\s+flow|inflation|budgeting)\b",
        r"\bexplain\s+(the\s+)?(50/30/20|difference|cash\s+flow|emergency\s+fund)\b",
        r"\bwhat\s+is\s+(cash\s+flow|savings\s+capacity|debt[- ]to[- ]income|liquidity)\b",
        # Khmer patterns:
        r"អ្វីទៅជា|តើអ្វីជា|ពន្យល់|របៀប|ក្បួន\s*50/30/20|50/30/20",
        r"មូលនិធិបន្ទាន់|មូលនិធិសង្គ្រោះបន្ទាន់|ប្រាក់បម្រុង",
        r"ការរៀបចំថវិកា|ការគ្រប់គ្រងបំណុល|វិធីសងបំណុល|ដោះបំណុល",
        r"លំហូរសាច់ប្រាក់|សមត្ថភាពសន្សំ",
    ]
    for p in patterns:
        if re.search(p, text, re.IGNORECASE):
            return True
    return False


class FinancialAdvisorAIRequestHandler(BaseHTTPRequestHandler):

    def _set_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def do_GET(self):
        if self.path == "/health":
            resp = {
                "status": "ok",
                "service": "Trained Financial Advisor AI",
                "base_model": BASE_MODEL_ID,
                "adapter": "financial_advisor_ai_v4",
                "device": "cuda",
                "vram_allocated_gb": round(torch.cuda.memory_allocated(0) / (1024**3), 2),
            }
            self._set_headers(200)
            self.wfile.write(json.dumps(resp).encode("utf-8"))
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not found"}).encode("utf-8"))

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        try:
            data = json.loads(body) if body else {}
        except Exception:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "Malformed JSON payload"}).encode("utf-8"))
            return

        # -------------------------------------------------------------
        # Endpoint: /extract
        # Extracts financial facts from natural language text and normalizes
        # -------------------------------------------------------------
        if self.path == "/extract":
            text = data.get("text", "").strip()
            if not text:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "Missing 'text' field"}).encode("utf-8"))
                return

            raw_out = generate_response(EXTRACTION_INSTRUCTION, text, max_new_tokens=150)
            normalized_slots = normalize_llm_output(raw_out, text)

            resp = {
                "success": True,
                "raw_output": raw_out,
                "slots": normalized_slots,
            }
            self._set_headers(200)
            self.wfile.write(json.dumps(resp).encode("utf-8"))

        # -------------------------------------------------------------
        # Endpoint: /explain
        # Generates plain-language "Understanding Your Recommendation"
        # -------------------------------------------------------------
        elif self.path == "/explain":
            lang = data.get("language") or "en"
            profile_str = data.get("profile_str")
            if not profile_str:
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
                "monthly_income": data.get("monthly_income"),
                "monthly_expense": data.get("monthly_expense"),
                "net_cashflow": data.get("net_cashflow"),
                "debt_status": data.get("debt_status") or ("debt" if data.get("debt_present") else "no debt"),
            }
            explanation = normalize_and_verify_response(
                explanation,
                user_input=profile_str,
                context_profile=context_prof,
                lang=lang
            )
            resp = {
                "success": True,
                "profile_str": profile_str,
                "language": lang,
                "explanation": explanation,
                "timing": last_generation_metrics,
            }
            self._set_headers(200)
            self.wfile.write(json.dumps(resp).encode("utf-8"))

        # -------------------------------------------------------------
        # Endpoint: /chat
        # Full conversational routing: safety -> education -> extraction
        # -------------------------------------------------------------
        elif self.path == "/chat":
            message = data.get("message", "").strip()
            if not message:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "Message cannot be empty"}).encode("utf-8"))
                return

            from training.llm_output_normalizer import (
                detect_language, CANONICAL_FIELDS,
                detect_debt_status, detect_employment_status
            )
            lang = data.get("language") or detect_language(message)
            existing_profile = data.get("existing_profile") or {}

            # 1. Safety Boundary Check
            if is_safety_violation(message):
                instr = SAFETY_INSTRUCTION_KM if lang == "km" else SAFETY_INSTRUCTION
                safety_resp = generate_response(instr, message, max_new_tokens=120)
                safety_resp = normalize_and_verify_response(safety_resp, user_input=message, lang=lang)
                self._set_headers(200)
                self.wfile.write(json.dumps({
                    "success": True,
                    "type": "safety_refusal",
                    "language": lang,
                    "response": safety_resp,
                    "timing": last_generation_metrics,
                }).encode("utf-8"))
                return

            # 2. Concept / Educational Check
            if is_educational_query(message):
                instr = EDUCATION_INSTRUCTION_KM if lang == "km" else EDUCATION_INSTRUCTION
                edu_resp = generate_response(instr, message, max_new_tokens=140)
                edu_resp = normalize_and_verify_response(edu_resp, user_input=message, lang=lang)
                self._set_headers(200)
                self.wfile.write(json.dumps({
                    "success": True,
                    "type": "financial_education",
                    "language": lang,
                    "response": edu_resp,
                    "timing": last_generation_metrics,
                }).encode("utf-8"))
                return

            # 3. Fast-path check: If message contains no numbers and no status keywords, skip slow LLM extraction
            has_numbers = bool(re.search(r"\d", message))
            debt_mentioned = detect_debt_status(message) is not None
            emp_mentioned = detect_employment_status(message) is not None

            if not has_numbers and not debt_mentioned and not emp_mentioned:
                normalized_slots = {k: None for k in CANONICAL_FIELDS}
            else:
                raw_out = generate_response(EXTRACTION_INSTRUCTION, message, max_new_tokens=75)
                normalized_slots = normalize_llm_output(raw_out, message)

            has_new_income = normalized_slots.get("monthly_income") is not None
            has_new_expense = normalized_slots.get("monthly_expense") is not None
            has_new_goal = normalized_slots.get("goal_cost") is not None
            has_new_debt = normalized_slots.get("debt_status") is not None
            has_new_emp = normalized_slots.get("employment_status") is not None

            any_new_facts = has_new_income or has_new_expense or has_new_goal or has_new_debt or has_new_emp

            has_existing_profile = (
                bool(existing_profile)
                and existing_profile.get("monthly_income") is not None
                and existing_profile.get("monthly_expense") is not None
            )

            consultant_advice = data.get("consultant_advice") or ""

            # Detect conversational greetings immediately
            is_greeting = bool(re.search(r"^(hello|hi|hey|greetings|good\s+(morning|afternoon|evening)|howdy|សួស្តី|ជំរាបសួរ|ជម្រាបសួរ)[.!?\s]*$", message.strip(), re.IGNORECASE))
            if is_greeting:
                greet_resp = (
                    "សួស្តី! ខ្ញុំជាជំនួយការប្រឹក្សាហិរញ្ញវត្ថុ AI របស់អ្នក។ តើខ្ញុំអាចជួយអ្នកក្នុងការរៀបចំផែនការហិរញ្ញវត្ថុ ថវិកា ឬការសន្សំយ៉ាងដូចម្តេចដែរ?"
                    if lang == "km"
                    else "Hello! I am your Financial Advisor AI. How can I help you with your budgeting, savings, or financial planning today?"
                )
                self._set_headers(200)
                self.wfile.write(json.dumps({
                    "success": True,
                    "type": "greeting",
                    "language": lang,
                    "response": greet_resp,
                    "timing": {"total_model_ms": 0.0},
                }).encode("utf-8"))
                return

            def _build_profile_context(prof, advice=""):
                inc = prof.get("monthly_income")
                exp = prof.get("monthly_expense")
                surplus = (inc - exp) if (inc is not None and exp is not None) else None
                debt_st = prof.get("debt_status") or "no debt"
                emp_st = prof.get("employment_status") or "employed"
                marital_st = prof.get("marital_status") or "Single"
                goal = prof.get("goal_cost")

                facts = []
                if inc is not None:
                    facts.append(f"income=${inc:,.0f}/mo")
                if exp is not None:
                    facts.append(f"expenses=${exp:,.0f}/mo")
                if surplus is not None:
                    if surplus > 0:
                        facts.append(f"surplus=+${surplus:,.0f}/mo (positive cash flow, NO deficit)")
                    elif surplus < 0:
                        facts.append(f"deficit=-${abs(surplus):,.0f}/mo")
                    else:
                        facts.append("net cash flow=$0/mo (break-even)")
                if goal:
                    facts.append(f"savings goal=${goal:,.0f}")
                facts.append(f"debt={debt_st}")
                if debt_st == "no debt":
                    facts.append("(user is completely debt-free; do NOT advise debt payoff)")
                facts.append(f"employment={emp_st}")
                facts.append(f"marital={marital_st}")
                if advice:
                    facts.append(f"authoritative advice={advice}")
                return "Verified user profile: " + ", ".join(facts)

            # If no new facts mentioned in message:
            if not any_new_facts:
                if has_existing_profile:
                    profile_str = _build_profile_context(existing_profile, consultant_advice)
                    enriched_msg = f"{profile_str}. User asks: {message}"
                    instr = GENERAL_GUIDANCE_INSTRUCTION_KM if lang == "km" else (
                        "You are a helpful Financial AI Assistant. The user already has a financial profile. "
                        "Provide helpful, short, high-value personal finance guidance strictly matching their verified profile facts. "
                        "Do not contradict the profile facts or invent debt or deficits. Omit fluff."
                    )
                    gen_resp = generate_response(instr, enriched_msg, max_new_tokens=180)
                    gen_resp = normalize_and_verify_response(gen_resp, user_input=message, context_profile=existing_profile, lang=lang)
                    self._set_headers(200)
                    self.wfile.write(json.dumps({
                        "success": True,
                        "type": "general_guidance",
                        "language": lang,
                        "slots": normalized_slots,
                        "response": gen_resp,
                        "timing": last_generation_metrics,
                    }).encode("utf-8"))
                    return

                instr = GENERAL_GUIDANCE_INSTRUCTION_KM if lang == "km" else (
                    "You are a helpful Financial AI Assistant. Provide helpful, short, high-value personal finance guidance. Omit fluff."
                )
                gen_resp = generate_response(instr, message, max_new_tokens=100)
                gen_resp = normalize_and_verify_response(gen_resp, user_input=message, context_profile=existing_profile, lang=lang)
                self._set_headers(200)
                self.wfile.write(json.dumps({
                    "success": True,
                    "type": "general_guidance",
                    "language": lang,
                    "response": gen_resp,
                    "timing": last_generation_metrics,
                }).encode("utf-8"))
                return

            # If user provided partial update but we already have an existing profile:
            if has_existing_profile:
                profile_str = _build_profile_context(existing_profile)
                enriched_msg = f"{profile_str}. User says: {message}"
                instr = GENERAL_GUIDANCE_INSTRUCTION_KM if lang == "km" else (
                    "You are a helpful Financial AI Assistant. The user is updating their financial profile. "
                    "Acknowledge the update and provide brief guidance based on their updated information. Omit fluff."
                )
                gen_resp = generate_response(instr, enriched_msg, max_new_tokens=120)
                gen_resp = normalize_and_verify_response(gen_resp, user_input=message, context_profile=existing_profile, lang=lang)
                self._set_headers(200)
                self.wfile.write(json.dumps({
                    "success": True,
                    "type": "profile_updated",
                    "language": lang,
                    "slots": normalized_slots,
                    "response": gen_resp,
                    "timing": last_generation_metrics,
                }).encode("utf-8"))
                return

            # If user has NO existing profile and only provided partial info:
            if not has_new_income or not has_new_expense:
                instr = MISSING_INFO_INSTRUCTION_KM if lang == "km" else MISSING_INFO_INSTRUCTION
                missing_resp = generate_response(instr, message, max_new_tokens=200)
                missing_resp = normalize_and_verify_response(missing_resp, user_input=message, context_profile=existing_profile, lang=lang)
                self._set_headers(200)
                self.wfile.write(json.dumps({
                    "success": True,
                    "type": "missing_information",
                    "language": lang,
                    "slots": normalized_slots,
                    "response": missing_resp,
                    "timing": last_generation_metrics,
                }).encode("utf-8"))
                return

            # Full financial facts extracted from scratch!
            inc = normalized_slots.get("monthly_income", 0)
            exp = normalized_slots.get("monthly_expense", 0)
            profile_str = f"User profile: income=${inc}/mo, expenses=${exp}/mo"
            goal_cost = normalized_slots.get("goal_cost")
            if goal_cost:
                profile_str += f", savings goal=${goal_cost}"
            enriched_msg = f"{profile_str}. User says: {message}"
            instr = GENERAL_GUIDANCE_INSTRUCTION_KM if lang == "km" else (
                "You are a helpful Financial AI Assistant. The user just provided their financial details. "
                "Acknowledge their income and expenses, and provide initial concise financial guidance. Omit fluff."
            )
            gen_resp = generate_response(instr, enriched_msg, max_new_tokens=150)
            gen_resp = normalize_and_verify_response(gen_resp, user_input=message, context_profile=existing_profile, lang=lang)
            self._set_headers(200)
            self.wfile.write(json.dumps({
                "success": True,
                "type": "financial_profile_extracted",
                "language": lang,
                "slots": normalized_slots,
                "response": gen_resp,
                "timing": last_generation_metrics,
            }).encode("utf-8"))

        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not found"}).encode("utf-8"))

    def log_message(self, format, *args):
        # Concise logging to stdout
        sys.stdout.write(f"[{self.log_date_time_string()}] {format % args}\n")
        sys.stdout.flush()


# Backward compatibility alias
QwenRequestHandler = FinancialAdvisorAIRequestHandler


def run_server():
    load_model()
    server_address = (HOST, PORT)
    httpd = ThreadingHTTPServer(server_address, FinancialAdvisorAIRequestHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.server_close()


if __name__ == "__main__":
    run_server()
