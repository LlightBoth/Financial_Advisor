"""
Standalone Model Merging Script for Financial Advisor AI v1.

Merges the base model (Qwen/Qwen2.5-1.5B-Instruct) with the trained LoRA adapter
(training/output/financial_advisor_ai_v1) into a single, standalone set of weights.

Output directories:
- training/output/financial_advisor_ai_v1_merged/
- training/huggingface/financial_advisor_ai_v1_merged/

Preserves:
- Native precision (bfloat16)
- Standard Transformers/Safetensors format
- Full tokenizer and generation configurations
"""

import os
import shutil
import hashlib
import time
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

BASE_DIR = r"d:\Year3\Finance\Financial_Advisor"
BASE_MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"
ADAPTER_DIR = os.path.join(BASE_DIR, "training", "output", "financial_advisor_ai_v1")
OUTPUT_MERGED_DIR = os.path.join(BASE_DIR, "training", "output", "financial_advisor_ai_v1_merged")
HF_MERGED_DIR = os.path.join(BASE_DIR, "training", "huggingface", "financial_advisor_ai_v1_merged")

def get_file_hash(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192 * 1024):
            h.update(chunk)
    return h.hexdigest(), os.path.getsize(filepath)

def main():
    print("=" * 70)
    print("FINANCIAL ADVISOR AI v1 - STANDALONE MODEL MERGE")
    print("=" * 70)

    # 1. Record pre-merge adapter hash
    adapter_weights = os.path.join(ADAPTER_DIR, "adapter_model.safetensors")
    pre_hash, pre_size = get_file_hash(adapter_weights)
    print(f"Source adapter: {ADAPTER_DIR}")
    print(f"Source adapter weights size: {pre_size:,} bytes")
    print(f"Source adapter SHA256: {pre_hash}")
    print("-" * 70)

    # 2. Create output directories
    os.makedirs(OUTPUT_MERGED_DIR, exist_ok=True)
    os.makedirs(HF_MERGED_DIR, exist_ok=True)

    # 3. Load Tokenizer
    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(ADAPTER_DIR)

    # 4. Load Base Model
    print(f"Loading base model ({BASE_MODEL_ID}) in bfloat16...")
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_ID,
        torch_dtype=torch.bfloat16,
        device_map=device,
    )
    print(f"Base model loaded on {device}.")

    # 5. Attach LoRA Adapter
    print(f"Attaching LoRA adapter from {ADAPTER_DIR}...")
    lora_model = PeftModel.from_pretrained(base_model, ADAPTER_DIR)

    # 6. Merge weights
    print("Merging adapter weights into base model (merge_and_unload)...")
    start_time = time.time()
    merged_model = lora_model.merge_and_unload()
    elapsed = time.time() - start_time
    print(f"Merge completed in {elapsed:.2f} seconds.")

    # 7. Save standalone model to OUTPUT_MERGED_DIR
    print(f"Saving merged model to {OUTPUT_MERGED_DIR}...")
    merged_model.save_pretrained(OUTPUT_MERGED_DIR, safe_serialization=True)
    tokenizer.save_pretrained(OUTPUT_MERGED_DIR)

    # Copy chat_template.jinja if present
    src_chat_jinja = os.path.join(ADAPTER_DIR, "chat_template.jinja")
    if os.path.exists(src_chat_jinja):
        shutil.copy2(src_chat_jinja, os.path.join(OUTPUT_MERGED_DIR, "chat_template.jinja"))

    print("OUTPUT_MERGED_DIR contents:", os.listdir(OUTPUT_MERGED_DIR))

    # 8. Copy to HF_MERGED_DIR
    print(f"Populating Hugging Face package directory at {HF_MERGED_DIR}...")
    for item in os.listdir(OUTPUT_MERGED_DIR):
        s = os.path.join(OUTPUT_MERGED_DIR, item)
        d = os.path.join(HF_MERGED_DIR, item)
        if os.path.isfile(s):
            shutil.copy2(s, d)
    print("HF_MERGED_DIR contents:", os.listdir(HF_MERGED_DIR))

    # 9. Verify source adapter remains untouched
    post_hash, post_size = get_file_hash(adapter_weights)
    print("-" * 70)
    print(f"Source adapter post-merge size: {post_size:,} bytes")
    print(f"Source adapter post-merge SHA256: {post_hash}")
    adapter_untouched = (pre_hash == post_hash and pre_size == post_size)
    print(f"Source adapter untouched: {adapter_untouched}")

    # Calculate merged disk size
    total_bytes = sum(os.path.getsize(os.path.join(OUTPUT_MERGED_DIR, f)) for f in os.listdir(OUTPUT_MERGED_DIR) if os.path.isfile(os.path.join(OUTPUT_MERGED_DIR, f)))
    print(f"Merged model total size: {total_bytes / (1024**3):.2f} GB ({total_bytes:,} bytes)")
    print("=" * 70)

if __name__ == "__main__":
    main()
