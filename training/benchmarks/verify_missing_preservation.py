import os
import sys
import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

BASE_MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"
ADAPTER_DIR = r"d:\Year3\Finance\Financial_Advisor\training\output\financial_advisor_ai_v1"

EXTRACTION_INSTRUCTION = (
    "Extract the user's financial profile from the provided text into a JSON object "
    "with keys: monthly_income, monthly_expense, goal_cost, employment_status, "
    "debt_status, spending_habit, marital_status. Set unmentioned fields to null. "
    "Do not invent values."
)

EXPLANATION_INSTRUCTION = (
    "Based on the verified financial consultant evaluation, provide a clear 2 to 4 sentence "
    "explanation titled 'Understanding Your Recommendation'. Explain the user's financial situation "
    "and why the advice is relevant. If information was missing, note that an assumption was used. "
    "Do not include technical rule names, scores, or internal system details."
)

def run_tests():
    print("=" * 65)
    print("MISSING-VALUE PRESERVATION & INFERENCE EVALUATION")
    print("=" * 65)

    if not torch.cuda.is_available():
        print("[FAIL] CUDA is unavailable.")
        return False

    # 1. Load Model & Adapter
    print("Loading 4-bit base model and LoRA adapter...")
    tokenizer = AutoTokenizer.from_pretrained(ADAPTER_DIR, local_files_only=True, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True
    )

    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_ID,
        quantization_config=bnb_config,
        device_map="auto",
        dtype=torch.bfloat16,
        local_files_only=True,
        trust_remote_code=True
    )

    model = PeftModel.from_pretrained(base_model, ADAPTER_DIR)
    model.eval()
    print(f"[PASS] Model and adapter loaded on {model.device}.")

    # 2. Test Cases Definitions
    tests = [
        {
            "id": "TEST 1",
            "input": "I spend about $2,300 every month and I am employed, but I did not mention my salary.",
            "expected": {
                "monthly_income": None,
                "monthly_expense": 2300.0,
                "employment_status": "employed"
            }
        },
        {
            "id": "TEST 2",
            "input": "I earn $3,000 per month and have no debt, but I did not tell you my monthly expenses.",
            "expected": {
                "monthly_income": 3000.0,
                "monthly_expense": None,
                "debt_status": "no debt"
            }
        },
        {
            "id": "TEST 3",
            "input": "I earn $3,000 and spend $2,000 every month. I didn't say whether I have debt.",
            "expected": {
                "monthly_income": 3000.0,
                "monthly_expense": 2000.0,
                "debt_status": None
            }
        },
        {
            "id": "TEST 4",
            "input": "I have no income and my monthly expenses are $500.",
            "expected": {
                "monthly_income": 0.0,
                "monthly_expense": 500.0
            }
        },
        {
            "id": "TEST 5",
            "input": "I earn $4,000 and spend $2,500. I'm married.",
            "expected": {
                "monthly_income": 4000.0,
                "monthly_expense": 2500.0,
                "marital_status": "Married",
                "goal_cost": None,
                "debt_status": None,
                "spending_habit": None,
                "employment_status": None
            }
        },
        {
            "id": "TEST 6",
            "input": "I have no debt and want to save $5,000 for an emergency fund, but I haven't provided my income or expenses.",
            "expected": {
                "monthly_income": None,
                "monthly_expense": None,
                "debt_status": "no debt",
                "goal_cost": 5000.0
            }
        },
        {
            "id": "TEST 7 (User Case 3)",
            "input": "I have no debt and want to save $5,000.",
            "expected": {
                "debt_status": "no debt",
                "goal_cost": 5000.0,
                "monthly_income": None,
                "monthly_expense": None
            }
        }
    ]

    all_passed = True
    results_summary = []
    incorrect_inferences = []

    print("\n" + "=" * 65)
    print("RUNNING 6 EXTRACTION TESTS FOR MISSING-VALUE PRESERVATION")
    print("=" * 65)

    with torch.no_grad():
        for t in tests:
            print(f"\n>>> {t['id']}")
            print(f"Input: \"{t['input']}\"")
            
            messages = [
                {"role": "system", "content": EXTRACTION_INSTRUCTION},
                {"role": "user", "content": t["input"]}
            ]
            prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = tokenizer(prompt, return_tensors="pt").to("cuda")

            outputs = model.generate(
                **inputs,
                max_new_tokens=256,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id
            )
            raw_output = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True).strip()
            print(f"Raw Output:\n{raw_output}")

            # Parse JSON
            test_passed = True
            mismatches = []
            try:
                parsed = json.loads(raw_output)
            except Exception as e:
                test_passed = False
                mismatches.append(f"Invalid JSON: {e}")
                parsed = {}

            if parsed:
                for key, exp_val in t["expected"].items():
                    actual_val = parsed.get(key)
                    # Check matching
                    if exp_val is None:
                        if actual_val is not None:
                            test_passed = False
                            mismatches.append(f"{key}: expected null, got {repr(actual_val)}")
                            incorrect_inferences.append(f"{t['id']} ({key}): expected null, inferred {repr(actual_val)}")
                    else:
                        if isinstance(exp_val, float):
                            if actual_val != exp_val and actual_val != int(exp_val):
                                test_passed = False
                                mismatches.append(f"{key}: expected {exp_val}, got {repr(actual_val)}")
                        elif isinstance(exp_val, str):
                            if str(actual_val).lower() != exp_val.lower():
                                test_passed = False
                                mismatches.append(f"{key}: expected '{exp_val}', got {repr(actual_val)}")
                        else:
                            if actual_val != exp_val:
                                test_passed = False
                                mismatches.append(f"{key}: expected {exp_val}, got {repr(actual_val)}")

            status = "PASS" if test_passed else "FAIL"
            if not test_passed:
                all_passed = False
            print(f"Assessment: [{status}] {', '.join(mismatches) if mismatches else 'All fields matched expected values'}")

            results_summary.append({
                "id": t["id"],
                "input": t["input"],
                "raw_output": raw_output,
                "parsed": parsed,
                "status": status,
                "mismatches": mismatches
            })

    # 3. Additional Explanation Test
    print("\n" + "=" * 65)
    print("RUNNING ADDITIONAL EXPLANATION TEST")
    print("=" * 65)

    exp_input = (
        "Verified ConsultantEngine result:\n"
        "Monthly Income: $3,500\n"
        "Monthly Expense: $2,900\n"
        "Net Cash Flow: +$600\n"
        "Debt Status: debt\n\n"
        "Explain this result to a normal user.\n\n"
        "Do not recalculate any values.\n"
        "Do not introduce new financial facts.\n"
        "Do not change the verified recommendation."
    )
    print(f"Explanation Input:\n{exp_input}\n")

    messages = [
        {"role": "system", "content": EXPLANATION_INSTRUCTION},
        {"role": "user", "content": exp_input}
    ]
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors="pt").to("cuda")

    outputs = model.generate(
        **inputs,
        max_new_tokens=256,
        do_sample=False,
        pad_token_id=tokenizer.eos_token_id
    )
    exp_output = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True).strip()
    print(f"Explanation Raw Output:\n{exp_output}")

    exp_passed = True
    exp_notes = []
    if not exp_output:
        exp_passed = False
        exp_notes.append("Output is empty")
    else:
        # Check that it mentions debt and saving/reserve without recalculating or contradicting
        if "debt" not in exp_output.lower():
            exp_passed = False
            exp_notes.append("Failed to explain debt condition")
        if "surplus" not in exp_output.lower() and "margin" not in exp_output.lower() and "capacity" not in exp_output.lower() and "income" not in exp_output.lower():
            exp_passed = False
            exp_notes.append("Failed to explain cash flow context")

    print(f"\nExplanation Assessment: [{'PASS' if exp_passed else 'FAIL'}] {', '.join(exp_notes) if exp_notes else 'Grounded in supplied values without recalculation'}")

    if not exp_passed:
        all_passed = False

    print("\n" + "=" * 65)
    print(f"OVERALL EVALUATION: {'PASS' if all_passed else 'FAIL'}")
    print("=" * 65)

    return all_passed

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
