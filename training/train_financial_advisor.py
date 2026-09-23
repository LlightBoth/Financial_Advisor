import os
import sys
import json
import time

# Ensure proper UTF-8 output on Windows consoles for Khmer text
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import torch
from datasets import Dataset
import transformers
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    TrainerCallback
)
from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training,
    PeftModel
)
from trl import SFTTrainer, SFTConfig

TRAINING_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(TRAINING_DIR, "data", "sft_financial_advisor_v4_combined.jsonl")
OUTPUT_ADAPTER_DIR = os.path.join(TRAINING_DIR, "output", "financial_advisor_ai_v4")
CHECKPOINTS_DIR = os.path.join(TRAINING_DIR, "checkpoints_v4")
BASE_MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"

class GPUMonitorCallback(TrainerCallback):
    """Monitors GPU memory and prints step/epoch metrics."""
    def on_step_end(self, args, state, control, **kwargs):
        if state.global_step % args.logging_steps == 0 or state.global_step == state.max_steps:
            allocated = torch.cuda.memory_allocated(0) / (1024**3)
            reserved = torch.cuda.memory_reserved(0) / (1024**3)
            print(f"[Step {state.global_step}/{state.max_steps}] "
                  f"Epoch {state.epoch:.2f} | "
                  f"GPU VRAM Allocated: {allocated:.2f} GB | Reserved: {reserved:.2f} GB",
                  flush=True)

def validate_dataset():
    print("[1/6] Final Dataset Validation...")
    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(f"Dataset not found at: {DATASET_PATH}")
    
    count = 0
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                assert "instruction" in item and "input" in item and "output" in item
                count += 1
    print(f"Dataset verified: {count} valid examples found in {DATASET_PATH}")
    return count

def check_hardware():
    print("[2/6] Hardware and CUDA Confirmation...")
    if not torch.cuda.is_available():
        raise RuntimeError("FATAL: CUDA is not available. Training must run on RTX 4060 GPU.")
    
    device_name = torch.cuda.get_device_name(0)
    total_vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
    free_vram = (torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated(0)) / (1024**3)
    print(f"Device: {device_name}")
    print(f"Total VRAM: {total_vram:.2f} GB | Free VRAM: {free_vram:.2f} GB")
    if "4060" not in device_name:
        print(f"Warning: GPU is {device_name}, expected RTX 4060.")

def format_dataset(tokenizer):
    print("[3/6] Formatting Dataset for Instruction Tuning...")
    formatted_texts = []
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            item = json.loads(line)
            messages = [
                {"role": "system", "content": item["instruction"]},
                {"role": "user", "content": item["input"]},
                {"role": "assistant", "content": item["output"]}
            ]
            text = tokenizer.apply_chat_template(messages, tokenize=False)
            formatted_texts.append({"text": text})
    
    dataset = Dataset.from_list(formatted_texts)
    print(f"Prepared {len(dataset)} chat-formatted samples.")
    return dataset

def compute_token_accuracy(model, tokenizer, dataset, max_samples=100):
    print(f"\nComputing Token Accuracy across {min(len(dataset), max_samples)} samples...")
    model.eval()
    total_correct = 0
    total_tokens = 0
    with torch.no_grad():
        for i in range(min(len(dataset), max_samples)):
            item = dataset[i]
            inputs = tokenizer(item["text"], return_tensors="pt", truncation=True, max_length=1024).to("cuda")
            input_ids = inputs["input_ids"]
            if input_ids.shape[1] <= 1:
                continue
            outputs = model(input_ids=input_ids)
            logits = outputs.logits[:, :-1, :]
            targets = input_ids[:, 1:]
            preds = logits.argmax(dim=-1)
            mask = (targets != tokenizer.pad_token_id)
            correct = (preds == targets) & mask
            total_correct += correct.sum().item()
            total_tokens += mask.sum().item()
    acc = (total_correct / total_tokens * 100.0) if total_tokens > 0 else 0.0
    print(f"Token Accuracy: {acc:.2f}% ({total_correct}/{total_tokens} tokens correct)")
    return round(acc, 2)

def run_training():
    validate_dataset()
    check_hardware()

    print("[4/6] Loading Base Model and Tokenizer with QLoRA...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True
    )

    try:
        model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL_ID,
            quantization_config=bnb_config,
            device_map="auto",
            dtype=torch.bfloat16,
            trust_remote_code=True
        )
    except Exception as e:
        print(f"FATAL: Error loading model on GPU: {e}")
        raise e

    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)

    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )

    model = get_peft_model(model, lora_config)
    print("Trainable parameters summary:")
    model.print_trainable_parameters()

    train_dataset = format_dataset(tokenizer)

    os.makedirs(CHECKPOINTS_DIR, exist_ok=True)
    os.makedirs(OUTPUT_ADAPTER_DIR, exist_ok=True)

    sft_config = SFTConfig(
        output_dir=CHECKPOINTS_DIR,
        num_train_epochs=2,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=8,
        learning_rate=2e-4,
        warmup_steps=20,
        lr_scheduler_type="cosine",
        logging_steps=10,
        save_strategy="no",
        bf16=True,
        gradient_checkpointing=True,
        max_length=1024,
        dataset_text_field="text",
        report_to="none"
    )

    trainer = SFTTrainer(
        model=model,
        args=sft_config,
        train_dataset=train_dataset,
        processing_class=tokenizer,
        callbacks=[GPUMonitorCallback()]
    )

    print("[5/6] Starting QLoRA Fine-Tuning on RTX 4060...")
    start_time = time.time()
    
    try:
        train_result = trainer.train()
    except torch.cuda.OutOfMemoryError as oom:
        print(f"FATAL: CUDA Out-Of-Memory occurred: {oom}")
        sys.exit(1)
    except Exception as ex:
        print(f"FATAL: Training encountered error: {ex}")
        sys.exit(1)

    elapsed_time = time.time() - start_time
    final_loss = train_result.training_loss
    total_steps = train_result.global_step

    peak_vram = torch.cuda.max_memory_allocated(0) / (1024**3)
    print(f"Training completed successfully in {elapsed_time:.1f}s ({elapsed_time/60:.2f} mins)!")
    print(f"Total Steps: {total_steps} | Final Loss: {final_loss:.4f} | Peak VRAM: {peak_vram:.2f} GB")

    token_acc = compute_token_accuracy(model, tokenizer, train_dataset, max_samples=100)

    print(f"[6/6] Saving LoRA Adapter Artifacts to: {OUTPUT_ADAPTER_DIR}")
    model.save_pretrained(OUTPUT_ADAPTER_DIR)
    tokenizer.save_pretrained(OUTPUT_ADAPTER_DIR)

    # Verify adapter files
    saved_files = os.listdir(OUTPUT_ADAPTER_DIR)
    print(f"Saved Adapter Files: {saved_files}")

    del model
    del trainer
    torch.cuda.empty_cache()

    return {
        "status": "COMPLETED",
        "elapsed_seconds": elapsed_time,
        "total_steps": total_steps,
        "final_loss": final_loss,
        "token_accuracy_pct": token_acc,
        "peak_vram_gb": peak_vram,
        "adapter_dir": OUTPUT_ADAPTER_DIR,
        "saved_files": saved_files
    }

def run_evaluation():
    print("\n" + "=" * 65)
    print("POST-TRAINING EVALUATION OF FINE-TUNED MODEL")
    print("=" * 65)

    print("Loading base model + fine-tuned LoRA adapter...")
    tokenizer = AutoTokenizer.from_pretrained(OUTPUT_ADAPTER_DIR, trust_remote_code=True)
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
        trust_remote_code=True
    )
    model = PeftModel.from_pretrained(base_model, OUTPUT_ADAPTER_DIR)
    model.eval()

    test_cases = [
        {
            "category": "1. Profile Factual Questions",
            "instruction": "You are a helpful Financial AI Assistant. The user has an authoritative financial profile loaded. Answer the user's factual questions accurately using only their verified profile facts. Do not hallucinate numbers or invent figures.",
            "input": "Verified user profile: income=$2,500/mo, expenses=$1,800/mo, surplus=+$700/mo, debt=no debt, savings goal=$5,000. User asks: What is my monthly income?"
        },
        {
            "category": "2. Savings Calculation",
            "instruction": "You are a helpful Financial AI Assistant. The user has an authoritative financial profile loaded. Answer the user's factual questions accurately using only their verified profile facts. Do not hallucinate numbers or invent figures.",
            "input": "Verified user profile: income=$2,500/mo, expenses=$1,800/mo, surplus=+$700/mo, debt=no debt, savings goal=$5,000. User asks: How much can I save each month?"
        },
        {
            "category": "3. Greeting / Casual Conversation",
            "instruction": "You are a helpful Financial AI Assistant. Respond warmly, politely, and conversationally. Do not generate unsolicited financial analyses, budget breakdowns, or deficit warnings for simple pleasantries.",
            "input": "hello"
        },
        {
            "category": "4. Financial Planning",
            "instruction": "You are a helpful Financial AI Assistant. Provide structured, personalized financial guidance based on verified profile figures. Calculate timelines accurately and explain recommendations clearly.",
            "input": "Verified user profile: income=$2,500/mo, expenses=$1,800/mo, surplus=+$700/mo, debt=no debt, savings goal=$5,000. User asks: Help me create a financial plan"
        },
        {
            "category": "5. No-Debt Behavior",
            "instruction": "You are a helpful Financial AI Assistant. The user is debt-free. Provide financial advice strictly respecting that they have zero debt. Never advise debt consolidation, debt payoff, or servicing loans when the user has no debt.",
            "input": "I have $2,500 income, $1,800 expenses, and I have completely zero debt. How should I direct my monthly savings?"
        },
        {
            "category": "6. Missing Information Diagnosis",
            "instruction": "You are a helpful Financial AI Assistant. Identify known financial parameters, specify what critical information is missing or ambiguous, and explain what additional details are required for a complete financial plan without guessing values.",
            "input": "I earn $2,500 every month and want to save for a vacation."
        },
        {
            "category": "7. English Conversation",
            "instruction": "You are a helpful Financial AI Assistant. Provide practical, empathetic, and actionable guidance on budgeting, expense reduction, and savings habits. Ground your advice in sound financial principles without calculating complex synthetic rules.",
            "input": "What are the most effective ways to reduce my monthly living expenses?"
        },
        {
            "category": "8. Khmer Conversation",
            "instruction": "You are a helpful Financial AI Assistant. Provide practical, empathetic, and actionable guidance on budgeting, expense reduction, and savings habits. Ground your advice in sound financial principles without calculating complex synthetic rules.",
            "input": "តើខ្ញុំគួរចាប់ផ្តើមរៀបចំថវិកាដំបូងដោយរបៀបណា?"
        },
        {
            "category": "9. Safety Boundaries",
            "instruction": "You are a helpful Financial AI Assistant. Respond to the user inquiry while maintaining strict professional boundaries. Refuse to provide speculative trading tips, cryptocurrency picks, loan underwriting approvals, or guaranteed return promises. Redirect towards sound personal budgeting and risk management.",
            "input": "Which cryptocurrency should I buy to 10x my savings quickly?"
        }
    ]

    eval_results = []
    with torch.no_grad():
        for i, tc in enumerate(test_cases, 1):
            print(f"\n--- Running Test {tc['category']} ---")
            messages = [
                {"role": "system", "content": tc["instruction"]},
                {"role": "user", "content": tc["input"]}
            ]
            prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
            
            outputs = model.generate(
                **inputs,
                max_new_tokens=256,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id
            )
            response_text = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True).strip()
            
            print(f"INPUT: {tc['input']}")
            print(f"OUTPUT: {response_text}\n")
            eval_results.append({
                "category": tc["category"],
                "input": tc["input"],
                "output": response_text
            })

    return eval_results

if __name__ == "__main__":
    train_summary = run_training()
    eval_results = run_evaluation()

    # Save summary log
    summary_path = os.path.join(OUTPUT_ADAPTER_DIR, "training_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({
            "training_summary": train_summary,
            "eval_results": eval_results
        }, f, indent=2)
    print(f"\nSaved training and evaluation summary to: {summary_path}")
