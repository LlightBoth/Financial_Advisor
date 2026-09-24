# 💰 Financial Advisor AI

An intelligent financial advisor web application built with Python (Flask), Bootstrap, and fine-tuned Local LLM (Qwen2.5-1.5B with LoRA).

It helps users manage their finances by analyzing income and expenses, tracking budgets, generating personalized 50/30/20 financial plans, and offering bilingual (English & Khmer) financial guidance.

---

## 🚀 Quick Start Guide (For Friends & Evaluators)

### 1. Prerequisites
- **Python**: Version 3.10, 3.11, or 3.12 *(Recommended: Python 3.11 or 3.10; PyTorch does not support 3.14 yet)*
- **Git**: Installed on your system

### 2. Clone the Repository
```bash
git clone https://github.com/LlightBoth/Financial_Consultant.git
cd Financial_Advisor
```

### 3. Create & Activate Virtual Environment

1. **Create the environment**:
   ```bash
   python -m venv .venv
   ```

2. **Activate the environment**:
   * **Windows (Git Bash):**
     ```bash
     source .venv/Scripts/activate
     ```
   * **Windows (PowerShell):**
     ```powershell
     # If script execution is blocked on your system, allow it for this session:
     Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
     .\.venv\Scripts\Activate.ps1
     ```
   * **Windows (Command Prompt):**
     ```cmd
     .venv\Scripts\activate
     ```
   * **macOS / Linux:**
     ```bash
     source .venv/bin/activate
     ```
   > *(You should see `(.venv)` appear at the beginning of your terminal prompt when activated).*

### 4. Install Dependencies
```bash
# 1. Install Web Application dependencies
pip install -r requirements.txt

# 2. Install Local LLM AI dependencies (REQUIRED to run the AI model server)
pip install -r requirements-llm.txt
```
*(If you do not install `requirements-llm.txt`, you will see `ModuleNotFoundError: No module named 'torch'` when starting the AI server).*

### 5. Start the Full System (Two Terminals)
> **Important**: Activate your virtual environment (`.venv`) in **both** terminal tabs before running!

#### 🔹 Terminal 1: Run the Local LLM AI Server
```bash
python training/serve_llm.py
```
* **Port**: `http://127.0.0.1:5006`
* Loads your trained **Financial Consultant AI LoRA v4** model (`training/output/financial_advisor_ai_v4/`).
* On first run, it auto-downloads the base `Qwen/Qwen2.5-1.5B-Instruct` model from Hugging Face.
* Runs on NVIDIA GPU (CUDA ~1.1 GB VRAM) or automatically falls back to CPU.

#### 🔹 Terminal 2: Run the Web Application
```bash
python run.py
```
* Open your browser and go to: **`http://127.0.0.1:5005`**
* The database, rules, and facts **auto-seed on first launch**.
* When you chat with the bot, it connects directly to the local LLM server in Terminal 1 for real-time AI responses!

*(Note: If you only run Terminal 2 without Terminal 1, the app still works using the built-in deterministic rule engine).*

---

## 🧠 AI Consultant Architecture

The system operates under a strict, safety-first hybrid architecture:

**User Input → Trained Financial Consultant AI → Output Normalization & Validation → ConsultantEngine → Deterministic Financial Recommendation → Financial Consultant AI Explanation → User Interface**

### Core Architectural Principles:
1. **Fact Extraction**: The **Financial Consultant AI** extracts financial facts and user goals from natural-language input.
2. **Deterministic Normalization**: The **Output Normalizer & Validator** validates, bounds, and protects the extracted information.
3. **Authoritative Decisioning**: **ConsultantEngine** performs the authoritative deterministic financial evaluation using formal financial rules and verified knowledge bases.
4. **Natural-Language Synthesis**: The **Financial Consultant AI** generates a user-friendly explanation of the verified recommendation.
5. **Strict Safety Boundary**: The AI cannot override ConsultantEngine's deterministic recommendations or give speculative investment advice.

---

## 📂 Project Structure

```text
Financial_Advisor/
├── app/
│   ├── models/         # ORM models (User, AIChat, History, Rule, Fact)
│   ├── routes/         # Blueprints (bot_route, advisor_route, auth_route, etc.)
│   ├── security/       # Seed scripts, rate limiter, cookie tokens
│   ├── services/       # ConsultantEngine, LLMService, AdvisorServices
│   ├── static/         # CSS, JS, branding assets
│   ├── templates/      # Jinja2 HTML templates (landing, bots, advisors, etc.)
│   └── translations/   # Khmer and English localization dictionaries
├── config.py           # Application configuration
├── requirements.txt    # Web application dependencies
├── requirements-llm.txt# Local LLM dependencies
├── run.py              # Application entrypoint
└── training/
    ├── data/            # SFT dataset JSONL files & financial domain knowledge
    ├── pipelines/       # Dataset synthesis & validation pipelines
    ├── benchmarks/      # Model verification & evaluation benchmarks
    ├── output/          # Fine-tuned LoRA adapter weights (35MB)
    │   └── financial_advisor_ai_v4/
    ├── llm_output_normalizer.py # Safe input/output normalization & regex engine
    ├── serve_llm.py     # Model server with automatic GPU/CPU fallback
    └── train_financial_advisor.py # QLoRA fine-tuning script
```
