# Financial Consultant AI — Model Training & Inference

This directory contains the machine learning pipelines, fine-tuning scripts, SFT training datasets, evaluation benchmarks, and the local inference server for the **Financial Consultant AI**.

---

## 📂 Directory Structure

```text
training/
├── data/                       # SFT dataset JSONL files and extracted financial domain knowledge
│   ├── sft_financial_advisor_v4_combined.jsonl       # Active v4 fine-tuning dataset (5,000 samples)
│   ├── sft_financial_advisor_v4_conversational.jsonl # Conversational & intent-classification dataset
│   ├── sft_financial_advisor_v4_expansion.jsonl      # Expanded financial scenarios dataset
│   ├── sft_financial_advisor_v3_combined.jsonl       # Milestone v3 baseline dataset
│   ├── sft_financial_advisor_v2_combined.jsonl       # Milestone v2 baseline dataset
│   ├── sft_financial_advisor_pdf_v1.jsonl            # Financial textbook SFT extractions
│   ├── pdf_knowledge_extracted.json                  # Domain knowledge extraction from textbook
│   └── v2_vs_v4_comparison_report.json               # Benchmark comparison report
│
├── pipelines/                  # Automated dataset synthesis and validation scripts
│   ├── build_v4_conversational_dataset.py # Generates conversational & intent-labeled samples
│   ├── build_v4_expansion_dataset.py      # Synthesizes edge cases and multilingual variants
│   ├── build_combined_sft_dataset.py      # Merges multi-source SFT datasets
│   ├── validate_v4_dataset.py             # Schema & token count validation for v4
│   └── validate_pdf_dataset.py            # PDF extraction quality audits
│
├── benchmarks/                 # Verification, benchmarking & regression test scripts
│   ├── compare_v2_v4_models.py            # Side-by-side evaluation of model generations
│   ├── test_llm_output_normalizer.py      # Unit tests for text normalization
│   ├── test_server_endpoints.py           # Integration tests for server REST endpoints
│   ├── verify_integration_tests.py        # End-to-end NLU verification
│   └── verify_local_inference.py          # Checks local model generation latency & accuracy
│
├── output/                     # Trained LoRA adapters
│   └── financial_advisor_ai_v4/           # ACTIVE PRODUCTION LoRA ADAPTER (~35 MB)
│       ├── adapter_model.safetensors      # LoRA weights (tracked in Git)
│       ├── adapter_config.json            # LoRA configuration (r=16, alpha=32, target_modules)
│       ├── tokenizer.json                 # Fast tokenizer dictionary
│       └── training_summary.json          # Loss curves and training metadata
│
├── llm_output_normalizer.py    # Production text parser, intent classifier, safety boundaries & Khmer sanitizer
├── serve_llm.py                # Production local inference server with automatic CUDA/CPU fallback (port 5006)
├── train_financial_advisor.py  # 4-bit QLoRA fine-tuning script using TRL / SFTTrainer
└── merge_financial_advisor_ai.py # Script to merge LoRA adapter into 16-bit standalone base model
```

---

## 🚀 Running the Local Model Server

To start the model inference server:
```bash
python training/serve_llm.py
```

* **Base Model**: `Qwen/Qwen2.5-1.5B-Instruct` (auto-downloaded from Hugging Face if not cached).
* **Adapter**: `training/output/financial_advisor_ai_v4/` (included directly in repository).
* **Hardware Support**:
  1. NVIDIA GPU (CUDA) using 4-bit BitsAndBytes quantization (~1.14 GB VRAM allocated).
  2. Fallback to 16-bit GPU if 4-bit is unavailable.
  3. Automatic CPU fallback (float32) if no NVIDIA GPU is detected.
* **Port**: `http://127.0.0.1:5006`

---

## 🛠️ Re-training or Fine-Tuning the Model

If you want to train the model on updated financial datasets:
```bash
# 1. Install training dependencies
pip install -r requirements-llm.txt

# 2. Run QLoRA training
python training/train_financial_advisor.py
```


Searched for "cloudflared"
Searched for "trycloudflare"
Ran command: `Test-Path "d:\Year3\Finance\Financial_Advisor\.venv_train"`

Here is the complete setup to run `serve_llm.py` on **Google Colab** (with Cloudflare tunnel) as well as **locally on your PC**.

---

### Option A: Running on Google Colab (Step-by-Step)

Copy and run these cells one by one in your Google Colab notebook:

#### Cell 1: Clone Repository and Enter Directory
```python
!git clone https://github.com/LlightBoth/Financial_Advisor.git
%cd /content/Financial_Advisor
```

#### Cell 2: Install AI Dependencies & Cloudflare Tunnel
```python
!pip install -r requirements-llm.txt
!wget -q -nc https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
!dpkg -i cloudflared-linux-amd64.deb
```

#### Cell 3: Start Cloudflare Tunnel (to get public URL)
```python
import subprocess, time, re

# Launch tunnel on port 5006 in background
process = subprocess.Popen(
    ["cloudflared", "tunnel", "--url", "http://127.0.0.1:5006"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

# Extract and print tunnel URL
time.sleep(4)
for _ in range(25):
    line = process.stdout.readline()
    match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
    if match:
        print("\n" + "=" * 55)
        print("🔗 YOUR CLOUDFLARE URL:")
        print(match.group(0))
        print("=" * 55 + "\n")
        break
```

#### Cell 4: Start the LLM Inference Server
```python
!python training/serve_llm.py
```

> [!IMPORTANT]
> Copy the generated URL (e.g. `https://xxxx.trycloudflare.com`) and paste it into your local [`.env`](file:///d:/Year3/Finance/Financial_Advisor/.env#L7) file:
> ```env
> LLM_SERVER_URL=https://your-generated-url.trycloudflare.com
> ```

---