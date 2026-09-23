import sys
import os
import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

BASE_MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"
ADAPTER_DIR = r"d:\Year3\Finance\Financial_Advisor\training\output\financial_advisor_ai_v1"

sys.path.insert(0, r"d:\Year3\Finance\Financial_Advisor")
from training.llm_output_normalizer import normalize_llm_output

def test_primitives():
    print("Testing primitive loading...")
    tokenizer = AutoTokenizer.from_pretrained(ADAPTER_DIR, local_files_only=True, trust_remote_code=True)
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

    # Test prompt 1: Extraction
    instruction = "Extract the user's financial profile from the provided text into a JSON object with keys: monthly_income, monthly_expense, goal_cost, employment_status, debt_status, spending_habit, marital_status. Set unmentioned fields to null. Do not invent values."
    user_input = "I take home $4,200 each month, usually spend around $2,750, and I want to save $8,000 for an emergency reserve. I am married and currently employed."
    
    messages = [
        {"role": "system", "content": instruction},
        {"role": "user", "content": user_input}
    ]
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
    
    with torch.no_grad():
        outputs = model.generate(**inputs, max_new_tokens=150, do_sample=False, pad_token_id=tokenizer.eos_token_id)
    raw_out = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True).strip()
    print("Raw Extraction Output:", raw_out)
    
    norm = normalize_llm_output(raw_out, user_input)
    print("Normalized:", json.dumps(norm, indent=2))
    assert norm["monthly_income"] == 4200.0
    assert norm["monthly_expense"] == 2750.0
    assert norm["goal_cost"] == 8000.0
    assert norm["marital_status"] == "Married"
    assert norm["employment_status"] == "employed"
    print("PRIMITIVES TEST PASSED!")

if __name__ == "__main__":
    test_primitives()
